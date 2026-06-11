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


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    billing_email = Column(String(255))
    billing_address = Column(Text)
    payment_terms = Column(String(100), default="net_30")
    credit_limit = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company = relationship("Company")
    projects = relationship("Project", back_populates="client")
    billing_records = relationship("BillingRecord", back_populates="client")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id = Column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False
    )
    role = Column(String(100))
    department = Column(String(100))
    hourly_rate = Column(Float, default=0.0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )

    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    project_type = Column(String(100))
    budget = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client = relationship("Client", back_populates="projects")
    company = relationship("Company", back_populates="projects")
    milestones = relationship("Milestone", back_populates="project")
    deliverables = relationship("Deliverable", back_populates="project")
    billing_records = relationship("BillingRecord", back_populates="project")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="milestones")


class Deliverable(Base):
    __tablename__ = "deliverables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_url = Column(String(500))
    status = Column(String(50), default="pending")
    due_date = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="deliverables")


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )

    invoice_number = Column(String(100), unique=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    billing_type = Column(String(50), default="project")
    status = Column(String(50), default="pending")
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client = relationship("Client", back_populates="billing_records")
    project = relationship("Project", back_populates="billing_records")
