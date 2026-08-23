"""ACP-2/ACP-3 founder oversight read model — compose AgentActionLog events.

Not a new SoT. Dedupes by work_id / idempotency_key for summary counts.
ACP-3 adds reconciliation buckets + pause/kill/resume gate visibility.
"""

from __future__ import annotations

import uuid as uuid_lib
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.automation_state import AgentActionLog
from revenue_os.services.acp2_orchestration import (
    LOG_ORCH_BLOCKED,
    LOG_ORCH_EXHAUSTED,
    LOG_ORCH_FAILED,
    LOG_ORCH_RETRYABLE,
    LOG_ORCH_SUCCEEDED,
    LOG_ORCH_WAITING,
)
from revenue_os.services.acp3_durable_runtime import runtime_gates
from revenue_os.services.acp3_reconciliation import reconcile_organization
from revenue_os.services.acp3_runtime_contract import LOG_ACP3_AMBIGUOUS
from revenue_os.services.acp4_production_runtime import (
    LOG_CLAIM_UNAVAILABLE,
    LOG_FENCE_REJECTED,
    LOG_STALE_EXECUTOR_REJECTED,
    coordination_backend_info,
)

_ORCH_TYPES = frozenset(
    {
        LOG_ORCH_SUCCEEDED,
        LOG_ORCH_BLOCKED,
        LOG_ORCH_WAITING,
        LOG_ORCH_FAILED,
        LOG_ORCH_EXHAUSTED,
        LOG_ORCH_RETRYABLE,
        LOG_ACP3_AMBIGUOUS,
        LOG_CLAIM_UNAVAILABLE,
        LOG_FENCE_REJECTED,
        LOG_STALE_EXECUTOR_REJECTED,
    }
)


