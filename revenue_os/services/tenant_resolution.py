"""SaaS S2 — tenant resolution and role enforcement."""

from __future__ import annotations

import logging
import os
import re
import uuid

from fastapi import HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from revenue_os.database import SessionLocal
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.identity_context import IdentityContext, PrincipalKind
from revenue_os.services.tenant_context import (
    TenantContext,
    assert_valid_membership_role,
    membership_role_allows_mutation,
    parse_org_uuid,
)
from runner_api_routers.identity import (
    IDENTITY_COOKIE,
    current_request,
    identity_from_request,
)

logger = logging.getLogger(__name__)

ORGANIZATION_COOKIE = "founder_os_organization"
ENV_BOOTSTRAP_ORG_NAME = "FOUNDER_OS_BOOTSTRAP_ORG_NAME"

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify_name(name: str) -> str:
    base = _SLUG_RE.sub("-", name.strip().lower()).strip("-") or "org"
    return base[:120]


def require_tenant_mutation_role(tenant: TenantContext) -> None:
    if not tenant.identity.is_human:
        raise HTTPException(
            status_code=403,
            detail=f"{tenant.identity.principal_kind.value} cannot perform tenant mutations",
        )
    if tenant.membership_status != MembershipStatus.ACTIVE.value:
        raise HTTPException(status_code=403, detail="Membership is not active")
    if not membership_role_allows_mutation(tenant.membership_role):
        raise HTTPException(
            status_code=403,
            detail="VIEWER role cannot perform mutations",
        )


def _load_membership(
    db: Session, user_id: uuid.UUID, organization_id: uuid.UUID
) -> OrganizationMembership | None:
    return (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
        )
        .first()
    )


def _active_memberships(db: Session, user_id: uuid.UUID) -> list[OrganizationMembership]:
    return (
        db.query(OrganizationMembership)
        .join(Organization)
        .filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
            Organization.status == OrganizationStatus.ACTIVE,
        )
        .all()
    )


def resolve_tenant_context(
    request: Request | None = None,
    *,
    organization_id_hint: str | None = None,
    fail_closed_on_db_error: bool = False,
) -> TenantContext | None:
    """Server-derived TenantContext. Client hints are validated against membership."""
    req = request if request is not None else current_request()
    if req is None:
        return None
    identity = identity_from_request(req)
    if identity is None or identity.principal_kind is not PrincipalKind.HUMAN:
        return None
    if not identity.user_id:
        return None

    org_hint = organization_id_hint or req.cookies.get(ORGANIZATION_COOKIE)
    try:
        user_uuid = uuid.UUID(str(identity.user_id))
    except ValueError:
        return None

    db = SessionLocal()
    try:
        memberships = _active_memberships(db, user_uuid)
        if not memberships:
            return None

        selected: OrganizationMembership | None = None
        org_uuid = parse_org_uuid(org_hint)
        if org_uuid is not None:
            selected = _load_membership(db, user_uuid, org_uuid)
            if selected is None or selected.status != MembershipStatus.ACTIVE:
                raise HTTPException(status_code=403, detail="Not a member of organization")
        elif len(memberships) == 1:
            selected = memberships[0]
        else:
            raise HTTPException(
                status_code=403,
                detail="Organization context required — select an active organization",
            )

        org = db.get(Organization, selected.organization_id)
        if org is None or org.status != OrganizationStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Organization is not active")

        return TenantContext(
            identity=identity,
            organization_id=str(org.id),
            organization_name=org.name,
            organization_slug=org.slug,
            membership_id=str(selected.id),
            membership_role=assert_valid_membership_role(selected.role or "member"),
            membership_status=selected.status.value,
        )
    except SQLAlchemyError as exc:
        logger.warning("Tenant resolution DB unavailable")
        if fail_closed_on_db_error:
            raise HTTPException(
                status_code=503,
                detail="Tenant resolution unavailable",
            ) from exc
        logger.warning("Falling back to legacy read mode")
        return None
    finally:
        db.close()


def require_tenant_context(request: Request | None = None) -> TenantContext:
    tenant = resolve_tenant_context(request)
    if tenant is None:
        raise HTTPException(
            status_code=403,
            detail="Authenticated human tenant context required",
        )
    return tenant


def set_organization_cookie(response, organization_id: str) -> None:  # noqa: ANN001
    from runner_api_routers.identity import _cookie_secure

    response.set_cookie(
        key=ORGANIZATION_COOKIE,
        value=organization_id,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
        max_age=60 * 60 * 24 * 30,
        path="/",
    )


def clear_organization_cookie(response) -> None:  # noqa: ANN001
    response.delete_cookie(key=ORGANIZATION_COOKIE, path="/")
