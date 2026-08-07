"""Reply-aware outreach sequences: enrolling a contact schedules one Activity
per step linked back to its sequence/step; a detected inbound reply (Gmail
sync) cancels whatever is still pending so the sequence stops messaging
someone who already responded.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest


@pytest.fixture
def contact(revenue_db):
    from revenue_os.models.contact import Contact

    c = Contact(
        first_name="Reply", last_name="Aware", email=f"replyaware-{uuid.uuid4().hex[:8]}@example.com",
    )
    revenue_db.add(c)
    revenue_db.commit()
    revenue_db.refresh(c)
    yield c


@pytest.fixture
def sequence_with_steps(revenue_db):
    from revenue_os.models.activity import OutreachSequence, SequenceStep

    seq = OutreachSequence(name="Reply-aware test sequence", channel="email", is_active=1)
    revenue_db.add(seq)
    revenue_db.commit()
    revenue_db.refresh(seq)

    steps = []
    for i in range(1, 4):
        step = SequenceStep(
            sequence_id=seq.id, step_order=i, delay_days=i, subject=f"Step {i}",
            template=f"Step {i} body", action_type="send_email",
        )
        revenue_db.add(step)
        steps.append(step)
    seq.steps_count = len(steps)
    revenue_db.add(seq)
    revenue_db.commit()
    for s in steps:
        revenue_db.refresh(s)
    yield seq, steps


class TestScheduleContactSequence:
    def test_scheduled_activities_are_linked_to_sequence_and_step(self, contact, sequence_with_steps, revenue_db) -> None:
        from revenue_os.models.activity import Activity
        from revenue_os.services.outreach_service import schedule_contact_sequence

        seq, steps = sequence_with_steps
        result = schedule_contact_sequence(revenue_db, seq, str(contact.id))
        revenue_db.commit()
        assert result["steps"] == 3

        activities = (
            revenue_db.query(Activity)
            .filter(Activity.contact_id == contact.id, Activity.sequence_id == seq.id)
            .order_by(Activity.scheduled_at)
            .all()
        )
        assert len(activities) == 3
        assert {a.status for a in activities} == {"scheduled"}
        assert [a.sequence_step_id for a in activities] == [s.id for s in steps]


class TestCancelPendingSequenceSteps:
    def test_cancels_only_scheduled_steps_for_that_contact(self, contact, sequence_with_steps, revenue_db) -> None:
        from revenue_os.models.activity import Activity
        from revenue_os.services.outreach_service import cancel_pending_sequence_steps, schedule_contact_sequence

        seq, _steps = sequence_with_steps
        schedule_contact_sequence(revenue_db, seq, str(contact.id))
        revenue_db.commit()

        # An unrelated already-completed activity for the same contact must survive untouched.
        untouched = Activity(
            contact_id=contact.id, activity_type="note", subject="unrelated note",
            body="hi", status="completed",
        )
        revenue_db.add(untouched)
        revenue_db.commit()

        cancelled_count = cancel_pending_sequence_steps(revenue_db, contact.id, reason="Replied: test")
        revenue_db.commit()
        assert cancelled_count == 3

        activities = revenue_db.query(Activity).filter(Activity.contact_id == contact.id).all()
        sequence_activities = [a for a in activities if a.sequence_id is not None]
        assert all(a.status == "cancelled" for a in sequence_activities)
        assert all("Replied: test" in (a.body or "") for a in sequence_activities)

        note = next(a for a in activities if a.sequence_id is None)
        assert note.status == "completed"  # untouched

    def test_no_pending_steps_is_a_no_op(self, contact, revenue_db) -> None:
        from revenue_os.services.outreach_service import cancel_pending_sequence_steps

        assert cancel_pending_sequence_steps(revenue_db, contact.id) == 0


class TestGmailSyncPausesSequenceOnReply:
    def _fake_message(self, message_id: str, sender_email: str, subject: str = "Re: following up"):
        return {
            "id": message_id, "snippet": "Thanks, I'm interested — let's talk.",
            "payload": {"headers": [
                {"name": "From", "value": f"Prospect <{sender_email}>"},
                {"name": "Subject", "value": subject},
            ]},
        }

    def test_inbound_reply_cancels_pending_sequence_steps(self, contact, sequence_with_steps, revenue_db) -> None:
        import revenue_os.integrations.gmail_sync as gs
        from revenue_os.models.activity import Activity, ActivityType
        from revenue_os.services.outreach_service import schedule_contact_sequence

        seq, _steps = sequence_with_steps
        schedule_contact_sequence(revenue_db, seq, str(contact.id))
        revenue_db.commit()

        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        with patch("revenue_os.services.credentials_vault.load_credentials",
                   return_value={"client_id": "x", "client_secret": "y", "refresh_token": "z"}), \
             patch.object(gs, "_refresh_access_token", return_value={"ok": True, "access_token": "fake"}), \
             patch.object(gs, "_list_message_ids", return_value=[message_id]), \
             patch.object(gs, "_get_message", return_value=self._fake_message(message_id, contact.email)):
            result = gs.sync_inbox()

        assert result["ok"] is True
        assert result["matched"] == 1
        assert result["sequence_steps_cancelled"] == 3

        pending = (
            revenue_db.query(Activity)
            .filter(Activity.contact_id == contact.id, Activity.sequence_id == seq.id, Activity.status == "scheduled")
            .count()
        )
        assert pending == 0

        # The inbound message itself is logged as a reply, not a generic outbound-typed email.
        inbound = (
            revenue_db.query(Activity)
            .filter(Activity.contact_id == contact.id, Activity.direction == "inbound")
            .order_by(Activity.created_at.desc())
            .first()
        )
        assert inbound is not None
        assert inbound.activity_type == ActivityType.EMAIL_REPLY

    def test_reply_with_no_active_sequence_is_a_no_op(self, contact) -> None:
        import revenue_os.integrations.gmail_sync as gs

        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        with patch("revenue_os.services.credentials_vault.load_credentials",
                   return_value={"client_id": "x", "client_secret": "y", "refresh_token": "z"}), \
             patch.object(gs, "_refresh_access_token", return_value={"ok": True, "access_token": "fake"}), \
             patch.object(gs, "_list_message_ids", return_value=[message_id]), \
             patch.object(gs, "_get_message", return_value=self._fake_message(message_id, contact.email)):
            result = gs.sync_inbox()

        assert result["ok"] is True
        assert result["matched"] == 1
        assert result["sequence_steps_cancelled"] == 0
