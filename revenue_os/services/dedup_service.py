from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact, Company


def find_duplicate_contacts(
    db: Session,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company_id: Optional[uuid.UUID] = None,
    threshold: float = 0.8,
) -> list[dict]:
    if not email and not (first_name and last_name):
        return []

    query = db.query(Contact)
    conditions = []

    if email:
        conditions.append(Contact.email == email)

    if first_name and last_name:
        conditions.append(
            Contact.first_name.ilike(first_name) & Contact.last_name.ilike(last_name)
        )

    if company_id:
        conditions.append(Contact.company_id == company_id)

    query = query.filter(or_(*conditions))
    duplicates = query.all()

    results = []
    for dup in duplicates:
        score = 0.0
        factors = []

        if email and dup.email and dup.email.lower() == email.lower():
            score += 0.5
            factors.append("email match")

        if first_name and last_name and dup.first_name and dup.last_name:
            if dup.first_name.lower() == first_name.lower() and dup.last_name.lower() == last_name.lower():
                score += 0.3
                factors.append("name match")

        if company_id and dup.company_id and str(dup.company_id) == str(company_id):
            score += 0.2
            factors.append("company match")

        if score >= threshold:
            results.append({
                "id": str(dup.id),
                "first_name": dup.first_name,
                "last_name": dup.last_name,
                "email": dup.email,
                "score": round(score, 2),
                "factors": factors,
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)


def merge_contacts(
    db: Session,
    primary_id: uuid.UUID,
    duplicate_id: uuid.UUID,
) -> dict:
    primary = db.query(Contact).filter(Contact.id == primary_id).first()
    duplicate = db.query(Contact).filter(Contact.id == duplicate_id).first()

    if not primary or not duplicate:
        return {"error": "One or both contacts not found"}

    merged = {}
    for field in ["first_name", "last_name", "email", "phone", "designation",
                   "linkedin_url", "twitter_url", "notes", "tags", "company_id"]:
        primary_val = getattr(primary, field, None)
        duplicate_val = getattr(duplicate, field, None)
        merged[field] = primary_val or duplicate_val
        if not primary_val and duplicate_val:
            setattr(primary, field, duplicate_val)

    if not primary.source or primary.source.value == "manual":
        primary.source = duplicate.source

    if duplicate.lead_score > primary.lead_score:
        primary.lead_score = duplicate.lead_score

    from revenue_os.models.activity import Activity
    db.query(Activity).filter(Activity.contact_id == duplicate_id).update(
        {"contact_id": primary_id}
    )
    from revenue_os.models.deal import Deal
    db.query(Deal).filter(Deal.contact_id == duplicate_id).update(
        {"contact_id": primary_id}
    )

    db.delete(duplicate)
    db.commit()
    db.refresh(primary)

    return {"merged": True, "primary_id": str(primary_id), "fields_merged": merged}


def find_duplicate_companies(db: Session, domain: Optional[str] = None, name: Optional[str] = None) -> list[dict]:
    if not domain and not name:
        return []

    query = db.query(Company)
    conditions = []
    if domain:
        conditions.append(Company.domain == domain)
    if name:
        conditions.append(Company.name.ilike(name))
    query = query.filter(or_(*conditions))
    duplicates = query.all()

    results = []
    for dup in duplicates:
        score = 0.0
        factors = []
        if domain and dup.domain and dup.domain.lower() == domain.lower():
            score += 0.6
            factors.append("domain match")
        if name and dup.name and dup.name.lower() == name.lower():
            score += 0.4
            factors.append("name match")
        if score >= 0.5:
            results.append({
                "id": str(dup.id), "name": dup.name, "domain": dup.domain,
                "score": round(score, 2), "factors": factors,
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)
