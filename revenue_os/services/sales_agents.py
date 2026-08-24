"""The Sales Agent crew — five specialized agents, each doing one real job.

    1. ICP Research      — pulls buying signals (funding, recent job change,
                            company fit) from real enrichment data in one pass
    2. Cold Email         — drafts a first-touch email from the contact's
                            actual CRM context, not a merge-tag template
    3. LinkedIn Opener    — drafts a connection note + follow-up DM
    4. Follow-Up Sequence — builds a 5-7 touch email/LinkedIn sequence
    5. Objection Handler  — classifies the latest inbound reply and drafts
                            a matching response, in the founder's pace

None of these send anything on their own. Every drafted email or LinkedIn
message is filed as an ApprovalRequest — a human decides before it goes
out, same as every other outbound action on this platform. LinkedIn has no
compliant send API, so approving a LinkedIn draft marks it ready to copy
and send by hand rather than pretending to automate it.
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

AGENT_ICP_RESEARCH = "icp_research_agent"
AGENT_COLD_EMAIL = "cold_email_agent"
AGENT_LINKEDIN_OPENER = "linkedin_opener_agent"
AGENT_FOLLOWUP_SEQUENCE = "followup_sequence_agent"
AGENT_OBJECTION_HANDLER = "objection_handler_agent"


def _load_contact(db: Session, contact_id: str, *, organization_id: str | None = None):
    """Load contact; when organization_id supplied, enforce tenant scope."""
    from revenue_os.models.contact import Contact
    from revenue_os.services.tenant_scoped_access import (
        TenantAccessError,
        get_contact_for_tenant,
    )

    if organization_id:
        try:
            return get_contact_for_tenant(db, organization_id, contact_id)
        except TenantAccessError:
            return None

    try:
        cid = uuid_lib.UUID(contact_id)
    except ValueError:
        return None
    return db.get(Contact, cid)


def _build_contact_context(db: Session, contact: Any) -> dict[str, Any]:
    """Assemble what's actually known about this contact — no placeholders."""
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
    """Turn the context dict into a paragraph an LLM (or a human) can use —
    this is the mechanism that replaces merge tags with real specifics."""
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


def _log_note(db: Session, contact_id: uuid_lib.UUID, subject: str, body: str) -> None:
    from revenue_os.models.activity import Activity, ActivityType

    db.add(Activity(
        contact_id=contact_id, activity_type=ActivityType.NOTE,
        subject=subject, body=body, status="completed",
    ))


# ── Agent 1: ICP Research ────────────────────────────────────────────────────


def _recent_job_change(experiences: list[dict]) -> dict[str, Any] | None:
    """A current role that started recently, read straight off LinkedIn data
    — not inferred or guessed."""
    if not experiences:
        return None
    current = next((e for e in experiences if not e.get("ends_at")), None)
    starts_at = (current or {}).get("starts_at")
    if not isinstance(starts_at, dict) or not starts_at.get("year"):
        return None
    try:
        started = datetime(starts_at["year"], starts_at.get("month") or 1, starts_at.get("day") or 1, tzinfo=timezone.utc)
    except ValueError:
        return None
    days_ago = (datetime.now(timezone.utc) - started).days
    if days_ago < 0 or days_ago > 180:
        return None
    return {"title": current.get("title"), "company": current.get("company"), "days_ago": days_ago}


