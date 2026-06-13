from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from revenue_os.agents.sdr_agent import score_and_enrich_lead
from revenue_os.models.activity import Activity, ActivityType, EmailActivity
from revenue_os.models.contact import Contact
from revenue_os.models.deal import Deal, DealStage


def build_prospect_profile(db: Session, contact_id: str) -> dict[str, Any]:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return {"error": "Contact not found"}

    company = contact.company

    profile: dict[str, Any] = {
        "contact": {
            "id": str(contact.id),
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "full_name": contact.full_name,
            "title": contact.designation,
            "email": contact.email,
            "linkedin_url": contact.linkedin_url,
            "status": contact.status.value if contact.status else None,
            "lead_score": contact.lead_score,
            "tags": contact.tags,
            "notes": contact.notes,
            "source": contact.source.value if contact.source else None,
            "created_at": (
                contact.created_at.isoformat() if contact.created_at else None
            ),
        },
        "company": None,
        "deal": None,
        "signals": {},
        "outreach_history": {
            "last_contacted_at": (
                contact.last_contacted_at.isoformat()
                if contact.last_contacted_at
                else None
            ),
            "total_activities": 0,
            "email_opens": 0,
            "email_clicks": 0,
            "email_replies": 0,
            "previous_subjects": [],
        },
    }

    if company:
        profile["company"] = {
            "id": str(company.id),
            "name": company.name,
            "domain": company.domain,
            "industry": company.industry.value if company.industry else None,
            "description": company.description,
            "employee_count": company.employee_count,
            "annual_revenue": company.annual_revenue,
            "funding_stage": company.funding_stage,
            "tech_stack": company.tech_stack,
            "hiring_activity": company.hiring_activity,
            "linkedin_url": company.linkedin_url,
            "website_url": company.website_url,
            "tags": company.tags,
        }

    active_deal = (
        db.query(Deal)
        .filter(
            Deal.contact_id == contact.id,
            Deal.stage.notin_(["closed_won", "closed_lost"]),
        )
        .order_by(Deal.created_at.desc())
        .first()
    )
    if active_deal:
        profile["deal"] = {
            "id": str(active_deal.id),
            "name": active_deal.name,
            "stage": active_deal.stage.value if active_deal.stage else None,
            "value": active_deal.value,
            "probability": active_deal.probability,
            "description": active_deal.description,
        }

    activities = (
        db.query(Activity)
        .filter(Activity.contact_id == contact.id)
        .order_by(Activity.performed_at.desc())
        .all()
    )
    if activities:
        profile["outreach_history"]["total_activities"] = len(activities)
        email_activity_ids = [
            a.id
            for a in activities
            if a.activity_type
            in (
                ActivityType.EMAIL,
                ActivityType.EMAIL_OPEN,
                ActivityType.EMAIL_CLICK,
                ActivityType.EMAIL_REPLY,
            )
        ]
        if email_activity_ids:
            email_activities = (
                db.query(EmailActivity)
                .filter(
                    EmailActivity.activity_id.in_(email_activity_ids)
                )
                .all()
            )
            for ea in email_activities:
                if ea.opened_at:
                    profile["outreach_history"]["email_opens"] += 1
                if ea.clicked_at:
                    profile["outreach_history"]["email_clicks"] += 1
                if ea.replied_at:
                    profile["outreach_history"]["email_replies"] += 1

        for a in activities:
            if a.subject and a.activity_type == ActivityType.EMAIL:
                profile["outreach_history"]["previous_subjects"].append(
                    a.subject
                )

    profile["signals"] = _gather_signals(contact, company)
    return profile


def _gather_signals(
    contact: Contact, company: Any
) -> dict[str, Any]:
    signals: dict[str, Any] = {
        "trigger_events": [],
        "icp_fit": "medium",
        "intent_signals": [],
        "outreach_tips": None,
    }

    if company:
        if company.hiring_activity:
            signals["trigger_events"].append(
                f"Hiring activity: {company.hiring_activity}"
            )
        if company.funding_stage:
            signals["trigger_events"].append(
                f"Funding stage: {company.funding_stage}"
            )
        if company.tech_stack:
            signals["trigger_events"].append(
                f"Tech stack: {company.tech_stack}"
            )

    icp_fit, intent_signals, outreach_tips = _ai_enrich(contact, company)
    signals["icp_fit"] = icp_fit
    signals["intent_signals"] = intent_signals
    signals["outreach_tips"] = outreach_tips

    return signals


def _ai_enrich(
    contact: Contact, company: Any
) -> tuple[str, list[str], str | None]:
    if not company:
        return "medium", [], None
    result = score_and_enrich_lead(
        company_name=company.name,
        company_domain=company.domain,
        industry=company.industry.value if company.industry else None,
    )
    return (
        result.get("icp_fit", "medium"),
        result.get("intent_signals", []),
        result.get("outreach_tips"),
    )
