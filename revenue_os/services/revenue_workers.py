"""REV-ORCH M1 — tenant-scoped specialized workers (proposal-only).

Research and personalization workers return structured proposals.
They do not file ApprovalRequest, send outbound, or mutate authority state.
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact
from revenue_os.services import ai_service

WORKER_RESEARCH = "research_worker"
WORKER_PERSONALIZATION = "personalization_worker"
WORKER_FOLLOWUP = "followup_worker"


def _build_contact_context(db: Session, contact: Contact) -> dict[str, Any]:
    from revenue_os.models.activity import Activity

    company = contact.company
    recent = (
        db.query(Activity)
        .filter(Activity.contact_id == contact.id)
        .order_by(Activity.created_at.desc())
        .limit(3)
        .all()
    )
    return {
        "name": f"{contact.first_name} {contact.last_name}".strip(),
        "first_name": contact.first_name,
        "email": contact.email,
        "designation": contact.designation,
        "company_name": company.name if company else None,
        "industry": company.industry.value if company and company.industry else None,
        "employee_count": company.employee_count if company else None,
        "funding_stage": company.funding_stage if company else None,
        "recent_activity": [
            {"subject": a.subject, "type": a.activity_type.value if a.activity_type else None}
            for a in recent
        ],
    }


def _context_summary(ctx: dict[str, Any]) -> str:
    parts = []
    if ctx.get("designation") and ctx.get("company_name"):
        parts.append(f"{ctx['name']} is {ctx['designation']} at {ctx['company_name']}.")
    elif ctx.get("company_name"):
        parts.append(f"{ctx['name']} works at {ctx['company_name']}.")
    if ctx.get("industry"):
        parts.append(f"Company industry: {ctx['industry']}.")
    if ctx.get("employee_count"):
        parts.append(f"Company size: ~{ctx['employee_count']} employees.")
    if ctx.get("funding_stage"):
        parts.append(f"Funding stage: {ctx['funding_stage']}.")
    if ctx.get("recent_activity"):
        subjects = [a["subject"] for a in ctx["recent_activity"] if a.get("subject")]
        if subjects:
            parts.append(f"Recent touches: {'; '.join(subjects)}.")
    return " ".join(parts) or "No additional CRM context on file."


def _recent_job_change(experiences: list[dict]) -> dict[str, Any] | None:
    if not experiences:
        return None
    current = next((e for e in experiences if not e.get("ends_at")), None)
    starts_at = (current or {}).get("starts_at")
    if not isinstance(starts_at, dict) or not starts_at.get("year"):
        return None
    try:
        started = datetime(
            starts_at["year"],
            starts_at.get("month") or 1,
            starts_at.get("day") or 1,
            tzinfo=timezone.utc,
        )
    except ValueError:
        return None
    days_ago = (datetime.now(timezone.utc) - started).days
    if days_ago < 0 or days_ago > 180:
        return None
    return {
        "title": current.get("title"),
        "company": current.get("company"),
        "days_ago": days_ago,
    }


def _log_research_note(
    db: Session, contact_id: uuid_lib.UUID, subject: str, body: str
) -> None:
    from revenue_os.models.activity import Activity, ActivityType

    db.add(
        Activity(
            contact_id=contact_id,
            activity_type=ActivityType.NOTE,
            subject=subject,
            body=body,
            status="completed",
        )
    )


def run_research_worker(
    db: Session,
    contact: Contact,
    organization_id: str,
) -> dict[str, Any]:
    """ResearchWorker — enrichment + signals. No outbound, no status mutation."""
    from revenue_os.services.linkedin_enrichment import (
        enrich_company,
        enrich_person,
        map_industry,
        score_icp_fit,
    )

    base = {
        "ok": True,
        "contact_id": str(contact.id),
        "organization_id": organization_id,
        "worker": WORKER_RESEARCH,
        "signals": {},
        "icp_fit": None,
        "observations": "",
        "evidence": [],
        "enrichment_configured": False,
    }

    ctx = _build_contact_context(db, contact)
    crm_summary = _context_summary(ctx)
    base["evidence"].append("crm_context")

    if not contact.linkedin_url:
        base["observations"] = crm_summary
        base["reason"] = "No LinkedIn URL — research limited to CRM context"
        _log_research_note(db, contact.id, "Research (CRM context only)", crm_summary)
        return base

    person = enrich_person(contact.linkedin_url, organization_id=organization_id)
    if not person.get("configured"):
        base["observations"] = crm_summary
        base["reason"] = person.get("reason", "Enrichment not configured")
        _log_research_note(db, contact.id, "Research (CRM context only)", crm_summary)
        return base

    base["enrichment_configured"] = True
    if not person.get("ok"):
        base["observations"] = crm_summary
        base["reason"] = person.get("reason")
        _log_research_note(db, contact.id, "Research (enrichment unavailable)", crm_summary)
        return base

    profile = person["profile"]
    experiences = profile.get("experiences") or []
    job_change = _recent_job_change(experiences)
    current_exp = next(
        (e for e in experiences if not e.get("ends_at")),
        experiences[0] if experiences else None,
    )
    company_linkedin_url = (current_exp or {}).get("company_linkedin_profile_url")

    signals: dict[str, Any] = {
        "job_change": job_change,
        "tech_stack": {
            "available": False,
            "reason": "No tech-stack provider configured",
        },
        "funding_rounds": [],
    }
    icp_fit = None
    if company_linkedin_url:
        company_res = enrich_company(company_linkedin_url, organization_id=organization_id)
        if company_res.get("ok"):
            c_profile = company_res["profile"]
            industry = map_industry(c_profile.get("industry"))
            size = c_profile.get("company_size")
            employee_count = (
                size[1]
                if isinstance(size, list) and len(size) == 2 and size[1]
                else None
            )
            signals["funding_rounds"] = [
                {
                    "type": r.get("funding_type"),
                    "amount": r.get("money_raised"),
                    "announced": r.get("announced_date"),
                }
                for r in (c_profile.get("funding_data") or [])
            ]
            icp_fit = score_icp_fit(industry, employee_count)
            base["evidence"].append("linkedin_enrichment")

    summary_bits = []
    if job_change:
        summary_bits.append(
            f"started as {job_change['title']} ~{job_change['days_ago']}d ago"
        )
    if signals["funding_rounds"]:
        latest = signals["funding_rounds"][0]
        summary_bits.append(f"latest funding: {latest['type']} ({latest['announced']})")
    if icp_fit:
        summary_bits.append(f"{icp_fit['fit']} ICP fit ({icp_fit['score']}/100)")

    observations = "; ".join(summary_bits) if summary_bits else crm_summary
    _log_research_note(db, contact.id, "ICP research signals", observations)

    base["signals"] = signals
    base["icp_fit"] = icp_fit
    base["observations"] = observations
    return base


def run_personalization_worker(
    db: Session,
    contact: Contact,
    organization_id: str,
    *,
    research: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """PersonalizationWorker — draft only. Does not file ApprovalRequest or send."""
    if not contact.email:
        return {
            "ok": False,
            "reason": "Contact has no email address",
            "worker": WORKER_PERSONALIZATION,
        }

    ctx = _build_contact_context(db, contact)
    summary = (research or {}).get("observations") or _context_summary(ctx)
    body = ai_service.generate_cold_email(
        ctx["name"],
        ctx["company_name"] or "their company",
        summary,
    )

    return {
        "ok": True,
        "contact_id": str(contact.id),
        "organization_id": organization_id,
        "worker": WORKER_PERSONALIZATION,
        "channel": "email",
        "email": contact.email,
        "name": ctx["name"],
        "body": body,
        "rationale": summary,
        "source_refs": ["research_proposal"] if research else ["crm_context"],
    }


def run_followup_worker(
    db: Session,
    contact: Contact,
    organization_id: str,
    *,
    cadence_step: int,
    source_activity_id: str,
    eligibility: dict[str, Any],
) -> dict[str, Any]:
    """FollowUpWorker — draft and recommend timing only. No ApprovalRequest or send."""
    if not contact.email:
        return {
            "ok": False,
            "reason": "Contact has no email address",
            "worker": WORKER_FOLLOWUP,
        }

    ctx = _build_contact_context(db, contact)
    summary = _context_summary(ctx)
    prior_subject = None
    from revenue_os.models.activity import Activity

    try:
        act = db.get(Activity, uuid_lib.UUID(str(source_activity_id)))
        if act is not None:
            prior_subject = act.subject
    except (ValueError, TypeError):
        pass

    draft = ai_service.generate_follow_up_email(
        ctx["name"],
        ctx["company_name"] or "their company",
        step=cadence_step,
        context=summary,
        prior_subject=prior_subject,
    )
    if not draft.get("body"):
        return {
            "ok": False,
            "reason": "Follow-up draft generation failed",
            "worker": WORKER_FOLLOWUP,
        }

    return {
        "ok": True,
        "contact_id": str(contact.id),
        "organization_id": organization_id,
        "worker": WORKER_FOLLOWUP,
        "worker_classification": "SPECIALIZED_AI_WORKER",
        "channel": "email",
        "email": contact.email,
        "name": ctx["name"],
        "subject": draft["subject"],
        "body": draft["body"],
        "rationale": draft.get("rationale", ""),
        "cadence_step": cadence_step,
        "source_activity_id": source_activity_id,
        "recommended_send_after": eligibility.get("recommended_send_after"),
        "source_refs": ["activity_history", "eligibility_policy"],
        "evidence": {
            "eligibility_state": eligibility.get("state"),
            "follow_ups_sent": eligibility.get("follow_ups_sent"),
        },
    }