def research_contact(contact_id: str, *, organization_id: str) -> dict[str, Any]:
    """Agent 1 — pull buying signals from real LinkedIn data in one pass:
    funding rounds and company fit from the company profile, a recent job
    change from the person profile. Tech stack isn't reported: no provider
    for it is configured, and guessing would be fabrication, not research."""
    from revenue_os.database import SessionLocal
    from revenue_os.services.linkedin_enrichment import enrich_company, enrich_person, map_industry, score_icp_fit

    db = SessionLocal()
    try:
        contact = _load_contact(db, contact_id, organization_id=organization_id)
        if contact is None:
            return {"ok": False, "reason": "Contact not found"}
        if not contact.linkedin_url:
            return {"ok": False, "reason": "No LinkedIn URL on this contact"}

        person = enrich_person(contact.linkedin_url)
        if not person.get("configured"):
            return {"ok": False, "configured": False, "reason": person.get("reason")}
        if not person.get("ok"):
            return {"ok": False, "configured": True, "reason": person.get("reason")}

        profile = person["profile"]
        experiences = profile.get("experiences") or []
        job_change = _recent_job_change(experiences)
        current_exp = next((e for e in experiences if not e.get("ends_at")), experiences[0] if experiences else None)
        company_linkedin_url = (current_exp or {}).get("company_linkedin_profile_url")

        signals: dict[str, Any] = {
            "job_change": job_change,
            "tech_stack": {"available": False, "reason": "No tech-stack provider configured (e.g. BuiltWith)"},
            "funding_rounds": [],
        }
        icp_fit = None
        if company_linkedin_url:
            company_res = enrich_company(company_linkedin_url)
            if company_res.get("ok"):
                c_profile = company_res["profile"]
                industry = map_industry(c_profile.get("industry"))
                size = c_profile.get("company_size")
                employee_count = size[1] if isinstance(size, list) and len(size) == 2 and size[1] else None
                signals["funding_rounds"] = [
                    {"type": r.get("funding_type"), "amount": r.get("money_raised"), "announced": r.get("announced_date")}
                    for r in (c_profile.get("funding_data") or [])
                ]
                icp_fit = score_icp_fit(industry, employee_count)

        summary_bits = []
        if job_change:
            summary_bits.append(f"started as {job_change['title']} ~{job_change['days_ago']}d ago (job change signal)")
        if signals["funding_rounds"]:
            latest = signals["funding_rounds"][0]
            summary_bits.append(f"latest funding: {latest['type']} ({latest['announced']})")
        if icp_fit:
            summary_bits.append(f"{icp_fit['fit']} ICP fit ({icp_fit['score']}/100)")
        _log_note(
            db, contact.id, "ICP research signals",
            "; ".join(summary_bits) if summary_bits else "Researched — no strong buying signals found.",
        )
        db.commit()

        return {"ok": True, "configured": True, "signals": signals, "icp_fit": icp_fit}
    finally:
        db.close()


# ── Agent 2: Cold Email ──────────────────────────────────────────────────────


def draft_cold_email(contact_id: str, *, organization_id: str) -> dict[str, Any]:
    """Agent 2 — drafts a first-touch email from real contact context and
    files it for approval. Never sends on its own."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service
    from revenue_os.services.approvals import request_approval

    db = SessionLocal()
    try:
        contact = _load_contact(db, contact_id, organization_id=organization_id)
        if contact is None:
            return {"ok": False, "reason": "Contact not found"}
        if not contact.email:
            return {"ok": False, "reason": "Contact has no email address"}

        ctx = _build_contact_context(db, contact)
        summary = _context_summary(ctx)
        body = ai_service.generate_cold_email(ctx["name"], ctx["company_name"] or "their company", summary)

        _log_note(db, contact.id, "Cold email drafted", body[:2000])
        db.commit()

        approval = request_approval(
            requested_by=AGENT_COLD_EMAIL, action_type="send_outreach_email",
            title=f"Cold email to {ctx['name']}",
            description=f"AI-drafted first-touch email using real CRM context: {summary}",
            target_type="contact", target_id=str(contact.id),
            payload={"contact_id": str(contact.id), "email": contact.email, "name": ctx["name"],
                     "template": "ai_cold_email", "context": {"body": body},
                     "organization_id": organization_id},
            organization_id=organization_id,
        )
        return {"ok": True, "approval_id": approval["id"], "body": body, "context_used": summary}
    finally:
        db.close()


# ── Agent 3: LinkedIn Opener ─────────────────────────────────────────────────


def draft_linkedin_opener(contact_id: str, *, organization_id: str) -> dict[str, Any]:
    """Agent 3 — drafts a connection note and follow-up DM. Filed for
    approval; LinkedIn has no compliant auto-send, so approval marks it
    ready to send by hand rather than pretending to automate delivery."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service
    from revenue_os.services.approvals import request_approval

    db = SessionLocal()
    try:
        contact = _load_contact(db, contact_id, organization_id=organization_id)
        if contact is None:
            return {"ok": False, "reason": "Contact not found"}
        if not contact.linkedin_url:
            return {"ok": False, "reason": "No LinkedIn URL on this contact"}

        ctx = _build_contact_context(db, contact)
        summary = _context_summary(ctx)
        opener = ai_service.generate_linkedin_opener(ctx["name"], ctx["company_name"] or "their company", summary)

        _log_note(db, contact.id, "LinkedIn opener drafted",
                   f"Connection note: {opener['connection_note']}\nFollow-up DM: {opener['follow_up_dm']}")
        db.commit()

        approval = request_approval(
            requested_by=AGENT_LINKEDIN_OPENER, action_type="send_linkedin_message",
            title=f"LinkedIn opener for {ctx['name']}",
            description=f"AI-drafted connection note + follow-up DM: {summary}",
            target_type="contact", target_id=str(contact.id),
            payload={"contact_id": str(contact.id), "linkedin_url": contact.linkedin_url, "name": ctx["name"],
                     "organization_id": organization_id, **opener},
            organization_id=organization_id,
        )
        return {"ok": True, "approval_id": approval["id"], **opener, "context_used": summary}
    finally:
        db.close()


