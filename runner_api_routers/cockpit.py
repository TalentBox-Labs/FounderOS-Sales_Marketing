"""Executive Cockpit — trusted human action proxies and read API.

UI2: mutations use server-configured operator identity (FOUNDER_OS_OPERATOR_NAME).
Client-supplied requested_by is never trusted.
"""

from __future__ import annotations

import logging
import os
import uuid as uuid_lib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from revenue_os.automation.events import Event, EventBus, EventType
from revenue_os.database import SessionLocal
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.services.cockpit_read_model import build_cockpit_snapshot
from revenue_os.services.qualified_demand_service import accept_qualified_demand
from revenue_os.services.lead_scoring_service import apply_contact_status_update
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.tenant_mutation_guard import (
    after_demand_accept,
    optional_tenant_mutation,
    require_tenant_mutation,
    scoped_contact,
    scoped_demand_handoff,
)
from revenue_os.services.tenant_resolution import resolve_tenant_context
from runner_api_routers.utils import _verify_api_key
from src.tools.editorial_approval import is_human_approver

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/cockpit", tags=["cockpit"])

ENV_OPERATOR = "FOUNDER_OS_OPERATOR_NAME"


def _trusted_cockpit_operator() -> str:
    """Return trusted human operator; never accept client spoofing.

    SaaS S1: authenticated IdentityContext (session) is authoritative.
    Legacy fallback: FOUNDER_OS_OPERATOR_NAME (not HUMAN via API key).
    """
    from runner_api_routers.identity import resolve_trusted_human

    return resolve_trusted_human()


def cockpit_operator_status() -> dict[str, Any]:
    from runner_api_routers.identity import identity_from_request, current_request

    request = current_request()
    ctx = identity_from_request(request) if request is not None else None
    if ctx is not None and ctx.is_human:
        return {
            "configured": True,
            "operator_name": ctx.display_name,
            "env_var": ENV_OPERATOR,
            "auth_method": ctx.auth_method.value,
            "role": ctx.role,
        }
    name = (os.environ.get(ENV_OPERATOR) or "").strip()
    configured = is_human_approver(name)
    return {
        "configured": configured,
        "operator_name": name if configured else None,
        "env_var": ENV_OPERATOR,
        "auth_method": "legacy_operator_env" if configured else "none",
        "role": None,
    }


class DemandAcceptBody(BaseModel):
    demand_id: str = Field(..., min_length=8, max_length=64)
    notes: str = Field(default="", max_length=2000)


class ContactStatusBody(BaseModel):
    contact_id: str = Field(..., min_length=8, max_length=64)
    status: str = Field(..., min_length=1, max_length=64)
    notes: str = Field(default="", max_length=2000)


@router.get("/snapshot")
def cockpit_snapshot(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    """Read-only cockpit composition for tests and optional client refresh."""
    tenant = resolve_tenant_context()
    org_id = tenant.organization_id if tenant else None
    return build_cockpit_snapshot(organization_id=org_id)


@router.get("/operator")
def cockpit_operator(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    """Whether trusted cockpit operator is configured (no secrets)."""
    status = cockpit_operator_status()
    return {"ok": True, **status}


@router.post("/actions/qualified-demand/accept")
def cockpit_accept_qualified_demand(
    body: DemandAcceptBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """MC04.5 accept via trusted server operator — canonical service path only."""
    operator = _trusted_cockpit_operator()
    tenant = require_tenant_mutation()
    db = SessionLocal()
    try:
        scoped_demand_handoff(db, tenant, body.demand_id.strip())
        try:
            result = accept_qualified_demand(
                db,
                body.demand_id.strip(),
                operator,
                body.notes.strip(),
                organization_id=tenant.organization_id,
            )
            after_demand_accept(db, tenant, result)
        except HumanAuthorityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        db.close()

    if result.get("idempotent") is False or result.get("contact_id"):
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.CONTACT_IMPORTED,
                    source="cockpit_sales_intake",
                    entity_id=result.get("contact_id") or body.demand_id,
                    entity_type="contact",
                    data={
                        "demand_id": body.demand_id,
                        "created": result.get("created"),
                        "merged": result.get("merged"),
                        "requested_by": operator,
                        "deal_created": False,
                        "via": "executive_cockpit",
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cockpit accept event publish failed: %s", exc)

    return {"ok": True, "operator": operator, **result}


@router.post("/actions/contact-status")
def cockpit_update_contact_status(
    body: ContactStatusBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """A4.5 status update via trusted server operator — canonical service path only."""
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    try:
        new_status = ContactStatus(body.status.strip().lower())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid status: {body.status}") from exc

    db = SessionLocal()
    try:
        contact = scoped_contact(db, tenant, body.contact_id.strip())
        try:
            result = apply_contact_status_update(
                db, contact, new_status, requested_by=operator
            )
        except HumanAuthorityError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
    finally:
        db.close()

    if result["changed"]:
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.CONTACT_STATUS_CHANGED,
                    source="cockpit_crm",
                    entity_id=result.get("contact_id") or body.contact_id,
                    entity_type="contact",
                    data={
                        "old_status": result["old_status"],
                        "new_status": result["new_status"],
                        "requested_by": operator,
                        "notes": body.notes.strip() or None,
                        "via": "executive_cockpit",
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cockpit status event publish failed: %s", exc)

    return {"ok": True, "operator": operator, **result}
