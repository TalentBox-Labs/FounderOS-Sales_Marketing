"""ACP-3 durable runtime — pause/kill/resume + bounded recovery execution.

Composes ACP-2 orchestration and ACP-1 authority. Durability never amplifies
authority. Recovery re-evaluates tenant + effect mode before any executor call.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact
from revenue_os.services.activity_log import log_agent_action
from revenue_os.services.acp1_autonomous_boundary import (
    BLOCKED_MISSING_TENANT,
    org_uuid_or_none,
    resolve_autonomous_organization_ids,
)
from revenue_os.services.acp2_orchestration import (
    assign_executor,
    autonomous_execution_enabled,
    evaluate_authority,
    heartbeat_pause_active,
    propose_work,
    retry_work,
)
from revenue_os.services.acp2_work_contract import (
    WORK_LEAD_SCORE,
    ExecutionMode,
    WorkItem,
    WorkState,
)
from revenue_os.services.acp3_reconciliation import (
    reconcile_organization,
)
from revenue_os.services.acp3_runtime_contract import (
    DEFAULT_RECOVERY_EXEC_LIMIT,
    DEFAULT_RECONCILE_SCAN_LIMIT,
    ENV_RESUME_ENABLED,
    LOG_ACP3_AMBIGUOUS,
    LOG_ACP3_KILL_GATE,
    LOG_ACP3_PAUSE_GATE,
    LOG_ACP3_RECOVERY_ATTEMPTED,
    LOG_ACP3_RECONCILED,
    LOG_ACP3_RESUME_PASS,
    RecoveryClass,
)
from revenue_os.services.lead_scoring_service import score_contact

logger = logging.getLogger(__name__)

ACTOR = "acp3_runtime"


def resume_enabled() -> bool:
    return os.environ.get(ENV_RESUME_ENABLED, "1") not in ("0", "false", "False")


def runtime_gates() -> dict[str, Any]:
    """Founder-visible pause/kill/resume state."""
    paused = heartbeat_pause_active()
    killed = not autonomous_execution_enabled()
    return {
        "heartbeat_paused": paused,
        "acp2_execution_killed": killed,
        "acp3_resume_enabled": resume_enabled(),
        "new_mutating_work_allowed": (not paused) and (not killed),
        "recovery_execution_allowed": (not paused) and (not killed) and resume_enabled(),
        "approvals_remain_human": True,
        "observational_reconcile_allowed": True,
        "note": (
            "PAUSE blocks new scheduler mutating work and recovery execution. "
            "KILL fails closed for autonomous execution. "
            "Neither rolls back committed external effects. "
            "HUMAN_REQUIRED approvals remain decideable by humans."
        ),
    }


def gate_new_mutating_work(*, actor: str = ACTOR, organization_id: str | None = None) -> dict[str, Any] | None:
    """Return blocked payload if pause/kill prevents new autonomous mutating work."""
    gates = runtime_gates()
    if gates["acp2_execution_killed"]:
        log_agent_action(
            actor=actor,
            action_type=LOG_ACP3_KILL_GATE,
            status="blocked",
            organization_id=organization_id,
            detail=gates,
        )
        return {
            "ok": False,
            "blocked": True,
            "blocked_reason": "acp2_autonomous_execution_disabled",
            "gates": gates,
        }
    if gates["heartbeat_paused"]:
        log_agent_action(
            actor=actor,
            action_type=LOG_ACP3_PAUSE_GATE,
            status="blocked",
            organization_id=organization_id,
            detail=gates,
        )
        return {
            "ok": False,
            "blocked": True,
            "blocked_reason": "heartbeat_paused",
            "gates": gates,
        }
    return None


def mark_ambiguous(
    *,
    organization_id: str | None,
    idempotency_key: str,
    work_kind: str,
    detail: dict[str, Any] | None = None,
) -> None:
    log_agent_action(
        actor=ACTOR,
        action_type=LOG_ACP3_AMBIGUOUS,
        status="blocked",
        organization_id=organization_id,
        detail={
            "idempotency_key": idempotency_key,
            "work_kind": work_kind,
            "recovery_class": RecoveryClass.AMBIGUOUS_EFFECT.value,
            "note": "human_review_required_no_blind_replay",
            **(detail or {}),
        },
    )


def recover_retryable_unit(
    db: Session,
    *,
    organization_id: str,
    item: dict[str, Any],
    executor: Callable[[WorkItem], dict[str, Any]],
) -> dict[str, Any]:
    """Re-evaluate authority and retry one RETRYABLE unit. Never amplifies authority."""
    gate = gate_new_mutating_work(organization_id=organization_id)
    if gate is not None:
        return gate

    if item.get("recovery_class") != RecoveryClass.RETRYABLE.value:
        return {
            "ok": False,
            "blocked": True,
            "blocked_reason": f"not_retryable:{item.get('recovery_class')}",
        }

    work_kind = str(item.get("work_kind") or "")
    if not work_kind:
        return {"ok": False, "blocked": True, "blocked_reason": "missing_work_kind"}

    # Reconstruct WorkItem — authority re-evaluated fresh (narrower current wins)
    work = propose_work(
        work_kind=work_kind,
        organization_id=organization_id,
        source="acp3_recovery",
        actor=str(item.get("actor") or ACTOR),
        target_type=item.get("target_type"),
        target_id=item.get("target_id"),
        logical_key=_logical_key_from_idem(item.get("idempotency_key"), work_kind, organization_id, item.get("target_id")),
        detail={
            "recovery_from": item.get("last_action_type"),
            "prior_attempt": item.get("attempt"),
            "treat_as_transient": True,
        },
        max_attempts=int(item.get("max_attempts") or 3),
    )
    # Preserve attempt counter from prior durable facts
    prior_attempt = int(item.get("attempt") or 0)
    work.attempt = prior_attempt
    assign_executor(work, preferred_agent=str(item.get("actor") or "heartbeat"))
    evaluate_authority(db, work)

    log_agent_action(
        actor=ACTOR,
        action_type=LOG_ACP3_RECOVERY_ATTEMPTED,
        status="completed",
        organization_id=organization_id,
        target_type=work.target_type,
        target_id=work.target_id,
        detail={
            **work.to_dict(),
            "prior_recovery_class": item.get("recovery_class"),
        },
    )

    if work.state == WorkState.WAITING_HUMAN:
        return {"ok": True, "work": work.to_dict(), "note": "still_human_required"}
    if work.state == WorkState.BLOCKED or work.state == WorkState.CANCELLED:
        return {"ok": False, "blocked": True, "work": work.to_dict()}
    if work.state == WorkState.SUCCEEDED and work.result.get("deduplicated"):
        return {"ok": True, "work": work.to_dict(), "deduplicated": True}

    if work.execution_mode == ExecutionMode.PROHIBITED:
        work.state = WorkState.BLOCKED
        return {"ok": False, "blocked": True, "work": work.to_dict(), "note": "prohibited_no_retry"}

    # Resume from RETRYABLE semantics
    work.state = WorkState.RETRYABLE
    out = retry_work(db, work, executor)
    return {"ok": out.state == WorkState.SUCCEEDED, "work": out.to_dict()}


def _logical_key_from_idem(
    idem: Any, work_kind: str, organization_id: str, target_id: Any
) -> str:
    """Extract logical_key tail from deterministic idempotency key when possible."""
    text = str(idem or "")
    prefix = f"acp2:{work_kind}:{organization_id or 'no-org'}:{target_id or 'no-target'}:"
    if text.startswith(prefix):
        return text[len(prefix) :]
    return "recovery"


def bounded_resume_pass(
    db: Session,
    *,
    organization_id: str,
    executors: dict[str, Callable[[WorkItem], dict[str, Any]]],
    scan_limit: int = DEFAULT_RECONCILE_SCAN_LIMIT,
    exec_limit: int = DEFAULT_RECOVERY_EXEC_LIMIT,
) -> dict[str, Any]:
    """Bounded resume: classify then recover up to exec_limit retryable units.

    Does not replay SUCCEEDED, WAITING_HUMAN into autonomous send, PROHIBITED,
    EXHAUSTED, or AMBIGUOUS_EFFECT.
    """
    gates = runtime_gates()
    report = reconcile_organization(
        db, organization_id=organization_id, limit=scan_limit
    )
    log_agent_action(
        actor=ACTOR,
        action_type=LOG_ACP3_RECONCILED,
        status="completed",
        organization_id=organization_id,
        detail={
            "counts": report.get("counts"),
            "requires_founder_action": report.get("requires_founder_action"),
            "gates": gates,
        },
    )

    if not gates["recovery_execution_allowed"]:
        log_agent_action(
            actor=ACTOR,
            action_type=LOG_ACP3_RESUME_PASS,
            status="blocked",
            organization_id=organization_id,
            detail={"gates": gates, "executed": 0},
        )
        return {
            "ok": True,
            "organization_id": organization_id,
            "reconcile": report,
            "recovered": [],
            "skipped_ambiguous": report.get("buckets", {}).get("ambiguous_effect", []),
            "executed": 0,
            "gates": gates,
            "note": "observational_only_under_pause_or_kill",
        }

    recovered: list[dict[str, Any]] = []
    retryable = list(report.get("buckets", {}).get("retryable", []))[:exec_limit]
    for item in retryable:
        kind = str(item.get("work_kind") or "")
        executor = executors.get(kind)
        if executor is None:
            recovered.append(
                {
                    "idempotency_key": item.get("idempotency_key"),
                    "skipped": True,
                    "reason": "no_executor_registered",
                }
            )
            continue
        result = recover_retryable_unit(
            db,
            organization_id=organization_id,
            item=item,
            executor=executor,
        )
        recovered.append(result)

    # Surface ambiguous for founder — never execute
    for amb in report.get("buckets", {}).get("ambiguous_effect", [])[:exec_limit]:
        mark_ambiguous(
            organization_id=organization_id,
            idempotency_key=str(amb.get("idempotency_key") or ""),
            work_kind=str(amb.get("work_kind") or ""),
            detail=amb,
        )

    log_agent_action(
        actor=ACTOR,
        action_type=LOG_ACP3_RESUME_PASS,
        status="completed",
        organization_id=organization_id,
        detail={
            "executed": len([r for r in recovered if r.get("ok")]),
            "attempted": len(recovered),
            "gates": gates,
        },
    )
    return {
        "ok": True,
        "organization_id": organization_id,
        "reconcile": report,
        "recovered": recovered,
        "executed": len([r for r in recovered if r.get("ok")]),
        "gates": gates,
        "resumed_at": datetime.now(timezone.utc).isoformat(),
    }


def job_reconcile_autonomous_work() -> dict[str, Any]:
    """Scheduler entry: bounded per-org reconcile + optional recovery for lead_score."""
    # Deferred import: revenue_os.database instantiates Settings at import time.
    from revenue_os.database import SessionLocal

    db = SessionLocal()
    try:
        orgs = resolve_autonomous_organization_ids(db)
        if not orgs:
            return {
                "ok": False,
                "blocked": True,
                "blocked_reason": BLOCKED_MISSING_TENANT,
                "gates": runtime_gates(),
            }

        def _lead_exec(work: WorkItem) -> dict[str, Any]:
            if not work.target_id or not work.organization_id:
                return {"blocked": True, "blocked_reason": "missing_target_or_org"}
            org_uuid = org_uuid_or_none(work.organization_id)
            try:
                cid = uuid.UUID(str(work.target_id))
            except ValueError:
                return {"blocked": True, "blocked_reason": "invalid_target"}
            contact = db.get(Contact, cid)
            if contact is None or org_uuid is None or contact.organization_id != org_uuid:
                return {"blocked": True, "blocked_reason": "tenant_entity_mismatch"}
            if contact.lead_score and contact.lead_score > 0:
                return {"ok": True, "already_scored": True, "score": contact.lead_score}
            payload = score_contact(db, contact)
            return {"ok": True, "score": payload["score"]}

        executors = {WORK_LEAD_SCORE: _lead_exec}
        results = []
        for organization_id in orgs:
            results.append(
                bounded_resume_pass(
                    db,
                    organization_id=organization_id,
                    executors=executors,
                )
            )
        db.commit()
        return {
            "ok": True,
            "organizations": orgs,
            "results": results,
            "gates": runtime_gates(),
            "orchestrated": True,
        }
    finally:
        db.close()
