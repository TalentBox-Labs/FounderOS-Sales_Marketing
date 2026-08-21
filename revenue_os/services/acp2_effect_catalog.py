"""ACP-2 effect catalog — maps work kinds to ACP-1 authority classes.

Assignment eligibility is declarative. It never grants authority; ACP-1
evaluation still decides AUTONOMOUS / HUMAN_REQUIRED / PROHIBITED at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from revenue_os.services.acp1_autonomous_boundary import (
    EFFECT_EXECUTE_GOVERNED,
    EFFECT_HUMAN_REQUIRED,
    EFFECT_PROHIBITED,
    EFFECT_PROPOSE,
    EFFECT_READ,
)
from revenue_os.services.acp2_work_contract import (
    WORK_APPROVAL_DECIDE,
    WORK_BOOKING_EXECUTE,
    WORK_BOOKING_PROPOSE,
    WORK_CONTACT_STATUS,
    WORK_DEAL_AT_RISK,
    WORK_DEAL_STAGE,
    WORK_FOLLOW_UP_PROPOSE,
    WORK_FOLLOW_UP_SEND,
    WORK_GMAIL_INBOUND,
    WORK_HERMES_DEAL_CREATE,
    WORK_HERMES_QUALIFY_RECOMMEND,
    WORK_HERMES_SCORE,
    WORK_LEAD_SCORE,
    WORK_METRICS_SNAPSHOT,
    WORK_OUTBOUND_SEND,
    WORK_QD_DECIDE,
    ExecutionMode,
)


@dataclass(frozen=True)
class EffectSpec:
    work_kind: str
    acp1_effect_class: str
    execution_mode: ExecutionMode
    eligible_agents: frozenset[str]
    requested_effect: str


# Eligible agents are assignment hints only — not authorization.
_CATALOG: dict[str, EffectSpec] = {
    WORK_LEAD_SCORE: EffectSpec(
        WORK_LEAD_SCORE,
        EFFECT_PROPOSE,
        ExecutionMode.AUTONOMOUS,
        frozenset({"heartbeat", "hermes", "scoring_worker"}),
        "lead_score_write",
    ),
    WORK_FOLLOW_UP_PROPOSE: EffectSpec(
        WORK_FOLLOW_UP_PROPOSE,
        EFFECT_PROPOSE,
        ExecutionMode.AUTONOMOUS,
        frozenset({"heartbeat", "followup_worker", "orchestrator"}),
        "follow_up_propose",
    ),
    WORK_FOLLOW_UP_SEND: EffectSpec(
        WORK_FOLLOW_UP_SEND,
        EFFECT_EXECUTE_GOVERNED,
        ExecutionMode.HUMAN_REQUIRED,
        frozenset({"approval_executor"}),
        "follow_up_send",
    ),
    WORK_OUTBOUND_SEND: EffectSpec(
        WORK_OUTBOUND_SEND,
        EFFECT_EXECUTE_GOVERNED,
        ExecutionMode.HUMAN_REQUIRED,
        frozenset({"approval_executor"}),
        "outbound_send",
    ),
    WORK_BOOKING_PROPOSE: EffectSpec(
        WORK_BOOKING_PROPOSE,
        EFFECT_PROPOSE,
        ExecutionMode.AUTONOMOUS,
        frozenset({"heartbeat", "booking_worker", "orchestrator"}),
        "booking_propose",
    ),
    WORK_BOOKING_EXECUTE: EffectSpec(
        WORK_BOOKING_EXECUTE,
        EFFECT_EXECUTE_GOVERNED,
        ExecutionMode.HUMAN_REQUIRED,
        frozenset({"approval_executor"}),
        "booking_execute",
    ),
    WORK_DEAL_AT_RISK: EffectSpec(
        WORK_DEAL_AT_RISK,
        EFFECT_READ,
        ExecutionMode.AUTONOMOUS,
        frozenset({"heartbeat", "hermes"}),
        "deal_at_risk_flag",
    ),
    WORK_GMAIL_INBOUND: EffectSpec(
        WORK_GMAIL_INBOUND,
        EFFECT_PROPOSE,
        ExecutionMode.AUTONOMOUS,
        frozenset({"heartbeat", "gmail_sync"}),
        "gmail_inbound_activity",
    ),
    WORK_METRICS_SNAPSHOT: EffectSpec(
        WORK_METRICS_SNAPSHOT,
        EFFECT_READ,
        ExecutionMode.AUTONOMOUS,
        frozenset({"heartbeat"}),
        "metrics_snapshot",
    ),
    WORK_HERMES_SCORE: EffectSpec(
        WORK_HERMES_SCORE,
        EFFECT_PROPOSE,
        ExecutionMode.AUTONOMOUS,
        frozenset({"hermes"}),
        "hermes_lead_score",
    ),
    WORK_HERMES_QUALIFY_RECOMMEND: EffectSpec(
        WORK_HERMES_QUALIFY_RECOMMEND,
        EFFECT_READ,
        ExecutionMode.AUTONOMOUS,
        frozenset({"hermes"}),
        "hermes_qualify_recommend",
    ),
    WORK_HERMES_DEAL_CREATE: EffectSpec(
        WORK_HERMES_DEAL_CREATE,
        EFFECT_PROHIBITED,
        ExecutionMode.PROHIBITED,
        frozenset(),  # no eligible autonomous agent
        "hermes_deal_create",
    ),
    WORK_DEAL_STAGE: EffectSpec(
        WORK_DEAL_STAGE,
        EFFECT_HUMAN_REQUIRED,
        ExecutionMode.PROHIBITED,  # autonomous path prohibited (optional_tenant)
        frozenset(),
        "deal_stage_mutation",
    ),
    WORK_CONTACT_STATUS: EffectSpec(
        WORK_CONTACT_STATUS,
        EFFECT_HUMAN_REQUIRED,
        ExecutionMode.PROHIBITED,
        frozenset(),
        "contact_status_mutation",
    ),
    WORK_QD_DECIDE: EffectSpec(
        WORK_QD_DECIDE,
        EFFECT_HUMAN_REQUIRED,
        ExecutionMode.HUMAN_REQUIRED,
        frozenset({"human_operator"}),
        "qualified_demand_decide",
    ),
    WORK_APPROVAL_DECIDE: EffectSpec(
        WORK_APPROVAL_DECIDE,
        EFFECT_HUMAN_REQUIRED,
        ExecutionMode.HUMAN_REQUIRED,
        frozenset({"human_operator"}),
        "approval_decide",
    ),
}


def get_effect_spec(work_kind: str) -> EffectSpec | None:
    return _CATALOG.get(work_kind)


def agent_eligible_for(work_kind: str, agent: str) -> bool:
    spec = get_effect_spec(work_kind)
    if spec is None:
        return False
    return agent in spec.eligible_agents