# ── Agent 4: Follow-Up Sequence ──────────────────────────────────────────────


def build_followup_sequence(contact_id: str, *, organization_id: str) -> dict[str, Any]:
    """Agent 4 — builds a 5-7 touch email/LinkedIn sequence as a real
    OutreachSequence, reusing the same models/UI as manually-built
    sequences. Each step after the first carries an advisory reply
    condition; nothing auto-enrolls or auto-branches on replies yet — a
    human reviews and enrolls from the Marketing > Sequences page."""
    from revenue_os.database import SessionLocal
    from revenue_os.models.activity import OutreachSequence, SequenceStep
    from revenue_os.services import ai_service

    db = SessionLocal()
    try:
        contact = _load_contact(db, contact_id, organization_id=organization_id)
        if contact is None:
            return {"ok": False, "reason": "Contact not found"}

        ctx = _build_contact_context(db, contact)
        summary = _context_summary(ctx)
        steps = ai_service.generate_followup_sequence(ctx["name"], ctx["company_name"] or "their company", summary)

        seq = OutreachSequence(name=f"AI sequence — {ctx['name']}", channel="mixed", is_active=1, steps_count=len(steps))
        db.add(seq)
        db.flush()
        for step in steps:
            condition_note = f" [{step['condition']}]" if step.get("condition") else ""
            db.add(SequenceStep(
                sequence_id=seq.id, step_order=step["step_order"], delay_days=step["delay_days"],
                subject=step["subject"], template=step["body"] + condition_note, action_type=step["action_type"],
                conditions=step.get("condition"),
            ))
        _log_note(db, contact.id, "Follow-up sequence drafted",
                   f"Built a {len(steps)}-step sequence ({summary}). Review under Marketing > Sequences before enrolling.")
        db.commit()

        return {"ok": True, "sequence_id": str(seq.id), "steps": steps, "context_used": summary}
    finally:
        db.close()


# ── Agent 5: Objection Handler ───────────────────────────────────────────────


def handle_latest_reply(contact_id: str, *, organization_id: str) -> dict[str, Any]:
    """Agent 5 — classifies the most recent inbound reply and drafts a
    matching response. Filed for approval, same as every other draft here:
    it responds in your voice, at your pace, not the moment a reply lands."""
    from revenue_os.database import SessionLocal
    from revenue_os.models.activity import Activity, ActivityType
    from revenue_os.services import ai_service
    from revenue_os.services.approvals import request_approval

    db = SessionLocal()
    try:
        contact = _load_contact(db, contact_id, organization_id=organization_id)
        if contact is None:
            return {"ok": False, "reason": "Contact not found"}

        reply = (
            db.query(Activity)
            .filter(Activity.contact_id == contact.id, Activity.activity_type == ActivityType.EMAIL,
                     Activity.direction == "inbound")
            .order_by(Activity.created_at.desc())
            .first()
        )
        if reply is None or not reply.body:
            return {"ok": False, "reason": "No inbound reply found for this contact"}

        ctx = _build_contact_context(db, contact)
        summary = _context_summary(ctx)
        result = ai_service.classify_and_draft_reply(ctx["name"], ctx["company_name"] or "their company", reply.body, summary)

        _log_note(db, contact.id, f"Reply classified: {result['category']}",
                   f"Reply: {reply.body[:500]}\n\nDrafted response: {result['draft_reply']}")
        db.commit()

        approval = None
        if contact.email:
            approval = request_approval(
            requested_by=AGENT_OBJECTION_HANDLER, action_type="send_reply_email",
            title=f"Reply to {ctx['name']} ({result['category'].replace('_', ' ')})",
            description=f"Classified inbound reply as '{result['category']}'. Drafted response for approval.",
            target_type="contact", target_id=str(contact.id),
            payload={"contact_id": str(contact.id), "email": contact.email, "name": ctx["name"],
                     "template": "objection_reply", "context": {"body": result["draft_reply"]},
                     "organization_id": organization_id,
                     "source_activity_id": str(reply.id)},
            organization_id=organization_id,
        )
        return {"ok": True, "category": result["category"], "draft_reply": result["draft_reply"],
                "approval_id": approval["id"] if approval else None, "original_reply": reply.body}
    finally:
        db.close()
