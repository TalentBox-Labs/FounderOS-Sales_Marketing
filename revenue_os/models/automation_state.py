"""Persisted state for automation: audit trail, heartbeat runs, analytics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from revenue_os.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AgentActionLog(Base):
    """Audit trail of every automated action taken by the platform."""

    __tablename__ = "agent_action_log"

    id = Column(String(36), primary_key=True, default=_uuid)
    actor = Column(String(64), nullable=False, index=True)  # heartbeat, hermes, workflow, api
    action_type = Column(String(64), nullable=False, index=True)
    target_type = Column(String(64), nullable=True)  # contact, deal, metric, ...
    target_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="completed")  # completed, failed, skipped
    detail = Column(JSON, nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_now, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "actor": self.actor,
            "action_type": self.action_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "status": self.status,
            "detail": self.detail,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class HeartbeatRun(Base):
    """Record of each scheduled heartbeat job execution."""

    __tablename__ = "heartbeat_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    job_name = Column(String(64), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=_now)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), nullable=False, default="running")  # running, completed, failed
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_name": self.job_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class AnalyticsMetricRecord(Base):
    """Persisted analytics metric definition."""

    __tablename__ = "analytics_metrics"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    metric_type = Column(String(32), nullable=False)
    calculation = Column(Text, nullable=False, default="")
    unit = Column(String(32), nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    target_value = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)


class AnalyticsDataPointRecord(Base):
    """Persisted time-series data point for a metric."""

    __tablename__ = "analytics_data_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_id = Column(String(64), nullable=False, index=True)
    value = Column(Float, nullable=False)
    dimension = Column(String(128), nullable=True)
    meta = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_now, index=True)


class WorkflowDefinitionRecord(Base):
    """Persisted definition for a WorkflowEngine workflow (event → conditions → actions).

    WorkflowEngine itself runs in-memory for speed; this is the write-through
    + startup-hydration store so workflows survive a restart instead of
    vanishing the moment the process recycles.
    """

    __tablename__ = "workflow_definitions"

    id = Column(String(64), primary_key=True)  # matches the in-memory wf_xxxxxxxx id
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    event_type = Column(String(64), nullable=True)
    conditions = Column(JSON, nullable=False, default=list)
    actions = Column(JSON, nullable=False, default=list)
    is_enabled = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)
