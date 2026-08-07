"""Outreach sequence scheduling — shared by the sequences API and prospecting import.

Enrolling a contact in a sequence has no separate send engine: each step
becomes one Activity scheduled ``delay_days`` after the previous step, typed
to match the step's channel (email/LinkedIn/WhatsApp/call) so it shows up on
the contact's timeline like any other outbound touch.

Reply-aware: each scheduled Activity records which sequence/step it came
from, so a detected inbound reply (see revenue_os.integrations.gmail_sync)
can cancel that contact's still-pending steps instead of continuing to fire
messages at someone who already responded.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.activity import Activity, ActivityType


def map_activity_type(step_action: str, sequence_channel: str) -> ActivityType:
    action = (step_action or "").strip().lower()
    channel = (sequence_channel or "").strip().lower()
    if action in {"send_email", "email"} or channel == "email":
        return ActivityType.EMAIL
    if action in {"linkedin_message", "linkedin"}:
        return ActivityType.LINKEDIN_MESSAGE
    if action in {"linkedin_connect"}:
        return ActivityType.LINKEDIN_CONNECT
    if action in {"whatsapp"} or channel == "whatsapp":
        return ActivityType.WHATSAPP
    if action in {"call"}:
        return ActivityType.CALL
    return ActivityType.TASK


def schedule_contact_sequence(db: Session, sequence: Any, contact_id: str) -> dict[str, Any]:
    """Schedule every step of ``sequence`` for one contact. Caller commits."""
    from revenue_os.models.activity import SequenceStep

    steps = (
        db.query(SequenceStep)
        .filter(SequenceStep.sequence_id == sequence.id)
        .order_by(SequenceStep.step_order)
        .all()
    )
    if not steps:
        activity = Activity(
            contact_id=uuid.UUID(contact_id),
            sequence_id=sequence.id,
            activity_type=map_activity_type("", sequence.channel),
            subject=f"{sequence.name} - outreach",
            body="Imported from prospecting plan",
            direction="outbound",
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc),
        )
        db.add(activity)
        return {"contact_id": contact_id, "steps": 1}

    cumulative_days = 0
    for step in steps:
        cumulative_days += max(0, int(step.delay_days or 0))
        activity = Activity(
            contact_id=uuid.UUID(contact_id),
            sequence_id=sequence.id,
            sequence_step_id=step.id,
            activity_type=map_activity_type(step.action_type, sequence.channel),
            subject=step.subject or f"{sequence.name} - step {step.step_order}",
            body=step.template or "",
            direction="outbound",
            status="scheduled",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=cumulative_days),
        )
        db.add(activity)
    return {"contact_id": contact_id, "steps": len(steps)}


def cancel_pending_sequence_steps(db: Session, contact_id: Any, reason: str = "Contact replied") -> int:
    """Cancel a contact's not-yet-sent sequence steps. Caller commits.

    Called when an inbound reply is detected (see gmail_sync.sync_inbox) so a
    sequence stops messaging someone who has already responded, across every
    sequence they're enrolled in — replies aren't scoped to one thread today.
    """
    pending = (
        db.query(Activity)
        .filter(
            Activity.contact_id == contact_id,
            Activity.sequence_id.isnot(None),
            Activity.status == "scheduled",
        )
        .all()
    )
    for activity in pending:
        activity.status = "cancelled"
        activity.body = f"{activity.body or ''}\n\n[Cancelled: {reason}]".strip()
        db.add(activity)
    return len(pending)
