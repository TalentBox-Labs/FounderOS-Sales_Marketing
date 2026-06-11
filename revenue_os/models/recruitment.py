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


class CandidateStage(str, enum.Enum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    SHORTLISTED = "shortlisted"
    OFFER = "offer"
    PLACED = "placed"
    REJECTED = "rejected"


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    description = Column(Text)
    requirements = Column(Text)
    skills = Column(Text)
    location = Column(String(255))
    salary_range = Column(String(100))
    employment_type = Column(String(50), default="full_time")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    candidates = relationship("Candidate", back_populates="job_description")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_description_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id"),
        nullable=True,
    )
    contact_id = Column(
        UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True
    )

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    current_company = Column(String(255))
    current_designation = Column(String(255))
    stage = Column(Enum(CandidateStage), default=CandidateStage.APPLIED)
    ai_rank = Column(Integer)
    resume_text = Column(Text)
    resume_url = Column(String(500))
    skills = Column(Text)
    experience_years = Column(Float)
    notes = Column(Text)
    source = Column(String(50), default="manual")
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job_description = relationship(
        "JobDescription", back_populates="candidates"
    )
    interviews = relationship("Interview", back_populates="candidate")
    placements = relationship("Placement", back_populates="candidate")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    interview_type = Column(String(50), default="technical")
    scheduled_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer, default=60)
    interviewer = Column(String(255))
    feedback = Column(Text)
    rating = Column(Integer)
    status = Column(String(50), default="scheduled")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("Candidate", back_populates="interviews")


class Placement(Base):
    __tablename__ = "placements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(
        UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False
    )
    client_company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    fee = Column(Float, default=0.0)
    salary = Column(Float)
    start_date = Column(DateTime(timezone=True))
    status = Column(String(50), default="active")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    candidate = relationship("Candidate", back_populates="placements")
