from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from revenue_os.database import SessionLocal
from revenue_os.models.activity import Activity, ActivityType, EmailActivity

from . import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, contact_id: str, subject: str, body: str) -> dict:
    db = SessionLocal()
    try:
        activity = Activity(
            contact_id=contact_id,
            activity_type=ActivityType.EMAIL,
            subject=subject,
            body=body,
            direction="outbound",
            status="sent",
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)

        return {
            "activity_id": str(activity.id),
            "status": "sent",
        }
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def schedule_outreach_sequence(
    self, sequence_id: str, contact_id: str
) -> dict:
    db = SessionLocal()
    try:
        from revenue_os.models.activity import SequenceStep

        steps = (
            db.query(SequenceStep)
            .filter(SequenceStep.sequence_id == sequence_id)
            .order_by(SequenceStep.step_order)
            .all()
        )

        scheduled = []
        cumulative_delay = 0
        for step in steps:
            cumulative_delay += step.delay_days
            scheduled.append(
                {
                    "step": step.step_order,
                    "delay_days": cumulative_delay,
                    "subject": step.subject,
                    "body": step.template,
                }
            )

        return {
            "sequence_id": sequence_id,
            "contact_id": contact_id,
            "steps_scheduled": len(scheduled),
        }
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_personalized_email_task(
    self, contact_id: str, subject: str, body_text: str, activity_id: str
) -> dict:
    from revenue_os.database import SessionLocal
    from revenue_os.services.gmail_client import inject_tracking, send_email
    from revenue_os.config import settings

    db = SessionLocal()
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            return {"error": "Activity not found"}

        contact_email = None
        contact = activity.contact
        if contact:
            contact_email = contact.email

        if not contact_email:
            activity.status = "failed"
            db.commit()
            return {"error": "No email address"}

        body_html = body_text.replace("\n", "<br>\n")
        domain = settings.TRACKING_DOMAIN.rstrip("/")
        body_html = inject_tracking(body_html, activity_id, domain)

        result = send_email(
            to=contact_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
        )

        activity.status = "sent"

        email_activity = EmailActivity(
            activity_id=activity.id,
            message_id=result.get("message_id"),
            from_address=contact_email,
            to_addresses=contact_email,
        )
        db.add(email_activity)
        db.commit()

        return {
            "activity_id": activity_id,
            "message_id": result.get("message_id"),
            "thread_id": result.get("thread_id"),
            "status": "sent",
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True)
def process_outreach_sequences(self):
    """Beat task: runs every 30 min, advances sequences based on engagement."""
    from sqlalchemy.orm import Session
    from revenue_os.database import SessionLocal
    from revenue_os.models.activity import SequenceStep, OutreachSequence
    from revenue_os.models.sequence_enrollment import SequenceEnrollment
    from revenue_os.services.email_composer import compose as compose_email
    from revenue_os.services.enrichment_service import build_prospect_profile
    from revenue_os.config import settings

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        sequences = (
            db.query(OutreachSequence)
            .filter(OutreachSequence.is_active == 1)
            .all()
        )

        processed = 0
        switch_to_linkedin = 0
        for seq in sequences:
            steps = (
                db.query(SequenceStep)
                .filter(SequenceStep.sequence_id == seq.id)
                .order_by(SequenceStep.step_order)
                .all()
            )
            if not steps:
                continue

            try:
                conditions = json.loads(steps[0].conditions or "{}")
            except (json.JSONDecodeError, TypeError):
                conditions = {}

            from revenue_os.models.activity import Activity as ActModel

            pending = (
                db.query(ActModel)
                .filter(
                    ActModel.activity_type == ActivityType.EMAIL,
                    ActModel.status == "pending",
                )
                .filter(ActModel.scheduled_at <= now)
                .all()
            )

            for activity in pending:
                if not activity.contact_id:
                    continue
                profile = build_prospect_profile(db, str(activity.contact_id))
                if "error" in profile:
                    continue
                composed = compose_email(profile)
                contact_email = profile.get("contact", {}).get("email")
                if not contact_email:
                    continue

                body_text = f"{composed.get('hook', '')}\n\n{composed.get('body', '')}"
                body_html = body_text.replace("\n", "<br>\n")
                domain = settings.TRACKING_DOMAIN.rstrip("/")

                from revenue_os.services.gmail_client import inject_tracking

                body_html = inject_tracking(body_html, str(activity.id), domain)
                try:
                    from revenue_os.services.gmail_client import send_email
                    result = send_email(
                        to=contact_email,
                        subject=composed.get("subject", ""),
                        body_text=body_text,
                        body_html=body_html,
                    )
                    activity.status = "sent"

                    email_activity = EmailActivity(
                        activity_id=activity.id,
                        message_id=result.get("message_id"),
                        from_address=contact_email,
                        to_addresses=contact_email,
                    )
                    db.add(email_activity)
                    processed += 1
                except Exception:
                    activity.status = "failed"

            # ── LinkedIn channel-switching ──
            # Check enrollments with low engagement after 3 email steps
            enrollments = (
                db.query(SequenceEnrollment)
                .filter(
                    SequenceEnrollment.sequence_id == seq.id,
                    SequenceEnrollment.status == "active",
                    SequenceEnrollment.channel == "email",
                    SequenceEnrollment.current_step >= 3,
                )
                .all()
            )

            for enr in enrollments:
                # Count recent email activities for this contact (last 60 days)
                thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
                recent_outbound = (
                    db.query(ActModel)
                    .filter(
                        ActModel.contact_id == enr.contact_id,
                        ActModel.activity_type == ActivityType.EMAIL,
                        ActModel.direction == "outbound",
                        ActModel.performed_at >= thirty_days_ago,
                    )
                    .count()
                )
                recent_opens = (
                    db.query(ActModel)
                    .filter(
                        ActModel.contact_id == enr.contact_id,
                        ActModel.activity_type == ActivityType.EMAIL_OPEN,
                        ActModel.performed_at >= thirty_days_ago,
                    )
                    .count()
                )
                recent_replies = (
                    db.query(ActModel)
                    .filter(
                        ActModel.contact_id == enr.contact_id,
                        ActModel.activity_type == ActivityType.EMAIL_REPLY,
                        ActModel.performed_at >= thirty_days_ago,
                    )
                    .count()
                )

                # If no engagement after 3+ steps, switch to LinkedIn
                if recent_outbound >= 3 and recent_opens == 0 and recent_replies == 0:
                    enr.channel = "linkedin"
                    enr.updated_at = datetime.now(timezone.utc)

                    # Create LinkedIn connection attempt activity
                    li_activity = ActModel(
                        contact_id=enr.contact_id,
                        activity_type=ActivityType.LINKEDIN_CONNECT,
                        subject=f"LinkedIn connect — {seq.name}",
                        direction="outbound",
                        status="pending",
                    )
                    db.add(li_activity)
                    switch_to_linkedin += 1

        db.commit()
        return {
            "processed": processed,
            "sequences_checked": len(sequences),
            "switched_to_linkedin": switch_to_linkedin,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
