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


class ContactSource(str, enum.Enum):
    MANUAL = "manual"
    IMPORT = "import"
    WEB_FORM = "web_form"
    LINKEDIN = "linkedin"
    REFERRAL = "referral"
    OUTREACH = "outreach"
    API = "api"
    N8N = "n8n"


class ContactStatus(str, enum.Enum):
    LEAD = "lead"
    PROSPECT = "prospect"
    QUALIFIED = "qualified"
    CUSTOMER = "customer"
    CHURNED = "churned"
    PARTNER = "partner"
    CANDIDATE = "candidate"
    VENDOR = "vendor"


class Industry(str, enum.Enum):
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    REAL_ESTATE = "real_estate"
    STAFFING = "staffing"
    RECRUITMENT = "recruitment"
    AGENCY = "agency"
    OTHER = "other"


class AccountType(str, enum.Enum):
    CUSTOMER = "customer"
    PARTNER = "partner"
    VENDOR = "vendor"
    PROSPECT = "prospect"
    COMPETITOR = "competitor"
    INVESTOR = "investor"
    OTHER = "other"


class AccountTier(str, enum.Enum):
    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMB = "smb"
    STRATEGIC = "strategic"
    OTHER = "other"


class LifecycleStage(str, enum.Enum):
    SUBSCRIBER = "subscriber"
    LEAD = "lead"
    MQL = "mql"
    SQL = "sql"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
    EVANGELIST = "evangelist"
    CHURNED = "churned"


class AccountRating(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class AccountSource(str, enum.Enum):
    MANUAL = "manual"
    IMPORT = "import"
    WEB_FORM = "web_form"
    LINKEDIN = "linkedin"
    REFERRAL = "referral"
    OUTREACH = "outreach"
    API = "api"
    N8N = "n8n"
    CRUNCHBASE = "crunchbase"
    MARKETPLACE = "marketplace"
    PARTNER = "partner"


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255))
    domain = Column(String(255), unique=True, index=True)
    description = Column(Text)
    industry = Column(Enum(Industry), default=Industry.OTHER)
    employee_count = Column(Integer)
    annual_revenue = Column(Float)
    annual_revenue_currency = Column(String(3), default="USD")
    funding_stage = Column(String(100))
    tech_stack = Column(Text)
    hiring_activity = Column(Text)

    # Contact info
    phone = Column(String(50))
    street = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    zip_code = Column(String(20))
    country = Column(String(100))

    # Social & digital presence
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    facebook_url = Column(String(500))
    website_url = Column(String(500))
    crunchbase_url = Column(String(500))
    logo_url = Column(String(500))

    # Classification
    account_type = Column(Enum(AccountType), default=AccountType.OTHER)
    account_tier = Column(Enum(AccountTier), default=AccountTier.OTHER)
    lifecycle_stage = Column(Enum(LifecycleStage), default=LifecycleStage.LEAD)
    rating = Column(Enum(AccountRating), default=AccountRating.WARM)
    account_source = Column(Enum(AccountSource), default=AccountSource.MANUAL)

    # Business identifiers
    sic_code = Column(String(20))
    naics_code = Column(String(20))
    ticker_symbol = Column(String(20))
    founded_year = Column(Integer)
    number_of_locations = Column(Integer)

    # Parent relationship
    parent_company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )

    # Ownership & relationship
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    primary_contact_id = Column(UUID(as_uuid=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)

    tags = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contacts = relationship("Contact", back_populates="company")
    deals = relationship("Deal", back_populates="company")
    projects = relationship("Project", back_populates="company")
    parent_company = relationship(
        "Company", remote_side="Company.id", backref="subsidiaries"
    )


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    designation = Column(String(255))
    email = Column(String(255), index=True)
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    source = Column(Enum(ContactSource), default=ContactSource.MANUAL)
    status = Column(Enum(ContactStatus), default=ContactStatus.LEAD)
    lead_score = Column(Integer, default=0)
    tags = Column(Text)
    notes = Column(Text)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="contacts")
    deals = relationship("Deal", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