def compose_orchestration_summary(
    db: Session, *, organization_id: str, limit: int = 200
) -> dict[str, Any]:
    """Org-scoped orchestration + durable recovery summary for founder oversight."""
    try:
        org_uuid = uuid_lib.UUID(str(organization_id))
    except ValueError:
        return _empty_summary(organization_id, error="invalid_organization_id")

    rows = (
        db.query(AgentActionLog)
        .filter(AgentActionLog.organization_id == org_uuid)
        .filter(AgentActionLog.action_type.in_(list(_ORCH_TYPES)))
        .order_by(AgentActionLog.created_at.desc())
        .limit(limit)
        .all()
    )

    latest: dict[str, AgentActionLog] = {}
    for row in rows:
        detail = row.detail or {}
        key = str(detail.get("work_id") or detail.get("idempotency_key") or row.id)
        if key not in latest:
            latest[key] = row

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for key, row in latest.items():
        detail = row.detail or {}
        item = {
            "work_id": detail.get("work_id") or key,
            "work_kind": detail.get("work_kind"),
            "state": detail.get("state") or row.status,
            "actor": row.actor,
            "assigned_agent": detail.get("assigned_agent"),
            "requested_effect": detail.get("requested_effect"),
            "execution_mode": detail.get("execution_mode"),
            "failure_reason": detail.get("failure_reason"),
            "escalation_reason": detail.get("escalation_reason"),
            "action_type": row.action_type,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        if row.action_type == LOG_ORCH_SUCCEEDED:
            buckets["succeeded_recently"].append(item)
        elif row.action_type == LOG_ORCH_WAITING:
            buckets["awaiting_human"].append(item)
        elif row.action_type == LOG_ORCH_BLOCKED:
            buckets["blocked"].append(item)
        elif row.action_type == LOG_ORCH_EXHAUSTED:
            buckets["exhausted"].append(item)
        elif row.action_type == LOG_ACP3_AMBIGUOUS:
            buckets["ambiguous_effect"].append(item)
        elif row.action_type == LOG_CLAIM_UNAVAILABLE:
            buckets["claim_rejected"].append(item)
        elif row.action_type in (LOG_FENCE_REJECTED, LOG_STALE_EXECUTOR_REJECTED):
            buckets["fence_rejected"].append(item)
        elif row.action_type in (LOG_ORCH_FAILED, LOG_ORCH_RETRYABLE):
            buckets["failed"].append(item)

    autonomous = [
        i
        for items in buckets.values()
        for i in items
        if i.get("execution_mode") == "AUTONOMOUS"
    ]
    human_required = [
        i
        for items in buckets.values()
        for i in items
        if i.get("execution_mode") == "HUMAN_REQUIRED"
    ]

    gates = runtime_gates()
    reconcile = reconcile_organization(db, organization_id=organization_id, limit=limit)
    retryable = reconcile.get("buckets", {}).get("retryable", [])[:20]
    ambiguous = (
        buckets.get("ambiguous_effect", [])[:20]
        or reconcile.get("buckets", {}).get("ambiguous_effect", [])[:20]
    )
    claim_rejected = buckets.get("claim_rejected", [])[:20]
    fence_rejected = buckets.get("fence_rejected", [])[:20]

    return {
        "organization_id": organization_id,
        "active": buckets.get("failed", [])[:10],
        "succeeded_recently": buckets.get("succeeded_recently", [])[:20],
        "blocked": buckets.get("blocked", [])[:20],
        "awaiting_human": buckets.get("awaiting_human", [])[:20],
        "failed": buckets.get("failed", [])[:20],
        "exhausted": buckets.get("exhausted", [])[:20],
        "retryable": retryable,
        "ambiguous_effect": ambiguous,
        "claim_rejected": claim_rejected,
        "fence_rejected": fence_rejected,
        "autonomous_count": len(autonomous),
        "human_required_count": len(human_required),
        "counts": {
            "succeeded": len(buckets.get("succeeded_recently", [])),
            "blocked": len(buckets.get("blocked", [])),
            "awaiting_human": len(buckets.get("awaiting_human", [])),
            "failed": len(buckets.get("failed", [])),
            "exhausted": len(buckets.get("exhausted", [])),
            "retryable": len(retryable),
            "ambiguous_effect": len(ambiguous),
            "claim_rejected": len(claim_rejected),
            "fence_rejected": len(fence_rejected),
            "requires_founder_action": reconcile.get("requires_founder_action", 0),
        },
        "source": "AgentActionLog.acp2_*+acp3_*+acp4_*",
        "pause": {
            "heartbeat_paused": gates["heartbeat_paused"],
            "acp2_execution_killed": gates["acp2_execution_killed"],
            "acp3_resume_enabled": gates["acp3_resume_enabled"],
            "new_mutating_work_allowed": gates["new_mutating_work_allowed"],
            "recovery_execution_allowed": gates["recovery_execution_allowed"],
        },
        "runtime_gates": gates,
        "reconcile_counts": reconcile.get("counts", {}),
        "acp4_coordination": coordination_backend_info(db),
    }


def _empty_summary(organization_id: str, *, error: str | None = None) -> dict[str, Any]:
    gates = runtime_gates()
    out = {
        "organization_id": organization_id,
        "active": [],
        "succeeded_recently": [],
        "blocked": [],
        "awaiting_human": [],
        "failed": [],
        "exhausted": [],
        "retryable": [],
        "ambiguous_effect": [],
        "claim_rejected": [],
        "fence_rejected": [],
        "autonomous_count": 0,
        "human_required_count": 0,
        "counts": {
            "succeeded": 0,
            "blocked": 0,
            "awaiting_human": 0,
            "failed": 0,
            "exhausted": 0,
            "retryable": 0,
            "ambiguous_effect": 0,
            "claim_rejected": 0,
            "fence_rejected": 0,
            "requires_founder_action": 0,
        },
        "source": "AgentActionLog.acp2_*+acp3_*+acp4_*",
        "pause": {
            "heartbeat_paused": gates["heartbeat_paused"],
            "acp2_execution_killed": gates["acp2_execution_killed"],
            "acp3_resume_enabled": gates["acp3_resume_enabled"],
            "new_mutating_work_allowed": gates["new_mutating_work_allowed"],
            "recovery_execution_allowed": gates["recovery_execution_allowed"],
        },
        "runtime_gates": gates,
        "reconcile_counts": {},
        "acp4_coordination": {
            "dialect": "unknown",
            "mechanism": "unavailable",
            "distributed_safety_claimed": False,
        },
    }
    if error:
        out["error"] = error
    return out
