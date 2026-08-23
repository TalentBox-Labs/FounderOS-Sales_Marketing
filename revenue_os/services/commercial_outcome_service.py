"""MC06 — CommercialOutcome Sales→Revenue handoff service.

Explicit human-triggered handoff after an eligible closed_won Deal.
Persists on existing AgentActionLog only — no new table, no Deal mutation,
no Client/Project/billing/revenue-recognition writes.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.deal import Deal, DealStage
from revenue_os.services.mutation_authority import require_human_mutation_authority

logger = logging.getLogger(__name__)

ACTION_HANDOFF = "commercial_outcome_handoff"
ACTION_ACCEPTED = "commercial_outcome_accepted"
ACTION_REJECTED = "commercial_outcome_rejected"

ELIGIBLE_OUTCOME = "closed_won"
TARGET_TYPE = "commercial_outcome"


class CommercialOutcomePayload(BaseModel):
    """Bounded handoff payload derived from SALES_REVENUE_CONTRACT.md §3."""

    outcome_id: str = Field(..., min_length=8, max_length=64)
    deal_id: str = Field(..., min_length=8, max_length=64)
    outcome: str = Field(..., min_length=3, max_length=32)
    occurred_at: str = Field(..., min_length=10, max_length=64)
    handoff_hints: str | None = Field(default=None, max_length=2000)

    @field_validator("outcome_id", "deal_id")
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        try:
            uuid_lib.UUID(value)
        except ValueError as exc:
            raise ValueError("identifier must be a valid UUID") from exc
        return value

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != ELIGIBLE_OUTCOME:
            raise ValueError(
                "CommercialOutcome v1 accepts outcome=closed_won only"
            )
        return normalized


def _parse_uuid(value: str, field: str) -> uuid_lib.UUID:
    try:
        return uuid_lib.UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid UUID") from exc


def _deal_stage_value(deal: Deal) -> str:
    stage = deal.stage
    if isinstance(stage, DealStage):
        return stage.value
    return str(stage)


def _load_deal(db: Session, deal_id: str) -> Deal:
    deal_uuid = _parse_uuid(deal_id, "deal_id")
    deal = db.get(Deal, deal_uuid)
    if deal is None:
        deal = db.query(Deal).filter(Deal.id == deal_uuid).first()
    if deal is None:
        raise ValueError("Deal not found")
    return deal


def _require_eligible_closed_won(deal: Deal) -> None:
    if _deal_stage_value(deal) != DealStage.CLOSED_WON.value:
        raise ValueError(
            "Deal is not in eligible closed_won state — "
            "CommercialOutcome v1 requires Deal.stage=closed_won"
        )


def _find_audit(db: Session, action_type: str, outcome_id: str) -> AgentActionLog | None:
    return (
        db.query(AgentActionLog)
        .filter(
            AgentActionLog.action_type == action_type,
            AgentActionLog.target_id == outcome_id,
        )
        .first()
    )


def _logs_of_type(db: Session, action_type: str) -> list[AgentActionLog]:
    return (
        db.query(AgentActionLog)
        .filter(AgentActionLog.action_type == action_type)
        .all()
    )


def _payload_deal_id(row: AgentActionLog) -> str | None:
    detail = row.detail or {}
    payload = detail.get("payload") if isinstance(detail.get("payload"), dict) else {}
    return payload.get("deal_id") or detail.get("deal_id")


def _find_handoff_for_deal(db: Session, deal_id: str) -> AgentActionLog | None:
    for row in _logs_of_type(db, ACTION_HANDOFF):
        if _payload_deal_id(row) == deal_id:
            return row
    return None


def _find_accepted_for_deal(db: Session, deal_id: str) -> AgentActionLog | None:
    for row in _logs_of_type(db, ACTION_ACCEPTED):
        if _payload_deal_id(row) == deal_id:
            return row
    return None


def _snapshot_deal(deal: Deal) -> dict[str, Any]:
    closed_at = deal.closed_at.isoformat() if getattr(deal, "closed_at", None) else None
    return {
        "deal_id": str(deal.id),
        "source_stage": _deal_stage_value(deal),
        "value_snapshot": getattr(deal, "value", None),
        "currency_snapshot": getattr(deal, "currency", None),
        "closed_at_snapshot": closed_at,
        "value_authoritative": False,
        "recognized_revenue": False,
    }


def _require_handoff(db: Session, outcome_id: str) -> dict[str, Any]:
    row = _find_audit(db, ACTION_HANDOFF, outcome_id)
    if row is None or not row.detail or "payload" not in row.detail:
        raise ValueError(
            "CommercialOutcome handoff not found — register Sales handoff first"
        )
    return row.detail["payload"]


def register_commercial_outcome_handoff(
    db: Session, payload: CommercialOutcomePayload, requested_by: str
) -> dict[str, Any]:
    """Sales-side handoff registration — does not write Revenue financial state."""
    existing = _find_audit(db, ACTION_HANDOFF, payload.outcome_id)
    if existing is not None:
        return {
            "ok": True,
            "idempotent": True,
            "outcome_id": payload.outcome_id,
            "deal_id": payload.deal_id,
            "handoff_registered": True,
            "requested_by": requested_by,
            "commercial_outcome_accepted": False,
        }

    require_human_mutation_authority(
        requested_by, action="Sales CommercialOutcome handoff"
    )

    deal = _load_deal(db, payload.deal_id)
    _require_eligible_closed_won(deal)

    accepted = _find_accepted_for_deal(db, payload.deal_id)
    if accepted is not None:
        raise ValueError("CommercialOutcome already accepted for this Deal")

    prior_handoff = _find_handoff_for_deal(db, payload.deal_id)
    if prior_handoff is not None:
        prior_rejected = _find_audit(db, ACTION_REJECTED, prior_handoff.target_id or "")
        if prior_rejected is None:
            raise ValueError("CommercialOutcome handoff already registered for this Deal")

    snapshot = _snapshot_deal(deal)
    db.add(
        AgentActionLog(
            actor=requested_by,
            action_type=ACTION_HANDOFF,
            target_type=TARGET_TYPE,
            target_id=payload.outcome_id,
            status="completed",
            detail={
                "payload": payload.model_dump(),
                "requested_by": requested_by,
                "occurred_at": payload.occurred_at,
                "deal_id": payload.deal_id,
                "provenance": snapshot,
            },
        )
    )
    db.commit()
    logger.info(
        "CommercialOutcome handoff registered",
        extra={"outcome_id": payload.outcome_id, "deal_id": payload.deal_id},
    )
    return {
        "ok": True,
        "idempotent": False,
        "outcome_id": payload.outcome_id,
        "deal_id": payload.deal_id,
        "handoff_registered": True,
        "requested_by": requested_by,
        "commercial_outcome_accepted": False,
        "recognized_revenue": False,
        "billing_created": False,
        "deal_mutated": False,
        "provenance": snapshot,
    }


def accept_commercial_outcome(
    db: Session, outcome_id: str, requested_by: str, notes: str = ""
) -> dict[str, Any]:
    """Revenue-side accept — records CommercialOutcome representation only."""
    prior = _find_audit(db, ACTION_ACCEPTED, outcome_id)
    if prior is not None and prior.detail:
        return {
            "ok": True,
            "idempotent": True,
            "outcome_id": outcome_id,
            "deal_id": prior.detail.get("deal_id"),
            "accepted": True,
            "commercial_outcome_emitted": True,
            "requested_by": prior.detail.get("requested_by", requested_by),
            "recognized_revenue": False,
        }

    require_human_mutation_authority(
        requested_by, action="Revenue CommercialOutcome accept"
    )

    rejected = _find_audit(db, ACTION_REJECTED, outcome_id)
    if rejected is not None:
        raise ValueError("CommercialOutcome already rejected — cannot accept")

    payload_dict = _require_handoff(db, outcome_id)
    payload = CommercialOutcomePayload.model_validate(payload_dict)

    deal = _load_deal(db, payload.deal_id)
    _require_eligible_closed_won(deal)

    existing_accept = _find_accepted_for_deal(db, payload.deal_id)
    if existing_accept is not None:
        raise ValueError("CommercialOutcome already accepted for this Deal")

    snapshot = _snapshot_deal(deal)
    db.add(
        AgentActionLog(
            actor=requested_by,
            action_type=ACTION_ACCEPTED,
            target_type=TARGET_TYPE,
            target_id=outcome_id,
            status="completed",
            detail={
                "deal_id": payload.deal_id,
                "outcome": payload.outcome,
                "requested_by": requested_by,
                "notes": notes or None,
                "payload": payload.model_dump(),
                "provenance": snapshot,
                "recognized_revenue": False,
                "billing_created": False,
                "invoice_created": False,
                "client_created": False,
                "project_created": False,
                "deal_mutated": False,
            },
        )
    )
    db.commit()
    return {
        "ok": True,
        "idempotent": False,
        "outcome_id": outcome_id,
        "deal_id": payload.deal_id,
        "outcome": payload.outcome,
        "accepted": True,
        "status": "accepted",
        "commercial_outcome_emitted": True,
        "requested_by": requested_by,
        "recognized_revenue": False,
        "value_authoritative": False,
        "billing_created": False,
        "invoice_created": False,
        "client_created": False,
        "project_created": False,
        "deal_mutated": False,
        "contact_status_mutated": False,
        "provenance": snapshot,
    }


def reject_commercial_outcome(
    db: Session, outcome_id: str, requested_by: str, reason: str
) -> dict[str, Any]:
    """Revenue-side reject — audit only; no Deal or financial mutation."""
    prior = _find_audit(db, ACTION_REJECTED, outcome_id)
    if prior is not None:
        return {
            "ok": True,
            "idempotent": True,
            "outcome_id": outcome_id,
            "rejected": True,
            "reason": prior.detail.get("reason") if prior.detail else reason,
        }

    require_human_mutation_authority(
        requested_by, action="Revenue CommercialOutcome reject"
    )

    payload_dict = _require_handoff(db, outcome_id)

    prior_accept = _find_audit(db, ACTION_ACCEPTED, outcome_id)
    if prior_accept is not None:
        raise ValueError("CommercialOutcome already accepted — cannot reject")

    db.add(
        AgentActionLog(
            actor=requested_by,
            action_type=ACTION_REJECTED,
            target_type=TARGET_TYPE,
            target_id=outcome_id,
            status="completed",
            detail={
                "reason": reason.strip(),
                "requested_by": requested_by,
                "deal_id": payload_dict.get("deal_id"),
                "payload": payload_dict,
            },
        )
    )
    db.commit()
    return {
        "ok": True,
        "idempotent": False,
        "outcome_id": outcome_id,
        "deal_id": payload_dict.get("deal_id"),
        "rejected": True,
        "reason": reason.strip(),
        "requested_by": requested_by,
        "deal_mutated": False,
        "recognized_revenue": False,
    }
