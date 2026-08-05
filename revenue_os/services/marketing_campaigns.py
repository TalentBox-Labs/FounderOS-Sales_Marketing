"""Email Marketing, WhatsApp Marketing, Campaign Manager, and Marketing
Automation agents.

Email and WhatsApp campaigns are AI-drafted, so both are filed to the
Approvals queue before anything sends — same gate as every other
AI-generated outbound content in this platform. Approving an email campaign
hands it to n8n's send-email workflow; approving a WhatsApp campaign sends
it via the real Meta Cloud API call now wired into WhatsAppClient.
"""

from __future__ import annotations

import json
from typing import Any

AGENT_EMAIL_MARKETING = "email_marketing_agent"
AGENT_WHATSAPP_MARKETING = "whatsapp_marketing_agent"
AGENT_CAMPAIGN_MANAGER = "campaign_manager_agent"
AGENT_MARKETING_AUTOMATION = "marketing_automation_agent"


def _campaign_dict(c: Any) -> dict[str, Any]:
    return {
        "id": str(c.id), "name": c.name, "goal": c.goal,
        "channels": [x for x in (c.channels or "").split(",") if x],
        "status": c.status, "kpis": c.kpis, "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


# ── Agent 11: Email Marketing ────────────────────────────────────────────────


def draft_email_campaign(campaign_type: str, context: str = "", audience_status: str | None = None) -> dict[str, Any]:
    """Drafts campaign copy and files ONE approval to send it to a real
    audience segment (contacts matching audience_status, or everyone with
    an email on file)."""
    from revenue_os.database import SessionLocal
    from revenue_os.models.contact import Contact, ContactStatus
    from revenue_os.services import ai_service
    from revenue_os.services.approvals import request_approval

    db = SessionLocal()
    try:
        query = db.query(Contact).filter(Contact.email.isnot(None))
        if audience_status:
            try:
                query = query.filter(Contact.status == ContactStatus(audience_status))
            except ValueError:
                return {"ok": False, "reason": f"Invalid audience_status: {audience_status}"}
        recipients = [c.email for c in query.limit(1000).all()]
    finally:
        db.close()

    campaign = ai_service.generate_email_campaign(campaign_type, context)

    approval = request_approval(
        requested_by=AGENT_EMAIL_MARKETING, action_type="send_email_campaign",
        title=f"Email campaign: {campaign_type} to {len(recipients)} contacts",
        description=f"AI-drafted campaign. Audience: {audience_status or 'all contacts with email'} ({len(recipients)} recipients).",
        payload={"campaign_type": campaign_type, "recipients": recipients, **campaign},
    )
    return {"ok": True, "recipient_count": len(recipients), "approval_id": approval["id"], **campaign}


# ── Agent 12: WhatsApp Marketing ─────────────────────────────────────────────


def draft_whatsapp_campaign(campaign_type: str, context: str = "", tag: str | None = None) -> dict[str, Any]:
    """Drafts WhatsApp campaign copy and files it for approval before
    sending to any real audience tag."""
    from revenue_os.integrations.whatsapp import WhatsAppClient
    from revenue_os.services import ai_service
    from revenue_os.services.approvals import request_approval

    recipients = WhatsAppClient.list_contacts(tag=tag)
    campaign = ai_service.generate_whatsapp_campaign(campaign_type, context)

    approval = request_approval(
        requested_by=AGENT_WHATSAPP_MARKETING, action_type="send_whatsapp_campaign",
        title=f"WhatsApp campaign: {campaign_type} to {len(recipients)} contact(s)" + (f" (tag: {tag})" if tag else ""),
        description=f"AI-drafted WhatsApp message for {len(recipients)} recipient(s).",
        payload={"campaign_type": campaign_type, "tag": tag, "message": campaign["message"]},
    )
    return {"ok": True, "recipient_count": len(recipients), "approval_id": approval["id"], **campaign}


# ── Agent 13: Campaign Manager ───────────────────────────────────────────────


def plan_campaign(name: str, goal: str, channels: list[str], context: str = "") -> dict[str, Any]:
    """Plans a multi-channel campaign and persists it as a real
    MarketingCampaign row other agents' work can be attributed to."""
    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import MarketingCampaign
    from revenue_os.services import ai_service

    plan = ai_service.generate_campaign_plan(goal, channels, context)

    db = SessionLocal()
    try:
        campaign = MarketingCampaign(
            name=name, goal=goal, channels=",".join(channels), status="planning",
            kpis="; ".join(plan.get("kpis", [])),
            notes=json.dumps(plan.get("timeline", [])),
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        result = _campaign_dict(campaign)
    finally:
        db.close()

    return {"ok": True, "campaign": result, "plan": plan}


def list_campaigns(status: str | None = None) -> list[dict[str, Any]]:
    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import MarketingCampaign

    db = SessionLocal()
    try:
        q = db.query(MarketingCampaign).order_by(MarketingCampaign.created_at.desc())
        if status:
            q = q.filter(MarketingCampaign.status == status)
        return [_campaign_dict(c) for c in q.limit(200).all()]
    finally:
        db.close()


def update_campaign_status(campaign_id: str, status: str) -> dict[str, Any]:
    import uuid as uuid_lib

    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import MarketingCampaign

    if status not in ("planning", "active", "completed"):
        return {"ok": False, "reason": f"Invalid status: {status}"}

    db = SessionLocal()
    try:
        try:
            cid = uuid_lib.UUID(campaign_id)
        except ValueError:
            return {"ok": False, "reason": "Invalid campaign_id"}
        campaign = db.get(MarketingCampaign, cid)
        if campaign is None:
            return {"ok": False, "reason": "Campaign not found"}
        campaign.status = status
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return {"ok": True, "campaign": _campaign_dict(campaign)}
    finally:
        db.close()


# ── Agent 14: Marketing Automation ───────────────────────────────────────────


def trigger_marketing_automation(workflow_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Fires a named n8n marketing workflow (e.g. "publish-content",
    "sync-crm-tags", "schedule-social-post") with real payload data —
    what that webhook actually does is whatever the founder has built in
    their own n8n instance, same convention as the platform's other
    n8n-triggered automations."""
    from revenue_os.integrations.n8n import trigger_workflow

    result = trigger_workflow(workflow_name, payload)
    return {
        "ok": result is not None, "workflow": workflow_name,
        "n8n_response": result,
        "note": None if result is not None else "n8n unreachable or workflow not configured — check Integrations.",
    }
