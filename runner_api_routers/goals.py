"""Hermes goals API — give the platform a target and let it work toward it."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from revenue_os.database import SessionLocal
from revenue_os.models.goals import Goal, GoalStep
from revenue_os.services.hermes_planner import (
    SUPPORTED_METRICS,
    create_goal,
    run_goal_check,
)
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hermes/goals", tags=["hermes-goals"])


class GoalCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    metric: str = Field(..., description=f"One of: {', '.join(SUPPORTED_METRICS)}")
    target_value: float = Field(..., gt=0)
    description: str = Field(default="")
    deadline: datetime | None = Field(default=None)
    agent_name: str | None = Field(default=None, description="Owning agent, if any — see /api/v1/agents/registry")


@router.post("")
def create_goal_endpoint(
    req: GoalCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a goal. Hermes snapshots the baseline and generates the plan."""
    try:
        goal = create_goal(
            title=req.title,
            metric=req.metric,
            target_value=req.target_value,
            description=req.description,
            deadline=req.deadline,
            agent_name=req.agent_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"ok": True, "goal": goal}


@router.get("")
def list_goals(
    status: str | None = None,
    agent_name: str | None = None,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List goals with live progress."""
    db = SessionLocal()
    try:
        query = db.query(Goal).order_by(Goal.created_at.desc())
        if status:
            query = query.filter(Goal.status == status)
        if agent_name:
            query = query.filter(Goal.agent_name == agent_name)
        goals = [g.to_dict() for g in query.limit(100).all()]
        return {"ok": True, "count": len(goals), "goals": goals}
    finally:
        db.close()


@router.get("/{goal_id}")
def get_goal(
    goal_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Goal detail including its full plan and step results."""
    db = SessionLocal()
    try:
        goal = db.get(Goal, goal_id)
        if goal is None:
            raise HTTPException(status_code=404, detail=f"Goal not found: {goal_id}")
        steps = (
            db.query(GoalStep)
            .filter(GoalStep.goal_id == goal_id)
            .order_by(GoalStep.order.asc())
            .all()
        )
        return {"ok": True, "goal": goal.to_dict(), "plan": [s.to_dict() for s in steps]}
    finally:
        db.close()


@router.post("/{goal_id}/check")
def check_goal_now(
    goal_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Run one Hermes cycle for this goal immediately."""
    try:
        result = run_goal_check(goal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ok": True, **result}


@router.post("/{goal_id}/pause")
def pause_goal(goal_id: str, _: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    return _set_status(goal_id, "paused")


@router.post("/{goal_id}/resume")
def resume_goal(goal_id: str, _: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    return _set_status(goal_id, "active")


def _set_status(goal_id: str, status: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        goal = db.get(Goal, goal_id)
        if goal is None:
            raise HTTPException(status_code=404, detail=f"Goal not found: {goal_id}")
        if goal.status == "achieved" and status == "active":
            raise HTTPException(status_code=409, detail="Goal already achieved")
        goal.status = status
        db.commit()
        return {"ok": True, "goal_id": goal_id, "status": status}
    finally:
        db.close()
