"""SaaS S2 — shared tenant mutation guards for Founder UI proxies."""

from __future__ import annotations

import uuid as uuid_lib

from fastapi import HTTPException
from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact
from revenue_os.models.deal import Deal
from revenue_os.services.commercial_outcome_service import ACTION_HANDOFF as CO_HANDOFF
from revenue_os.services.commercial_outcome_service import (
    ACTION_ACCEPTED as CO_ACCEPTED,
)
from revenue_os.services.commercial_outcome_service import (
    ACTION_REJECTED as CO_REJECTED,
)
from revenue_os.services.qualified_demand_service import ACTION_HANDOFF as QD_HANDOFF
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED as QD_ACCEPTED,
)
from revenue_os.services.qualified_demand_service import (
    ACTION_REJECTED as QD_REJECTED,
)
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.tenant_resolution import require_tenant_mutation_role, resolve_tenant_context
from revenue_os.services.tenant_scoped_access import (
    TenantAccessError,
    get_commercial_outcome_handoff_for_tenant,
    get_contact_for_tenant,
    get_deal_for_tenant,
    get_qualified_demand_handoff_for_tenant,
    stamp_agent_action_log_organization,
    stamp_contact_organization_if_missing,
)


def require_tenant_mutation() -> TenantContext:
    """Fail closed when organization context is missing for tenant-scoped mutations."""
    tenant = resolve_tenant_context(fail_closed_on_db_error=True)
    if tenant is None:
        raise HTTPException(status_code=403, detail="Organization context required")
    require_tenant_mutation_role(tenant)
    return tenant


def optional_tenant_mutation() -> TenantContext | None:
    """Return tenant context when resolvable; None preserves legacy env-operator paths."""
    tenant = resolve_tenant_context()
    if tenant is None:
        return None
    require_tenant_mutation_role(tenant)
    return tenant


def resolve_crm_tenant_read() -> TenantContext | None:
    """CRM read paths — resolves tenant without VIEWER mutation block."""
    return resolve_tenant_context()


def crm_tenant_org_id(tenant: TenantContext | None) -> str | None:
    return tenant.organization_id if tenant is not None else None


def scoped_contact(
    db: Session, tenant: TenantContext | None, contact_id: str
) -> Contact:
    if tenant is not None:
        try:
            return get_contact_for_tenant(db, tenant.organization_id, contact_id)
        except TenantAccessError as exc:
            raise HTTPException(status_code=404, detail="Contact not found") from exc
    try:
        cid = uuid_lib.UUID(contact_id.strip())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid contact_id") from exc
    contact = db.get(Contact, cid)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


def scoped_deal(db: Session, tenant: TenantContext | None, deal_id: str) -> Deal:
    if tenant is not None:
        try:
            return get_deal_for_tenant(db, tenant.organization_id, deal_id)
        except TenantAccessError as exc:
            raise HTTPException(status_code=404, detail="Deal not found") from exc
    try:
        did = uuid_lib.UUID(deal_id.strip())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid deal_id") from exc
    deal = db.get(Deal, did)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


def scoped_demand_handoff(
    db: Session, tenant: TenantContext | None, demand_id: str
) -> None:
    if tenant is None:
        return
    try:
        get_qualified_demand_handoff_for_tenant(db, tenant.organization_id, demand_id)
    except TenantAccessError as exc:
        raise HTTPException(status_code=404, detail="QualifiedDemand not found") from exc


def scoped_outcome_handoff(
    db: Session, tenant: TenantContext | None, outcome_id: str
) -> None:
    if tenant is None:
        return
    try:
        get_commercial_outcome_handoff_for_tenant(db, tenant.organization_id, outcome_id)
    except TenantAccessError as exc:
        raise HTTPException(status_code=404, detail="CommercialOutcome not found") from exc


def after_demand_register(
    db: Session, tenant: TenantContext | None, demand_id: str
) -> None:
    if tenant is None:
        return
    stamp_agent_action_log_organization(
        db,
        action_type=QD_HANDOFF,
        target_id=demand_id,
        organization_id=tenant.organization_id,
    )


def after_demand_accept(
    db: Session, tenant: TenantContext | None, result: dict
) -> None:
    if tenant is None:
        return
    contact_id = result.get("contact_id")
    if contact_id:
        stamp_contact_organization_if_missing(db, str(contact_id), tenant.organization_id)
    demand_id = result.get("demand_id")
    if demand_id:
        stamp_agent_action_log_organization(
            db,
            action_type=QD_ACCEPTED,
            target_id=str(demand_id),
            organization_id=tenant.organization_id,
        )


def after_demand_reject(
    db: Session, tenant: TenantContext | None, demand_id: str
) -> None:
    if tenant is None:
        return
    stamp_agent_action_log_organization(
        db,
        action_type=QD_REJECTED,
        target_id=demand_id,
        organization_id=tenant.organization_id,
    )


def assign_new_deal_org(deal: Deal, tenant: TenantContext | None) -> None:
    if tenant is not None:
        deal.organization_id = uuid_lib.UUID(tenant.organization_id)


def after_outcome_handoff(
    db: Session, tenant: TenantContext | None, outcome_id: str
) -> None:
    if tenant is None:
        return
    stamp_agent_action_log_organization(
        db,
        action_type=CO_HANDOFF,
        target_id=outcome_id,
        organization_id=tenant.organization_id,
    )


def after_outcome_decision(
    db: Session,
    tenant: TenantContext | None,
    *,
    outcome_id: str,
    accepted: bool,
) -> None:
    if tenant is None:
        return
    stamp_agent_action_log_organization(
        db,
        action_type=CO_ACCEPTED if accepted else CO_REJECTED,
        target_id=outcome_id,
        organization_id=tenant.organization_id,
    )
