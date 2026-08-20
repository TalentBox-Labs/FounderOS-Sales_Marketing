"""ACP-2 founder oversight read model — compose AgentActionLog orchestration events.

Not a new SoT. Dedupes by work_id / idempotency_key for summary counts.
Suitable for Founder Command attachment without a new dashboard (COS-6 deferred).
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

_ORCH_TYPES = frozenset(
    {
        LOG_ORCH_SUCCEEDED,
        LOG_ORCH_BLOCKED,
        LOG_ORCH_WAITING,
        LOG_ORCH_FAILED,
        LOG_ORCH_EXHAUSTED,
        LOG_ORCH_RETRYABLE,
    }
)


def compose_orchestration_summary(
    db: Session, *, organization_id: str, limit: int = 200
) -> dict[str, Any]:
    """Org-scoped orchestration summary for founder oversight."""
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

    # Latest event per work identity (prefer work_id, else idempotency_key)
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

    return {
        "organization_id": organization_id,
        "active": buckets.get("failed", [])[:10],  # retryable surfaced under failed
        "succeeded_recently": buckets.get("succeeded_recently", [])[:20],
        "blocked": buckets.get("blocked", [])[:20],
        "awaiting_human": buckets.get("awaiting_human", [])[:20],
        "failed": buckets.get("failed", [])[:20],
        "exhausted": buckets.get("exhausted", [])[:20],
        "autonomous_count": len(autonomous),
        "human_required_count": len(human_required),
        "counts": {
            "succeeded": len(buckets.get("succeeded_recently", [])),
            "blocked": len(buckets.get("blocked", [])),
            "awaiting_human": len(buckets.get("awaiting_human", [])),
            "failed": len(buckets.get("failed", [])),
            "exhausted": len(buckets.get("exhausted", [])),
        },
        "source": "AgentActionLog.acp2_*",
        "pause": {
            "heartbeat_paused": _env_paused("HEARTBEAT_ENABLED"),
            "acp2_execution_killed": _env_paused("ACP2_AUTONOMOUS_EXECUTION_ENABLED"),
        },
    }


def _env_paused(name: str) -> bool:
    import os

    default = "1"
    return os.environ.get(name, default) in ("0", "false", "False")


def _empty_summary(organization_id: str, *, error: str | None = None) -> dict[str, Any]:
    out = {
        "organization_id": organization_id,
        "active": [],
        "succeeded_recently": [],
        "blocked": [],
        "awaiting_human": [],
        "failed": [],
        "exhausted": [],
        "autonomous_count": 0,
        "human_required_count": 0,
        "counts": {
            "succeeded": 0,
            "blocked": 0,
            "awaiting_human": 0,
            "failed": 0,
            "exhausted": 0,
        },
        "source": "AgentActionLog.acp2_*",
        "pause": {
            "heartbeat_paused": _env_paused("HEARTBEAT_ENABLED"),
            "acp2_execution_killed": _env_paused("ACP2_AUTONOMOUS_EXECUTION_ENABLED"),
        },
    }
    if error:
        out["error"] = error
    return out
