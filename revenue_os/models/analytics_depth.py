"""Manual marketing-spend log — the real cost input CAC needs.

Nothing in this platform tracks ad spend automatically (no ad-platform
integration exists), so CAC is only ever computed from spend a founder
actually logs here. Without an entry for a channel, CAC for that channel
is reported as unavailable rather than fabricated.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, String, Text

from revenue_os.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MarketingSpendRecord(Base):
    __tablename__ = "marketing_spend"

    id = Column(String(36), primary_key=True, default=_uuid)
    channel = Column(String(64), nullable=False, index=True)  # matches Contact.source values
    period = Column(String(7), nullable=False, index=True)  # "YYYY-MM"
    amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "period": self.period,
            "amount": self.amount,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
