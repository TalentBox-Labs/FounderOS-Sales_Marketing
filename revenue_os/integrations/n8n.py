from __future__ import annotations

import logging
from typing import Any

import httpx

from revenue_os.config import settings

logger = logging.getLogger(__name__)


def _log_outbound(webhook_id: str, payload: dict[str, Any], status: str, error: str | None = None) -> None:
    """Record every outbound n8n call in the audit trail (best-effort)."""
    try:
        from revenue_os.services.activity_log import log_agent_action

        log_agent_action(
            actor="platform",
            action_type="n8n_outbound",
            target_type="webhook",
            target_id=webhook_id,
            status=status,
            detail={"event": payload.get("event"), "error": error} if error else {"event": payload.get("event")},
        )
    except Exception:  # pragma: no cover - defensive
        pass


def trigger_workflow(
    webhook_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    url = f"{settings.N8N_WEBHOOK_BASE_URL}/{webhook_id}"
    headers = {
        "Content-Type": "application/json",
    }
    if settings.N8N_API_KEY:
        headers["Authorization"] = f"Bearer {settings.N8N_API_KEY}"

    try:
        resp = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        _log_outbound(webhook_id, payload, "completed")
        return resp.json() if resp.content else None
    except Exception as e:
        logger.warning(f"[n8n] trigger_workflow failed ({webhook_id}): {e}")
        _log_outbound(webhook_id, payload, "failed", error=str(e))
        return None


def new_lead_webhook(
    contact_id: str,
    contact_name: str,
    email: str,
    company: str | None = None,
) -> dict[str, Any] | None:
    return trigger_workflow("new-lead", {
        "event": "contact.created",
        "contact_id": contact_id,
        "name": contact_name,
        "email": email,
        "company": company,
    })


def new_deal_webhook(
    deal_id: str,
    deal_name: str,
    value: float,
    stage: str,
) -> dict[str, Any] | None:
    return trigger_workflow("new-deal", {
        "event": "deal.created",
        "deal_id": deal_id,
        "name": deal_name,
        "value": value,
        "stage": stage,
    })


def deal_stage_changed_webhook(
    deal_id: str,
    deal_name: str,
    previous_stage: str,
    new_stage: str,
) -> dict[str, Any] | None:
    return trigger_workflow("deal-stage-changed", {
        "event": "deal.stage_changed",
        "deal_id": deal_id,
        "name": deal_name,
        "previous_stage": previous_stage,
        "new_stage": new_stage,
    })


# ── EventBus → n8n bridge ────────────────────────────────────────────────────

# Internal events forwarded to n8n's generic "revenue-os-events" webhook so
# external workflows (Slack alerts, sequences, CRM sync) can react to them.
BRIDGED_EVENT_TYPES = {
    "lead_qualified",
    "deal_created",
    "deal_stage_changed",
    "deal_at_risk",
    "deal_closed",
}

BRIDGE_WEBHOOK_ID = "revenue-os-events"


def _bridge_handler(event) -> None:
    """Forward selected internal events to n8n. Skips events that came FROM n8n."""
    try:
        if event.data.get("origin") == "n8n":
            return  # loop guard: don't echo n8n's own results back at it
        if event.event_type.value not in BRIDGED_EVENT_TYPES:
            return
        payload = {
            "event": event.event_type.value,
            "entity_id": event.entity_id,
            "entity_type": event.entity_type,
            "priority": event.priority.value,
            "data": event.data,
            "timestamp": event.timestamp,
        }
        # Fire-and-forget in a thread so a slow/unreachable n8n can never
        # block the event bus (and with it, API request handling).
        import threading

        threading.Thread(
            target=trigger_workflow,
            args=(BRIDGE_WEBHOOK_ID, payload),
            daemon=True,
        ).start()
    except Exception as e:  # pragma: no cover - never break the event bus
        logger.warning(f"[n8n] bridge handler error: {e}")


def initialize_n8n_bridge() -> bool:
    """Subscribe the bridge to the EventBus. Call once at app startup.

    Returns True if the bridge was attached. The bridge is skipped when no
    N8N_WEBHOOK_BASE_URL is configured beyond the localhost default AND
    N8N_BRIDGE_ENABLED is not explicitly set.
    """
    import os

    enabled = os.environ.get("N8N_BRIDGE_ENABLED", "")
    if enabled in ("0", "false", "False"):
        logger.info("[n8n] bridge disabled via N8N_BRIDGE_ENABLED=0")
        return False

    from revenue_os.automation.events import EventBus

    EventBus.subscribe_all(_bridge_handler)
    logger.info(
        f"[n8n] bridge attached: forwarding {sorted(BRIDGED_EVENT_TYPES)} "
        f"to {settings.N8N_WEBHOOK_BASE_URL}/{BRIDGE_WEBHOOK_ID}"
    )
    return True
