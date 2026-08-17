"""OF1 — trusted-human operator workflow proxies.

Composes frozen MC04.5 / A4.5 / A3.5 / MC06.5 services.
Client-supplied requested_by is never trusted.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from revenue_os.database import SessionLocal
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from revenue_os.services.commercial_outcome_service import (
    CommercialOutcomePayload,
    accept_commercial_outcome,
    register_commercial_outcome_handoff,
    reject_commercial_outcome,
)
from revenue_os.services.deal_automation_service import (
    apply_deal_stage_update,
    get_or_create_sales_pipeline,
)
from revenue_os.services.lead_scoring_service import apply_contact_status_update
from revenue_os.services.mutation_authority import HumanAuthorityError
from revenue_os.services.operator_flow_read_model import (
    OPERATOR_CREATE_STAGES,
    build_operator_flow_snapshot,
)
from revenue_os.services.qualified_demand_service import (
    accept_qualified_demand,
    reject_qualified_demand,
)
from revenue_os.services.tenant_mutation_guard import (
    after_demand_accept,
    after_demand_reject,
    after_outcome_decision,
    after_outcome_handoff,
    assign_new_deal_org,
    optional_tenant_mutation,
    scoped_contact,
    scoped_deal,
    scoped_demand_handoff,
    scoped_outcome_handoff,
)
from revenue_os.services.tenant_resolution import resolve_tenant_context
from runner_api_routers.cockpit import _trusted_cockpit_operator, cockpit_operator_status
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/operator", tags=["operator-flow"])


class DemandDecisionBody(BaseModel):
    demand_id: str = Field(..., min_length=8, max_length=64)
    notes: str = Field(default="", max_length=2000)
    reason: str = Field(default="", max_length=2000)


class ContactStatusBody(BaseModel):
    contact_id: str = Field(..., min_length=8, max_length=64)
    status: str = Field(..., min_length=1, max_length=64)


class DealCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    contact_id: str = Field(..., min_length=8, max_length=64)
    value: float = Field(default=0.0, ge=0)
    stage: str = Field(default="discovery", max_length=64)


class DealStageBody(BaseModel):
    deal_id: str = Field(..., min_length=8, max_length=64)
    stage: str = Field(..., min_length=1, max_length=64)
    notes: str = Field(default="", max_length=2000)


class OutcomeHandoffBody(BaseModel):
    deal_id: str = Field(..., min_length=8, max_length=64)
    handoff_hints: str | None = Field(default=None, max_length=2000)


class OutcomeDecisionBody(BaseModel):
    outcome_id: str = Field(..., min_length=8, max_length=64)
    notes: str = Field(default="", max_length=2000)
    reason: str = Field(default="", max_length=2000)


def _service_http(exc: Exception) -> HTTPException:
    if isinstance(exc, HumanAuthorityError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Operator request failed")


@router.get("/snapshot")
def operator_snapshot(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    tenant = resolve_tenant_context()
    org_id = tenant.organization_id if tenant else None
    return {"ok": True, **build_operator_flow_snapshot(organization_id=org_id)}


@router.get("/operator")
def operator_identity(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    return {"ok": True, **cockpit_operator_status()}


@router.post("/actions/qualified-demand/accept")
def operator_accept_demand(
    body: DemandDecisionBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """MC04.5 accept via trusted server operator — canonical service path only."""
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    db = SessionLocal()
    try:
        scoped_demand_handoff(db, tenant, body.demand_id.strip())
        try:
            result = accept_qualified_demand(
                db, body.demand_id.strip(), operator, body.notes.strip()
            )
            after_demand_accept(db, tenant, result)
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "qualified_demand_accept", **result}


@router.post("/actions/qualified-demand/reject")
def operator_reject_demand(
    body: DemandDecisionBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    reason = body.reason.strip() or body.notes.strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail="Reject reason is required")
    db = SessionLocal()
    try:
        scoped_demand_handoff(db, tenant, body.demand_id.strip())
        try:
            result = reject_qualified_demand(
                db, body.demand_id.strip(), operator, reason
            )
            after_demand_reject(db, tenant, body.demand_id.strip())
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "qualified_demand_reject", **result}


@router.post("/actions/contact-status")
def operator_contact_status(
    body: ContactStatusBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    try:
        new_status = ContactStatus(body.status.strip().lower())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid contact_id or status") from exc
    db = SessionLocal()
    try:
        contact = scoped_contact(db, tenant, body.contact_id.strip())
        try:
            result = apply_contact_status_update(
                db, contact, new_status, requested_by=operator
            )
        except HumanAuthorityError as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "contact_status", **result}


@router.post("/actions/deal/create")
def operator_create_deal(
    body: DealCreateBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Trusted-human Deal create — does not replace ungated CRM POST."""
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    try:
        stage = DealStage(body.stage.strip().lower())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid stage or contact_id") from exc
    if stage not in OPERATOR_CREATE_STAGES:
        raise HTTPException(
            status_code=422,
            detail="Operator Deal create allows non-terminal sales stages only",
        )
    db = SessionLocal()
    try:
        contact = scoped_contact(db, tenant, body.contact_id.strip())
        contact_id = contact.id
        pipeline = get_or_create_sales_pipeline(db)
        deal = Deal(
            name=body.name.strip(),
            value=body.value,
            stage=stage,
            contact_id=contact_id,
            pipeline_id=pipeline.id,
        )
        assign_new_deal_org(deal, tenant)
        db.add(deal)
        db.commit()
        db.refresh(deal)
        result = {
            "deal_id": str(deal.id),
            "stage": deal.stage.value,
            "contact_id": str(contact_id),
            "created_by": operator,
        }
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "deal_create", **result}


