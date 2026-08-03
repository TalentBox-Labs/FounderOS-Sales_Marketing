"""Heartbeat and audit-trail API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from revenue_os.database import SessionLocal
from revenue_os.models.automation_state import HeartbeatRun
from revenue_os.scheduler import scheduler, heartbeat_enabled
from revenue_os.services.activity_log import get_recent_actions
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/heartbeat", tags=["heartbeat"])


@router.get("/status")
def heartbeat_status(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    """Current scheduler state: registered jobs, last runs, intervals."""
    status = scheduler.status()
    status["enabled"] = heartbeat_enabled()
    return {"ok": True, **status}


@router.get("/runs")
def heartbeat_runs(
    job_name: str | None = Query(None, description="Filter by job name"),
    limit: int = Query(20, ge=1, le=200),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Recent persisted job runs, newest first."""
    db = SessionLocal()
    try:
        query = db.query(HeartbeatRun).order_by(HeartbeatRun.started_at.desc())
        if job_name:
            query = query.filter(HeartbeatRun.job_name == job_name)
        runs = [r.to_dict() for r in query.limit(limit).all()]
        return {"ok": True, "count": len(runs), "runs": runs}
    finally:
        db.close()


@router.post("/run/{job_name}")
def heartbeat_run_now(
    job_name: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Trigger one heartbeat job immediately (useful for testing)."""
    if job_name not in scheduler.jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown job '{job_name}'. Available: {list(scheduler.jobs)}",
        )
    result = scheduler.run_job_now(job_name)
    return {"ok": result.get("status") == "completed", **result}


@router.get("/activity")
def heartbeat_activity(
    actor: str | None = Query(None, description="Filter by actor (heartbeat, hermes, ...)"),
    action_type: str | None = Query(None, description="Filter by action type"),
    limit: int = Query(50, ge=1, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Audit trail of autonomous actions, newest first."""
    actions = get_recent_actions(limit=limit, actor=actor, action_type=action_type)
    return {"ok": True, "count": len(actions), "actions": actions}
