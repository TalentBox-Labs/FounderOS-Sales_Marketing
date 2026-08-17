"""Inbound n8n webhook receiver — closes the automation loop.

S4: organization resolved from trusted integration binding (X-N8N-Secret),
never from payload contact_id/deal_id. Object IDs validated within org scope.
"""

from __future__ import annotations

import logging
import os
import uuid as uuid_lib
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException

from revenue_os.automation.events import Event, EventBus, EventPriority, EventType
from revenue_os.database import SessionLocal
from revenue_os.models.contact import Contact
from revenue_os.services.activity_log import log_agent_action
from revenue_os.services.integration_tenant_resolution import (
    build_integration_tenant_context,
    resolve_n8n_organization_id,
)
from revenue_os.services.tenant_mutation_guard import scoped_contact
from revenue_os.services.tenant_scoped_access import stamp_agent_action_log_organization
from runner_api_routers.utils import _get_runner_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/n8n", tags=["n8n"])

REPLY_SCORE_BOOST = 10

INBOUND_CATALOG: dict[str, str] = {
    "email.sent": "Logged to audit trail",
    "email.delivered": "Logged to audit trail",
    "email.opened": "Logged; republished as outreach signal",
    "email.clicked": "Logged; republished as outreach signal",
    "email.replied": f"Contact lead_score +{REPLY_SCORE_BOOST}; lead_scored event emitted",
    "email.bounced": "Logged to audit trail",
    "meeting.booked": "Recommendation logged; human gate required for Contact.status qualify",
    "enrichment.completed": "contact_enriched event emitted with payload",
    "workflow.completed": "Logged to audit trail (generic n8n workflow result)",
    "workflow.failed": "Logged to audit trail with failed status",
}

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

    return "open"


def _legacy_load_contact(db, contact_id: str) -> Contact | None:
    try:
        return db.get(Contact, uuid_lib.UUID(str(contact_id)))
    except (ValueError, TypeError):
        return None


def _resolve_scoped_contact(
    db,
    contact_id: str,
    *,
    organization_id: str | None,
    x_n8n_secret: str | None,
) -> Contact | None:
    if not contact_id:
        return None
    if organization_id is not None:
        tenant = build_integration_tenant_context(organization_id)
        try:
            return scoped_contact(db, tenant, contact_id)
        except HTTPException:
            return None
    if x_n8n_secret and resolve_n8n_organization_id(x_n8n_secret=x_n8n_secret):
        return None
    return _legacy_load_contact(db, contact_id)


def _publish(event_type: EventType, entity_id: str, entity_type: str, data: dict[str, Any]) -> None:
    EventBus.publish(
        Event(
            event_type=event_type,
            source="n8n_inbound",
            entity_id=entity_id,
            entity_type=entity_type,
            priority=EventPriority.HIGH,
            data={**data, "origin": "n8n"},
        )
    )


@router.get("/catalog")
def n8n_catalog() -> dict[str, Any]:
    return {
        "ok": True,
        "inbound": {
            "url_pattern": "POST /webhooks/n8n/{event_name}",
            "auth": "Authorization: Bearer <api key>  OR  X-N8N-Secret: <bound secret>",
            "tenant_binding": "Organization resolved from X-N8N-Secret binding — never from contact_id",
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
    x_n8n_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    if event_name not in INBOUND_CATALOG:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown event '{event_name}'. Accepted: {sorted(INBOUND_CATALOG)}",
        )

    organization_id = resolve_n8n_organization_id(x_n8n_secret=x_n8n_secret)
    if payload.get("organization_id") or payload.get("tenant_id"):
        pass

    contact_id = str(payload.get("contact_id") or "")
    actions: list[str] = []
    status = "completed"

    db = SessionLocal()
    try:
        if event_name == "email.replied" and contact_id:
            contact = _resolve_scoped_contact(
                db, contact_id, organization_id=organization_id, x_n8n_secret=x_n8n_secret
            )
            if contact is not None:
                old_score = contact.lead_score or 0
                contact.lead_score = old_score + REPLY_SCORE_BOOST
                from revenue_os.models.activity import Activity, ActivityType

                db.add(
                    Activity(
                        contact_id=contact.id,
                        activity_type=ActivityType.EMAIL_REPLY,
                        subject="Inbound email reply",
                        body=str(payload.get("body") or payload.get("snippet") or "")[:2000],
                        direction="inbound",
                        status="completed",
                    )
                )
                db.commit()
                actions.append(f"lead_score {old_score} -> {contact.lead_score}")
                _publish(
                    EventType.LEAD_SCORED,
                    contact_id,
                    "contact",
                    {
                        "score": contact.lead_score,
                        "old_score": old_score,
                        "reason": "email_reply",
                    },
                )
            elif organization_id is not None:
                raise HTTPException(status_code=404, detail="Contact not found")
            else:
                actions.append("contact not found; logged only")

        elif event_name == "meeting.booked" and contact_id:
            contact = _resolve_scoped_contact(
                db, contact_id, organization_id=organization_id, x_n8n_secret=x_n8n_secret
            )
            if contact is not None:
                current_status = contact.status.value if contact.status else None
                actions.append(
                    f"meeting booked; status unchanged ({current_status}); "
                    "human gate required for qualify"
                )
                _publish(
                    EventType.LEAD_SCORED,
                    contact_id,
                    "contact",
                    {
                        "signal": "meeting_booked",
                        "current_status": current_status,
                        "qualification_recommended": True,
                        "human_gate_required": True,
                        "meeting": payload.get("meeting", {}),
                    },
                )
            elif organization_id is not None:
                raise HTTPException(status_code=404, detail="Contact not found")
            else:
                actions.append("contact not found; logged only")

        elif event_name == "enrichment.completed" and contact_id:
            contact = _resolve_scoped_contact(
                db, contact_id, organization_id=organization_id, x_n8n_secret=x_n8n_secret
            )
            if contact is not None:
                _publish(EventType.CONTACT_ENRICHED, contact_id, "contact", payload)
                actions.append("contact_enriched event emitted")
            elif organization_id is not None:
                raise HTTPException(status_code=404, detail="Contact not found")
            else:
                actions.append("contact not found; logged only")

        elif event_name in ("email.opened", "email.clicked"):
            if contact_id:
                contact = _resolve_scoped_contact(
                    db, contact_id, organization_id=organization_id, x_n8n_secret=x_n8n_secret
                )
                if contact is not None:
                    _publish(
                        EventType.OUTREACH_COMPLETED,
                        contact_id,
                        "contact",
                        {"signal": event_name, **payload},
                    )
                elif organization_id is not None:
                    raise HTTPException(status_code=404, detail="Contact not found")
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
        detail={"payload": _redact_payload(payload), "actions": actions},
    )
    if organization_id and contact_id:
        db2 = SessionLocal()
        try:
            stamp_agent_action_log_organization(
                db2,
                action_type=event_name,
                target_id=contact_id,
                organization_id=organization_id,
            )
        finally:
            db2.close()

    logger.info("n8n inbound: %s -> %s", event_name, actions)
    return {"ok": status == "completed", "event": event_name, "actions": actions}


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip likely secret fields from audit detail."""
    redacted = dict(payload)
    for key in ("api_key", "secret", "token", "password", "authorization"):
        if key in redacted:
            redacted[key] = "[REDACTED]"
    return redacted
