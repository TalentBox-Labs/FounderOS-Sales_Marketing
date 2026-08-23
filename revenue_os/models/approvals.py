"""Approval queue — human sign-off before risky autonomous actions execute."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String, Text

from revenue_os.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalRequest(Base):
    """A proposed action waiting for a human decision.

    Lifecycle: pending -> approved (then executed) | rejected
    The proposed action only runs after approval; rejection archives it.
    """

    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=_uuid)
    requested_by = Column(String(64), nullable=False)  # hermes, workflow, api, ...
    action_type = Column(String(64), nullable=False)   # key into the approval executor registry
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    target_type = Column(String(64), nullable=True)
    target_id = Column(String(64), nullable=True)
    payload = Column(JSON, nullable=True)              # everything the executor needs
    status = Column(String(32), nullable=False, default="pending", index=True)
    # pending | approved | rejected
    decided_by = Column(String(128), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decision_note = Column(Text, nullable=True)
    execution_result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
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
