"""MC04 — QualifiedDemand Marketing→Sales handoff runner routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from revenue_os.automation.events import Event, EventBus, EventType
from revenue_os.database import SessionLocal
from revenue_os.services.qualified_demand_service import (
    QualifiedDemandPayload,
    accept_qualified_demand,
    register_marketing_handoff,
    reject_qualified_demand,
)
from runner_api_routers.utils import _verify_api_key
from src.tools.editorial_approval import is_human_approver

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["qualified-demand"])


class HandoffRequest(BaseModel):
    """Marketing operator handoff — registers payload; does not create CRM entities."""

    demand_id: str
    occurred_at: str
    source: str
    channel: str | None = None
    person: dict[str, Any]
    company_hint: dict[str, Any] | None = None
    marketing_qualification: dict[str, Any] | None = None
    consent: dict[str, Any] | None = None
    content_attribution: dict[str, Any] | None = None
    requested_by: str = Field(..., min_length=2, max_length=200)


class IntakeAcceptRequest(BaseModel):
    demand_id: str = Field(..., min_length=8, max_length=64)
    requested_by: str = Field(..., min_length=2, max_length=200)
    notes: str = Field(default="", max_length=2000)


class IntakeRejectRequest(BaseModel):
    demand_id: str = Field(..., min_length=8, max_length=64)
    requested_by: str = Field(..., min_length=2, max_length=200)
    reason: str = Field(..., min_length=2, max_length=2000)


def _human_gate(requested_by: str, action: str) -> None:
    if not is_human_approver(requested_by):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Human requester required for {action}. "
                "AI/automation identities cannot perform MC04 handoff or intake."
            ),
        )


@router.post("/marketing/qualified-demand/handoff")
def marketing_qualified_demand_handoff(
    req: HandoffRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Register Marketing-qualified demand for Sales intake (no CRM mutation)."""
    _human_gate(req.requested_by, "Marketing QualifiedDemand handoff")
    try:
        payload = QualifiedDemandPayload(
            demand_id=req.demand_id,
            occurred_at=req.occurred_at,
            source=req.source,
            channel=req.channel,
            person=req.person,
            company_hint=req.company_hint,
            marketing_qualification=req.marketing_qualification,
            consent=req.consent,
            content_attribution=req.content_attribution,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db = SessionLocal()
    try:
        result = register_marketing_handoff(db, payload, req.requested_by.strip())
    finally:
        db.close()

    try:
        EventBus.publish(
            Event(
                event_type=EventType.LEAD_CREATED,
                source="marketing_qualified_demand",
                entity_id=payload.demand_id,
                entity_type="qualified_demand",
                data={
                    "demand_id": payload.demand_id,
                    "source": payload.source,
                    "handoff_only": True,
                    "crm_created": False,
                    "requested_by": req.requested_by.strip(),
                },
            )
        )
    except Exception as e:
        logger.warning(f"QualifiedDemand handoff event publish failed: {e}")

    return result


@router.post("/sales/intake/demand/accept")
def sales_intake_accept(
    req: IntakeAcceptRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Human-gated Sales intake accept — canonical Contact create/link only."""
    _human_gate(req.requested_by, "Sales demand intake accept")
    db = SessionLocal()
    try:
        try:
            result = accept_qualified_demand(
                db, req.demand_id, req.requested_by.strip(), req.notes
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        db.close()

    if result.get("idempotent") is False or result.get("contact_id"):
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.CONTACT_IMPORTED,
                    source="sales_intake",
                    entity_id=result.get("contact_id") or req.demand_id,
                    entity_type="contact",
                    data={
                        "demand_id": req.demand_id,
                        "created": result.get("created"),
                        "merged": result.get("merged"),
                        "requested_by": req.requested_by.strip(),
                        "deal_created": False,
                    },
                )
            )
        except Exception as e:
            logger.warning(f"Sales intake accept event publish failed: {e}")

    return result


@router.post("/sales/intake/demand/reject")
def sales_intake_reject(
    req: IntakeRejectRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Human-gated Sales intake reject — audit only."""
    _human_gate(req.requested_by, "Sales demand intake reject")
    db = SessionLocal()
    try:
        try:
            result = reject_qualified_demand(
                db, req.demand_id, req.requested_by.strip(), req.reason
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        db.close()

    if result.get("idempotent") is False:
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.LEAD_CREATED,
                    source="sales_intake_reject",
                    entity_id=req.demand_id,
                    entity_type="qualified_demand",
                    data={
                        "demand_id": req.demand_id,
                        "rejected": True,
                        "reason": result.get("reason"),
                        "requested_by": req.requested_by.strip(),
                    },
                )
            )
        except Exception as e:
            logger.warning(f"Sales intake reject event publish failed: {e}")

    return result
