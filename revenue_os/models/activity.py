from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from revenue_os.models.base import Base


class ActivityType(str, enum.Enum):
    EMAIL = "email"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    EMAIL_REPLY = "email_reply"
    CALL = "call"
    MEETING = "meeting"
    LINKEDIN_MESSAGE = "linkedin_message"
    LINKEDIN_CONNECT = "linkedin_connect"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    TASK = "task"
    NOTE = "note"


class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True
    )
    deal_id = Column(
        UUID(as_uuid=True), ForeignKey("deals.id"), nullable=True
    )

    activity_type = Column(Enum(ActivityType), nullable=False)
    subject = Column(String(500))
    body = Column(Text)
    direction = Column(String(10), default="outbound")
    status = Column(String(50), default="pending")
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Task tracking — only meaningful when activity_type == TASK, but kept on
    # the shared table so the timeline query stays a single, ordered feed.
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    contact = relationship("Contact", back_populates="activities")
    deal = relationship("Deal")


class EmailActivity(Base):
    __tablename__ = "email_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(
        UUID(as_uuid=True), ForeignKey("activities.id"), nullable=False
    )
    message_id = Column(String(255))
    from_address = Column(String(255))
    to_addresses = Column(Text)
    cc_addresses = Column(Text)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    bounce_type = Column(String(50), nullable=True)


class MeetingActivity(Base):
    __tablename__ = "meeting_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(
        UUID(as_uuid=True), ForeignKey("activities.id"), nullable=False
    )
    meeting_url = Column(String(500))
    duration_minutes = Column(Integer)
    recording_url = Column(String(500))
    notes = Column(Text)


class OutreachSequence(Base):
    __tablename__ = "outreach_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), default="email")
    steps_count = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SequenceStep(Base):
    __tablename__ = "sequence_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("outreach_sequences.id"),
        nullable=False,
    )
    step_order = Column(Integer, nullable=False)
    delay_days = Column(Integer, default=1)
    subject = Column(String(500))
    template = Column(Text)
    action_type = Column(String(50), default="send_email")
    conditions = Column(Text)
