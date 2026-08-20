"""COS-4 — Founder commercial funnel & pipeline intelligence (no persistence).

Read-only composition over the existing commercial spine: QualifiedDemand logs,
Deal, Contact, ApprovalRequest, commercial outcomes, and COS-3 decision items.
Does not write CRM entities, approvals, bookings, or outbound communication.
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from revenue_os import database
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.deal import DealStage
from revenue_os.services.commercial_outcome_service import (
    ACTION_ACCEPTED as CO_ACCEPTED,
)
from revenue_os.services.commercial_outcome_service import (
    ACTION_HANDOFF as CO_HANDOFF,
)
from revenue_os.services.commercial_outcome_service import (
    ACTION_REJECTED as CO_REJECTED,
)
from revenue_os.services.operator_flow_read_model import build_operator_flow_snapshot
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED as QD_ACCEPTED,
)
from revenue_os.services.qualified_demand_service import (
    ACTION_HANDOFF as QD_HANDOFF,
)
from revenue_os.services.qualified_demand_service import (
    ACTION_REJECTED as QD_REJECTED,
)

# Funnel bands — deterministic mapping to canonical repository states.
FUNNEL_BAND_DEMAND = "demand"
FUNNEL_BAND_PIPELINE = "pipeline"
FUNNEL_BAND_OUTCOME = "outcome"

# Explicit sales Deal stage sets (from DealStage + SALES_PIPELINE_STAGES evidence).
SALES_OPEN_STAGES: frozenset[str] = frozenset(
    {
        DealStage.DISCOVERY.value,
        DealStage.QUALIFIED.value,
        DealStage.PROPOSAL.value,
        DealStage.NEGOTIATION.value,
    }
)
SALES_WON_STAGES: frozenset[str] = frozenset({DealStage.CLOSED_WON.value})
SALES_LOST_STAGES: frozenset[str] = frozenset({DealStage.CLOSED_LOST.value})
NON_SALES_STAGES: frozenset[str] = frozenset(
    {
        DealStage.SOURCING.value,
        DealStage.SCREENING.value,
        DealStage.INTERVIEW.value,
        DealStage.OFFER.value,
        DealStage.PLACED.value,
        DealStage.REJECTED.value,
    }
)

# Attention reason codes — explicit state labels, no scores.
REASON_PENDING_QUALIFIED_DEMAND = "pending_qualified_demand"
REASON_PENDING_APPROVAL = "pending_approval"
REASON_PENDING_COMMERCIAL_OUTCOME_HANDOFF = "pending_commercial_outcome_handoff"
REASON_PENDING_COMMERCIAL_OUTCOME_DECISION = "pending_commercial_outcome_decision"
REASON_FOLLOW_UP_ELIGIBLE = "follow_up_eligible"
REASON_MEETING_INTEREST_READY = "meeting_interest_ready"

_ATTENTION_ORDER = (
    REASON_PENDING_QUALIFIED_DEMAND,
    REASON_PENDING_APPROVAL,
    REASON_PENDING_COMMERCIAL_OUTCOME_HANDOFF,
    REASON_PENDING_COMMERCIAL_OUTCOME_DECISION,
    REASON_FOLLOW_UP_ELIGIBLE,
    REASON_MEETING_INTEREST_READY,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _org_uuid(organization_id: str | None) -> uuid_lib.UUID | None:
    if organization_id is None:
        return None
    try:
        return uuid_lib.UUID(str(organization_id))
    except ValueError:
        return None


def _unique_target_ids(
    org_uuid: uuid_lib.UUID, action_type: str
) -> set[str]:
    """Unique AgentActionLog.target_id values for an org-scoped action type."""
    db = database.SessionLocal()
    try:
        rows = (
            db.query(AgentActionLog.target_id)
            .filter(AgentActionLog.action_type == action_type)
            .filter(AgentActionLog.organization_id == org_uuid)
            .all()
        )
        return {str(tid) for (tid,) in rows if tid}
    finally:
        db.close()


def _action_event_count(org_uuid: uuid_lib.UUID, action_type: str) -> int:
    """Raw event count (audit only — not unique-object outcomes)."""
    db = database.SessionLocal()
    try:
        return (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == action_type)
            .filter(AgentActionLog.organization_id == org_uuid)
            .count()
        )
    finally:
        db.close()


def _qualified_demand_state(org_uuid: uuid_lib.UUID) -> dict[str, Any]:
    """Reconcile QD by stable demand_id (AgentActionLog.target_id).

    One demand_id has one presentation state: accepted > rejected > pending.
    Duplicate events do not inflate unique demand counts.
    """
    accepted_ids = _unique_target_ids(org_uuid, QD_ACCEPTED)
    rejected_ids = _unique_target_ids(org_uuid, QD_REJECTED)
    handoff_ids = _unique_target_ids(org_uuid, QD_HANDOFF)
    # Accepted wins over rejected if both somehow exist.
    rejected_only = rejected_ids - accepted_ids
    pending_ids = handoff_ids - accepted_ids - rejected_ids
    return {
        "accepted": len(accepted_ids),
        "rejected": len(rejected_only),
        "pending_ids": pending_ids,
        "accepted_ids": accepted_ids,
        "rejected_ids": rejected_only,
        "handoff_event_count": _action_event_count(org_uuid, QD_HANDOFF),
        "accepted_event_count": _action_event_count(org_uuid, QD_ACCEPTED),
        "rejected_event_count": _action_event_count(org_uuid, QD_REJECTED),
    }


def dedupe_pending_demands(
    pending_demands: list[dict[str, Any]],
    *,
    accepted_ids: set[str] | None = None,
    rejected_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """One row per demand_id; drop accepted/rejected; keep first occurrence."""
    accepted = accepted_ids or set()
    rejected = rejected_ids or set()
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in pending_demands:
        demand_id = str(row.get("demand_id") or "").strip()
        if not demand_id or demand_id in seen:
            continue
        if demand_id in accepted or demand_id in rejected:
            continue
        seen.add(demand_id)
        out.append(row)
    return out


def _commercial_outcome_state(org_uuid: uuid_lib.UUID) -> dict[str, Any]:
    """Reconcile MC06 outcomes by stable outcome_id (AgentActionLog.target_id).

    Unique accepted / unique rejected are realized commercial-outcome decisions.
    Handoff event totals are audit-only and never summed into realized outcomes.
    """
    accepted_ids = _unique_target_ids(org_uuid, CO_ACCEPTED)
    rejected_ids = _unique_target_ids(org_uuid, CO_REJECTED)
    handoff_ids = _unique_target_ids(org_uuid, CO_HANDOFF)
    rejected_only = rejected_ids - accepted_ids
    pending_decision_ids = handoff_ids - accepted_ids - rejected_ids
    return {
        "accepted": len(accepted_ids),
        "rejected": len(rejected_only),
        "pending_decision_ids": pending_decision_ids,
        "handoff_event_count": _action_event_count(org_uuid, CO_HANDOFF),
        "accepted_event_count": _action_event_count(org_uuid, CO_ACCEPTED),
        "rejected_event_count": _action_event_count(org_uuid, CO_REJECTED),
    }


def _classify_deals(deals: list[dict[str, Any]]) -> dict[str, Any]:
    """Map Deal rows using explicit sales open/won/lost sets.

    Unknown and non-sales (recruitment) stages are ignored — never open.
    """
    open_by_stage: dict[str, int] = {}
    open_count = 0
    closed_won = 0
    closed_lost = 0
    ignored_non_sales = 0
    ignored_unknown = 0
    for deal in deals:
        stage = str(deal.get("stage") or "").strip() or "unknown"
        if stage in SALES_WON_STAGES:
            closed_won += 1
            continue
        if stage in SALES_LOST_STAGES:
            closed_lost += 1
            continue
        if stage in SALES_OPEN_STAGES:
            open_count += 1
            open_by_stage[stage] = open_by_stage.get(stage, 0) + 1
            continue
        if stage in NON_SALES_STAGES:
            ignored_non_sales += 1
            continue
        ignored_unknown += 1
    return {
        "open_count": open_count,
        "open_by_stage": open_by_stage,
        "closed_won": closed_won,
        "closed_lost": closed_lost,
        "ignored_non_sales": ignored_non_sales,
        "ignored_unknown": ignored_unknown,
        "pipeline_stages_included": sorted(open_by_stage.keys()),
        "sales_open_stages": sorted(SALES_OPEN_STAGES),
        "sales_won_stages": sorted(SALES_WON_STAGES),
        "sales_lost_stages": sorted(SALES_LOST_STAGES),
        "non_sales_stages": sorted(NON_SALES_STAGES),
    }


def _attention_item(
    *,
    reason_code: str,
    label: str,
    detail: str,
    count: int,
    href: str | None,
    source: str,
) -> dict[str, Any]:
    return {
        "reason_code": reason_code,
        "label": label,
        "detail": detail,
        "count": count,
        "href": href,
        "source": source,
    }


def _compose_attention(
    *,
    pending_demands: list[dict[str, Any]],
    pending_approvals: list[dict[str, Any]],
    outcomes: dict[str, Any],
    follow_up_signals: list[dict[str, Any]],
    meeting_interest: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    pending_demand_count = len(pending_demands)
    if pending_demand_count:
        items.append(
            _attention_item(
                reason_code=REASON_PENDING_QUALIFIED_DEMAND,
                label="Qualified demand awaiting intake",
                detail="Marketing handoff recorded; accept or reject on People.",
                count=pending_demand_count,
                href="/demand",
                source="AgentActionLog.qualified_demand_handoff",
            )
        )
    pending_approval_count = len(pending_approvals)
    if pending_approval_count:
        items.append(
            _attention_item(
                reason_code=REASON_PENDING_APPROVAL,
                label="Approvals waiting",
                detail="Governed proposals require your approve or reject.",
                count=pending_approval_count,
                href="/pending-approvals",
                source="ApprovalRequest.status=pending",
            )
        )
    pending_handoff = outcomes.get("pending_handoff") or []
    if pending_handoff:
        items.append(
            _attention_item(
                reason_code=REASON_PENDING_COMMERCIAL_OUTCOME_HANDOFF,
                label="Closed-won deals without outcome handoff",
                detail="Eligible deals need a commercial outcome handoff on Operator.",
                count=len(pending_handoff),
                href="/operator",
                source="Deal.stage=closed_won without commercial_outcome_handoff",
            )
        )
    pending_revenue = outcomes.get("pending_revenue") or []
    if pending_revenue:
        items.append(
            _attention_item(
                reason_code=REASON_PENDING_COMMERCIAL_OUTCOME_DECISION,
                label="Commercial outcomes awaiting decision",
                detail="Outcome handoff recorded; accept or reject the revenue signal.",
                count=len(pending_revenue),
                href="/operator",
                source="AgentActionLog.commercial_outcome_handoff",
            )
        )
    eligible_followups = [f for f in follow_up_signals if f.get("eligible")]
    if eligible_followups:
        items.append(
            _attention_item(
                reason_code=REASON_FOLLOW_UP_ELIGIBLE,
                label="Follow-up eligible",
                detail="A governed follow-up may be proposed from the person workspace.",
                count=len(eligible_followups),
                href="/demand",
                source="rev_orch_followup_eligibility",
            )
        )
    ready_meetings = [
        m
        for m in meeting_interest
        if m.get("booking_status") == "eligible" or m.get("booking_eligible")
    ]
    if ready_meetings:
        items.append(
            _attention_item(
                reason_code=REASON_MEETING_INTEREST_READY,
                label="Meeting interest ready for proposal",
                detail="Booking remains proposal-only until you approve.",
                count=len(ready_meetings),
                href="/demand",
                source="rev_orch_reply_assessment",
            )
        )
    order = {code: idx for idx, code in enumerate(_ATTENTION_ORDER)}
    items.sort(key=lambda row: order.get(str(row.get("reason_code")), 99))
    return items


def compose_commercial_funnel_snapshot(
    *,
    organization_id: str | None = None,
    operator_flow: dict[str, Any] | None = None,
    pending_approvals: list[dict[str, Any]] | None = None,
    pending_demands: list[dict[str, Any]] | None = None,
    follow_up_signals: list[dict[str, Any]] | None = None,
    meeting_interest: list[dict[str, Any]] | None = None,
    recent_activity: list[dict[str, Any]] | None = None,
    decision_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compose org-scoped commercial funnel & pipeline intelligence.

    Returns unavailable snapshot when organization_id is missing (fail closed).
    Read-only: opens SessionLocal only for org-scoped AgentActionLog queries.
    Does not query Company rows. Does not expose finance-grade forecast semantics.
    """
    empty: dict[str, Any] = {
        "state": "unavailable",
        "message": "Organization context required",
        "generated_at": _utc_now(),
        "summary": {},
        "funnel": {},
        "pipeline": {},
        "outcomes": {},
        "attention": {"entries": [], "total": 0},
        "recent_movement": [],
        "provenance": {"sources": [], "organization_id": None},
    }
    org_uuid = _org_uuid(organization_id)
    if org_uuid is None:
        return empty

    flow = operator_flow
    if flow is None:
        flow = build_operator_flow_snapshot(organization_id=str(org_uuid))

    deals = flow.get("deals") or []
    contacts = flow.get("contacts") or []
    raw_demands = (
        pending_demands
        if pending_demands is not None
        else (flow.get("pending_demands") or [])
    )
    outcomes = flow.get("outcomes") or {}
    deal_stats = _classify_deals(deals)
    qd_state = _qualified_demand_state(org_uuid)
    co_state = _commercial_outcome_state(org_uuid)

    # Presentation rows: dedupe + drop accepted/rejected. Count: unique DB pending.
    demands = dedupe_pending_demands(
        raw_demands,
        accepted_ids=qd_state["accepted_ids"],
        rejected_ids=qd_state["rejected_ids"],
    )
    pending_intake = len(qd_state["pending_ids"])
    attention_demands = demands
    if not attention_demands and qd_state["pending_ids"]:
        attention_demands = [
            {"demand_id": did} for did in sorted(qd_state["pending_ids"])
        ]

    attention_items = _compose_attention(
        pending_demands=attention_demands,
        pending_approvals=pending_approvals or [],
        outcomes=outcomes,
        follow_up_signals=follow_up_signals or [],
        meeting_interest=meeting_interest or [],
    )

    funnel_demand = {
        "band": FUNNEL_BAND_DEMAND,
        "pending_intake": pending_intake,
        "accepted": qd_state["accepted"],
        "rejected": qd_state["rejected"],
        "event_counts": {
            "handoff_events": qd_state["handoff_event_count"],
            "accepted_events": qd_state["accepted_event_count"],
            "rejected_events": qd_state["rejected_event_count"],
        },
        "states_included": [
            "unique demand_id pending (handoff without accept/reject)",
            "unique demand_id accepted",
            "unique demand_id rejected",
        ],
        "states_excluded": [
            "Contact.status (not a demand signal)",
            "inferred channel attribution",
            "raw AgentActionLog event totals as demand outcomes",
        ],
    }
    funnel_pipeline = {
        "band": FUNNEL_BAND_PIPELINE,
        "open_deals": deal_stats["open_count"],
        "people": len(contacts),
        "by_stage": deal_stats["open_by_stage"],
        "ignored_non_sales": deal_stats["ignored_non_sales"],
        "ignored_unknown": deal_stats["ignored_unknown"],
        "states_included": deal_stats["sales_open_stages"],
        "states_excluded": sorted(
            SALES_WON_STAGES | SALES_LOST_STAGES | NON_SALES_STAGES
        )
        + ["unknown/unsupported"],
    }
    funnel_outcome = {
        "band": FUNNEL_BAND_OUTCOME,
        "deals_closed_won": deal_stats["closed_won"],
        "deals_closed_lost": deal_stats["closed_lost"],
        "commercial_outcome_accepted": co_state["accepted"],
        "commercial_outcome_rejected": co_state["rejected"],
        "pending_outcome_handoff": len(outcomes.get("pending_handoff") or []),
        "pending_outcome_decision": len(outcomes.get("pending_revenue") or []),
        "event_counts": {
            "handoff_events": co_state["handoff_event_count"],
            "accepted_events": co_state["accepted_event_count"],
            "rejected_events": co_state["rejected_event_count"],
        },
        "states_included": [
            "Deal.stage closed_won / closed_lost",
            "unique outcome_id commercial_outcome_accepted",
            "unique outcome_id commercial_outcome_rejected",
        ],
        "states_excluded": [
            "BillingRecord",
            "Hermes Goal",
            "inferred conversion percentages",
            "handoff events as realized outcomes",
        ],
    }

    movement: list[dict[str, Any]] = []
    for row in (recent_activity or [])[:8]:
        movement.append(
            {
                "label": row.get("label") or row.get("action_type"),
                "action_type": row.get("action_type"),
                "occurred_at": row.get("created_at"),
                "source": "AgentActionLog",
            }
        )

    return {
        "state": "ok",
        "message": "",
        "generated_at": _utc_now(),
        "summary": {
            "demand_pending": pending_intake,
            "demand_accepted": qd_state["accepted"],
            "demand_rejected": qd_state["rejected"],
            "people": len(contacts),
            "open_deals": deal_stats["open_count"],
            "deals_closed_won": deal_stats["closed_won"],
            "deals_closed_lost": deal_stats["closed_lost"],
            "outcomes_pending_decision": len(outcomes.get("pending_revenue") or []),
            "outcomes_pending_handoff": len(outcomes.get("pending_handoff") or []),
            "approvals_pending": len(pending_approvals or []),
            "decision_items_total": len(decision_items or []),
        },
        "funnel": {
            "demand": funnel_demand,
            "pipeline": funnel_pipeline,
            "outcome": funnel_outcome,
        },
        "pipeline": {
            "open_count": deal_stats["open_count"],
            "by_stage": deal_stats["open_by_stage"],
            "ignored_non_sales": deal_stats["ignored_non_sales"],
            "ignored_unknown": deal_stats["ignored_unknown"],
            "total_deals": len(deals),
        },
        "outcomes": {
            "pending_handoff": outcomes.get("pending_handoff") or [],
            "pending_decision": outcomes.get("pending_revenue") or [],
            "commercial_outcome_accepted": co_state["accepted"],
            "commercial_outcome_rejected": co_state["rejected"],
            "event_counts": {
                "handoff_events": co_state["handoff_event_count"],
                "accepted_events": co_state["accepted_event_count"],
                "rejected_events": co_state["rejected_event_count"],
            },
        },
        "attention": {
            "entries": attention_items,
            "total": sum(int(i.get("count") or 0) for i in attention_items),
        },
        "recent_movement": movement,
        "provenance": {
            "sources": [
                "AgentActionLog",
                "Deal",
                "Contact",
                "ApprovalRequest",
                "operator_flow_read_model",
                "commercial_decision_loop (decision_items count only)",
            ],
            "organization_id": str(org_uuid),
            "reconciliation": {
                "qualified_demand": "unique demand_id (target_id)",
                "commercial_outcome": "unique outcome_id (target_id)",
                "deal_stages": "SALES_OPEN / SALES_WON / SALES_LOST; non-sales+unknown ignored",
            },
        },
    }
