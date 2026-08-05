"""Inbound n8n webhook receiver — closes the automation loop.

n8n workflows (email sending, calendar booking, enrichment, ...) call these
endpoints to report results back to the platform. Each inbound event is:

  1. authenticated (API key bearer, or X-N8N-Secret when configured)
  2. recorded in the audit trail (actor = "n8n")
  3. applied to CRM state where it has a concrete meaning
     (e.g. a reply bumps the lead score, a booked meeting qualifies the contact)
  4. republished on the internal EventBus so workflows can react

Configure n8n with an HTTP Request node pointing at:
    POST {platform}/webhooks/n8n/{event_name}
"""

from __future__ import annotations

import logging
import os
import uuid as uuid_lib
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException

from revenue_os.automation.events import Event, EventBus, EventPriority, EventType
from revenue_os.database import SessionLocal
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.services.activity_log import log_agent_action
from runner_api_routers.utils import _get_runner_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/n8n", tags=["n8n"])

REPLY_SCORE_BOOST = 10

# Inbound events the platform understands, and what it does with them.
INBOUND_CATALOG: dict[str, str] = {
    "email.sent": "Logged to audit trail",
    "email.delivered": "Logged to audit trail",
    "email.opened": "Logged; republished as outreach signal",
    "email.clicked": "Logged; republished as outreach signal",
    "email.replied": f"Contact lead_score +{REPLY_SCORE_BOOST}; lead_scored event emitted",
    "email.bounced": "Logged to audit trail",
    "meeting.booked": "Contact status -> qualified; lead_qualified event emitted",
    "enrichment.completed": "contact_enriched event emitted with payload",
    "workflow.completed": "Logged to audit trail (generic n8n workflow result)",
    "workflow.failed": "Logged to audit trail with failed status",
}

# Outbound webhooks the platform fires (documented for building the n8n side).
OUTBOUND_CATALOG: dict[str, str] = {
    "new-lead": "Fired when a contact is created (event: contact.created)",
    "new-deal": "Fired when a deal is created (event: deal.created)",
    "deal-stage-changed": "Fired when a deal changes stage (event: deal.stage_changed)",
    "revenue-os-events": "Generic bridge: qualified leads, at-risk/closed deals",
}


def _verify_n8n_auth(
    authorization: str | None = Header(default=None),
    x_n8n_secret: str | None = Header(default=None),
) -> str:
    """Accept the platform API key (Bearer) or a dedicated n8n shared secret."""
    inbound_secret = os.environ.get("N8N_INBOUND_SECRET", "")
    if inbound_secret and x_n8n_secret == inbound_secret:
        return "n8n-secret"

    expected = _get_runner_api_key()
    if expected:
        if authorization == f"Bearer {expected}":
            return "api-key"
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # No API key configured on the platform (open/dev mode)
    return "open"


def _load_contact(db, contact_id: str) -> Contact | None:
    try:
        return db.get(Contact, uuid_lib.UUID(str(contact_id)))
    except (ValueError, TypeError):
        return None


def _publish(event_type: EventType, entity_id: str, entity_type: str, data: dict[str, Any]) -> None:
    """Republish an inbound n8n result on the internal event bus."""
    EventBus.publish(Event(
        event_type=event_type,
        source="n8n_inbound",
        entity_id=entity_id,
        entity_type=entity_type,
        priority=EventPriority.HIGH,
        data={**data, "origin": "n8n"},
    ))


@router.get("/catalog")
def n8n_catalog() -> dict[str, Any]:
    """Reference for building n8n workflows against this platform."""
    return {
        "ok": True,
        "inbound": {
            "url_pattern": "POST /webhooks/n8n/{event_name}",
            "auth": "Authorization: Bearer <api key>  OR  X-N8N-Secret: <N8N_INBOUND_SECRET>",
            "common_fields": {"contact_id": "UUID (optional)", "deal_id": "UUID (optional)"},
            "events": INBOUND_CATALOG,
        },
        "outbound": {
            "base_url_env": "N8N_WEBHOOK_BASE_URL",
            "webhooks": OUTBOUND_CATALOG,
        },
    }


@router.post("/{event_name}")
def receive_n8n_event(
    event_name: str,
    payload: dict[str, Any] = Body(default={}),
    _auth: str = Depends(_verify_n8n_auth),
) -> dict[str, Any]:
    """Receive a result event from an n8n workflow and apply it."""
    if event_name not in INBOUND_CATALOG:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown event '{event_name}'. Accepted: {sorted(INBOUND_CATALOG)}",
        )

    contact_id = str(payload.get("contact_id") or "")
    actions: list[str] = []
    status = "completed"

    db = SessionLocal()
    try:
        if event_name == "email.replied" and contact_id:
            contact = _load_contact(db, contact_id)
            if contact is not None:
                old_score = contact.lead_score or 0
                contact.lead_score = old_score + REPLY_SCORE_BOOST
                db.commit()
                actions.append(f"lead_score {old_score} -> {contact.lead_score}")
                _publish(EventType.LEAD_SCORED, contact_id, "contact", {
                    "score": contact.lead_score, "old_score": old_score, "reason": "email_reply",
                })
            else:
                actions.append("contact not found; logged only")

        elif event_name == "meeting.booked" and contact_id:
            contact = _load_contact(db, contact_id)
            if contact is not None:
                old_status = contact.status.value if contact.status else None
                contact.status = ContactStatus.QUALIFIED
                db.commit()
                actions.append(f"status {old_status} -> qualified")
                _publish(EventType.LEAD_QUALIFIED, contact_id, "contact", {
                    "old_status": old_status, "reason": "meeting_booked",
                    "meeting": payload.get("meeting", {}),
                })
            else:
                actions.append("contact not found; logged only")

        elif event_name == "enrichment.completed" and contact_id:
            _publish(EventType.CONTACT_ENRICHED, contact_id, "contact", payload)
            actions.append("contact_enriched event emitted")

        elif event_name in ("email.opened", "email.clicked"):
            if contact_id:
                _publish(EventType.OUTREACH_COMPLETED, contact_id, "contact", {
                    "signal": event_name, **payload,
                })
            actions.append("outreach signal recorded")

        elif event_name == "workflow.failed":
            status = "failed"
            actions.append("n8n workflow failure recorded")

        else:
            actions.append("logged")
    finally:
        db.close()

    log_agent_action(
        actor="n8n",
        action_type=event_name,
        target_type="contact" if contact_id else None,
        target_id=contact_id or None,
        status=status,
        detail={"payload": payload, "actions": actions},
    )
    logger.info(f"n8n inbound: {event_name} -> {actions}")
    return {"ok": status == "completed", "event": event_name, "actions": actions}
