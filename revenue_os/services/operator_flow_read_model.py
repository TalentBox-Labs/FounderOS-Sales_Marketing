"""OF1 — non-persistent operator workflow composition.

Derives entirely from Contact, Deal, and AgentActionLog.
Contains no independent business state and performs no domain writes.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from revenue_os.database import SessionLocal
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from revenue_os.services.commercial_outcome_service import (
    ACTION_ACCEPTED as CO_ACCEPTED,
)
from revenue_os.services.commercial_outcome_service import (
    ACTION_HANDOFF as CO_HANDOFF,
)
from revenue_os.services.commercial_outcome_service import (
    ACTION_REJECTED as CO_REJECTED,
)
from revenue_os.services.deal_automation_service import (
    SALES_PIPELINE_STAGES,
    TERMINAL_SALES_STAGES,
)
from revenue_os.services.lead_scoring_service import LeadScorer
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED as QD_ACCEPTED,
)
from revenue_os.services.qualified_demand_service import (
    ACTION_HANDOFF as QD_HANDOFF,
)
from revenue_os.services.qualified_demand_service import (
    ACTION_REJECTED as QD_REJECTED,
)

logger = logging.getLogger(__name__)

OPERATOR_CREATE_STAGES: frozenset[DealStage] = frozenset(
    {
        DealStage.DISCOVERY,
        DealStage.QUALIFIED,
        DealStage.PROPOSAL,
        DealStage.NEGOTIATION,
    }
)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _stage_value(stage: Any) -> str:
    if isinstance(stage, DealStage):
        return stage.value
    return str(stage)


def _status_value(status: Any) -> str:
    if isinstance(status, ContactStatus):
        return status.value
    return str(status)


def _permitted_stages(deal: Deal) -> list[str]:
    current = deal.stage
    if current in TERMINAL_SALES_STAGES:
        return []
    return sorted(
        s.value for s in SALES_PIPELINE_STAGES if s != current
    )


def _payload_deal_id(row: AgentActionLog) -> str | None:
    detail = row.detail or {}
    payload = detail.get("payload") if isinstance(detail.get("payload"), dict) else {}
    return payload.get("deal_id") or detail.get("deal_id")


def _org_uuid(organization_id: str | None) -> uuid_lib.UUID | None:
    if organization_id is None:
        return None
    try:
        return uuid_lib.UUID(str(organization_id))
    except ValueError:
        return None


def build_operator_flow_snapshot(*, organization_id: str | None = None) -> dict[str, Any]:
    """Read-only composition for GET /operator."""
    generated_at = datetime.now(timezone.utc).isoformat()
    db = SessionLocal()
    try:
        try:
            pending_demands = _pending_qualified_demands(db, organization_id=organization_id)
            contacts = _contacts(db, organization_id=organization_id)
            deals = _deals(db, organization_id=organization_id)
            outcomes = _commercial_outcomes(db, deals, organization_id=organization_id)
            attention = _attention_queue(pending_demands, contacts, deals, outcomes)
            return {
                "generated_at": generated_at,
                "pending_demands": pending_demands,
                "contacts": contacts,
                "deals": deals,
                "outcomes": outcomes,
                "attention": attention,
                "contact_statuses": [s.value for s in ContactStatus],
                "operator_create_stages": sorted(s.value for s in OPERATOR_CREATE_STAGES),
                "sales_stages": sorted(s.value for s in SALES_PIPELINE_STAGES),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Operator flow snapshot degraded: %s", exc)
            return {
                "generated_at": generated_at,
                "pending_demands": [],
                "contacts": [],
                "deals": [],
                "outcomes": {
                    "pending_handoff": [],
                    "pending_revenue": [],
                    "state": "unavailable",
                    "message": "Deal / outcome sources unavailable",
                },
                "attention": {
                    "state": "unavailable",
                    "message": "Operator sources unavailable",
                    "items": [],
                },
                "contact_statuses": [s.value for s in ContactStatus],
                "operator_create_stages": sorted(s.value for s in OPERATOR_CREATE_STAGES),
                "sales_stages": sorted(s.value for s in SALES_PIPELINE_STAGES),
            }
    finally:
        db.close()


def _pending_qualified_demands(
    db, *, organization_id: str | None = None
) -> list[dict[str, Any]]:  # noqa: ANN001
    org_uuid = _org_uuid(organization_id)
    handoff_q = db.query(AgentActionLog).filter(AgentActionLog.action_type == QD_HANDOFF)
    if org_uuid is not None:
        handoff_q = handoff_q.filter(AgentActionLog.organization_id == org_uuid)
    handoffs = handoff_q.order_by(AgentActionLog.created_at.desc()).all()
    accepted_q = db.query(AgentActionLog).filter(AgentActionLog.action_type == QD_ACCEPTED)
    rejected_q = db.query(AgentActionLog).filter(AgentActionLog.action_type == QD_REJECTED)
    if org_uuid is not None:
        accepted_q = accepted_q.filter(AgentActionLog.organization_id == org_uuid)
        rejected_q = rejected_q.filter(AgentActionLog.organization_id == org_uuid)
    accepted = {row.target_id for row in accepted_q.all() if row.target_id}
    rejected = {row.target_id for row in rejected_q.all() if row.target_id}
    pending: list[dict[str, Any]] = []
    for row in handoffs:
        demand_id = row.target_id or ""
        if not demand_id or demand_id in accepted or demand_id in rejected:
            continue
        payload = (row.detail or {}).get("payload") or {}
        person = payload.get("person") or {}
        pending.append(
            {
                "demand_id": demand_id,
                "source": payload.get("source"),
                "channel": payload.get("channel"),
                "email": person.get("email"),
                "name": person.get("name"),
                "occurred_at": payload.get("occurred_at"),
                "registered_at": _iso(row.created_at),
                "contact_link": "not_yet_created",
            }
        )
    return pending


def _contacts(
    db, *, organization_id: str | None = None
) -> list[dict[str, Any]]:  # noqa: ANN001
    org_uuid = _org_uuid(organization_id)
    contact_q = db.query(Contact)
    deal_q = db.query(Deal)
    if org_uuid is not None:
        contact_q = contact_q.filter(Contact.organization_id == org_uuid)
        deal_q = deal_q.filter(Deal.organization_id == org_uuid)
    contacts = contact_q.all()
    deals = deal_q.all()
    deals_by_contact: dict[str, list[str]] = {}
    for deal in deals:
        if deal.contact_id is None:
            continue
        deals_by_contact.setdefault(str(deal.contact_id), []).append(str(deal.id))

    accept_q = db.query(AgentActionLog).filter(AgentActionLog.action_type == QD_ACCEPTED)
    if org_uuid is not None:
        accept_q = accept_q.filter(AgentActionLog.organization_id == org_uuid)
    accept_by_contact: dict[str, str] = {}
    for row in accept_q.all():
        contact_id = (row.detail or {}).get("contact_id")
        if contact_id and row.target_id:
            accept_by_contact[str(contact_id)] = row.target_id

    rows: list[dict[str, Any]] = []
    for contact in contacts:
        score = contact.lead_score or 0
        linked_deals = deals_by_contact.get(str(contact.id), [])
        demand_id = accept_by_contact.get(str(contact.id))
        rows.append(
            {
                "id": str(contact.id),
                "name": f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                or "Unnamed",
                "email": contact.email,
                "status": _status_value(contact.status),
                "lead_score": score,
                "recommendation": LeadScorer.suggest_status_from_score(score).value,
                "source": contact.source.value if contact.source else None,
                "linked_deal_ids": linked_deals,
                "deal_link": "linked" if linked_deals else "no_linked_record",
                "demand_id": demand_id,
                "demand_link": "linked" if demand_id else "no_linked_record",
            }
        )
    rows.sort(key=lambda item: item["lead_score"], reverse=True)
    return rows


def _deals(
    db, *, organization_id: str | None = None
) -> list[dict[str, Any]]:  # noqa: ANN001
    org_uuid = _org_uuid(organization_id)
    deal_q = db.query(Deal)
    if org_uuid is not None:
        deal_q = deal_q.filter(Deal.organization_id == org_uuid)
    deals = deal_q.all()
    rows: list[dict[str, Any]] = []
    for deal in deals:
        stage = _stage_value(deal.stage)
        rows.append(
            {
                "id": str(deal.id),
                "name": deal.name,
                "stage": stage,
                "value": deal.value,
                "currency": deal.currency,
                "contact_id": str(deal.contact_id) if deal.contact_id else None,
                "contact_link": "linked" if deal.contact_id else "no_linked_record",
                "closed_at": _iso(deal.closed_at),
                "permitted_stages": _permitted_stages(deal),
                "eligible_commercial_outcome": stage == DealStage.CLOSED_WON.value,
                "terminal": deal.stage in TERMINAL_SALES_STAGES,
            }
        )
    return rows


def _commercial_outcomes(
    db, deals: list[dict[str, Any]], *, organization_id: str | None = None
) -> dict[str, Any]:  # noqa: ANN001
    org_uuid = _org_uuid(organization_id)
    handoff_q = db.query(AgentActionLog).filter(AgentActionLog.action_type == CO_HANDOFF)
    accepted_q = db.query(AgentActionLog).filter(AgentActionLog.action_type == CO_ACCEPTED)
    rejected_q = db.query(AgentActionLog).filter(AgentActionLog.action_type == CO_REJECTED)
    if org_uuid is not None:
        handoff_q = handoff_q.filter(AgentActionLog.organization_id == org_uuid)
        accepted_q = accepted_q.filter(AgentActionLog.organization_id == org_uuid)
        rejected_q = rejected_q.filter(AgentActionLog.organization_id == org_uuid)
    handoffs = handoff_q.all()
    accepted_ids = {row.target_id for row in accepted_q.all() if row.target_id}
    rejected_ids = {row.target_id for row in rejected_q.all() if row.target_id}
    accepted_deal_ids = set()
    open_handoff_deal_ids = set()
    pending_revenue: list[dict[str, Any]] = []
    for row in handoffs:
        outcome_id = row.target_id or ""
        deal_id = _payload_deal_id(row)
        if outcome_id in accepted_ids:
            if deal_id:
                accepted_deal_ids.add(deal_id)
            continue
        if outcome_id in rejected_ids:
            continue
        if deal_id:
            open_handoff_deal_ids.add(deal_id)
        pending_revenue.append(
            {
                "outcome_id": outcome_id,
                "deal_id": deal_id,
                "occurred_at": (row.detail or {}).get("occurred_at"),
                "state": "pending_human_decision",
            }
        )

    pending_handoff: list[dict[str, Any]] = []
    for deal in deals:
        if not deal.get("eligible_commercial_outcome"):
            continue
        deal_id = deal["id"]
        if deal_id in accepted_deal_ids or deal_id in open_handoff_deal_ids:
            continue
        pending_handoff.append(
            {
                "deal_id": deal_id,
                "deal_name": deal.get("name"),
                "state": "not_yet_created",
            }
        )

    return {
        "state": "ok",
        "pending_handoff": pending_handoff,
        "pending_revenue": pending_revenue,
        "message": "",
    }


def _attention_queue(
    pending_demands: list[dict[str, Any]],
    contacts: list[dict[str, Any]],
    deals: list[dict[str, Any]],
    outcomes: dict[str, Any],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for demand in pending_demands:
        items.append(
            {
                "kind": "qualified_demand",
                "label": demand.get("name") or demand.get("email") or demand["demand_id"],
                "detail": "QualifiedDemand awaiting Sales decision",
                "href": "#stage-demand",
            }
        )
    for contact in contacts:
        if contact["lead_score"] >= 70 and contact["status"] not in {
            ContactStatus.QUALIFIED.value,
            ContactStatus.CUSTOMER.value,
        }:
            items.append(
                {
                    "kind": "contact_status",
                    "label": contact["name"],
                    "detail": f"Score {contact['lead_score']} — recommendation {contact['recommendation']}",
                    "href": "#stage-qualification",
                }
            )
    for deal in deals:
        if deal["permitted_stages"]:
            items.append(
                {
                    "kind": "deal_progression",
                    "label": deal["name"],
                    "detail": f"Stage {deal['stage']} — human progression available",
                    "href": "#stage-deals",
                }
            )
    for item in outcomes.get("pending_handoff") or []:
        items.append(
            {
                "kind": "commercial_handoff",
                "label": item.get("deal_name") or item["deal_id"],
                "detail": "closed_won Deal awaiting CommercialOutcome handoff",
                "href": "#stage-outcome",
            }
        )
    for item in outcomes.get("pending_revenue") or []:
        items.append(
            {
                "kind": "revenue_decision",
                "label": item["outcome_id"],
                "detail": "CommercialOutcome awaiting Revenue accept/reject",
                "href": "#stage-revenue",
            }
        )
    if not items:
        return {
            "state": "empty",
            "message": "No operator decisions pending",
            "items": [],
        }
    return {"state": "ok", "message": "", "items": items[:25]}
