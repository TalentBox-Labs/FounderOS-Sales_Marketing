from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from revenue_os.models.contact import Company, Contact


def find_company_by_domain(db: Session, domain: str) -> Optional[Company]:
    return db.query(Company).filter(Company.domain == domain).first()


def find_contact_by_email(db: Session, email: str) -> Optional[Contact]:
    return db.query(Contact).filter(Contact.email == email).first()


def bulk_upsert_contacts(
    db: Session, contacts_data: list[dict]
) -> list[Contact]:
    results: list[Contact] = []
    for data in contacts_data:
        email = data.get("email")
        existing = None
        if email:
            existing = find_contact_by_email(db, email)

        if existing:
            for key, value in data.items():
                if value is not None:
                    setattr(existing, key, value)
            results.append(existing)
        else:
            contact = Contact(**data)
            db.add(contact)
            results.append(contact)

    db.commit()
    for c in results:
        db.refresh(c)
    return results
