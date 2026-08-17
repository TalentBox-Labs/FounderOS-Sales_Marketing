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
from revenue_os.services.revenue_workers import (
    WORKER_FOLLOWUP,
    WORKER_PERSONALIZATION,
    WORKER_RESEARCH,
    run_followup_worker,
    run_personalization_worker,
    run_research_worker,
)
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
