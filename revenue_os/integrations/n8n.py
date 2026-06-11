from __future__ import annotations

import json
from typing import Any

import httpx

from revenue_os.config import settings


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
        return resp.json() if resp.content else None
    except Exception as e:
        if settings.DEBUG:
            print(f"[n8n] trigger_workflow error: {e}")
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
