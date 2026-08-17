"""Best-effort audit logging for automated actions.

Every autonomous action (heartbeat job, workflow action, Hermes decision)
should be recorded here so there is a durable trail of what the platform
did on its own. Failures to log never break the calling code path.
"""

from __future__ import annotations

import logging
from typing import Any

from revenue_os.database import SessionLocal
from revenue_os.models.automation_state import AgentActionLog

logger = logging.getLogger(__name__)


def log_agent_action(
    actor: str,
    action_type: str,
    target_type: str | None = None,
    target_id: str | None = None,
    status: str = "completed",
    detail: dict[str, Any] | None = None,
    organization_id: str | None = None,
) -> None:
    """Persist one audit-trail entry. Never raises."""
    try:
        import uuid as uuid_lib

        org_uuid = None
        if organization_id:
            try:
                org_uuid = uuid_lib.UUID(str(organization_id))
            except ValueError:
                org_uuid = None

        db = SessionLocal()
        try:
            db.add(AgentActionLog(
                actor=actor,
                action_type=action_type,
                target_type=target_type,
                target_id=target_id,
                status=status,
                detail=detail,
                organization_id=org_uuid,
            ))
            db.commit()
        finally:
            db.close()
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Failed to write agent action log: {e}")


def get_recent_actions(
    limit: int = 50,
    actor: str | None = None,
    action_type: str | None = None,
) -> list[dict[str, Any]]:
    """Read recent audit-trail entries, newest first."""
    db = SessionLocal()
    try:
        query = db.query(AgentActionLog).order_by(AgentActionLog.created_at.desc())
        if actor:
            query = query.filter(AgentActionLog.actor == actor)
        if action_type:
            query = query.filter(AgentActionLog.action_type == action_type)
        return [row.to_dict() for row in query.limit(min(limit, 500)).all()]
    finally:
        db.close()
