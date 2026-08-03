"""Goals and plans for the Hermes autonomous planner."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from revenue_os.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Goal(Base):
    """A business goal Hermes plans toward and checks on every heartbeat."""

    __tablename__ = "hermes_goals"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    metric = Column(String(64), nullable=False)  # qualified_leads | pipeline_value | deals_closed
    target_value = Column(Float, nullable=False)
    baseline_value = Column(Float, nullable=False, default=0.0)
    current_value = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="active", index=True)
    # active | paused | achieved | archived
    deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    checks = Column(Integer, nullable=False, default=0)

    def progress(self) -> float:
        """Fraction of target achieved since baseline, clamped to [0, 1]."""
        span = self.target_value - self.baseline_value
        if span <= 0:
            return 1.0 if self.current_value >= self.target_value else 0.0
        return max(0.0, min(1.0, (self.current_value - self.baseline_value) / span))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "metric": self.metric,
            "target_value": self.target_value,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "progress": round(self.progress(), 3),
            "status": self.status,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "checks": self.checks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GoalStep(Base):
    """One executable step in a goal's plan."""

    __tablename__ = "hermes_goal_steps"

    id = Column(String(36), primary_key=True, default=_uuid)
    goal_id = Column(String(36), nullable=False, index=True)
    order = Column(Integer, nullable=False, default=0)
    title = Column(String(255), nullable=False)
    action_type = Column(String(64), nullable=False)  # key into the action registry
    params = Column(JSON, nullable=True)
    repeat = Column(Integer, nullable=False, default=0)  # 1 = re-run on every check
    status = Column(String(32), nullable=False, default="pending", index=True)
    # pending | completed | failed | skipped
    result = Column(JSON, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    runs = Column(Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order": self.order,
            "title": self.title,
            "action_type": self.action_type,
            "params": self.params,
            "repeat": bool(self.repeat),
            "status": self.status,
            "result": self.result,
            "runs": self.runs,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }
