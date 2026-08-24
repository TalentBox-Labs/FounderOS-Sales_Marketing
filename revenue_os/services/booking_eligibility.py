"""REV-ORCH M4 — deterministic booking eligibility (policy before AI).

Evaluates whether a governed meeting booking may be proposed. Does not query
calendars, file ApprovalRequest, or create calendar events.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.contact import Contact
from revenue_os.services.approval_request_identity import FAMILY_BOOK_MEETING
from revenue_os.services.follow_up_eligibility import contact_has_stop_tags

STATE_NOT_ELIGIBLE = "BOOKING_NOT_ELIGIBLE"
STATE_ELIGIBLE = "BOOKING_ELIGIBLE"
STATE_STOPPED = "BOOKING_STOPPED"
STATE_ALREADY_BOOKED = "BOOKING_ALREADY_BOOKED"
STATE_PENDING = "BOOKING_APPROVAL_PENDING"
STATE_NO_MEETING_INTEREST = "BOOKING_NO_MEETING_INTEREST"

DEFAULT_DURATION_MINUTES = 30
DEFAULT_TIMEZONE = "UTC"


def _latest_reply_assessment(
    db: Session, organization_id: str, contact_id: uuid.UUID
) -> dict[str, Any] | None:
    log = (
        db.query(AgentActionLog)
        .filter(
            AgentActionLog.organization_id == uuid.UUID(str(organization_id)),
            AgentActionLog.target_id == str(contact_id),
            AgentActionLog.action_type == "rev_orch_reply_assessment",
        )
        .order_by(AgentActionLog.created_at.desc())
        .first()
    )
    if log is None:
        return None
    return log.detail or {}


def _has_booking_eligible_assessment(detail: dict[str, Any]) -> bool:
    routing = detail.get("routing") or {}
    if routing.get("booking_eligible"):
        return True
    if routing.get("recommended_next_action") == "BOOKING_ELIGIBLE":
        return True
    assessment = detail.get("assessment") or {}
    reply_type = str(assessment.get("reply_type") or "").upper()
    return reply_type == "MEETING_INTEREST" or bool(assessment.get("meeting_interest"))


def _pending_booking_approval(
    db: Session, organization_id: str, contact_id: uuid.UUID
) -> ApprovalRequest | None:
    return (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.status == "pending",
            ApprovalRequest.organization_id == str(organization_id),
            ApprovalRequest.approval_family == FAMILY_BOOK_MEETING,
            ApprovalRequest.target_id == str(contact_id),
        )
        .first()
    )


def _completed_meeting_activity(db: Session, contact_id: uuid.UUID) -> Activity | None:
    return (
        db.query(Activity)
        .filter(
            Activity.contact_id == contact_id,
            Activity.activity_type == ActivityType.MEETING,
            Activity.status == "completed",
            Activity.direction == "outbound",
        )
        .order_by(Activity.performed_at.desc())
        .first()
    )


def evaluate_booking_eligibility(
    db: Session,
    contact: Contact,
    organization_id: str,
) -> dict[str, Any]:
    """Deterministic booking eligibility — AI and client payload cannot override."""
    org_id = str(organization_id)
    contact_id = contact.id

    if contact.organization_id is None:
        return {
            "eligible": False,
            "state": STATE_STOPPED,
            "reason": "Contact missing tenant organization",
        }

    if str(contact.organization_id) != org_id:
        return {
            "eligible": False,
            "state": STATE_STOPPED,
            "reason": "Contact not in tenant scope",
        }

    if contact_has_stop_tags(contact):
        return {
            "eligible": False,
            "state": STATE_STOPPED,
            "reason": "Contact has do-not-contact / unsubscribe tag",
        }

    assessment_detail = _latest_reply_assessment(db, org_id, contact_id)
    if assessment_detail is None:
        return {
            "eligible": False,
            "state": STATE_NO_MEETING_INTEREST,
            "reason": "No inbound reply assessment — booking requires M3 meeting interest",
        }

    if not _has_booking_eligible_assessment(assessment_detail):
        return {
            "eligible": False,
            "state": STATE_NO_MEETING_INTEREST,
            "reason": "Latest reply assessment does not indicate booking eligibility",
            "source_assessment": {
                "reply_type": (assessment_detail.get("assessment") or {}).get("reply_type"),
                "recommended_next_action": (assessment_detail.get("routing") or {}).get(
                    "recommended_next_action"
                ),
            },
        }

    pending = _pending_booking_approval(db, org_id, contact_id)
    if pending is not None:
        return {
            "eligible": False,
            "state": STATE_PENDING,
            "reason": "Pending booking approval already exists",
            "approval_id": str(pending.id),
        }

    existing_meeting = _completed_meeting_activity(db, contact_id)
    if existing_meeting is not None:
        return {
            "eligible": False,
            "state": STATE_ALREADY_BOOKED,
            "reason": "Contact already has a completed meeting activity",
            "meeting_activity_id": str(existing_meeting.id),
        }

    source_activity_id = assessment_detail.get("activity_id")
    idempotency_key = f"rev-orch-m4:book:{contact_id}:{source_activity_id or 'latest'}"

    return {
        "eligible": True,
        "state": STATE_ELIGIBLE,
        "reason": "Meeting interest confirmed; booking may be proposed",
        "source_activity_id": source_activity_id,
        "source_message_id": assessment_detail.get("message_id"),
        "duration_minutes": DEFAULT_DURATION_MINUTES,
        "timezone": DEFAULT_TIMEZONE,
        "idempotency_key": idempotency_key,
        "assessment_detail": {
            "reply_type": (assessment_detail.get("assessment") or {}).get("reply_type"),
            "booking_eligible": (assessment_detail.get("routing") or {}).get("booking_eligible"),
        },
    }


def revalidate_booking_execution(
    db: Session,
    contact: Contact,
    organization_id: str,
    payload: dict[str, Any],
) -> None:
    """Execution-time stale authority revalidation before calendar side effect."""
    eligibility = evaluate_booking_eligibility(db, contact, organization_id)
    if eligibility.get("state") == STATE_ALREADY_BOOKED:
        raise ValueError(eligibility.get("reason", "Meeting already booked for contact"))
    if not eligibility.get("eligible") and eligibility.get("state") != STATE_PENDING:
        raise ValueError(eligibility.get("reason", "Booking no longer eligible"))

    if contact_has_stop_tags(contact):
        raise ValueError("Contact has suppression tag — booking blocked")

    slot_start = payload.get("selected_slot_start")
    if slot_start:
        try:
            start = datetime.fromisoformat(str(slot_start).replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if start <= datetime.now(timezone.utc):
                raise ValueError("Selected slot is in the past — booking blocked")
        except ValueError as exc:
            if "past" in str(exc):
                raise
            raise ValueError("Invalid selected slot timestamp") from exc

    expected_key = payload.get("idempotency_key")
    if expected_key and eligibility.get("idempotency_key") and expected_key != eligibility["idempotency_key"]:
        raise ValueError("Idempotency key mismatch — booking blocked")
