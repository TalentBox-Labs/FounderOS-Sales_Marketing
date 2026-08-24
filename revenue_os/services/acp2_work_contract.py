"""ACP-2 — canonical work contract (in-memory orchestration, not a persistent SoT).

Work identity and idempotency are deterministic strings. Lifecycle state lives on
the in-memory WorkItem for the duration of an orchestration call. Durable
evidence is append-only AgentActionLog + existing ApprovalRequest — AgentActionLog
is never used as a mutable workflow database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WorkState(str, Enum):
    PROPOSED = "PROPOSED"
    ELIGIBLE = "ELIGIBLE"
    BLOCKED = "BLOCKED"
    WAITING_HUMAN = "WAITING_HUMAN"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RETRYABLE = "RETRYABLE"
    EXHAUSTED = "EXHAUSTED"
    CANCELLED = "CANCELLED"


class ExecutionMode(str, Enum):
    AUTONOMOUS = "AUTONOMOUS"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    PROHIBITED = "PROHIBITED"


# Work kinds aligned to ACP-1 effect matrix / existing autonomous paths.
WORK_LEAD_SCORE = "lead_score"
WORK_FOLLOW_UP_PROPOSE = "follow_up_propose"
WORK_FOLLOW_UP_SEND = "follow_up_send"
WORK_RESEARCH_OUTREACH_PROPOSE = "research_outreach_propose"
WORK_DEAL_AT_RISK = "deal_at_risk_flag"
WORK_GMAIL_INBOUND = "gmail_inbound_match"
WORK_METRICS_SNAPSHOT = "metrics_snapshot"
WORK_HERMES_SCORE = "hermes_score"
WORK_HERMES_QUALIFY_RECOMMEND = "hermes_qualify_recommend"
WORK_HERMES_DEAL_CREATE = "hermes_deal_create"
WORK_OUTBOUND_SEND = "outbound_send"
WORK_BOOKING_EXECUTE = "booking_execute"
WORK_BOOKING_PROPOSE = "booking_propose"
WORK_DEAL_STAGE = "deal_stage_mutation"
WORK_CONTACT_STATUS = "contact_status_mutation"
WORK_QD_DECIDE = "qualified_demand_decide"
WORK_APPROVAL_DECIDE = "approval_decide"

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MAX_DELEGATION_DEPTH = 2

# Terminal states (no silent resurrection into RUNNING)
TERMINAL_STATES = frozenset(
    {
        WorkState.SUCCEEDED,
        WorkState.FAILED,
        WorkState.EXHAUSTED,
        WorkState.CANCELLED,
        WorkState.BLOCKED,
    }
)

# Forbidden silent transitions into RUNNING
FORBIDDEN_TO_RUNNING = frozenset(
    {
        WorkState.BLOCKED,
        WorkState.EXHAUSTED,
        WorkState.CANCELLED,
        WorkState.SUCCEEDED,
        WorkState.WAITING_HUMAN,
    }
)


@dataclass
class WorkItem:
    """In-memory orchestrated work unit (not a DB model)."""

    work_kind: str
    organization_id: str | None
    requested_effect: str
    source: str  # scheduler | hermes | agent | founder | event
    actor: str
    execution_mode: ExecutionMode
    state: WorkState = WorkState.PROPOSED
    work_id: str = ""
    parent_work_id: str | None = None
    root_work_id: str | None = None
    correlation_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    assigned_agent: str | None = None
    requesting_agent: str | None = None
    attempt: int = 0
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    delegation_depth: int = 0
    max_delegation_depth: int = DEFAULT_MAX_DELEGATION_DEPTH
    idempotency_key: str = ""
    authority_requirement: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    failure_reason: str | None = None
    escalation_reason: str | None = None
    approval_id: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_id": self.work_id,
            "organization_id": self.organization_id,
            "work_kind": self.work_kind,
            "requested_effect": self.requested_effect,
            "source": self.source,
            "actor": self.actor,
            "assigned_agent": self.assigned_agent,
            "requesting_agent": self.requesting_agent,
            "parent_work_id": self.parent_work_id,
            "root_work_id": self.root_work_id or self.work_id,
            "correlation_id": self.correlation_id,
            "execution_mode": self.execution_mode.value,
            "authority_requirement": self.authority_requirement,
            "state": self.state.value,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "delegation_depth": self.delegation_depth,
            "idempotency_key": self.idempotency_key,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "result": self.result,
            "failure_reason": self.failure_reason,
            "escalation_reason": self.escalation_reason,
            "approval_id": self.approval_id,
            "created_at": self.created_at,
        }


def deterministic_idempotency_key(
    *,
    work_kind: str,
    organization_id: str | None,
    target_id: str | None,
    logical_key: str = "",
) -> str:
    """Stable key — not a random UUID. Duplicate ticks share this key."""
    org = organization_id or "no-org"
    tgt = target_id or "no-target"
    tail = logical_key or "default"
    return f"acp2:{work_kind}:{org}:{tgt}:{tail}"


def derive_work_id(idempotency_key: str, *, attempt: int = 0) -> str:
    """Work identity derived from idempotency scope (+ attempt for retry provenance)."""
    if attempt <= 1:
        return f"work:{idempotency_key}"
    return f"work:{idempotency_key}:a{attempt}"


def can_transition_to_running(state: WorkState) -> bool:
    return state in (WorkState.ELIGIBLE, WorkState.RETRYABLE)


def is_terminal(state: WorkState) -> bool:
    return state in (
        WorkState.SUCCEEDED,
        WorkState.FAILED,
        WorkState.EXHAUSTED,
        WorkState.CANCELLED,
        WorkState.BLOCKED,
    )
