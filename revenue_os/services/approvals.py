"""Approval queue service: propose -> human decides -> execute on approval.

Risky autonomous actions (outbound email, deal creation on behalf of a rep)
are filed here instead of executing directly. Approving a request runs its
executor; rejecting archives it. Every transition is audit-logged.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from revenue_os.database import SessionLocal
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.services.activity_log import log_agent_action
from revenue_os.services.mutation_authority import (
    HumanAuthorityError,
    require_human_mutation_authority,
)
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.tenant_scoped_access import (
    TenantAccessError,
    get_approval_for_tenant,
    get_contact_for_tenant,
)

logger = logging.getLogger(__name__)


# ── Executors: what actually happens when a human approves ───────────────────


def _validate_outbound_payload(db: Session, payload: dict) -> None:
    contact_id = payload.get("contact_id")
    org_id = payload.get("organization_id")
    if not contact_id or not org_id:
        raise ValueError("Outbound payload missing contact_id or organization_id")
    get_contact_for_tenant(db, str(org_id), str(contact_id))


def _execute_send_outreach_email(db: Session, payload: dict) -> dict[str, Any]:
    """Hand approved email to n8n. Validates tenant scope before external send."""
    from revenue_os.integrations.n8n import trigger_workflow
    from revenue_os.models.activity import Activity, ActivityType

    _validate_outbound_payload(db, payload)

    idempotency_key = payload.get("idempotency_key")
    n8n_payload = {
        "event": "outreach.approved",
        "contact_id": payload.get("contact_id"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "template": payload.get("template", "intro"),
        "context": payload.get("context", {}),
    }
    if idempotency_key:
        n8n_payload["idempotency_key"] = idempotency_key

    result = trigger_workflow("send-email", n8n_payload)
    delivered = result is not None

    if delivered:
        try:
            cid = uuid_lib.UUID(str(payload.get("contact_id")))
            db.add(
                Activity(
                    contact_id=cid,
                    activity_type=ActivityType.EMAIL,
                    subject=f"Outbound: {payload.get('template', 'email')}",
                    body=(payload.get("context") or {}).get("body", "")[:2000],
                    direction="outbound",
                    status="completed",
                )
            )
            db.flush()
        except (ValueError, TypeError):
            pass

    return {
        "handed_to_n8n": delivered,
        "idempotency_key": idempotency_key,
        "note": None if delivered else "n8n unreachable — check n8n and retry",
    }


def _execute_create_deal(db: Session, payload: dict) -> dict[str, Any]:
    """Open a deal for a contact once a human signs off."""
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
    organization_id: str | None = None,
) -> dict[str, Any]:
    """File a pending approval request. Duplicate pending requests for the
    same (action_type, target_id) are collapsed into the existing one."""
    merged_payload = dict(payload or {})
    if organization_id and "organization_id" not in merged_payload:
        merged_payload["organization_id"] = organization_id

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
            payload=merged_payload,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        result = request.to_dict()
    finally:
        db.close()

    log_agent_action(
        actor=requested_by,
        action_type="approval_requested",
        target_type="approval",
        target_id=result["id"],
        organization_id=organization_id,
        detail={"title": title, "action": action_type},
    )
    return result


def _human_decider(tenant: TenantContext | None, decided_by: str | None) -> str:
    if tenant is not None:
        if not tenant.identity.is_human:
            raise HumanAuthorityError(
                f"{tenant.identity.principal_kind.value} cannot approve outbound actions"
            )
        name = (
            tenant.identity.display_name
            or tenant.identity.email
            or "human"
        )
        return require_human_mutation_authority(name, action="approval decision")
    raise HumanAuthorityError(
        "Session tenant context required for approval decisions — "
        "client-supplied decided_by cannot establish human authority"
    )


def decide(
    request_id: str,
    approve: bool,
    decided_by: str = "user",
    note: str | None = None,
    *,
    tenant: TenantContext | None = None,
) -> dict[str, Any]:
    """Apply a human decision. Approval executes the action synchronously."""
    approver = _human_decider(tenant, decided_by if tenant is None else None)

    db = SessionLocal()
    try:
        if tenant is not None:
            try:
                request = get_approval_for_tenant(db, tenant.organization_id, request_id)
            except TenantAccessError as exc:
                raise ValueError("Approval request not found") from exc
        else:
            request = db.get(ApprovalRequest, request_id)
            if request is None:
                raise ValueError(f"Approval request not found: {request_id}")

        if request.status != "pending":
            raise ValueError(f"Request already {request.status}")

        request.decided_by = approver
        request.decided_at = datetime.now(timezone.utc)
        request.decision_note = note

        if not approve:
            request.status = "rejected"
            db.commit()
            result = request.to_dict()
        else:
            request.status = "approved"
            prior = request.execution_result or {}
            if prior.get("executed") and prior.get("handed_to_n8n"):
                db.commit()
                result = request.to_dict()
            else:
                executor = EXECUTORS.get(request.action_type)
                if executor is None:
                    request.execution_result = {
                        "executed": False,
                        "note": f"no executor for '{request.action_type}' — approval recorded only",
                    }
                else:
                    try:
                        request.execution_result = {
                            "executed": True,
                            **executor(db, request.payload or {}),
                        }
                    except Exception as e:
                        logger.error(f"Approval execution failed ({request_id}): {e}")
                        request.execution_result = {"executed": False, "error": str(e)}
                db.commit()
                result = request.to_dict()
    finally:
        db.close()

    org_id = None
    if tenant is not None:
        org_id = tenant.organization_id
    elif isinstance(result.get("payload"), dict):
        org_id = result["payload"].get("organization_id")

    log_agent_action(
        actor=approver,
        action_type="approval_approved" if approve else "approval_rejected",
        target_type="approval",
        target_id=request_id,
        organization_id=str(org_id) if org_id else None,
        detail={"title": result["title"], "execution": result.get("execution_result")},
    )
    return result


def list_requests(
    status: str | None = None,
    limit: int = 100,
    *,
    organization_id: str | None = None,
) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        query = db.query(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())
        if status:
            query = query.filter(ApprovalRequest.status == status)
        rows = query.limit(min(limit, 500)).all()
        if organization_id is None:
            return [r.to_dict() for r in rows]
        filtered = []
        for row in rows:
            payload = row.payload or {}
            org = payload.get("organization_id")
            if org is not None and str(org) == str(organization_id):
                filtered.append(row.to_dict())
            elif row.target_type == "contact" and row.target_id:
                try:
                    get_contact_for_tenant(db, organization_id, str(row.target_id))
                    filtered.append(row.to_dict())
                except TenantAccessError:
                    continue
        return filtered
    finally:
        db.close()


def pending_count(*, organization_id: str | None = None) -> int:
    if organization_id is None:
        db = SessionLocal()
        try:
            return db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").count()
        finally:
            db.close()
    return len(list_requests(status="pending", limit=500, organization_id=organization_id))
