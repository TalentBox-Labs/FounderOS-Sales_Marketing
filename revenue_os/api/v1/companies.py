from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.models.contact import Company, Industry

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    description: Optional[str] = None
    industry: Industry = Industry.OTHER
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    funding_stage: Optional[str] = None
    tech_stack: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    tags: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[Industry] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    funding_stage: Optional[str] = None
    tech_stack: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    tags: Optional[str] = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    domain: Optional[str] = None
    description: Optional[str] = None
    industry: Industry
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    funding_stage: Optional[str] = None
    tech_stack: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    tags: Optional[str] = None
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
    company = Company(
        name=body.name,
        domain=body.domain,
        description=body.description,
        industry=body.industry,
        employee_count=body.employee_count,
        annual_revenue=body.annual_revenue,
        funding_stage=body.funding_stage,
        tech_stack=body.tech_stack,
        linkedin_url=body.linkedin_url,
        website_url=body.website_url,
        tags=body.tags,
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
