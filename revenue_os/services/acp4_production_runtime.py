"""ACP-4 production runtime — claim + fence around protected autonomous execution.

Composes ACP-1/2/3. Does not expand authority.
Does not claim distributed exactly-once execution.

Ordering:
  discover → claim → fence (current authority/tenant/pause/kill) →
  idempotency evidence → execute → provenance → claim release (xact end / finally)
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.orm import Session

from revenue_os.services.activity_log import log_agent_action
from revenue_os.services.acp2_orchestration import (
    assign_executor,
    evaluate_authority,
    propose_work,
    run_work,
)
from revenue_os.services.acp2_work_contract import (
    ExecutionMode,
    WorkItem,
    WorkState,
)
from revenue_os.services.acp4_distributed_claim import (
    ClaimResult,
    dialect_name,
    try_acquire_claim,
)
from revenue_os.services.acp4_execution_fence import FenceResult, pre_effect_fence

ACTOR = "acp4_runtime"

LOG_CLAIM_ACQUIRED = "acp4_claim_acquired"
LOG_CLAIM_UNAVAILABLE = "acp4_claim_unavailable"
LOG_FENCE_REJECTED = "acp4_fence_rejected"
LOG_STALE_EXECUTOR_REJECTED = "acp4_stale_executor_rejected"
LOG_EXECUTION_STARTED = "acp4_execution_started"


def coordination_backend_info(db: Session) -> dict[str, Any]:
    dialect = dialect_name(db)
    if dialect in ("postgresql", "postgres"):
        return {
            "dialect": dialect,
            "mechanism": "pg_try_advisory_xact_lock",
            "distributed_safety_claimed": True,
        }
    return {
        "dialect": dialect or "unknown",
        "mechanism": "process_local_test_only",
        "distributed_safety_claimed": False,
        "note": (
            "Non-PostgreSQL backends do not provide multi-replica advisory locks. "
            "ACP-4 does not claim distributed multi-worker safety on this backend."
        ),
    }


def run_work_claimed(
    db: Session,
    work: WorkItem,
    executor: Callable[[WorkItem], dict[str, Any]],
    *,
    transient_failure: bool = False,
    require_autonomous: bool = True,
) -> WorkItem:
    """Claim → fence → run_work. Claim ≠ authorized ≠ succeeded."""
    if work.state == WorkState.WAITING_HUMAN:
        return work
    if work.execution_mode == ExecutionMode.PROHIBITED:
        work.state = WorkState.BLOCKED
        work.failure_reason = work.failure_reason or "effect_prohibited"
        return work
    if work.state not in (WorkState.ELIGIBLE, WorkState.RETRYABLE, WorkState.PROPOSED):
        return work

    org_id = str(work.organization_id or "").strip()
    if not org_id:
        work.state = WorkState.BLOCKED
        work.failure_reason = "missing_tenant"
        _log(
            LOG_FENCE_REJECTED,
            work,
            status="blocked",
            extra={"reason": "missing_tenant"},
        )
        return work

    claim = try_acquire_claim(
        db,
        organization_id=org_id,
        idempotency_key=work.idempotency_key,
    )
    if not claim.acquired:
        work.state = WorkState.CANCELLED
        work.failure_reason = claim.reason or "claim_unavailable"
        work.result = {"claim": claim.to_dict(), "suppressed_duplicate_worker": True}
        _log(LOG_CLAIM_UNAVAILABLE, work, status="blocked", extra=claim.to_dict())
        return work

    _log(LOG_CLAIM_ACQUIRED, work, status="completed", extra=claim.to_dict())

    fence = pre_effect_fence(
        db,
        work,
        require_autonomous=require_autonomous,
        claim_held=True,
    )
    if not fence.ok:
        return _reject_fence(work, fence)

    _log(
        LOG_EXECUTION_STARTED,
        work,
        status="completed",
        extra={"claim": claim.to_dict(), "fence": fence.to_dict()},
    )
    return run_work(db, work, executor, transient_failure=transient_failure)


def _reject_fence(work: WorkItem, fence: FenceResult) -> WorkItem:
    reason = fence.reason or "fence_rejected"
    work.failure_reason = reason
    work.result = {"fence": fence.to_dict()}
    if reason == "already_succeeded":
        work.state = WorkState.SUCCEEDED
        work.result = {
            "deduplicated": True,
            "idempotency_key": work.idempotency_key,
            "fence": fence.to_dict(),
        }
        _log(LOG_FENCE_REJECTED, work, status="completed", extra=fence.to_dict())
        return work

    work.state = WorkState.BLOCKED
    action = LOG_STALE_EXECUTOR_REJECTED if reason in (
        "acp2_autonomous_execution_disabled",
        "heartbeat_paused",
        "authority_now_human_required",
        "effect_prohibited",
        "tenant_not_active",
        "tenant_not_autonomous_eligible",
    ) else LOG_FENCE_REJECTED
    _log(action, work, status="blocked", extra=fence.to_dict())
    return work


def orchestrate_claimed(
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
    """Propose → assign → evaluate → claim → fence → run if eligible."""
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
        return run_work_claimed(db, work, executor)
    return work


def retry_work_claimed(
    db: Session,
    work: WorkItem,
    executor: Callable[[WorkItem], dict[str, Any]],
) -> WorkItem:
    """ACP-3 recovery path: RETRYABLE → ELIGIBLE → claim → fence → run."""
    if work.state != WorkState.RETRYABLE:
        return work
    if work.execution_mode in (ExecutionMode.HUMAN_REQUIRED, ExecutionMode.PROHIBITED):
        work.state = WorkState.BLOCKED
        work.failure_reason = "retry_forbidden_for_mode"
        _log(LOG_FENCE_REJECTED, work, status="blocked", extra={"reason": work.failure_reason})
        return work
    work.state = WorkState.ELIGIBLE
    return run_work_claimed(db, work, executor, transient_failure=True)


def _log(
    action_type: str,
    work: WorkItem,
    *,
    status: str,
    extra: dict[str, Any] | None = None,
) -> None:
    log_agent_action(
        actor=work.assigned_agent or work.actor or ACTOR,
        action_type=action_type,
        target_type=work.target_type,
        target_id=work.target_id,
        status=status,
        organization_id=work.organization_id,
        detail={**work.to_dict(), **(extra or {})},
    )


# Re-export types for callers/tests
__all__ = [
    "ClaimResult",
    "FenceResult",
    "LOG_CLAIM_ACQUIRED",
    "LOG_CLAIM_UNAVAILABLE",
    "LOG_FENCE_REJECTED",
    "LOG_STALE_EXECUTOR_REJECTED",
    "LOG_EXECUTION_STARTED",
    "coordination_backend_info",
    "orchestrate_claimed",
    "retry_work_claimed",
    "run_work_claimed",
]
