"""Durable HUMAN session JWT revocation records (shared across processes)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, String, func

from revenue_os.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionRevocation(Base):
    """JTI denylist for HUMAN identity cookies until the JWT would expire."""

    __tablename__ = "session_revocations"
    __table_args__ = (Index("ix_session_revocations_expires_at", "expires_at"),)

    jti = Column(String(64), primary_key=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
        server_default=func.now(),
    )
