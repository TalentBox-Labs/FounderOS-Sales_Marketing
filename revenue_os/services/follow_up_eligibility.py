"""REV-ORCH M2 — deterministic follow-up eligibility (policy before AI).

Evaluates whether a governed follow-up may be proposed. Does not draft content,
file ApprovalRequest, or send outbound.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.contact import Contact

# Bounded M2 cadence: initial outreach → wait → follow-up 1 → wait → follow-up 2
MAX_FOLLOW_UP_STEPS = 2
FOLLOW_UP_INTERVALS_DAYS = (3, 7)

STATE_NOT_DUE = "FOLLOWUP_NOT_DUE"
STATE_ELIGIBLE = "FOLLOWUP_ELIGIBLE"
STATE_STOPPED = "FOLLOWUP_STOPPED"
STATE_REPLY = "FOLLOWUP_REPLY_RECEIVED"
STATE_CADENCE_COMPLETE = "FOLLOWUP_CADENCE_COMPLETE"
STATE_PENDING = "FOLLOWUP_APPROVAL_PENDING"

_STOP_TAGS = frozenset({"do-not-contact", "dnc", "unsubscribed", "stop"})

_INBOUND_TYPES = (
    ActivityType.EMAIL,
    ActivityType.EMAIL_REPLY,
    ActivityType.LINKEDIN_MESSAGE,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _contact_stop_tags(contact: Contact) -> bool:
    raw = (contact.tags or "").lower()
    if not raw:
        return False
    tokens = {t.strip() for t in raw.replace(",", " ").split()}
    return bool(tokens & _STOP_TAGS)


def _latest_outbound_email(db: Session, contact_id: uuid.UUID) -> Activity | None:
    return (
        db.query(Activity)
        .filter(
            Activity.contact_id == contact_id,
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
            Activity.status == "completed",
        )
        .order_by(Activity.performed_at.desc())
        .first()
    )


def _initial_outbound_email(db: Session, contact_id: uuid.UUID) -> Activity | None:
    return (
        db.query(Activity)
        .filter(
            Activity.contact_id == contact_id,
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
            Activity.status == "completed",
        )
        .order_by(Activity.performed_at.asc())
        .first()
    )


def _count_follow_ups_after(db: Session, contact_id: uuid.UUID, source: Activity) -> int:
    source_at = _normalize_dt(source.performed_at) or _normalize_dt(source.created_at)
    if source_at is None:
        return 0
    rows = (
        db.query(Activity)
        .filter(
            Activity.contact_id == contact_id,
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "outbound",
            Activity.status == "completed",
            Activity.id != source.id,
        )
        .all()
    )
    count = 0
    for row in rows:
        ts = _normalize_dt(row.performed_at) or _normalize_dt(row.created_at)
        if ts and ts > source_at:
            count += 1
    return count


def _has_inbound_reply_after(
    db: Session, contact_id: uuid.UUID, after: datetime
) -> bool:
    rows = (
        db.query(Activity)
        .filter(
            Activity.contact_id == contact_id,
            Activity.direction == "inbound",
            Activity.activity_type.in_(_INBOUND_TYPES),
        )
        .all()
    )
    for row in rows:
        ts = _normalize_dt(row.performed_at) or _normalize_dt(row.created_at)
        if ts and ts > after:
            return True
    return False


def _pending_follow_up_approval(
    db: Session,
    contact_id: str,
    *,
    cadence_step: int,
    source_activity_id: str,
    idempotency_key: str,
) -> ApprovalRequest | None:
    pending = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.status == "pending",
            ApprovalRequest.action_type == "send_outreach_email",
            ApprovalRequest.target_id == contact_id,
        )
        .all()
    )
    for row in pending:
        payload = row.payload or {}
        if payload.get("workflow_kind") != "rev_orch_m2_follow_up":
            continue
        if (
            payload.get("follow_up_step") == cadence_step
            and str(payload.get("source_activity_id")) == source_activity_id
        ):
            return row
        if payload.get("idempotency_key") == idempotency_key:
            return row
    return None


def follow_up_idempotency_key(
    contact_id: str, cadence_step: int, source_activity_id: str
) -> str:
    return f"rev-orch-m2:{contact_id}:{cadence_step}:{source_activity_id}"


def evaluate_follow_up_eligibility(
    db: Session,
    contact: Contact,
    *,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Deterministic eligibility — AI must not override a negative result."""
    now = _normalize_dt(as_of) or _utc_now()
    contact_id = str(contact.id)

    if contact.organization_id is None:
        return {
            "eligible": False,
            "state": STATE_STOPPED,
            "reason": "Contact missing tenant organization",
            "cadence_step": None,
            "source_activity_id": None,
        }

    if _contact_stop_tags(contact):
        return {
            "eligible": False,
            "state": STATE_STOPPED,
            "reason": "Contact has do-not-contact / unsubscribe tag",
            "cadence_step": None,
            "source_activity_id": None,
        }

    source = _initial_outbound_email(db, contact.id)
    if source is None:
        return {
            "eligible": False,
            "state": STATE_NOT_DUE,
            "reason": "No completed initial outbound email",
            "cadence_step": None,
            "source_activity_id": None,
        }

    source_at = _normalize_dt(source.performed_at) or _normalize_dt(source.created_at)
    if source_at is None:
        return {
            "eligible": False,
            "state": STATE_NOT_DUE,
            "reason": "Initial outbound missing timestamp",
            "cadence_step": None,
            "source_activity_id": str(source.id),
        }

    if _has_inbound_reply_after(db, contact.id, source_at):
        return {
            "eligible": False,
            "state": STATE_REPLY,
            "reason": "Inbound reply recorded after initial outreach",
            "cadence_step": None,
            "source_activity_id": str(source.id),
        }

    follow_ups_sent = _count_follow_ups_after(db, contact.id, source)
    next_step = follow_ups_sent + 1
    if next_step > MAX_FOLLOW_UP_STEPS:
        return {
            "eligible": False,
            "state": STATE_CADENCE_COMPLETE,
            "reason": f"Cadence complete ({MAX_FOLLOW_UP_STEPS} follow-ups sent)",
            "cadence_step": None,
            "source_activity_id": str(source.id),
            "follow_ups_sent": follow_ups_sent,
        }

    anchor = _latest_outbound_email(db, contact.id) or source
    anchor_at = _normalize_dt(anchor.performed_at) or _normalize_dt(anchor.created_at)
    if anchor_at and _has_inbound_reply_after(db, contact.id, anchor_at):
        return {
            "eligible": False,
            "state": STATE_REPLY,
            "reason": "Inbound reply recorded after latest outbound",
            "cadence_step": None,
            "source_activity_id": str(source.id),
        }

    interval_idx = min(next_step - 1, len(FOLLOW_UP_INTERVALS_DAYS) - 1)
    required_days = FOLLOW_UP_INTERVALS_DAYS[interval_idx]
    wait_until = anchor_at + timedelta(days=required_days) if anchor_at else now
    if now < wait_until:
        return {
            "eligible": False,
            "state": STATE_NOT_DUE,
            "reason": f"Follow-up interval not elapsed ({required_days} days after last send)",
            "cadence_step": next_step,
            "source_activity_id": str(source.id),
            "wait_until": wait_until.isoformat(),
            "follow_ups_sent": follow_ups_sent,
        }

    idem = follow_up_idempotency_key(contact_id, next_step, str(source.id))
    pending = _pending_follow_up_approval(
        db,
        contact_id,
        cadence_step=next_step,
        source_activity_id=str(source.id),
        idempotency_key=idem,
    )
    if pending is not None:
        return {
            "eligible": False,
            "state": STATE_PENDING,
            "reason": "Duplicate pending follow-up ApprovalRequest",
            "cadence_step": next_step,
            "source_activity_id": str(source.id),
            "pending_approval_id": str(pending.id),
            "follow_ups_sent": follow_ups_sent,
        }

    return {
        "eligible": True,
        "state": STATE_ELIGIBLE,
        "reason": "Policy permits follow-up proposal",
        "cadence_step": next_step,
        "source_activity_id": str(source.id),
        "source_outbound_activity_id": str(anchor.id),
        "follow_ups_sent": follow_ups_sent,
        "recommended_send_after": now.isoformat(),
        "idempotency_key": idem,
    }


