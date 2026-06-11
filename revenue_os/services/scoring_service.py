from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact, ContactSource, ContactStatus


def score_contact(db: Session, contact_id: str) -> int:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        return 0

    score = 0

    if contact.email:
        score += 10
    if contact.phone:
        score += 5
    if contact.linkedin_url:
        score += 10
    if contact.designation:
        score += 5

    if contact.company_id:
        score += 15

    if contact.source == ContactSource.REFERRAL:
        score += 20
    elif contact.source == ContactSource.LINKEDIN:
        score += 5
    elif contact.source == ContactSource.WEB_FORM:
        score += 10

    if contact.status == ContactStatus.QUALIFIED:
        score += 15
    elif contact.status == ContactStatus.PROSPECT:
        score += 5

    contact.lead_score = min(score, 100)
    db.commit()
    return contact.lead_score
