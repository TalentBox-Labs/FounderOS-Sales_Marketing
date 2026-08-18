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
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.qualified_demand_service import (
    ACTION_HANDOFF,
    QualifiedDemandPayload,
    PersonPayload,
    register_marketing_handoff,
)

DEMO_EMAIL = os.environ.get("FOUNDER_DEMO_EMAIL", "founder@demo.local")
DEMO_PASSWORD = os.environ.get("FOUNDER_DEMO_PASSWORD", "FounderDemo123!")
DEMO_NAME = os.environ.get("FOUNDER_DEMO_NAME", "Demo Founder")
DEMO_ORG = os.environ.get("FOUNDER_DEMO_ORG", "Demo Workspace")
DEMAND_ID = "11111111-1111-1111-1111-111111111111"
CONTACT_ID = "22222222-2222-2222-2222-222222222222"


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

        contact = db.get(Contact, uuid.UUID(CONTACT_ID))
        if contact is None:
            contact = Contact(
                id=uuid.UUID(CONTACT_ID),
                organization_id=org.id,
                first_name="Alex",
                last_name="Prospect",
                email="alex.prospect@example.com",
                status=ContactStatus.LEAD,
                lead_score=72,
                source=ContactSource.WEB_FORM,
                company="Acme Labs",
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
            payload = QualifiedDemandPayload(
                demand_id=DEMAND_ID,
                occurred_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                source="manual",
                person=PersonPayload(email="new.demand@example.com", name="New Demand Lead"),
            )
            register_marketing_handoff(db, payload, DEMO_NAME)

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
