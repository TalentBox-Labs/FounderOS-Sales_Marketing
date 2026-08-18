"""REV-ORCH M1 — canonical revenue orchestration API on runner_api."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from revenue_os.database import SessionLocal
from revenue_os.agents.orchestration import (
    REV_ORCH_M1_WORKFLOW_KEY,
    REV_ORCH_M2_WORKFLOW_KEY,
    REV_ORCH_M4_WORKFLOW_KEY,
    WorkflowOrchestrator,
)
from revenue_os.services.revenue_orchestration_service import (
    RevenueOrchestrationError,
    inspect_booking_availability,
    inspect_booking_eligibility,
    inspect_follow_up_eligibility,
    inspect_latest_reply_assessment,
)
from revenue_os.services.tenant_resolution import require_tenant_context
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/revenue", tags=["revenue-orchestration"])


class ResearchToOutreachRequest(BaseModel):
    """Optional body; organization comes from server TenantContext only."""

    organization_id: str | None = Field(
        default=None,
        description="Ignored if supplied — tenant is server-derived",
    )


class BookingProposeRequest(BaseModel):
    """Optional slot selection for M4 booking proposal."""

    organization_id: str | None = Field(
        default=None,
        description="Ignored if supplied — tenant is server-derived",
    )
    selected_slot: dict[str, str] | None = Field(
        default=None,
        description="Optional human-selected slot {start, end} in ISO8601 UTC",
    )


@router.post("/contacts/{contact_id}/research-to-outreach")
def research_to_outreach(
    contact_id: str,
    http_request: Request,
    _: ResearchToOutreachRequest = ResearchToOutreachRequest(),
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M1 vertical slice: research → qualify → draft → ApprovalRequest (pending)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        result = WorkflowOrchestrator.execute_revenue_workflow(
            REV_ORCH_M1_WORKFLOW_KEY,
            db=db,
            tenant=tenant,
            contact_id=contact_id,
        )
        return {"ok": True, **result}
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("M1 orchestration failed for contact %s", contact_id)
        raise HTTPException(status_code=500, detail="Orchestration failed") from exc
    finally:
        db.close()


@router.get("/contacts/{contact_id}/follow-up/eligibility")
def follow_up_eligibility(
    contact_id: str,
    http_request: Request,
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M2: deterministic follow-up eligibility inspection (no AI, no send)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        return inspect_follow_up_eligibility(db, tenant, contact_id)
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        db.close()


@router.post("/contacts/{contact_id}/follow-up/propose")
def follow_up_propose(
    contact_id: str,
    http_request: Request,
    _: ResearchToOutreachRequest = ResearchToOutreachRequest(),
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M2: eligibility → FollowUpWorker → ApprovalRequest (pending)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        result = WorkflowOrchestrator.execute_revenue_workflow(
            REV_ORCH_M2_WORKFLOW_KEY,
            db=db,
            tenant=tenant,
            contact_id=contact_id,
        )
        return {"ok": True, **result}
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("M2 follow-up orchestration failed for contact %s", contact_id)
        raise HTTPException(status_code=500, detail="Orchestration failed") from exc
    finally:
        db.close()


@router.get("/contacts/{contact_id}/reply/latest-assessment")
def latest_reply_assessment(
    contact_id: str,
    http_request: Request,
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M3: inspect last inbound-reply assessment (no AI, no mutation)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        return inspect_latest_reply_assessment(db, tenant, contact_id)
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        db.close()


@router.get("/contacts/{contact_id}/booking/eligibility")
def booking_eligibility(
    contact_id: str,
    http_request: Request,
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M4: deterministic booking eligibility inspection (no AI, no calendar)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        return inspect_booking_eligibility(db, tenant, contact_id)
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        db.close()


@router.get("/contacts/{contact_id}/booking/availability")
def booking_availability(
    contact_id: str,
    http_request: Request,
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M4: tenant-scoped calendar availability (requires booking eligibility)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        return inspect_booking_availability(db, tenant, contact_id)
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        db.close()


@router.post("/contacts/{contact_id}/booking/propose")
def booking_propose(
    contact_id: str,
    http_request: Request,
    body: BookingProposeRequest = BookingProposeRequest(),
    __: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """M4: eligibility → availability → BookingWorker → ApprovalRequest (pending)."""
    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        extra = {"selected_slot": body.selected_slot} if body.selected_slot else None
        result = WorkflowOrchestrator.execute_revenue_workflow(
            REV_ORCH_M4_WORKFLOW_KEY,
            db=db,
            tenant=tenant,
            contact_id=contact_id,
            extra=extra,
        )
        return {"ok": True, **result}
    except RevenueOrchestrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("M4 booking orchestration failed for contact %s", contact_id)
        raise HTTPException(status_code=500, detail="Orchestration failed") from exc
    finally:
        db.close()
