"""Approval queue service: propose -> human decides -> execute on approval.

Risky autonomous actions (outbound email, deal creation on behalf of a rep)
are filed here instead of executing directly. Approving a request runs its
executor; rejecting archives it. Every transition is audit-logged.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from revenue_os.database import SessionLocal
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.services.activity_log import log_agent_action

logger = logging.getLogger(__name__)


# ── Executors: what actually happens when a human approves ───────────────────


def _execute_send_outreach_email(db: Session, payload: dict) -> dict[str, Any]:
    """Hand the email to n8n's send-email workflow (it owns delivery)."""
    from revenue_os.integrations.n8n import trigger_workflow

    result = trigger_workflow("send-email", {
        "event": "outreach.approved",
        "contact_id": payload.get("contact_id"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "template": payload.get("template", "intro"),
        "context": payload.get("context", {}),
    })
    delivered = result is not None
    return {"handed_to_n8n": delivered,
            "note": None if delivered else "n8n unreachable — check n8n and retry"}


def _execute_create_deal(db: Session, payload: dict) -> dict[str, Any]:
    """Open a deal for a contact once a human signs off."""
    import uuid as uuid_lib

    from revenue_os.models.contact import Contact
    from revenue_os.services.deal_automation_service import create_deal_from_contact

    contact = db.get(Contact, uuid_lib.UUID(str(payload.get("contact_id"))))
    if contact is None:
        return {"created": False, "note": "contact not found"}
    deal = create_deal_from_contact(db, contact, value=float(payload.get("value", 5000.0)))
    db.commit()
    if deal is None:
        return {"created": False, "note": "contact not qualified or deal exists"}
    return {"created": True, "deal_id": str(deal.id)}


def _execute_send_linkedin_message(db: Session, payload: dict) -> dict[str, Any]:
    """LinkedIn has no compliant API for sending arbitrary connection
    requests or DMs — approving this doesn't send it, it marks the draft
    ready to copy and send by hand."""
    return {
        "delivery": "manual",
        "note": "LinkedIn has no compliant send API — copy the approved text and send it yourself.",
        "connection_note": payload.get("connection_note"),
        "follow_up_dm": payload.get("follow_up_dm"),
    }


EXECUTORS: dict[str, Callable[[Session, dict], dict[str, Any]]] = {
    "send_outreach_email": _execute_send_outreach_email,
    "create_deal": _execute_create_deal,
    "send_linkedin_message": _execute_send_linkedin_message,
    # Same delivery mechanism as send_outreach_email, kept as a distinct
    # action_type so a reply draft never dedupes against (and gets silently
    # dropped by) an unrelated pending cold-outreach draft for the same
    # contact — request_approval() collapses duplicates by (action_type,
    # target_id) alone.
    "send_reply_email": _execute_send_outreach_email,
}


# ── Queue operations ─────────────────────────────────────────────────────────


def request_approval(
    requested_by: str,
    action_type: str,
    title: str,
    description: str = "",
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """File a pending approval request. Duplicate pending requests for the
    same (action_type, target_id) are collapsed into the existing one."""
    db = SessionLocal()
    try:
        if target_id:
            existing = (
                db.query(ApprovalRequest)
                .filter(
                    ApprovalRequest.status == "pending",
                    ApprovalRequest.action_type == action_type,
                    ApprovalRequest.target_id == target_id,
                )
                .first()
            )
            if existing is not None:
                return {**existing.to_dict(), "deduplicated": True}

        request = ApprovalRequest(
            requested_by=requested_by,
            action_type=action_type,
            title=title,
            description=description,
            target_type=target_type,
            target_id=target_id,
            payload=payload or {},
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        result = request.to_dict()
    finally:
        db.close()

    log_agent_action(
        actor=requested_by, action_type="approval_requested",
        target_type="approval", target_id=result["id"],
        detail={"title": title, "action": action_type},
    )
    return result


def decide(
    request_id: str,
    approve: bool,
    decided_by: str = "user",
    note: str | None = None,
) -> dict[str, Any]:
    """Apply a human decision. Approval executes the action synchronously."""
    db = SessionLocal()
    try:
        request = db.get(ApprovalRequest, request_id)
        if request is None:
            raise ValueError(f"Approval request not found: {request_id}")
        if request.status != "pending":
            raise ValueError(f"Request already {request.status}")

        request.decided_by = decided_by
        request.decided_at = datetime.now(timezone.utc)
        request.decision_note = note

        if not approve:
            request.status = "rejected"
            db.commit()
            result = request.to_dict()
        else:
            request.status = "approved"
            executor = EXECUTORS.get(request.action_type)
            if executor is None:
                request.execution_result = {
                    "executed": False,
                    "note": f"no executor for '{request.action_type}' — approval recorded only",
                }
            else:
                try:
                    request.execution_result = {"executed": True, **executor(db, request.payload or {})}
                except Exception as e:
                    logger.error(f"Approval execution failed ({request_id}): {e}")
                    request.execution_result = {"executed": False, "error": str(e)}
            db.commit()
            result = request.to_dict()
    finally:
        db.close()

    log_agent_action(
        actor=decided_by,
        action_type="approval_approved" if approve else "approval_rejected",
        target_type="approval", target_id=request_id,
        detail={"title": result["title"], "execution": result.get("execution_result")},
    )
    return result


def list_requests(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        query = db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
        if status:
            query = query.filter(ApprovalRequest.status == status)
        return [r.to_dict() for r in query.limit(min(limit, 500)).all()]
    finally:
        db.close()


def pending_count() -> int:
    db = SessionLocal()
    try:
        return db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").count()
    finally:
        db.close()
