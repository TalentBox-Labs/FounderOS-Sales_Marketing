"""Marketing Agent crew — persistence for outputs that accumulate over time
rather than being thrown away after one request/response (research findings,
personas that get refreshed, campaigns, partnership pipeline)."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from revenue_os.models.base import Base


class MarketingInsight(Base):
    """One finding from the Market Research / Community Engagement / Brand
    Monitoring agents — a growing log, not a single ephemeral report."""

    __tablename__ = "marketing_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(64), nullable=False)
    category = Column(String(50), nullable=False)  # market_research | community | brand_mention | partnership
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False, default="")
    source_url = Column(String(1000))
    sentiment = Column(String(20))  # positive | neutral | negative — brand monitoring only
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class CustomerPersona(Base):
    """A buyer persona, refreshed in place (upsert by name) as new CRM/
    market data comes in — 'continuously updated', not regenerated blind."""

    __tablename__ = "customer_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    summary = Column(Text, nullable=False, default="")
    pain_points = Column(Text, default="")
    motivations = Column(Text, default="")
    objections = Column(Text, default="")
    messaging = Column(Text, default="")
    based_on = Column(Text, default="")  # what CRM/research data fed this version
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarketingCampaign(Base):
    """Cross-channel campaign coordination — the Campaign Manager agent's
    output. Channels/KPIs are stored as plain text lists (comma-separated)
    to avoid a JSON column dependency the rest of this codebase doesn't use."""

    __tablename__ = "marketing_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    goal = Column(Text, default="")
    channels = Column(Text, default="")  # comma-separated: seo,email,linkedin,whatsapp,...
    status = Column(String(20), nullable=False, default="planning")  # planning|active|completed
    kpis = Column(Text, default="")
    owner_agents = Column(Text, default="")  # comma-separated agent names assigned
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PartnershipLead(Base):
    """A potential partner, influencer, podcast, newsletter, or community —
    the Partnership & Influencer agent's discovery pipeline."""

    __tablename__ = "partnership_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    lead_type = Column(String(50), nullable=False, default="other")  # influencer|podcast|newsletter|community|affiliate|other
    url = Column(String(1000))
    status = Column(String(20), nullable=False, default="discovered")  # discovered|contacted|active|declined
    notes = Column(Text, default="")
    source = Column(String(100), default="")  # how it was found (reddit, manual, ...)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
