"""REV-ORCH M1 — governed revenue orchestration vertical slice.

WorkflowOrchestrator-mediated flow:
Contact (tenant-scoped) → research → qualification → draft → ApprovalRequest
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.services.activity_log import log_agent_action
from revenue_os.services.approvals import request_approval
from revenue_os.services.lead_scoring_service import score_contact
from revenue_os.services.follow_up_eligibility import evaluate_follow_up_eligibility
from revenue_os.services.booking_eligibility import evaluate_booking_eligibility
from revenue_os.services.calendar_executor import get_tenant_availability
from revenue_os.services.revenue_workers import (
    WORKER_BOOKING,
    WORKER_FOLLOWUP,
    WORKER_PERSONALIZATION,
    WORKER_REPLY_ANALYSIS,
    WORKER_RESEARCH,
    run_booking_worker,
    run_followup_worker,
    run_personalization_worker,
    run_reply_analysis_worker,
    run_research_worker,
)
from revenue_os.services.reply_routing import merge_opt_out_tag, route_reply_assessment
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.tenant_scoped_access import (
    TenantAccessError,
    get_contact_for_tenant,
)

ORCHESTRATOR_ACTOR = "revenue_workflow_orchestrator"

# Conceptual states (not a separate SoT)
STATE_CONTACT_SELECTED = "CONTACT_SELECTED"
STATE_RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
STATE_QUALIFICATION_COMPLETED = "QUALIFICATION_COMPLETED"
STATE_DRAFT_CREATED = "DRAFT_CREATED"
STATE_APPROVAL_PENDING = "APPROVAL_PENDING"
STATE_FOLLOWUP_ELIGIBLE = "FOLLOWUP_ELIGIBLE"
STATE_FOLLOWUP_PROPOSED = "FOLLOWUP_PROPOSED"
STATE_BOOKING_PROPOSED = "BOOKING_PROPOSED"


class RevenueOrchestrationError(ValueError):
    """Workflow step failed in a tenant-safe, non-mutating way."""


def run_research_to_outreach(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
    *,
    workflow_run_id: str | None = None,
) -> dict[str, Any]:
    """M1 vertical slice through APPROVAL_PENDING. Does not send outbound."""
    run_id = workflow_run_id or str(uuid.uuid4())
    org_id = tenant.organization_id

    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    log_agent_action(
        actor=ORCHESTRATOR_ACTOR,
        action_type="rev_orch_workflow_started",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        detail={"workflow_run_id": run_id, "state": STATE_CONTACT_SELECTED},
    )

    research = run_research_worker(db, contact, org_id)
    db.commit()
    log_agent_action(
        actor=WORKER_RESEARCH,
        action_type="worker_research",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        status="completed" if research.get("ok") else "failed",
        detail={"workflow_run_id": run_id, "research_ok": research.get("ok")},
    )

    qualification = score_contact(db, contact)
    db.commit()
    log_agent_action(
        actor=ORCHESTRATOR_ACTOR,
        action_type="rev_orch_qualification",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        detail={
            "workflow_run_id": run_id,
            "score": qualification["score"],
            "suggested_status": qualification["suggested_status"],
            "status_changed": False,
        },
    )

    draft = run_personalization_worker(db, contact, org_id, research=research)
    if not draft.get("ok"):
        db.commit()
        raise RevenueOrchestrationError(draft.get("reason", "Draft generation failed"))

    _log_note(db, contact.id, "Cold email drafted (M1)", draft["body"][:2000])
    db.commit()

    idempotency_key = f"rev-orch-m1:{run_id}:send"
    approval = request_approval(
        requested_by=WORKER_PERSONALIZATION,
        action_type="send_outreach_email",
        title=f"Cold email to {draft['name']}",
        description=f"M1 workflow draft: {draft.get('rationale', '')[:500]}",
        target_type="contact",
        target_id=str(contact.id),
        payload={
            "contact_id": str(contact.id),
            "organization_id": org_id,
            "email": draft["email"],
            "name": draft["name"],
            "template": "ai_cold_email",
            "context": {"body": draft["body"]},
            "workflow_run_id": run_id,
            "idempotency_key": idempotency_key,
        },
        organization_id=org_id,
    )

    log_agent_action(
        actor=WORKER_PERSONALIZATION,
        action_type="worker_personalize",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        detail={
            "workflow_run_id": run_id,
            "approval_id": approval["id"],
        },
    )

    return {
        "ok": True,
        "state": STATE_APPROVAL_PENDING,
        "workflow_run_id": run_id,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        "research": research,
        "qualification": qualification,
        "draft": {
            "channel": draft["channel"],
            "body_preview": draft["body"][:200],
        },
        "approval_id": approval["id"],
        "approval_status": approval.get("status", "pending"),
    }


def inspect_follow_up_eligibility(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
) -> dict[str, Any]:
    """Deterministic eligibility inspection — no AI, no ApprovalRequest."""
    org_id = tenant.organization_id
    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    result = evaluate_follow_up_eligibility(db, contact)
    return {
        "ok": True,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        **result,
    }


def run_follow_up_to_outreach(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
    *,
    workflow_run_id: str | None = None,
) -> dict[str, Any]:
    """M2: eligibility (deterministic) → FollowUpWorker → ApprovalRequest."""
    return _run_follow_up_proposal(
        db,
        tenant.organization_id,
        contact_id,
        workflow_run_id=workflow_run_id,
    )


def run_follow_up_proposal_scheduled(
    db: Session,
    organization_id: str,
    contact_id: str,
) -> dict[str, Any]:
    """Scheduler path — tenant from persisted Contact.organization_id only."""
    try:
        contact = get_contact_for_tenant(db, organization_id, contact_id)
    except TenantAccessError:
        return {"ok": False, "reason": "Contact not in tenant scope"}

    if str(contact.organization_id) != str(organization_id):
        return {"ok": False, "reason": "Organization mismatch"}

    try:
        return _run_follow_up_proposal(db, organization_id, contact_id)
    except RevenueOrchestrationError as exc:
        return {"ok": False, "reason": str(exc)}


def run_booking_proposal_scheduled(
    db: Session,
    organization_id: str,
    contact_id: str,
) -> dict[str, Any]:
    """Scheduler path — proposal-only; soft-fail expected eligibility/calendar failures.

    Composes ``_run_booking_proposal``. Does not write calendars or create meetings.
    """
    try:
        contact = get_contact_for_tenant(db, organization_id, contact_id)
    except TenantAccessError:
        return {"ok": False, "reason": "Contact not in tenant scope"}

    if str(contact.organization_id) != str(organization_id):
        return {"ok": False, "reason": "Organization mismatch"}

    try:
        return _run_booking_proposal(db, organization_id, contact_id)
    except RevenueOrchestrationError as exc:
        return {"ok": False, "reason": str(exc)}


def _run_follow_up_proposal(
    db: Session,
    org_id: str,
    contact_id: str,
    *,
    workflow_run_id: str | None = None,
) -> dict[str, Any]:
    run_id = workflow_run_id or str(uuid.uuid4())

    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    eligibility = evaluate_follow_up_eligibility(db, contact)
    log_agent_action(
        actor=ORCHESTRATOR_ACTOR,
        action_type="rev_orch_followup_eligibility",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        detail={
            "workflow_run_id": run_id,
            "eligible": eligibility.get("eligible"),
            "state": eligibility.get("state"),
            "cadence_step": eligibility.get("cadence_step"),
        },
    )

    if not eligibility.get("eligible"):
        raise RevenueOrchestrationError(eligibility.get("reason", "Not eligible for follow-up"))

    proposal = run_followup_worker(
        db,
        contact,
        org_id,
        cadence_step=int(eligibility["cadence_step"]),
        source_activity_id=str(eligibility["source_activity_id"]),
        eligibility=eligibility,
    )
    if not proposal.get("ok"):
        raise RevenueOrchestrationError(proposal.get("reason", "Follow-up draft failed"))

    idempotency_key = eligibility["idempotency_key"]
    approval = request_approval(
        requested_by=WORKER_FOLLOWUP,
        action_type="send_outreach_email",
        title=f"Follow-up #{proposal['cadence_step']} to {proposal['name']}",
        description=f"M2 follow-up: {proposal.get('rationale', '')[:500]}",
        target_type="contact",
        target_id=str(contact.id),
        payload={
            "contact_id": str(contact.id),
            "organization_id": org_id,
            "email": proposal["email"],
            "name": proposal["name"],
            "template": "ai_follow_up_email",
            "context": {
                "body": proposal["body"],
                "subject": proposal["subject"],
            },
            "workflow_run_id": run_id,
            "workflow_kind": "rev_orch_m2_follow_up",
            "follow_up_step": proposal["cadence_step"],
            "source_activity_id": proposal["source_activity_id"],
            "recommended_send_after": proposal.get("recommended_send_after"),
            "idempotency_key": idempotency_key,
        },
        organization_id=org_id,
    )

    log_agent_action(
        actor=WORKER_FOLLOWUP,
        action_type="worker_followup_proposal",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        detail={
            "workflow_run_id": run_id,
            "approval_id": approval["id"],
            "cadence_step": proposal["cadence_step"],
            "source_activity_id": proposal["source_activity_id"],
        },
    )

    return {
        "ok": True,
        "state": STATE_FOLLOWUP_PROPOSED,
        "workflow_run_id": run_id,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        "eligibility": eligibility,
        "proposal": {
            "channel": proposal["channel"],
            "cadence_step": proposal["cadence_step"],
            "subject": proposal["subject"],
            "body_preview": proposal["body"][:200],
            "recommended_send_after": proposal.get("recommended_send_after"),
        },
        "approval_id": approval["id"],
        "approval_status": approval.get("status", "pending"),
    }


def inspect_latest_reply_assessment(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
) -> dict[str, Any]:
    """Read last M3 reply assessment from AgentActionLog. No AI, no mutation."""
    from revenue_os.models.automation_state import AgentActionLog

    org_id = tenant.organization_id
    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    log = (
        db.query(AgentActionLog)
        .filter(
            AgentActionLog.organization_id == uuid.UUID(str(org_id)),
            AgentActionLog.target_id == str(contact.id),
            AgentActionLog.action_type == "rev_orch_reply_assessment",
        )
        .order_by(AgentActionLog.created_at.desc())
        .first()
    )
    if log is None:
        return {
            "ok": True,
            "contact_id": str(contact.id),
            "organization_id": org_id,
            "assessment": None,
        }
    return {
        "ok": True,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        "assessment": log.detail or {},
    }


def run_inbound_reply_handling(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
    *,
    activity_id: str | None = None,
    message_id: str | None = None,
    workflow_run_id: str | None = None,
) -> dict[str, Any]:
    """M3: inbound Activity → ReplyAnalysisWorker → deterministic routing. No CRM authority mutation."""
    from revenue_os.models.activity import Activity
    from revenue_os.models.automation_state import AgentActionLog

    run_id = workflow_run_id or str(uuid.uuid4())
    org_id = tenant.organization_id

    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    if message_id:
        prior = (
            db.query(AgentActionLog)
            .filter(
                AgentActionLog.organization_id == uuid.UUID(str(org_id)),
                AgentActionLog.target_id == str(contact.id),
                AgentActionLog.action_type == "rev_orch_reply_assessment",
            )
            .order_by(AgentActionLog.created_at.desc())
            .all()
        )
        for row in prior:
            detail = row.detail or {}
            if detail.get("message_id") == message_id:
                return {
                    "ok": True,
                    "deduplicated": True,
                    "state": "REPLY_ASSESSED",
                    "workflow_run_id": detail.get("workflow_run_id", run_id),
                    "contact_id": str(contact.id),
                    "organization_id": org_id,
                    "activity_id": detail.get("activity_id"),
                    "message_id": message_id,
                    "assessment": detail.get("assessment"),
                    "routing": detail.get("routing"),
                }

    activity = None
    if activity_id:
        try:
            activity = db.get(Activity, uuid.UUID(str(activity_id)))
        except (ValueError, TypeError):
            activity = None
        if activity is not None and str(activity.contact_id) != str(contact.id):
            raise RevenueOrchestrationError("Activity not in tenant contact scope")

    reply_body = (activity.body if activity is not None else "") or ""
    status_before = contact.status.value if contact.status else None

    assessment = run_reply_analysis_worker(
        db,
        contact,
        org_id,
        reply_body=reply_body,
        activity_id=str(activity.id) if activity is not None else None,
    )
    routing = route_reply_assessment(assessment)

    if routing.get("apply_opt_out_tag"):
        contact.tags = merge_opt_out_tag(contact.tags)
        db.add(contact)
        db.commit()

    log_agent_action(
        actor=ORCHESTRATOR_ACTOR,
        action_type="rev_orch_reply_assessment",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        status="completed" if assessment.get("ok") else "failed",
        detail={
            "workflow_run_id": run_id,
            "activity_id": str(activity.id) if activity is not None else None,
            "message_id": message_id,
            "assessment": {
                "ok": assessment.get("ok"),
                "reply_type": assessment.get("reply_type"),
                "confidence": assessment.get("confidence"),
                "summary": assessment.get("summary"),
                "objection_category": assessment.get("objection_category"),
                "meeting_interest": assessment.get("meeting_interest"),
                "worker": WORKER_REPLY_ANALYSIS,
            },
            "routing": routing,
            "contact_status_unchanged": True,
            "status_before": status_before,
        },
    )

    log_agent_action(
        actor=WORKER_REPLY_ANALYSIS,
        action_type="worker_reply_analysis",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        status="completed" if assessment.get("ok") else "failed",
        detail={
            "workflow_run_id": run_id,
            "reply_type": routing.get("reply_type"),
            "recommended_next_action": routing.get("recommended_next_action"),
        },
    )

    return {
        "ok": True,
        "deduplicated": False,
        "state": "REPLY_ASSESSED" if assessment.get("ok") else "REPLY_HUMAN_REVIEW",
        "workflow_run_id": run_id,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        "activity_id": str(activity.id) if activity is not None else None,
        "message_id": message_id,
        "assessment": {
            "reply_type": routing.get("reply_type"),
            "confidence": routing.get("confidence"),
            "summary": assessment.get("summary"),
            "objection_category": routing.get("objection_category")
            or assessment.get("objection_category"),
            "meeting_interest": routing.get("meeting_interest"),
        },
        "routing": routing,
        "contact_status": contact.status.value if contact.status else None,
        "contact_status_changed": False,
    }


def wake_inbound_reply_handling(
    db: Session,
    organization_id: str,
    contact_id: str,
    *,
    activity_id: str | None = None,
    message_id: str | None = None,
) -> dict[str, Any]:
    """Webhook/scheduler wake — tenant from integration binding, dispatch via orchestrator."""
    from revenue_os.agents.orchestration import REV_ORCH_M3_WORKFLOW_KEY, WorkflowOrchestrator
    from revenue_os.services.integration_tenant_resolution import build_integration_tenant_context

    try:
        get_contact_for_tenant(db, organization_id, contact_id)
    except TenantAccessError:
        return {"ok": False, "reason": "Contact not in tenant scope"}

    tenant = build_integration_tenant_context(organization_id)
    try:
        return WorkflowOrchestrator.execute_revenue_workflow(
            REV_ORCH_M3_WORKFLOW_KEY,
            db=db,
            tenant=tenant,
            contact_id=contact_id,
            extra={"activity_id": activity_id, "message_id": message_id},
        )
    except RevenueOrchestrationError as exc:
        return {"ok": False, "reason": str(exc)}


def inspect_booking_eligibility(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
) -> dict[str, Any]:
    """M4: deterministic booking eligibility inspection (no AI, no calendar)."""
    org_id = tenant.organization_id
    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    eligibility = evaluate_booking_eligibility(db, contact, org_id)
    return {
        "ok": True,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        **eligibility,
    }


def inspect_booking_availability(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
    *,
    duration_minutes: int = 30,
) -> dict[str, Any]:
    """M4: tenant-scoped availability read (requires booking eligibility)."""
    org_id = tenant.organization_id
    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    eligibility = evaluate_booking_eligibility(db, contact, org_id)
    if not eligibility.get("eligible"):
        raise RevenueOrchestrationError(eligibility.get("reason", "Not eligible for booking"))

    availability = get_tenant_availability(
        org_id,
        duration_minutes=duration_minutes or eligibility.get("duration_minutes", 30),
    )
    return {
        "ok": True,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        "eligibility": eligibility,
        "availability": availability,
    }


def run_booking_to_meeting(
    db: Session,
    tenant: TenantContext,
    contact_id: str,
    *,
    workflow_run_id: str | None = None,
    selected_slot: dict[str, str] | None = None,
) -> dict[str, Any]:
    """M4: eligibility → availability → BookingWorker → ApprovalRequest."""
    return _run_booking_proposal(
        db,
        tenant.organization_id,
        contact_id,
        workflow_run_id=workflow_run_id,
        selected_slot=selected_slot,
    )


def _run_booking_proposal(
    db: Session,
    org_id: str,
    contact_id: str,
    *,
    workflow_run_id: str | None = None,
    selected_slot: dict[str, str] | None = None,
) -> dict[str, Any]:
    run_id = workflow_run_id or str(uuid.uuid4())

    try:
        contact = get_contact_for_tenant(db, org_id, contact_id)
    except TenantAccessError as exc:
        raise RevenueOrchestrationError("Contact not in tenant scope") from exc

    eligibility = evaluate_booking_eligibility(db, contact, org_id)
    log_agent_action(
        actor=ORCHESTRATOR_ACTOR,
        action_type="rev_orch_booking_eligibility",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        detail={
            "workflow_run_id": run_id,
            "eligible": eligibility.get("eligible"),
            "state": eligibility.get("state"),
        },
    )

    if not eligibility.get("eligible"):
        raise RevenueOrchestrationError(eligibility.get("reason", "Not eligible for booking"))

    availability = get_tenant_availability(
        org_id,
        duration_minutes=int(eligibility.get("duration_minutes") or 30),
    )
    if not availability.get("ok"):
        raise RevenueOrchestrationError(
            availability.get("reason", "Calendar availability unavailable")
        )

    proposal = run_booking_worker(
        db,
        contact,
        org_id,
        availability=availability,
        eligibility=eligibility,
        duration_minutes=int(eligibility.get("duration_minutes") or 30),
    )
    if not proposal.get("ok"):
        raise RevenueOrchestrationError(proposal.get("reason", "Booking proposal failed"))

    slot = selected_slot or proposal.get("recommended_slot") or {}
    if not slot.get("start") or not slot.get("end"):
        raise RevenueOrchestrationError("No valid slot selected for booking proposal")

    idempotency_key = eligibility["idempotency_key"]
    approval = request_approval(
        requested_by=WORKER_BOOKING,
        action_type="book_meeting",
        title=f"Book meeting with {proposal.get('meeting_title', contact.email or 'contact')}",
        description=proposal.get("rationale", "")[:500],
        target_type="contact",
        target_id=str(contact.id),
        payload={
            "contact_id": str(contact.id),
            "organization_id": org_id,
            "selected_slot_start": slot["start"],
            "selected_slot_end": slot["end"],
            "meeting_title": proposal["meeting_title"],
            "meeting_notes": proposal.get("meeting_notes", ""),
            "attendees": proposal.get("attendees") or ([contact.email] if contact.email else []),
            "timezone": proposal.get("timezone", "UTC"),
            "duration_minutes": proposal.get("duration_minutes", 30),
            "workflow_run_id": run_id,
            "workflow_kind": "rev_orch_m4_booking",
            "source_activity_id": proposal.get("source_activity_id"),
            "idempotency_key": idempotency_key,
            "candidate_slots": proposal.get("candidate_slots"),
        },
        organization_id=org_id,
    )

    log_agent_action(
        actor=WORKER_BOOKING,
        action_type="worker_booking_proposal",
        target_type="contact",
        target_id=str(contact.id),
        organization_id=org_id,
        detail={
            "workflow_run_id": run_id,
            "approval_id": approval["id"],
            "selected_slot": slot,
            "candidate_slots": proposal.get("candidate_slots"),
        },
    )

    return {
        "ok": True,
        "state": STATE_BOOKING_PROPOSED,
        "workflow_run_id": run_id,
        "contact_id": str(contact.id),
        "organization_id": org_id,
        "eligibility": eligibility,
        "proposal": {
            "meeting_title": proposal["meeting_title"],
            "candidate_slots": proposal.get("candidate_slots"),
            "recommended_slot": proposal.get("recommended_slot"),
            "selected_slot": slot,
            "duration_minutes": proposal.get("duration_minutes"),
            "timezone": proposal.get("timezone"),
        },
        "approval_id": approval["id"],
        "approval_status": approval.get("status", "pending"),
    }


def _log_note(db: Session, contact_id: uuid.UUID, subject: str, body: str) -> None:
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
