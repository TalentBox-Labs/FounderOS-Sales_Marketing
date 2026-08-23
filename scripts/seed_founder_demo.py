#!/usr/bin/env python3
"""Development-only demo seed for Founder OS UI-D1 live demo journey.

Usage:
  SECRET_KEY=... DATABASE_URL=sqlite:///./founder_demo.db python scripts/seed_founder_demo.py

Does not run on application startup. Safe for local demos only.
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from revenue_os.auth import hash_password
from revenue_os.database import SessionLocal, init_db
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.contact import Company, Contact, ContactSource, ContactStatus
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.marketing_qualified_demand import compose_marketing_qualified_demand
from revenue_os.services.qualified_demand_service import (
    ACTION_HANDOFF,
    PersonPayload,
    register_marketing_handoff,
)

DEMO_EMAIL = os.environ.get("FOUNDER_DEMO_EMAIL", "founder@demo.local")
DEMO_PASSWORD = os.environ.get("FOUNDER_DEMO_PASSWORD", "FounderDemo123!")
DEMO_NAME = os.environ.get("FOUNDER_DEMO_NAME", "Demo Founder")
DEMO_ORG = os.environ.get("FOUNDER_DEMO_ORG", "Demo Workspace")
DEMO_COMPANY_NAME = "Acme Labs"
DEMO_COMPANY_DOMAIN = "acmelabs.demo.local"
DEMO_COMPANY_ID = "ca11e001-0000-4000-8000-000000000001"
DEMAND_ID = "11111111-1111-1111-1111-111111111111"
CONTACT_ID = "c2222222-2222-2222-2222-222222222222"
CONTACT_EMAIL = "alex.prospect@example.com"


def ensure_demo_company(db) -> Company:  # noqa: ANN001
    """Create or reuse the Founder demo Company. Repeat-safe via unique domain."""
    company = (
        db.query(Company).filter(Company.domain == DEMO_COMPANY_DOMAIN).first()
    )
    if company is None:
        company = db.query(Company).filter(Company.name == DEMO_COMPANY_NAME).first()
    if company is None:
        company = Company(
            id=uuid.UUID(DEMO_COMPANY_ID),
            name=DEMO_COMPANY_NAME,
            domain=DEMO_COMPANY_DOMAIN,
        )
        db.add(company)
        db.flush()
    elif company.domain is None:
        company.domain = DEMO_COMPANY_DOMAIN
        db.flush()
    return company


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "demo-workspace").first()
        if org is None:
            org = Organization(
                id=uuid.uuid4(),
                name=DEMO_ORG,
                slug="demo-workspace",
                status=OrganizationStatus.ACTIVE,
            )
            db.add(org)
            db.flush()

        user = db.query(User).filter(User.email == DEMO_EMAIL.lower()).first()
        if user is None:
            user = User(
                email=DEMO_EMAIL.lower(),
                hashed_password=hash_password(DEMO_PASSWORD),
                full_name=DEMO_NAME,
                role="owner",
                is_active=1,
            )
            db.add(user)
            db.flush()

        membership = (
            db.query(OrganizationMembership)
            .filter(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.organization_id == org.id,
            )
            .first()
        )
        if membership is None:
            db.add(
                OrganizationMembership(
                    user_id=user.id,
                    organization_id=org.id,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                )
            )

        company = ensure_demo_company(db)

        contact = (
            db.query(Contact).filter(Contact.email == CONTACT_EMAIL).first()
        )
        if contact is None:
            contact = Contact(
                id=uuid.UUID(CONTACT_ID),
                organization_id=org.id,
                first_name="Alex",
                last_name="Prospect",
                email=CONTACT_EMAIL,
                status=ContactStatus.LEAD,
                lead_score=72,
                source=ContactSource.WEB_FORM,
                company=company,
            )
            db.add(contact)

        existing_handoff = (
            db.query(AgentActionLog)
            .filter(
                AgentActionLog.action_type == ACTION_HANDOFF,
                AgentActionLog.target_id == DEMAND_ID,
            )
            .first()
        )
        if existing_handoff is None:
            payload = compose_marketing_qualified_demand(
                demand_id=DEMAND_ID,
                occurred_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                source="web_form",
                channel="website",
                person=PersonPayload(email="new.demand@example.com", name="New Demand Lead"),
                company_hint={"name": "Inbound Co"},
                marketing_qualification={
                    "tier": "mql",
                    "score": 72,
                    "reason": "Requested a product walkthrough from the website form.",
                    "qualification_mode": "marketing_signal",
                },
                content_attribution={
                    "utm_source": "website",
                    "campaign": "demo-inbound",
                },
            )
            register_marketing_handoff(
                db,
                payload,
                DEMO_NAME,
                organization_id=str(org.id),
            )

        db.commit()
        print("✅ Founder demo seed complete")
        print(f"   Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"   Organization: {org.name} ({org.id})")
        print(f"   Contact workspace: /contacts/{CONTACT_ID}")
        print("   Set FOUNDER_OS_OPERATOR_NAME or sign in to enable actions")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
