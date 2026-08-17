"""SaaS S2 — bootstrap Organization + membership for existing Founder installs."""

from __future__ import annotations

import logging
import os
import uuid

from sqlalchemy.orm import Session

from revenue_os.database import SessionLocal
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.contact import Contact
from revenue_os.models.deal import Deal
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.tenant_resolution import ENV_BOOTSTRAP_ORG_NAME, slugify_name

logger = logging.getLogger(__name__)


def _default_org_name() -> str:
    return (
        os.environ.get(ENV_BOOTSTRAP_ORG_NAME)
        or os.environ.get("FOUNDER_OS_OPERATOR_NAME")
        or "Founder Organization"
    ).strip() or "Founder Organization"


def _ensure_unique_slug(db: Session, base_slug: str) -> str:
    slug = base_slug
    suffix = 0
    while db.query(Organization).filter(Organization.slug == slug).first() is not None:
        suffix += 1
        slug = f"{base_slug}-{suffix}"
    return slug


def bootstrap_organization_for_users(db: Session) -> Organization | None:
    """Create one default organization and OWNER memberships for users without any."""
    users = db.query(User).filter(User.is_active == 1).all()
    if not users:
        return None

    existing_org = db.query(Organization).first()
    if existing_org is None:
        name = _default_org_name()
        slug = _ensure_unique_slug(db, slugify_name(name))
        org = Organization(name=name, slug=slug, status=OrganizationStatus.ACTIVE)
        db.add(org)
        db.flush()
        for user in users:
            db.add(
                OrganizationMembership(
                    user_id=user.id,
                    organization_id=org.id,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                )
            )
        db.commit()
        logger.info("Bootstrapped organization %s for %d user(s)", slug, len(users))
        return org

    for user in users:
        has_membership = (
            db.query(OrganizationMembership)
            .filter(OrganizationMembership.user_id == user.id)
            .first()
        )
        if has_membership is None:
            db.add(
                OrganizationMembership(
                    user_id=user.id,
                    organization_id=existing_org.id,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                )
            )
    db.commit()
    return existing_org


def backfill_tenant_ownership(db: Session, organization_id: uuid.UUID) -> None:
    """Assign null organization_id on tenant-owned rows to the bootstrap org."""
    oid = organization_id
    for contact in db.query(Contact).filter(Contact.organization_id.is_(None)).all():
        contact.organization_id = oid
        db.add(contact)
    for deal in db.query(Deal).filter(Deal.organization_id.is_(None)).all():
        deal.organization_id = oid
        db.add(deal)
    for row in db.query(AgentActionLog).filter(AgentActionLog.organization_id.is_(None)).all():
        row.organization_id = oid
        db.add(row)
    db.commit()
    logger.info("Backfilled tenant ownership for organization %s", organization_id)


def bootstrap_tenant_if_needed() -> None:
    db = SessionLocal()
    try:
        org = bootstrap_organization_for_users(db)
        if org is not None:
            backfill_tenant_ownership(db, org.id)
    except Exception:
        logger.exception("Tenant bootstrap failed")
        db.rollback()
    finally:
        db.close()
