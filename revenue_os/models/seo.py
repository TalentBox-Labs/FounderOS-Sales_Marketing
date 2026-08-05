from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from revenue_os.models.base import Base


class SEOKeyword(Base):
    """A keyword/phrase tracked for search + AI-answer-engine visibility."""

    __tablename__ = "seo_keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(String(255), nullable=False)
    target_url = Column(String(500))
    geo = Column(String(100))  # e.g. "United States", "Bengaluru, IN", blank = global
    target_rank = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    checks = relationship(
        "SEORankCheck", back_populates="keyword", order_by="SEORankCheck.checked_at",
        cascade="all, delete-orphan",
    )


class SEORankCheck(Base):
    """One point-in-time observation of a keyword's rank / AI visibility."""

    __tablename__ = "seo_rank_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("seo_keywords.id"), nullable=False)
    rank = Column(Integer)  # null = not found in top results
    ai_visible = Column(Boolean, default=False)  # surfaced in an AI answer engine (GEO)
    source = Column(String(50), default="manual")
    notes = Column(Text)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

    keyword = relationship("SEOKeyword", back_populates="checks")
