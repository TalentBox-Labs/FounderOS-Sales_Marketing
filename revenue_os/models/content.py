from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
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


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    kb_type = Column(String(50), default="playbook")
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    articles = relationship(
        "KnowledgeBaseArticle", back_populates="knowledge_base"
    )


class KnowledgeBaseArticle(Base):
    __tablename__ = "kb_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id"),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    content = Column(Text)
    tags = Column(Text)
    embedding_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    knowledge_base = relationship(
        "KnowledgeBase", back_populates="articles"
    )


class ContentLibrary(Base):
    __tablename__ = "content_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), default="blog")
    body = Column(Text)
    excerpt = Column(Text)
    tags = Column(Text)
    status = Column(String(50), default="draft")
    canonical_url = Column(String(500))
    author_id = Column(UUID(as_uuid=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_library_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content_library.id"),
        nullable=True,
    )
    platform = Column(String(50), nullable=False)
    body = Column(Text)
    media_urls = Column(Text)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="draft")
    engagement_data = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Article(Base):
    """Bridge to existing CMS OS content (tracker.csv + 05_Final.md)."""

    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String(50), unique=True, index=True)
    title = Column(String(255))
    status = Column(String(50), default="draft")
    week_id = Column(String(10))
    canonical_url = Column(String(500))
    primary_keyword = Column(String(255))
    search_intent = Column(String(100))
    funnel_stage = Column(String(100))
    cta_type = Column(String(100))
    word_count = Column(Integer)
    seo_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
