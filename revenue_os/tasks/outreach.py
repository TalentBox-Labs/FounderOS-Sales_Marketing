from __future__ import annotations

from revenue_os.database import SessionLocal
from revenue_os.models.activity import Activity, ActivityType

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
