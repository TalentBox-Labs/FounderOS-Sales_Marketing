from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from revenue_os.models.base import Base


class PipelineType(str, enum.Enum):
    SALES = "sales"
    RECRUITMENT = "recruitment"
    PARTNERSHIP = "partnership"
    INVESTMENT = "investment"


class DealStage(str, enum.Enum):
    # Sales stages
    DISCOVERY = "discovery"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

    # Recruitment stages
    SOURCING = "sourcing"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    PLACED = "placed"
    REJECTED = "rejected"


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    pipeline_type = Column(Enum(PipelineType), default=PipelineType.SALES)
    stages = Column(Text)
    is_default = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    deals = relationship("Deal", back_populates="pipeline")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(
        UUID(as_uuid=True), ForeignKey("pipelines.id"), nullable=False
    )
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    contact_id = Column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True
    )

    name = Column(String(255), nullable=False)
    stage = Column(Enum(DealStage), default=DealStage.DISCOVERY)
    probability = Column(Integer, default=10)
    value = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    expected_close_date = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    pipeline = relationship("Pipeline", back_populates="deals")
    company = relationship("Company", back_populates="deals")
    contact = relationship("Contact", back_populates="deals")
