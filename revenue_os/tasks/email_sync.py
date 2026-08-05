from __future__ import annotations

from datetime import datetime, timezone, timedelta

from revenue_os.database import SessionLocal
from revenue_os.models.activity import Activity, ActivityType, EmailActivity
from revenue_os.models.contact import Contact

from . import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_gmail_inbox(self):
    db = SessionLocal()
    try:
        contact_emails = {
            row[0].strip().lower()
            for row in db.query(Contact.email)
            .filter(Contact.email.isnot(None))
            .all()
            if row[0]
        }

        if not contact_emails:
            return {"synced": 0, "reason": "no contacts with email"}

        from revenue_os.services.gmail_client import fetch_new_messages

        last_sync = db.query(Activity).filter(
            Activity.activity_type == ActivityType.EMAIL,
            Activity.direction == "inbound",
        ).order_by(
            Activity.performed_at.desc()
        ).first()

        if last_sync and last_sync.performed_at:
            after = last_sync.performed_at.replace(tzinfo=timezone.utc)
        else:
            after = datetime.now(timezone.utc) - timedelta(days=7)

        messages = fetch_new_messages(
            after=after,
            known_emails=contact_emails,
            max_results=50,
        )

        synced = 0
        for msg in messages:
            from_address = (msg.get("from") or "").strip().lower()
            matched_contact = None

            for row in db.query(Contact).filter(Contact.email.isnot(None)).all():
                if row.email.strip().lower() in from_address:
                    matched_contact = row
                    break

            if not matched_contact:
                continue

            existing = (
                db.query(Activity)
                .filter(
                    Activity.contact_id == matched_contact.id,
                    Activity.activity_type == ActivityType.EMAIL,
                    Activity.direction == "inbound",
                )
                .filter(Activity.body.contains(msg.get("snippet", "")[:50]))
                .first()
            )
            if existing:
                continue

            activity = Activity(
                contact_id=matched_contact.id,
                activity_type=ActivityType.EMAIL,
                subject=msg.get("subject", ""),
                body=msg.get("snippet", ""),
                direction="inbound",
                status="received",
            )
            db.add(activity)
            db.flush()

            email_activity = EmailActivity(
                activity_id=activity.id,
                message_id=msg.get("id"),
                from_address=msg.get("from"),
                to_addresses=msg.get("to", ""),
            )
            db.add(email_activity)

            existing_outbound = (
                db.query(Activity)
                .filter(
                    Activity.contact_id == matched_contact.id,
                    Activity.activity_type == ActivityType.EMAIL,
                    Activity.direction == "outbound",
                )
                .filter(Activity.subject == msg.get("subject"))
                .order_by(Activity.performed_at.desc())
                .first()
            )
            if existing_outbound:
                from revenue_os.models.activity import EmailActivity as EA

                ea_record = (
                    db.query(EA)
                    .filter(EA.activity_id == existing_outbound.id)
                    .first()
                )
                if ea_record and not ea_record.replied_at:
                    ea_record.replied_at = datetime.now(timezone.utc)

                reply_activity = Activity(
                    contact_id=matched_contact.id,
                    activity_type=ActivityType.EMAIL_REPLY,
                    subject=msg.get("subject", ""),
                    direction="inbound",
                    status="tracked",
                )
                db.add(reply_activity)

            matched_contact.last_contacted_at = datetime.now(timezone.utc)
            synced += 1

            from revenue_os.services.search_service import index_activity
            index_activity(
                activity_id=activity.id,
                subject=activity.subject,
                body=activity.body,
            )

        db.commit()
        return {"synced": synced, "messages_fetched": len(messages)}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()