@router.post("/actions/deal/stage")
def operator_deal_stage(
    body: DealStageBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    try:
        new_stage = DealStage(body.stage.strip().lower())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid deal_id or stage") from exc
    db = SessionLocal()
    try:
        deal = scoped_deal(db, tenant, body.deal_id.strip())
        try:
            result = apply_deal_stage_update(
                db, deal, new_stage, requested_by=operator
            )
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "deal_stage", **result}


@router.post("/actions/commercial-outcome/handoff")
def operator_outcome_handoff(
    body: OutcomeHandoffBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    payload = CommercialOutcomePayload(
        outcome_id=str(uuid_lib.uuid4()),
        deal_id=body.deal_id.strip(),
        outcome="closed_won",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        handoff_hints=body.handoff_hints,
    )
    db = SessionLocal()
    try:
        scoped_deal(db, tenant, body.deal_id.strip())
        try:
            result = register_commercial_outcome_handoff(db, payload, operator)
            after_outcome_handoff(db, tenant, payload.outcome_id)
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "commercial_outcome_handoff", **result}


@router.post("/actions/commercial-outcome/accept")
def operator_outcome_accept(
    body: OutcomeDecisionBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    db = SessionLocal()
    try:
        scoped_outcome_handoff(db, tenant, body.outcome_id.strip())
        try:
            result = accept_commercial_outcome(
                db, body.outcome_id.strip(), operator, body.notes.strip()
            )
            after_outcome_decision(
                db, tenant, outcome_id=body.outcome_id.strip(), accepted=True
            )
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "commercial_outcome_accept", **result}


@router.post("/actions/commercial-outcome/reject")
def operator_outcome_reject(
    body: OutcomeDecisionBody,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    tenant = optional_tenant_mutation()
    operator = _trusted_cockpit_operator()
    reason = body.reason.strip() or body.notes.strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail="Reject reason is required")
    db = SessionLocal()
    try:
        scoped_outcome_handoff(db, tenant, body.outcome_id.strip())
        try:
            result = reject_commercial_outcome(
                db, body.outcome_id.strip(), operator, reason
            )
            after_outcome_decision(
                db, tenant, outcome_id=body.outcome_id.strip(), accepted=False
            )
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_http(exc) from exc
    finally:
        db.close()
    return {"ok": True, "operator": operator, "action": "commercial_outcome_reject", **result}