def has_reply_stop_after_activity(
    db: Session, contact_id: uuid.UUID, source_activity_id: str
) -> bool:
    """Public helper — reply recorded after source outbound blocks follow-up send."""
    try:
        source = db.get(Activity, uuid.UUID(str(source_activity_id)))
    except (ValueError, TypeError):
        return False
    if source is None:
        return False
    anchor_at = _normalize_dt(source.performed_at) or _normalize_dt(source.created_at)
    if anchor_at is None:
        return False
    return _has_inbound_reply_after(db, contact_id, anchor_at)


def contact_has_stop_tags(contact: Contact) -> bool:
    return _contact_stop_tags(contact)


def scan_eligible_follow_ups(db: Session, *, limit: int = 25) -> list[dict[str, str]]:
    """Scheduler scan — server-trusted Contact.organization_id only."""
    contacts = (
        db.query(Contact)
        .filter(Contact.organization_id.isnot(None), Contact.email.isnot(None))
        .limit(limit * 4)
        .all()
    )
    eligible: list[dict[str, str]] = []
    for contact in contacts:
        if len(eligible) >= limit:
            break
        result = evaluate_follow_up_eligibility(db, contact)
        if result.get("eligible"):
            eligible.append(
                {
                    "organization_id": str(contact.organization_id),
                    "contact_id": str(contact.id),
                    "cadence_step": str(result["cadence_step"]),
                    "source_activity_id": str(result["source_activity_id"]),
                }
            )
    return eligible
