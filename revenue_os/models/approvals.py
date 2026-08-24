"""Approval queue — human sign-off before risky autonomous actions execute."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Index, String, Text, text

from revenue_os.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalRequest(Base):
    """A proposed action waiting for a human decision.

    Lifecycle: pending -> approved | rejected | superseded
    The proposed action only runs after approval; rejection/supersede archives it.
    """

    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=_uuid)
    organization_id = Column(String(36), nullable=False, index=True)
    approval_family = Column(String(64), nullable=False)
    logical_key = Column(String(255), nullable=False)
    requested_by = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    target_type = Column(String(64), nullable=True)
    target_id = Column(String(64), nullable=True)
    payload = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    decided_by = Column(String(128), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decision_note = Column(Text, nullable=True)
    execution_result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, index=True)

    __table_args__ = (
        Index(
            "uq_approval_requests_pending_identity",
            "organization_id",
            "approval_family",
            "logical_key",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
        Index("ix_approval_requests_org_status", "organization_id", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "approval_family": self.approval_family,
            "logical_key": self.logical_key,
            "requested_by": self.requested_by,
            "action_type": self.action_type,
            "title": self.title,
            "description": self.description,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "payload": self.payload,
            "status": self.status,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decision_note": self.decision_note,
            "execution_result": self.execution_result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
