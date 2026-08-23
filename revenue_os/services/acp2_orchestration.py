"""ACP-2 — Agent Orchestration & Work Control Plane.

Composes ACP-1 authority. Does not grant, widen, or replace ACP-1.
No new persistent SoT: WorkItem is in-memory; provenance is append-only
AgentActionLog; human gates reuse ApprovalRequest; pause/kill uses env flags.
"""

from __future__ import annotations

import os
from typing import Any, Callable

from sqlalchemy.orm import Session

from revenue_os.services.activity_log import log_agent_action
from revenue_os.services.acp1_autonomous_boundary import (
    BLOCKED_HERMES_DEAL,
    BLOCKED_MISSING_TENANT,
    BLOCKED_PROHIBITED_EFFECT,
    BLOCKED_TENANT_MISMATCH,
    resolve_autonomous_organization_ids,
)
from revenue_os.services.acp2_effect_catalog import agent_eligible_for, get_effect_spec
from revenue_os.services.acp2_work_contract import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_DELEGATION_DEPTH,
    WORK_HERMES_DEAL_CREATE,
    ExecutionMode,
    WorkItem,
    WorkState,
    can_transition_to_running,
    derive_work_id,
    deterministic_idempotency_key,
    is_terminal,
)

ENV_ACP2_EXECUTION = "ACP2_AUTONOMOUS_EXECUTION_ENABLED"
ACTOR_ORCHESTRATOR = "acp2_orchestrator"

# Provenance action types (append-only; not a workflow SoT)
LOG_ORCH_PROPOSED = "acp2_work_proposed"
LOG_ORCH_BLOCKED = "acp2_work_blocked"
LOG_ORCH_WAITING = "acp2_work_waiting_human"
LOG_ORCH_RUNNING = "acp2_work_running"
LOG_ORCH_SUCCEEDED = "acp2_work_succeeded"
LOG_ORCH_FAILED = "acp2_work_failed"
LOG_ORCH_RETRYABLE = "acp2_work_retryable"
LOG_ORCH_EXHAUSTED = "acp2_work_exhausted"
LOG_ORCH_DELEGATED = "acp2_work_delegated"
LOG_ORCH_CANCELLED = "acp2_work_cancelled"


def autonomous_execution_enabled() -> bool:
    """KILL switch for ACP-2 autonomous effect execution (future work)."""
    return os.environ.get(ENV_ACP2_EXECUTION, "1") not in ("0", "false", "False")


def heartbeat_pause_active() -> bool:
    """PAUSE: existing HEARTBEAT_ENABLED=0 prevents scheduler-driven wake."""
    return os.environ.get("HEARTBEAT_ENABLED", "1") in ("0", "false", "False")


