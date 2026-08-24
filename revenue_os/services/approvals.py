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
    contact = get_contact_for_tenant(db, str(org_id), str(contact_id))
    if payload.get("workflow_kind") == "rev_orch_m2_follow_up":
        _revalidate_follow_up_before_send(db, contact, payload)


def _revalidate_follow_up_before_send(db: Session, contact, payload: dict) -> None:
    """Execution-time stale authority revalidation for delayed follow-up sends."""
    from revenue_os.services.follow_up_eligibility import (
        contact_has_stop_tags,
        has_reply_stop_after_activity,
    )

    if contact_has_stop_tags(contact):
        raise ValueError("Contact has do-not-contact / unsubscribe tag — send blocked")

    source_id = str(payload.get("source_activity_id") or "")
    if source_id and has_reply_stop_after_activity(db, contact.id, source_id):
        raise ValueError("Reply recorded since follow-up was proposed — send blocked")


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
            subject = f"Outbound: {payload.get('template', 'email')}"
            if payload.get("workflow_kind") == "rev_orch_m2_follow_up":
                step = payload.get("follow_up_step")
                subject = f"Follow-up #{step}: {payload.get('template', 'email')}"
            db.add(
                Activity(
                    contact_id=cid,
                    activity_type=ActivityType.EMAIL,
                    subject=subject,
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


def _execute_book_meeting(db: Session, payload: dict) -> dict[str, Any]:
    """Create calendar event after human approval. Revalidates tenant and slot at execution time."""
    import json
    import uuid as uuid_lib
    from datetime import datetime, timezone

    from revenue_os.models.activity import Activity, ActivityType, MeetingActivity
    from revenue_os.models.contact import Contact
    from revenue_os.services.booking_eligibility import revalidate_booking_execution
    from revenue_os.services.calendar_executor import create_tenant_calendar_event

    org_id = str(payload.get("organization_id") or "")
    contact_id = str(payload.get("contact_id") or "")
    if not org_id or not contact_id:
        raise ValueError("Booking payload missing organization_id or contact_id")

    contact = get_contact_for_tenant(db, org_id, contact_id)
    revalidate_booking_execution(db, contact, org_id, payload)

    idempotency_key = payload.get("idempotency_key")
    if idempotency_key:
        existing = (
            db.query(Activity)
            .filter(
                Activity.contact_id == contact.id,
                Activity.activity_type == ActivityType.MEETING,
                Activity.status == "completed",
                Activity.body.contains(idempotency_key),
            )
            .first()
        )
        if existing is not None:
            return {
                "executed": True,
                "deduplicated": True,
                "activity_id": str(existing.id),
                "idempotency_key": idempotency_key,
                "note": "Meeting already booked for this idempotency key",
            }

    start_raw = payload.get("selected_slot_start")
    end_raw = payload.get("selected_slot_end")
    if not start_raw or not end_raw:
        raise ValueError("Booking payload missing selected slot")

    start_time = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    if start_time <= datetime.now(timezone.utc):
        raise ValueError("Selected slot is stale or in the past — booking blocked")

    attendees = [a for a in (payload.get("attendees") or []) if a]
    if contact.email and contact.email not in attendees:
        attendees.append(contact.email)

    calendar_result = create_tenant_calendar_event(
        org_id,
        title=str(payload.get("meeting_title") or "Meeting"),
        description=str(payload.get("meeting_notes") or ""),
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        idempotency_key=idempotency_key,
    )

    if not calendar_result.get("ok"):
        return {
            "executed": False,
            "note": calendar_result.get("reason", "Calendar execution failed"),
            "idempotency_key": idempotency_key,
        }

    activity = Activity(
        contact_id=contact.id,
        activity_type=ActivityType.MEETING,
        subject=str(payload.get("meeting_title") or "Booked meeting"),
        body=json.dumps(
            {
                "idempotency_key": idempotency_key,
                "provider_event_id": calendar_result.get("provider_event_id"),
                "connector": calendar_result.get("connector"),
                "selected_slot_start": start_raw,
                "selected_slot_end": end_raw,
                "workflow_kind": payload.get("workflow_kind"),
            }
        ),
        direction="outbound",
        status="completed",
        performed_at=datetime.now(timezone.utc),
    )
    db.add(activity)
    db.flush()
    db.add(
        MeetingActivity(
            activity_id=activity.id,
            meeting_url=calendar_result.get("meeting_url"),
            duration_minutes=int(payload.get("duration_minutes") or 30),
            notes=str(payload.get("meeting_notes") or "")[:2000],
        )
    )
    db.flush()

    status_before = contact.status.value if contact.status else None
    return {
        "executed": True,
        "provider_event_id": calendar_result.get("provider_event_id"),
        "connector": calendar_result.get("connector"),
        "activity_id": str(activity.id),
        "idempotency_key": idempotency_key,
        "contact_status_unchanged": True,
        "status_before": status_before,
    }


def _execute_send_email_campaign(db: Session, payload: dict) -> dict[str, Any]:
    """Hand a broadcast campaign to n8n — same delivery pattern as a single
    outreach email, just with a recipient list in the payload."""
    from revenue_os.integrations.n8n import trigger_workflow

    recipients = payload.get("recipients", [])
    result = trigger_workflow("send-campaign-email", {
        "event": "campaign.approved",
        "recipients": recipients,
        "subject": payload.get("subject"),
        "body": payload.get("body"),
        "cta": payload.get("cta"),
    })
    delivered = result is not None
    return {"handed_to_n8n": delivered, "recipient_count": len(recipients),
            "note": None if delivered else "n8n unreachable — check n8n and retry"}


def _execute_send_whatsapp_campaign(db: Session, payload: dict) -> dict[str, Any]:
    """Sends the approved message to every WhatsApp contact matching the
    campaign's tag via the real Meta Cloud API call in WhatsAppClient."""
    from revenue_os.integrations.whatsapp import MessageType, WhatsAppClient

    recipients = WhatsAppClient.list_contacts(tag=payload.get("tag"))
    sent, failed = 0, 0
    for contact in recipients:
        message = WhatsAppClient.send_message(contact.phone_number, MessageType.TEXT, {"body": payload.get("message", "")})
        if message and message.status == "sent":
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed, "total": len(recipients)}


def _execute_publish_linkedin_post(db: Session, payload: dict) -> dict[str, Any]:
    """LinkedIn has no compliant API for posting on a company's behalf
    without app review this platform doesn't have — approving marks the
    copy ready to post by hand."""
    return {"delivery": "manual", "note": "No compliant LinkedIn posting API configured — copy the approved text and post it yourself.",
            "body": payload.get("body")}


def _execute_publish_social_post(db: Session, payload: dict) -> dict[str, Any]:
    """Same manual-posting caveat as LinkedIn, across every platform."""
    return {"delivery": "manual", "note": "No compliant posting API configured for these platforms — copy the approved variants and post them yourself.",
            "variants": payload.get("variants")}


EXECUTORS: dict[str, Callable[[Session, dict], dict[str, Any]]] = {
    "send_outreach_email": _execute_send_outreach_email,
    "create_deal": _execute_create_deal,
    "send_linkedin_message": _execute_send_linkedin_message,
    "send_reply_email": _execute_send_outreach_email,
    "book_meeting": _execute_book_meeting,
    "send_email_campaign": _execute_send_email_campaign,
    "send_whatsapp_campaign": _execute_send_whatsapp_campaign,
    "publish_linkedin_post": _execute_publish_linkedin_post,
    "publish_social_post": _execute_publish_social_post,
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
    """Apply a human decision. Approval executes the action synchronously.

    ACP-4: concurrent approve is serialized via SELECT FOR UPDATE (when supported)
    plus a deterministic process/DB claim so at most one effect executor runs.
    """
    from revenue_os.services.acp4_distributed_claim import (
        release_process_local_claim,
        try_acquire_claim,
    )

    approver = _human_decider(tenant, decided_by if tenant is None else None)

    db = SessionLocal()
    claim_key = None
    claim_backend = None
    try:
        # Row lock when the dialect supports it (PostgreSQL).
        q = db.query(ApprovalRequest).filter(ApprovalRequest.id == str(request_id).strip())
        try:
            request = q.with_for_update().one_or_none()
        except Exception:
            request = q.one_or_none()

        if request is None:
            raise ValueError(f"Approval request not found: {request_id}")

        # Tenant binding — required for approve/reject when tenant provided;
        # also enforce payload/contact org match against tenant.
        if tenant is not None:
            try:
                bound = get_approval_for_tenant(db, tenant.organization_id, request_id)
            except TenantAccessError as exc:
                raise ValueError("Approval request not found") from exc
            if bound.id != request.id:
                raise ValueError("Approval request not found")

        if request.status != "pending":
            raise ValueError(f"Request already {request.status}")

        org_id = None
        if tenant is not None:
            org_id = str(tenant.organization_id)
        else:
            payload = request.payload or {}
            if payload.get("organization_id"):
                org_id = str(payload.get("organization_id"))
            elif request.target_type == "contact" and request.target_id:
                from revenue_os.models.contact import Contact

                try:
                    c = db.get(Contact, uuid_lib.UUID(str(request.target_id)))
                except ValueError:
                    c = None
                if c is not None and c.organization_id is not None:
                    org_id = str(c.organization_id)

        if not approve:
            request.decided_by = approver
            request.decided_at = datetime.now(timezone.utc)
            request.decision_note = note
            request.status = "rejected"
            db.commit()
            result = request.to_dict()
        else:
            if not org_id:
                raise ValueError("Approval execution requires organization scope")

            # Cross-check payload org when present
            payload_org = (request.payload or {}).get("organization_id")
            if payload_org is not None and str(payload_org) != str(org_id):
                raise ValueError("Approval organization mismatch — execution blocked")

            claim = try_acquire_claim(
                db,
                organization_id=str(org_id),
                idempotency_key=f"approval_execute:{request_id}",
            )
            claim_key = claim.claim_key
            claim_backend = claim.backend
            if not claim.acquired:
                raise ValueError(
                    "Approval execution claim unavailable — concurrent decide in progress"
                )

            # Re-read status under claim (TOCTOU close) before mutating
            db.refresh(request)
            if request.status != "pending":
                raise ValueError(f"Request already {request.status}")

            request.decided_by = approver
            request.decided_at = datetime.now(timezone.utc)
            request.decision_note = note
            request.status = "approved"
            prior = request.execution_result or {}
            if prior.get("executed") and (
                prior.get("handed_to_n8n") or prior.get("effect_completed")
            ):
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
                            "effect_completed": True,
                            **executor(db, request.payload or {}),
                        }
                    except Exception as e:
                        logger.error(f"Approval execution failed ({request_id}): {e}")
                        request.execution_result = {"executed": False, "error": str(e)}
                db.commit()
                result = request.to_dict()
    finally:
        # Process-local claims also release via session hooks on commit/rollback;
        # explicit release covers early raise paths before commit.
        if claim_backend == "process_local_test_only":
            release_process_local_claim(claim_key)
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
