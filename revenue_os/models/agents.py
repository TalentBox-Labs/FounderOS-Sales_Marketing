"""Persisted state for the agent registry (revenue_os.agents.orchestration.AgentCoordinator).

AgentCoordinator runs in-memory for speed; these are the write-through +
startup-hydration tables so the registry and inter-agent messages survive a
restart instead of resetting to empty every deploy.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from revenue_os.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AgentRegistryRecord(Base):
    """A registered agent — a platform subsystem or crew that acts autonomously."""

    __tablename__ = "agent_registry"

    name = Column(String(64), primary_key=True)
    agent_type = Column(String(32), nullable=False)
    description = Column(Text, nullable=False, default="")
    capabilities = Column(JSON, nullable=False, default=list)
    status = Column(String(32), nullable=False, default="active")
    registered_at = Column(DateTime(timezone=True), default=_now)
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.agent_type,
            "description": self.description,
            "capabilities": self.capabilities or [],
            "status": self.status,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
        }


class AgentMessageRecord(Base):
    """An inter-agent message — how one agent hands work or context to another."""

    __tablename__ = "agent_messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    from_agent = Column(String(64), nullable=False, index=True)
    to_agent = Column(String(64), nullable=False, index=True)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    is_read = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=_now, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from": self.from_agent,
            "to": self.to_agent,
            "message": self.message,
            "data": self.data or {},
            "read": bool(self.is_read),
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }
