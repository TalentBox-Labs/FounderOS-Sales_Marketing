from __future__ import annotations

from revenue_os.database import SessionLocal
from revenue_os.models.contact import Contact
from revenue_os.services.scoring_service import score_contact

from . import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def enrich_lead(self, contact_id: str) -> dict:
    db = SessionLocal()
    try:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return {"error": "contact not found"}

        score = score_contact(db, contact.id)

        return {
            "contact_id": contact_id,
            "score": score,
            "status": contact.status.value,
        }
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def bulk_enrich_leads(self, contact_ids: list[str]) -> list[dict]:
    results = []
    for cid in contact_ids:
        result = enrich_lead.delay(cid)
        results.append({"contact_id": cid, "task_id": result.id})
    return results
