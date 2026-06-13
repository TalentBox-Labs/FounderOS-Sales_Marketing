from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.services.export_service import export_companies_csv
from revenue_os.services.dedup_service import find_duplicate_companies
from revenue_os.models.contact import (
    AccountRating,
    AccountSource,
    AccountTier,
    AccountType,
    Company,
    Industry,
    LifecycleStage,
)

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyCreate(BaseModel):
    name: str
    legal_name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    industry: Industry = Industry.OTHER
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    annual_revenue_currency: Optional[str] = None
    funding_stage: Optional[str] = None
    tech_stack: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    account_type: AccountType = AccountType.OTHER
    account_tier: AccountTier = AccountTier.OTHER
    lifecycle_stage: LifecycleStage = LifecycleStage.LEAD
    rating: AccountRating = AccountRating.WARM
    account_source: AccountSource = AccountSource.MANUAL
    sic_code: Optional[str] = None
    naics_code: Optional[str] = None
    ticker_symbol: Optional[str] = None
    founded_year: Optional[int] = None
    number_of_locations: Optional[int] = None
    parent_company_id: Optional[str] = None
    owner_id: Optional[str] = None
    primary_contact_id: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[Industry] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    annual_revenue_currency: Optional[str] = None
    funding_stage: Optional[str] = None
    tech_stack: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    account_type: Optional[AccountType] = None
    account_tier: Optional[AccountTier] = None
    lifecycle_stage: Optional[LifecycleStage] = None
    rating: Optional[AccountRating] = None
    account_source: Optional[AccountSource] = None
    sic_code: Optional[str] = None
    naics_code: Optional[str] = None
    ticker_symbol: Optional[str] = None
    founded_year: Optional[int] = None
    number_of_locations: Optional[int] = None
    parent_company_id: Optional[str] = None
    owner_id: Optional[str] = None
    primary_contact_id: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    legal_name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    industry: Industry
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    annual_revenue_currency: Optional[str] = None
    funding_stage: Optional[str] = None
    tech_stack: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    account_type: AccountType
    account_tier: AccountTier
    lifecycle_stage: LifecycleStage
    rating: AccountRating
    account_source: AccountSource
    sic_code: Optional[str] = None
    naics_code: Optional[str] = None
    ticker_symbol: Optional[str] = None
    founded_year: Optional[int] = None
    number_of_locations: Optional[int] = None
    parent_company_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    primary_contact_id: Optional[uuid.UUID] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=list[CompanyResponse])
def list_companies(
    industry: Optional[Industry] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Company)
    if industry:
        query = query.filter(Company.industry == industry)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Company.name.ilike(pattern) | Company.domain.ilike(pattern)
        )
    return query.offset(skip).limit(limit).all()


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("", response_model=CompanyResponse, status_code=201)
def create_company(body: CompanyCreate, db: Session = Depends(get_db)):
    parent_id = uuid.UUID(body.parent_company_id) if body.parent_company_id else None
    owner = uuid.UUID(body.owner_id) if body.owner_id else None
    primary = uuid.UUID(body.primary_contact_id) if body.primary_contact_id else None
    company = Company(
        name=body.name,
        legal_name=body.legal_name,
        domain=body.domain,
        description=body.description,
        industry=body.industry,
        employee_count=body.employee_count,
        annual_revenue=body.annual_revenue,
        annual_revenue_currency=body.annual_revenue_currency,
        funding_stage=body.funding_stage,
        tech_stack=body.tech_stack,
        phone=body.phone,
        street=body.street,
        city=body.city,
        state=body.state,
        zip_code=body.zip_code,
        country=body.country,
        linkedin_url=body.linkedin_url,
        facebook_url=body.facebook_url,
        twitter_url=body.twitter_url,
        crunchbase_url=body.crunchbase_url,
        website_url=body.website_url,
        logo_url=body.logo_url,
        account_type=body.account_type,
        account_tier=body.account_tier,
        lifecycle_stage=body.lifecycle_stage,
        rating=body.rating,
        account_source=body.account_source,
        sic_code=body.sic_code,
        naics_code=body.naics_code,
        ticker_symbol=body.ticker_symbol,
        founded_year=body.founded_year,
        number_of_locations=body.number_of_locations,
        parent_company_id=parent_id,
        owner_id=owner,
        primary_contact_id=primary,
        tags=body.tags,
        notes=body.notes,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: str,
    body: CompanyUpdate,
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()


@router.get("/export/csv")
def export_companies(db: Session = Depends(get_db)):
    from fastapi.responses import Response
    csv_data = export_companies_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=companies.csv"},
    )


@router.get("/dedup")
def find_dup_companies(
    domain: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return find_duplicate_companies(db, domain=domain, name=name)
