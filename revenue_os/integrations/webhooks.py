from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from revenue_os.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/n8n/{webhook_id}")
async def n8n_webhook(webhook_id: str, request: Request):
    """Receive webhook calls from n8n workflows."""
    body = await request.json()
    if settings.DEBUG:
        print(f"[webhook] n8n/{webhook_id}: {body}")
    return {"status": "received", "webhook_id": webhook_id}


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Receive Stripe webhook events."""
    body = await request.json()
    event_type = body.get("type", "unknown")
    if settings.DEBUG:
        print(f"[webhook] stripe: {event_type}")
    return {"status": "received", "event_type": event_type}
