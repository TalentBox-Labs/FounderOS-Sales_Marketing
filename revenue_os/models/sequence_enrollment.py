from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from revenue_os.models.base import Base


class SequenceEnrollment(Base):
    __tablename__ = "sequence_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("outreach_sequences.id"),
        nullable=False,
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id"),
        nullable=False,
    )
    current_step = Column(Integer, default=1)
    status = Column(String(50), default="active")  # active, paused, completed, unsubscribed
    channel = Column(String(50), default="email")  # email, linkedin
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    sequence = relationship("OutreachSequence")
    contact = relationship("Contact")
