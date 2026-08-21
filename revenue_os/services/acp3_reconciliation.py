"""ACP-3 reconciliation — reconstruct durable work state from AgentActionLog.

Does not mutate AgentActionLog into a workflow SoT: reads latest event per
idempotency_key and classifies recovery. Domain state may prove completion
(e.g. lead_score already written) without fabricating approval.
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.contact import Contact
from revenue_os.services.acp2_orchestration import (
    LOG_ORCH_BLOCKED,
    LOG_ORCH_CANCELLED,
    LOG_ORCH_EXHAUSTED,
    LOG_ORCH_FAILED,
    LOG_ORCH_PROPOSED,
    LOG_ORCH_RETRYABLE,
    LOG_ORCH_RUNNING,
    LOG_ORCH_SUCCEEDED,
    LOG_ORCH_WAITING,
)
from revenue_os.services.acp2_work_contract import (
    WORK_FOLLOW_UP_PROPOSE,
    WORK_HERMES_DEAL_CREATE,
    WORK_LEAD_SCORE,
    WORK_OUTBOUND_SEND,
    WORK_BOOKING_EXECUTE,
    WORK_FOLLOW_UP_SEND,
    ExecutionMode,
)
from revenue_os.services.acp3_runtime_contract import (
    DEFAULT_RECONCILE_SCAN_LIMIT,
    LOG_ACP3_AMBIGUOUS,
    RecoveryClass,
)

_ORCH_EVENT_TYPES = frozenset(
    {
        LOG_ORCH_PROPOSED,
        LOG_ORCH_BLOCKED,
        LOG_ORCH_WAITING,
        LOG_ORCH_RUNNING,
        LOG_ORCH_SUCCEEDED,
        LOG_ORCH_FAILED,
        LOG_ORCH_RETRYABLE,
        LOG_ORCH_EXHAUSTED,
        LOG_ORCH_CANCELLED,
        LOG_ACP3_AMBIGUOUS,
    }
)

# Effects that must never be blindly replayed on ambiguous crash
_AMBIGUOUS_EXTERNAL_KINDS = frozenset(
    {
        WORK_OUTBOUND_SEND,
        WORK_FOLLOW_UP_SEND,
        WORK_BOOKING_EXECUTE,
    }
)


def _org_uuid(organization_id: str) -> uuid_lib.UUID | None:
    try:
        return uuid_lib.UUID(str(organization_id))
    except ValueError:
        return None


def latest_orch_events_by_idempotency(
    db: Session, *, organization_id: str, limit: int = DEFAULT_RECONCILE_SCAN_LIMIT
) -> dict[str, AgentActionLog]:
    """Latest ACP-2/ACP-3 orchestration event per idempotency_key (org-scoped)."""
    org_uuid = _org_uuid(organization_id)
    if org_uuid is None:
        return {}
    rows = (
        db.query(AgentActionLog)
        .filter(AgentActionLog.organization_id == org_uuid)
        .filter(AgentActionLog.action_type.in_(list(_ORCH_EVENT_TYPES)))
        .order_by(AgentActionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    latest: dict[str, AgentActionLog] = {}
    for row in rows:
        detail = row.detail or {}
        key = str(detail.get("idempotency_key") or "").strip()
        if not key or key in latest:
            continue
        latest[key] = row
    return latest


def classify_recovery(
    db: Session,
    *,
    organization_id: str,
    row: AgentActionLog,
) -> dict[str, Any]:
    """Classify one durable work unit for recovery. Never invents success/approval."""
    detail = row.detail or {}
    work_kind = str(detail.get("work_kind") or "")
    execution_mode = str(detail.get("execution_mode") or "")
    idem = str(detail.get("idempotency_key") or "")
    attempt = int(detail.get("attempt") or 0)
    max_attempts = int(detail.get("max_attempts") or 3)
    action = row.action_type

    base = {
        "organization_id": organization_id,
        "idempotency_key": idem,
        "work_id": detail.get("work_id"),
        "work_kind": work_kind,
        "execution_mode": execution_mode,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "last_action_type": action,
        "failure_reason": detail.get("failure_reason"),
        "escalation_reason": detail.get("escalation_reason"),
        "approval_id": detail.get("approval_id"),
        "target_type": detail.get("target_type") or row.target_type,
        "target_id": detail.get("target_id") or row.target_id,
        "actor": row.actor,
    }

    if action == LOG_ORCH_SUCCEEDED:
        return {**base, "recovery_class": RecoveryClass.SUCCEEDED.value, "actionable": False}

    if action == LOG_ORCH_EXHAUSTED:
        return {**base, "recovery_class": RecoveryClass.EXHAUSTED.value, "actionable": True}

    if action == LOG_ORCH_CANCELLED:
        return {**base, "recovery_class": RecoveryClass.CANCELLED.value, "actionable": False}

    if action == LOG_ORCH_BLOCKED or work_kind == WORK_HERMES_DEAL_CREATE:
        return {**base, "recovery_class": RecoveryClass.BLOCKED.value, "actionable": False}

    if action == LOG_ACP3_AMBIGUOUS:
        return {
            **base,
            "recovery_class": RecoveryClass.AMBIGUOUS_EFFECT.value,
            "actionable": True,
            "note": "human_review_required_no_blind_replay",
        }

    # RUNNING before HUMAN_REQUIRED blanket — crash mid-effect must classify
    # ambiguous/replay-safe, not silently become waiting-human.
    if action == LOG_ORCH_RUNNING:
        proved = prove_effect_completed(
            db, work_kind=work_kind, detail=detail, organization_id=organization_id
        )
        if proved is True:
            return {
                **base,
                "recovery_class": RecoveryClass.SUCCEEDED.value,
                "actionable": False,
                "note": "domain_state_proves_completion",
            }
        if work_kind in _AMBIGUOUS_EXTERNAL_KINDS or proved is None:
            return {
                **base,
                "recovery_class": RecoveryClass.AMBIGUOUS_EFFECT.value,
                "actionable": True,
                "note": "running_without_success_no_blind_replay",
            }
        if attempt < max_attempts:
            return {**base, "recovery_class": RecoveryClass.RETRYABLE.value, "actionable": True}
        return {**base, "recovery_class": RecoveryClass.EXHAUSTED.value, "actionable": True}

    if action == LOG_ORCH_WAITING or (
        execution_mode == ExecutionMode.HUMAN_REQUIRED.value
        and action
        in (LOG_ORCH_PROPOSED, LOG_ORCH_RETRYABLE, LOG_ORCH_FAILED, LOG_ORCH_WAITING)
    ):
        approval_id = detail.get("approval_id")
        approval_status = _approval_status(db, approval_id) if approval_id else None
        if approval_status == "approved":
            # Approval exists — autonomous runtime still must NOT auto-execute
            # HUMAN_REQUIRED effects; surface waiting/ready-for-human-executor.
            return {
                **base,
                "recovery_class": RecoveryClass.WAITING_HUMAN.value,
                "actionable": True,
                "note": "approval_present_execution_remains_human_governed",
                "approval_status": approval_status,
            }
        if approval_status == "rejected":
            return {
                **base,
                "recovery_class": RecoveryClass.BLOCKED.value,
                "actionable": False,
                "approval_status": approval_status,
            }
        return {
            **base,
            "recovery_class": RecoveryClass.WAITING_HUMAN.value,
            "actionable": True,
            "approval_status": approval_status or "pending_or_unknown",
        }

    if action in (LOG_ORCH_RETRYABLE, LOG_ORCH_FAILED):
        if execution_mode == ExecutionMode.PROHIBITED.value:
            return {**base, "recovery_class": RecoveryClass.PROHIBITED.value, "actionable": False}
        if execution_mode == ExecutionMode.HUMAN_REQUIRED.value:
            return {**base, "recovery_class": RecoveryClass.WAITING_HUMAN.value, "actionable": True}
        if attempt >= max_attempts:
            return {**base, "recovery_class": RecoveryClass.EXHAUSTED.value, "actionable": True}
        return {**base, "recovery_class": RecoveryClass.RETRYABLE.value, "actionable": True}

    if action == LOG_ORCH_PROPOSED:
        # Eligible but never ran (discovery before execution crash)
        if execution_mode == ExecutionMode.HUMAN_REQUIRED.value:
            return {
                **base,
                "recovery_class": RecoveryClass.WAITING_HUMAN.value,
                "actionable": True,
            }
        if execution_mode == ExecutionMode.PROHIBITED.value:
            return {**base, "recovery_class": RecoveryClass.PROHIBITED.value, "actionable": False}
        return {**base, "recovery_class": RecoveryClass.RETRYABLE.value, "actionable": True}

    return {
        **base,
        "recovery_class": RecoveryClass.AMBIGUOUS_EFFECT.value,
        "actionable": True,
        "note": "unrecognized_orchestration_state",
    }


def prove_effect_completed(
    db: Session,
    *,
    work_kind: str,
    detail: dict[str, Any],
    organization_id: str,
) -> bool | None:
    """True=completed, False=incomplete, None=cannot prove (ambiguous)."""
    target_id = detail.get("target_id")
    if work_kind == WORK_LEAD_SCORE and target_id:
        try:
            cid = uuid_lib.UUID(str(target_id))
            oid = uuid_lib.UUID(str(organization_id))
        except ValueError:
            return None
        contact = db.get(Contact, cid)
        if contact is None:
            return False
        if contact.organization_id != oid:
            return None
        return bool(contact.lead_score and contact.lead_score > 0)

    if work_kind == WORK_FOLLOW_UP_PROPOSE and target_id:
        # Proposal completion ≈ pending/decided approval for this contact
        pending = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.target_id == str(target_id))
            .filter(ApprovalRequest.action_type.in_(["send_outreach_email", "send_reply_email"]))
            .order_by(ApprovalRequest.created_at.desc())
            .first()
        )
        if pending is not None:
            return True
        return False

    if work_kind in _AMBIGUOUS_EXTERNAL_KINDS:
        return None

    # Observational / flag effects: cannot prove without success log
    return None


def _approval_status(db: Session, approval_id: str | None) -> str | None:
    if not approval_id:
        return None
    row = db.get(ApprovalRequest, str(approval_id))
    if row is None:
        return None
    return str(row.status)


def reconcile_organization(
    db: Session,
    *,
    organization_id: str,
    limit: int = DEFAULT_RECONCILE_SCAN_LIMIT,
) -> dict[str, Any]:
    """Bounded reconciliation for one tenant. Observational classification."""
    if not organization_id:
        return {
            "ok": False,
            "blocked": True,
            "blocked_reason": "missing_tenant",
            "items": [],
        }

    latest = latest_orch_events_by_idempotency(
        db, organization_id=organization_id, limit=limit
    )
    items = [
        classify_recovery(db, organization_id=organization_id, row=row)
        for row in latest.values()
    ]

    buckets: dict[str, list[dict[str, Any]]] = {
        "succeeded": [],
        "retryable": [],
        "exhausted": [],
        "waiting_human": [],
        "blocked": [],
        "prohibited": [],
        "ambiguous_effect": [],
        "cancelled": [],
    }
    for item in items:
        rc = item.get("recovery_class")
        if rc == RecoveryClass.SUCCEEDED.value:
            buckets["succeeded"].append(item)
        elif rc == RecoveryClass.RETRYABLE.value:
            buckets["retryable"].append(item)
        elif rc == RecoveryClass.EXHAUSTED.value:
            buckets["exhausted"].append(item)
        elif rc == RecoveryClass.WAITING_HUMAN.value:
            buckets["waiting_human"].append(item)
        elif rc == RecoveryClass.PROHIBITED.value:
            buckets["prohibited"].append(item)
        elif rc == RecoveryClass.AMBIGUOUS_EFFECT.value:
            buckets["ambiguous_effect"].append(item)
        elif rc == RecoveryClass.CANCELLED.value:
            buckets["cancelled"].append(item)
        else:
            buckets["blocked"].append(item)

    return {
        "ok": True,
        "organization_id": organization_id,
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
        "scanned": len(items),
        "buckets": buckets,
        "counts": {k: len(v) for k, v in buckets.items()},
        "requires_founder_action": (
            len(buckets["exhausted"])
            + len(buckets["waiting_human"])
            + len(buckets["ambiguous_effect"])
        ),
    }