def propose_work(
    *,
    work_kind: str,
    organization_id: str | None,
    source: str,
    actor: str,
    target_type: str | None = None,
    target_id: str | None = None,
    logical_key: str = "",
    parent: WorkItem | None = None,
    requesting_agent: str | None = None,
    detail: dict[str, Any] | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> WorkItem:
    """Create a PROPOSED WorkItem. Assignment/source never imply authority."""
    spec = get_effect_spec(work_kind)
    if spec is None:
        mode = ExecutionMode.PROHIBITED
        effect = work_kind
        authority = "unknown_work_kind"
    else:
        mode = spec.execution_mode
        effect = spec.requested_effect
        authority = spec.acp1_effect_class

    depth = (parent.delegation_depth + 1) if parent else 0
    idem = deterministic_idempotency_key(
        work_kind=work_kind,
        organization_id=organization_id,
        target_id=target_id,
        logical_key=logical_key,
    )
    work = WorkItem(
        work_kind=work_kind,
        organization_id=organization_id,
        requested_effect=effect,
        source=source,
        actor=actor,
        execution_mode=mode,
        authority_requirement=authority,
        target_type=target_type,
        target_id=target_id,
        idempotency_key=idem,
        work_id=derive_work_id(idem, attempt=1),
        parent_work_id=parent.work_id if parent else None,
        root_work_id=(parent.root_work_id or parent.work_id) if parent else None,
        correlation_id=(parent.correlation_id or parent.work_id) if parent else None,
        requesting_agent=requesting_agent or (parent.assigned_agent if parent else None),
        delegation_depth=depth,
        max_attempts=max_attempts,
        detail=dict(detail or {}),
    )
    if work.root_work_id is None:
        work.root_work_id = work.work_id
    if work.correlation_id is None:
        work.correlation_id = work.work_id
    return work


def assign_executor(work: WorkItem, preferred_agent: str | None = None) -> WorkItem:
    """Deterministic assignment hint. Does not grant authority."""
    agent = preferred_agent or work.actor
    if not agent_eligible_for(work.work_kind, agent):
        # Still record who was asked; eligibility failure handled in evaluate
        work.assigned_agent = agent
        work.detail["assignment_eligible"] = False
        return work
    work.assigned_agent = agent
    work.detail["assignment_eligible"] = True
    return work


def _already_succeeded(db: Session, idempotency_key: str) -> bool:
    from revenue_os.models.automation_state import AgentActionLog

    row = (
        db.query(AgentActionLog)
        .filter(AgentActionLog.action_type == LOG_ORCH_SUCCEEDED)
        .filter(AgentActionLog.status == "completed")
        .order_by(AgentActionLog.created_at.desc())
        .limit(50)
        .all()
    )
    for r in row:
        detail = r.detail or {}
        if detail.get("idempotency_key") == idempotency_key:
            return True
    return False


def _provenance(
    work: WorkItem,
    *,
    action_type: str,
    status: str,
    extra: dict[str, Any] | None = None,
) -> None:
    detail = {
        **work.to_dict(),
        **(extra or {}),
    }
    log_agent_action(
        actor=work.assigned_agent or work.actor or ACTOR_ORCHESTRATOR,
        action_type=action_type,
        target_type=work.target_type,
        target_id=work.target_id,
        status=status,
        organization_id=work.organization_id,
        detail=detail,
    )


def evaluate_authority(db: Session, work: WorkItem) -> WorkItem:
    """ACP-1-backed authority evaluation. Assignment/planning never authorize."""
    if not autonomous_execution_enabled() and work.execution_mode == ExecutionMode.AUTONOMOUS:
        work.state = WorkState.CANCELLED
        work.failure_reason = "acp2_autonomous_execution_disabled"
        _provenance(work, action_type=LOG_ORCH_CANCELLED, status="blocked")
        return work

    if work.execution_mode == ExecutionMode.PROHIBITED:
        work.state = WorkState.BLOCKED
        work.failure_reason = BLOCKED_PROHIBITED_EFFECT
        if work.work_kind == WORK_HERMES_DEAL_CREATE:
            work.failure_reason = BLOCKED_HERMES_DEAL
        _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return work

    if work.execution_mode == ExecutionMode.HUMAN_REQUIRED:
        work.state = WorkState.WAITING_HUMAN
        work.escalation_reason = "human_approval_required"
        _provenance(work, action_type=LOG_ORCH_WAITING, status="blocked")
        return work

    # AUTONOMOUS path — mandatory tenant
    if not work.organization_id:
        work.state = WorkState.BLOCKED
        work.failure_reason = BLOCKED_MISSING_TENANT
        _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return work

    allowed = set(resolve_autonomous_organization_ids(db))
    if str(work.organization_id) not in allowed:
        work.state = WorkState.BLOCKED
        work.failure_reason = BLOCKED_MISSING_TENANT
        work.detail["tenant_not_in_autonomous_set"] = True
        _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return work

    # ACP-1 hard prohibition (defense in depth beyond catalog)
    if work.work_kind == WORK_HERMES_DEAL_CREATE:
        work.state = WorkState.BLOCKED
        work.failure_reason = BLOCKED_HERMES_DEAL
        _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return work

    if work.detail.get("assignment_eligible") is False:
        work.state = WorkState.BLOCKED
        work.failure_reason = "agent_not_eligible_for_work_kind"
        _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return work

    if _already_succeeded(db, work.idempotency_key):
        work.state = WorkState.SUCCEEDED
        work.result = {"deduplicated": True, "idempotency_key": work.idempotency_key}
        _provenance(
            work,
            action_type=LOG_ORCH_SUCCEEDED,
            status="completed",
            extra={"deduplicated": True},
        )
        return work

    work.state = WorkState.ELIGIBLE
    _provenance(work, action_type=LOG_ORCH_PROPOSED, status="completed")
    return work


def run_work(
    db: Session,
    work: WorkItem,
    executor: Callable[[WorkItem], dict[str, Any]],
    *,
    transient_failure: bool = False,
) -> WorkItem:
    """Execute eligible work. Never runs BLOCKED/WAITING_HUMAN/PROHIBITED/CANCELLED."""
    if work.state == WorkState.PROPOSED:
        evaluate_authority(db, work)

    if work.state == WorkState.WAITING_HUMAN:
        return work
    if is_terminal(work.state) and work.state != WorkState.RETRYABLE:
        return work
    if not can_transition_to_running(work.state):
        if work.state not in (WorkState.BLOCKED, WorkState.WAITING_HUMAN, WorkState.CANCELLED):
            work.state = WorkState.BLOCKED
            work.failure_reason = work.failure_reason or "illegal_transition_to_running"
            _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return work

    work.attempt += 1
    work.work_id = derive_work_id(work.idempotency_key, attempt=work.attempt)
    work.state = WorkState.RUNNING
    _provenance(work, action_type=LOG_ORCH_RUNNING, status="completed")

    try:
        result = executor(work) or {}
        if result.get("blocked"):
            work.state = WorkState.BLOCKED
            work.failure_reason = str(result.get("blocked_reason") or "executor_blocked")
            work.result = result
            _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
            return work
        if result.get("waiting_human") or result.get("approval_id"):
            work.state = WorkState.WAITING_HUMAN
            work.approval_id = result.get("approval_id")
            work.escalation_reason = result.get("escalation_reason") or "approval_filed"
            work.result = result
            _provenance(work, action_type=LOG_ORCH_WAITING, status="completed")
            return work
        work.state = WorkState.SUCCEEDED
        work.result = result
        _provenance(work, action_type=LOG_ORCH_SUCCEEDED, status="completed")
        return work
    except Exception as exc:  # noqa: BLE001 — orchestration boundary
        work.failure_reason = str(exc)
        work.result = {"error": str(exc)}
        if transient_failure or work.detail.get("treat_as_transient"):
            if work.attempt < work.max_attempts:
                work.state = WorkState.RETRYABLE
                _provenance(work, action_type=LOG_ORCH_RETRYABLE, status="failed")
            else:
                work.state = WorkState.EXHAUSTED
                _provenance(work, action_type=LOG_ORCH_EXHAUSTED, status="failed")
        else:
            # Authority / validation style failures: do not retry into execution
            reason = str(exc).lower()
            if any(
                k in reason
                for k in ("tenant", "authority", "prohibited", "forbidden", "approval")
            ):
                work.state = WorkState.BLOCKED
                _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
            elif work.attempt < work.max_attempts:
                work.state = WorkState.RETRYABLE
                _provenance(work, action_type=LOG_ORCH_RETRYABLE, status="failed")
            else:
                work.state = WorkState.EXHAUSTED
                _provenance(work, action_type=LOG_ORCH_EXHAUSTED, status="failed")
        return work


def retry_work(
    db: Session,
    work: WorkItem,
    executor: Callable[[WorkItem], dict[str, Any]],
) -> WorkItem:
    """Retry only from RETRYABLE. Never retries HUMAN_REQUIRED or PROHIBITED."""
    if work.state != WorkState.RETRYABLE:
        return work
    if work.execution_mode in (ExecutionMode.HUMAN_REQUIRED, ExecutionMode.PROHIBITED):
        work.state = WorkState.BLOCKED
        work.failure_reason = "retry_forbidden_for_mode"
        _provenance(work, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return work
    work.state = WorkState.ELIGIBLE
    return run_work(db, work, executor, transient_failure=True)


def delegate_child(
    db: Session,
    parent: WorkItem,
    *,
    child_work_kind: str,
    actor: str,
    target_type: str | None = None,
    target_id: str | None = None,
    logical_key: str = "",
    executor: Callable[[WorkItem], dict[str, Any]] | None = None,
) -> WorkItem:
    """Bounded subagent delegation. Never amplifies authority."""
    if parent.organization_id is None:
        child = propose_work(
            work_kind=child_work_kind,
            organization_id=None,
            source="delegation",
            actor=actor,
            parent=parent,
            requesting_agent=parent.assigned_agent or parent.actor,
            target_type=target_type,
            target_id=target_id,
            logical_key=logical_key,
        )
        child.state = WorkState.BLOCKED
        child.failure_reason = BLOCKED_MISSING_TENANT
        _provenance(child, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return child

    if parent.delegation_depth >= parent.max_delegation_depth:
        child = propose_work(
            work_kind=child_work_kind,
            organization_id=parent.organization_id,
            source="delegation",
            actor=actor,
            parent=parent,
            requesting_agent=parent.assigned_agent or parent.actor,
            target_type=target_type,
            target_id=target_id,
            logical_key=logical_key,
        )
        child.state = WorkState.BLOCKED
        child.failure_reason = "delegation_depth_exceeded"
        _provenance(child, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return child

    child = propose_work(
        work_kind=child_work_kind,
        organization_id=parent.organization_id,  # cross-tenant prohibited
        source="delegation",
        actor=actor,
        parent=parent,
        requesting_agent=parent.assigned_agent or parent.actor,
        target_type=target_type,
        target_id=target_id,
        logical_key=logical_key,
    )

    # Cross-tenant guard (explicit)
    if str(child.organization_id) != str(parent.organization_id):
        child.state = WorkState.BLOCKED
        child.failure_reason = BLOCKED_TENANT_MISMATCH
        _provenance(child, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return child

    # Authority intersection: child mode cannot exceed parent effective authority
    parent_mode = parent.execution_mode
    if parent_mode == ExecutionMode.PROHIBITED:
        child.state = WorkState.BLOCKED
        child.failure_reason = "parent_prohibited_cannot_delegate"
        _provenance(child, action_type=LOG_ORCH_BLOCKED, status="blocked")
        return child
    if (
        parent_mode == ExecutionMode.HUMAN_REQUIRED
        and child.execution_mode == ExecutionMode.AUTONOMOUS
    ):
        # Cannot amplify: force child to HUMAN_REQUIRED
        child.execution_mode = ExecutionMode.HUMAN_REQUIRED
        child.detail["authority_capped_by_parent"] = True

    assign_executor(child, preferred_agent=actor)
    _provenance(
        child,
        action_type=LOG_ORCH_DELEGATED,
        status="completed",
        extra={
            "parent_work_id": parent.work_id,
            "root_work_id": child.root_work_id,
            "requesting_agent": child.requesting_agent,
            "executing_agent": child.assigned_agent,
        },
    )
    evaluate_authority(db, child)
    if executor is not None and child.state == WorkState.ELIGIBLE:
        return run_work(db, child, executor)
    return child


def orchestrate(
    db: Session,
    *,
    work_kind: str,
    organization_id: str | None,
    source: str,
    actor: str,
    executor: Callable[[WorkItem], dict[str, Any]],
    target_type: str | None = None,
    target_id: str | None = None,
    logical_key: str = "",
    detail: dict[str, Any] | None = None,
) -> WorkItem:
    """Propose → assign → evaluate (ACP-1) → run if eligible."""
    work = propose_work(
        work_kind=work_kind,
        organization_id=organization_id,
        source=source,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
        logical_key=logical_key,
        detail=detail,
    )
    assign_executor(work, preferred_agent=actor)
    evaluate_authority(db, work)
    if work.state == WorkState.ELIGIBLE:
        return run_work(db, work, executor)
    return work
