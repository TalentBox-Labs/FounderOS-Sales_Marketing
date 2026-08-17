"""MC06 — CommercialOutcome Sales→Revenue handoff runner routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from revenue_os.automation.events import Event, EventBus, EventType
from revenue_os.database import SessionLocal
from revenue_os.services.commercial_outcome_service import (
    CommercialOutcomePayload,
    accept_commercial_outcome,
    register_commercial_outcome_handoff,
    reject_commercial_outcome,
)
from revenue_os.services.mutation_authority import HumanAuthorityError
from runner_api_routers.utils import _verify_api_key
from src.tools.editorial_approval import is_human_approver

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["commercial-outcome"])


class HandoffRequest(BaseModel):
    """Sales operator handoff after eligible closed_won — no Revenue intake."""

    outcome_id: str
    deal_id: str
    outcome: str = "closed_won"
    occurred_at: str
    handoff_hints: str | None = None
    requested_by: str = Field(..., min_length=2, max_length=200)


class IntakeAcceptRequest(BaseModel):
    outcome_id: str = Field(..., min_length=8, max_length=64)
    requested_by: str = Field(..., min_length=2, max_length=200)
    notes: str = Field(default="", max_length=2000)


class IntakeRejectRequest(BaseModel):
    outcome_id: str = Field(..., min_length=8, max_length=64)
    requested_by: str = Field(..., min_length=2, max_length=200)
    reason: str = Field(..., min_length=2, max_length=2000)


def _human_gate(requested_by: str, action: str) -> None:
    if not is_human_approver(requested_by):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Human requester required for {action}. "
                "AI/automation identities cannot perform MC06 handoff or intake."
            ),
        )


def _service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, HumanAuthorityError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="CommercialOutcome request failed")


@router.post("/sales/commercial-outcome/handoff")
def sales_commercial_outcome_handoff(
    req: HandoffRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Register Sales closed-won CommercialOutcome for Revenue intake."""
    _human_gate(req.requested_by, "Sales CommercialOutcome handoff")
    try:
        payload = CommercialOutcomePayload(
            outcome_id=req.outcome_id,
            deal_id=req.deal_id,
            outcome=req.outcome,
            occurred_at=req.occurred_at,
            handoff_hints=req.handoff_hints,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db = SessionLocal()
    try:
        try:
            result = register_commercial_outcome_handoff(
                db, payload, req.requested_by.strip()
            )
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_error(exc) from exc
    finally:
        db.close()

    if result.get("idempotent") is False:
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.COMMERCIAL_OUTCOME_HANDED_OFF,
                    source="sales_commercial_outcome",
                    entity_id=payload.outcome_id,
                    entity_type="commercial_outcome",
                    data={
                        "outcome_id": payload.outcome_id,
                        "deal_id": payload.deal_id,
                        "handoff_only": True,
                        "revenue_accepted": False,
                        "requested_by": req.requested_by.strip(),
                    },
                )
            )
        except Exception as e:
            logger.warning(f"CommercialOutcome handoff event publish failed: {e}")

    return result


@router.post("/revenue/intake/commercial-outcome/accept")
def revenue_intake_accept(
    req: IntakeAcceptRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Human-gated Revenue accept — CommercialOutcome representation only."""
    _human_gate(req.requested_by, "Revenue CommercialOutcome accept")
    db = SessionLocal()
    try:
        try:
            result = accept_commercial_outcome(
                db, req.outcome_id, req.requested_by.strip(), req.notes
            )
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_error(exc) from exc
    finally:
        db.close()

    if result.get("idempotent") is False:
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.COMMERCIAL_OUTCOME_ACCEPTED,
                    source="revenue_intake",
                    entity_id=req.outcome_id,
                    entity_type="commercial_outcome",
                    data={
                        "outcome_id": req.outcome_id,
                        "deal_id": result.get("deal_id"),
                        "accepted": True,
                        "recognized_revenue": False,
                        "requested_by": req.requested_by.strip(),
                    },
                )
            )
        except Exception as e:
            logger.warning(f"CommercialOutcome accept event publish failed: {e}")

    return result


@router.post("/revenue/intake/commercial-outcome/reject")
def revenue_intake_reject(
    req: IntakeRejectRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Human-gated Revenue reject — audit only."""
    _human_gate(req.requested_by, "Revenue CommercialOutcome reject")
    db = SessionLocal()
    try:
        try:
            result = reject_commercial_outcome(
                db, req.outcome_id, req.requested_by.strip(), req.reason
            )
        except (HumanAuthorityError, ValueError) as exc:
            raise _service_error(exc) from exc
    finally:
        db.close()

    if result.get("idempotent") is False:
        try:
            EventBus.publish(
                Event(
                    event_type=EventType.COMMERCIAL_OUTCOME_REJECTED,
                    source="revenue_intake_reject",
                    entity_id=req.outcome_id,
                    entity_type="commercial_outcome",
                    data={
                        "outcome_id": req.outcome_id,
                        "rejected": True,
                        "reason": result.get("reason"),
                        "requested_by": req.requested_by.strip(),
                    },
                )
            )
        except Exception as e:
            logger.warning(f"CommercialOutcome reject event publish failed: {e}")

    return result
