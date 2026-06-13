from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.integrations.n8n import new_lead_webhook
from revenue_os.models.contact import (
    AccountRating,
    AccountSource,
    AccountTier,
    AccountType,
    Company,
    Contact,
    ContactSource,
    ContactStatus,
    Industry,
    LifecycleStage,
)
from revenue_os.services.export_service import export_contacts_csv
from revenue_os.services.scoring_service import score_contact
from revenue_os.services.search_service import delete_index, index_contact, search
from revenue_os.services.dedup_service import find_duplicate_contacts, merge_contacts

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    company_id: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    source: ContactSource = ContactSource.MANUAL
    status: ContactStatus = ContactStatus.LEAD
    tags: Optional[str] = None
    notes: Optional[str] = None
    # Company fields
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_legal_name: Optional[str] = None
    company_industry: Optional[str] = None
    company_website: Optional[str] = None
    company_description: Optional[str] = None
    company_phone: Optional[str] = None
    company_street: Optional[str] = None
    company_city: Optional[str] = None
    company_state: Optional[str] = None
    company_zip_code: Optional[str] = None
    company_country: Optional[str] = None
    company_employee_count: Optional[int] = None
    company_annual_revenue: Optional[float] = None
    company_annual_revenue_currency: Optional[str] = None
    company_funding_stage: Optional[str] = None
    company_tech_stack: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_facebook_url: Optional[str] = None
    company_twitter_url: Optional[str] = None
    company_crunchbase_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_account_type: Optional[str] = None
    company_account_tier: Optional[str] = None
    company_lifecycle_stage: Optional[str] = None
    company_rating: Optional[str] = None
    company_account_source: Optional[str] = None
    company_sic_code: Optional[str] = None
    company_naics_code: Optional[str] = None
    company_ticker_symbol: Optional[str] = None
    company_founded_year: Optional[int] = None
    company_number_of_locations: Optional[int] = None
    company_owner_id: Optional[str] = None
    company_tags: Optional[str] = None
    company_notes: Optional[str] = None


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_id: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    status: Optional[ContactStatus] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    company_id: Optional[uuid.UUID] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    source: ContactSource
    status: ContactStatus
    lead_score: int
    tags: Optional[str] = None
    notes: Optional[str] = None
    # Company fields
    company_name: Optional[str] = None
    company_legal_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_industry: Optional[str] = None
    company_website: Optional[str] = None
    company_description: Optional[str] = None
    company_phone: Optional[str] = None
    company_street: Optional[str] = None
    company_city: Optional[str] = None
    company_state: Optional[str] = None
    company_zip_code: Optional[str] = None
    company_country: Optional[str] = None
    company_employee_count: Optional[int] = None
    company_annual_revenue: Optional[float] = None
    company_annual_revenue_currency: Optional[str] = None
    company_funding_stage: Optional[str] = None
    company_tech_stack: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    company_facebook_url: Optional[str] = None
    company_twitter_url: Optional[str] = None
    company_crunchbase_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_account_type: Optional[str] = None
    company_account_tier: Optional[str] = None
    company_lifecycle_stage: Optional[str] = None
    company_rating: Optional[str] = None
    company_account_source: Optional[str] = None
    company_sic_code: Optional[str] = None
    company_naics_code: Optional[str] = None
    company_ticker_symbol: Optional[str] = None
    company_founded_year: Optional[int] = None
    company_number_of_locations: Optional[int] = None
    company_owner_id: Optional[str] = None
    company_tags: Optional[str] = None
    company_notes: Optional[str] = None
    company_created_at: Optional[datetime] = None
    company_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_company(cls, contact):
        company = getattr(contact, "company", None)
        return cls(
            id=contact.id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            full_name=contact.full_name,
            company_id=contact.company_id,
            designation=contact.designation,
            email=contact.email,
            phone=contact.phone,
            linkedin_url=contact.linkedin_url,
            twitter_url=contact.twitter_url,
            source=contact.source,
            status=contact.status,
            lead_score=contact.lead_score,
            tags=contact.tags,
            notes=contact.notes,
            company_name=company.name if company else None,
            company_legal_name=company.legal_name if company else None,
            company_domain=company.domain if company else None,
            company_industry=company.industry.value if company and company.industry else None,
            company_website=company.website_url if company else None,
            company_description=company.description if company else None,
            company_phone=company.phone if company else None,
            company_street=company.street if company else None,
            company_city=company.city if company else None,
            company_state=company.state if company else None,
            company_zip_code=company.zip_code if company else None,
            company_country=company.country if company else None,
            company_employee_count=company.employee_count if company else None,
            company_annual_revenue=company.annual_revenue if company else None,
            company_annual_revenue_currency=company.annual_revenue_currency if company else None,
            company_funding_stage=company.funding_stage if company else None,
            company_tech_stack=company.tech_stack if company else None,
            company_linkedin_url=company.linkedin_url if company else None,
            company_facebook_url=company.facebook_url if company else None,
            company_twitter_url=company.twitter_url if company else None,
            company_crunchbase_url=company.crunchbase_url if company else None,
            company_logo_url=company.logo_url if company else None,
            company_account_type=company.account_type.value if company and company.account_type else None,
            company_account_tier=company.account_tier.value if company and company.account_tier else None,
            company_lifecycle_stage=company.lifecycle_stage.value if company and company.lifecycle_stage else None,
            company_rating=company.rating.value if company and company.rating else None,
            company_account_source=company.account_source.value if company and company.account_source else None,
            company_sic_code=company.sic_code if company else None,
            company_naics_code=company.naics_code if company else None,
            company_ticker_symbol=company.ticker_symbol if company else None,
            company_founded_year=company.founded_year if company else None,
            company_number_of_locations=company.number_of_locations if company else None,
            company_owner_id=str(company.owner_id) if company and company.owner_id else None,
            company_tags=company.tags if company else None,
            company_notes=company.notes if company else None,
            company_created_at=company.created_at if company else None,
            company_updated_at=company.updated_at if company else None,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )


@router.get("", response_model=list[ContactResponse])
def list_contacts(
    status: Optional[ContactStatus] = Query(None),
    source: Optional[ContactSource] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import joinedload
    query = db.query(Contact).options(joinedload(Contact.company))
    if status:
        query = query.filter(Contact.status == status)
    if source:
        query = query.filter(Contact.source == source)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Contact.first_name.ilike(pattern)
            | Contact.last_name.ilike(pattern)
            | Contact.email.ilike(pattern)
            | Contact.designation.ilike(pattern)
        )
    contacts = query.offset(skip).limit(limit).all()
    return [ContactResponse.from_orm_with_company(c) for c in contacts]


@router.get("/{contact_id}/timeline")
def contact_timeline(
    contact_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    from revenue_os.models.activity import Activity
    from revenue_os.models.activity import EmailActivity

    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    activities = (
        db.query(Activity)
        .filter(Activity.contact_id == contact_id)
        .order_by(Activity.performed_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for a in activities:
        item = {
            "id": str(a.id),
            "type": a.activity_type.value,
            "subject": a.subject,
            "body": a.body[:500] if a.body else None,
            "direction": a.direction,
            "status": a.status,
            "performed_at": a.performed_at.isoformat() if a.performed_at else None,
        }
        if a.activity_type.value in ("email", "email_open", "email_click", "email_reply"):
            ea = (
                db.query(EmailActivity)
                .filter(EmailActivity.activity_id == a.id)
                .first()
            )
            if ea:
                item["email"] = {
                    "message_id": ea.message_id,
                    "from": ea.from_address,
                    "to": ea.to_addresses,
                    "opened_at": ea.opened_at.isoformat() if ea.opened_at else None,
                    "clicked_at": ea.clicked_at.isoformat() if ea.clicked_at else None,
                }
        results.append(item)
    return results


@router.post("/bulk-upload")
def bulk_upload_contacts(file: UploadFile = File(...), db: Session = Depends(get_db)):
    import io
    import csv

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Use .csv, .xlsx, or .xls",
        )

    content = file.file.read()
    rows = []

    if ext == "csv":
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            rows.append(row)
    else:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        headers = [str(c.value).strip().lower().replace(" ", "_") for c in next(ws.iter_rows(min_row=1, max_row=1))]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if any(v is not None for v in row):
                rows.append(dict(zip(headers, [str(v) if v is not None else "" for v in row])))

    column_map = {
        "first_name": "first_name", "firstname": "first_name", "first name": "first_name",
        "last_name": "last_name", "lastname": "last_name", "last name": "last_name",
        "email": "email", "e-mail": "email",
        "designation": "designation", "title": "designation", "job_title": "designation", "job title": "designation", "role": "designation",
        "phone": "phone", "telephone": "phone", "mobile": "phone",
        "linkedin_url": "linkedin_url", "linkedin": "linkedin_url", "linkedin url": "linkedin_url", "linkedin profile": "linkedin_url",
        "company": "company_name", "company_name": "company_name", "organization": "company_name",
        "tags": "tags",
        "notes": "notes", "note": "notes",
        "source": "source",
        "status": "status",
        "lead_score": "lead_score", "score": "lead_score",
    }

    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(rows):
        try:
            mapped = {}
            for k, v in row.items():
                target = column_map.get(k.strip().lower(), None)
                if target:
                    mapped[target] = v.strip() if v else ""

            first = mapped.get("first_name", "")
            last = mapped.get("last_name", "")
            if not first and not last:
                skipped += 1
                continue
            if not first:
                first = last
                last = ""

            company_name = mapped.get("company_name", "")
            company_id = None
            if company_name:
                existing = db.query(Company).filter(Company.name.ilike(f"%{company_name}%")).first()
                if existing:
                    company_id = existing.id
                else:
                    company = Company(name=company_name)
                    db.add(company)
                    db.flush()
                    company_id = company.id

            email = mapped.get("email")

            source_str = mapped.get("source", "manual").lower()
            try:
                source = ContactSource(source_str)
            except ValueError:
                source = ContactSource.MANUAL

            status_str = mapped.get("status", "lead").lower()
            try:
                status = ContactStatus(status_str)
            except ValueError:
                status = ContactStatus.LEAD

            score_str = mapped.get("lead_score", "0")
            try:
                score = int(score_str)
            except (ValueError, TypeError):
                score = 0

            contact = Contact(
                first_name=first,
                last_name=last,
                company_id=company_id,
                designation=mapped.get("designation"),
                email=email,
                phone=mapped.get("phone"),
                linkedin_url=mapped.get("linkedin_url"),
                source=source,
                status=status,
                lead_score=score,
                tags=mapped.get("tags"),
                notes=mapped.get("notes"),
            )
            db.add(contact)
            db.flush()

            score_contact(db, contact.id)
            index_contact(
                contact_id=contact.id,
                first_name=contact.first_name,
                last_name=contact.last_name,
                email=contact.email,
                designation=contact.designation,
                tags=contact.tags,
                notes=contact.notes,
            )
            new_lead_webhook(
                contact_id=str(contact.id),
                contact_name=contact.full_name,
                email=email or "",
            )
            created += 1
        except Exception as e:
            errors.append({"row": i + 2, "error": str(e)})

    db.commit()
    return {
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "total_rows": len(rows),
    }


@router.get("/search")
def search_contacts(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return search(query=q, limit=limit, db=db, type_filter="contact")


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: str, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    contact = db.query(Contact).options(joinedload(Contact.company)).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse.from_orm_with_company(contact)


@router.post("", response_model=ContactResponse, status_code=201)
def create_contact(body: ContactCreate, db: Session = Depends(get_db)):
    company_id = None
    if body.company_id:
        company_id = uuid.UUID(body.company_id)
    elif body.company_name:
        existing = db.query(Company).filter(
            Company.name.ilike(body.company_name)
        ).first()
        if existing:
            company_id = existing.id
        else:
            industry_val = None
            if body.company_industry:
                try:
                    industry_val = Industry(body.company_industry.lower())
                except ValueError:
                    industry_val = Industry.OTHER

            account_type_val = None
            if body.company_account_type:
                try:
                    account_type_val = AccountType(body.company_account_type.lower())
                except ValueError:
                    pass

            account_tier_val = None
            if body.company_account_tier:
                try:
                    account_tier_val = AccountTier(body.company_account_tier.lower())
                except ValueError:
                    pass

            lifecycle_val = None
            if body.company_lifecycle_stage:
                try:
                    lifecycle_val = LifecycleStage(body.company_lifecycle_stage.lower())
                except ValueError:
                    pass

            rating_val = None
            if body.company_rating:
                try:
                    rating_val = AccountRating(body.company_rating.lower())
                except ValueError:
                    pass

            account_source_val = None
            if body.company_account_source:
                try:
                    account_source_val = AccountSource(body.company_account_source.lower())
                except ValueError:
                    pass

            company = Company(
                name=body.company_name,
                legal_name=body.company_legal_name,
                domain=body.company_domain,
                industry=industry_val,
                website_url=body.company_website,
                description=body.company_description,
                phone=body.company_phone,
                street=body.company_street,
                city=body.company_city,
                state=body.company_state,
                zip_code=body.company_zip_code,
                country=body.company_country,
                employee_count=body.company_employee_count,
                annual_revenue=body.company_annual_revenue,
                annual_revenue_currency=body.company_annual_revenue_currency,
                funding_stage=body.company_funding_stage,
                tech_stack=body.company_tech_stack,
                linkedin_url=body.company_linkedin_url,
                facebook_url=body.company_facebook_url,
                twitter_url=body.company_twitter_url,
                crunchbase_url=body.company_crunchbase_url,
                logo_url=body.company_logo_url,
                account_type=account_type_val,
                account_tier=account_tier_val,
                lifecycle_stage=lifecycle_val,
                rating=rating_val,
                account_source=account_source_val,
                sic_code=body.company_sic_code,
                naics_code=body.company_naics_code,
                ticker_symbol=body.company_ticker_symbol,
                founded_year=body.company_founded_year,
                number_of_locations=body.company_number_of_locations,
                owner_id=uuid.UUID(body.company_owner_id) if body.company_owner_id else None,
                tags=body.company_tags,
                notes=body.company_notes,
            )
            db.add(company)
            db.flush()
            company_id = company.id

    contact = Contact(
        first_name=body.first_name,
        last_name=body.last_name,
        company_id=company_id,
        designation=body.designation,
        email=body.email,
        phone=body.phone,
        linkedin_url=body.linkedin_url,
        twitter_url=body.twitter_url,
        source=body.source,
        status=body.status,
        tags=body.tags,
        notes=body.notes,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)

    score_contact(db, contact.id)
    index_contact(
        contact_id=contact.id,
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        designation=contact.designation,
        tags=contact.tags,
        notes=contact.notes,
    )
    new_lead_webhook(
        contact_id=str(contact.id),
        contact_name=contact.full_name,
        email=contact.email or "",
    )

    return ContactResponse.from_orm_with_company(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: str,
    body: ContactUpdate,
    db: Session = Depends(get_db),
):
    from sqlalchemy.orm import joinedload
    contact = db.query(Contact).options(joinedload(Contact.company)).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "company_id" and value is not None:
            setattr(contact, key, uuid.UUID(value))
        elif value is not None:
            setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return ContactResponse.from_orm_with_company(contact)


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: str, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    delete_index(contact.id)
    db.delete(contact)
    db.commit()


@router.get("/export/csv")
def export_contacts(db: Session = Depends(get_db)):
    from fastapi.responses import Response
    csv_data = export_contacts_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


class MergeBody(BaseModel):
    primary_id: str
    duplicate_id: str


@router.post("/merge")
def merge_contacts_endpoint(body: MergeBody, db: Session = Depends(get_db)):
    result = merge_contacts(
        db, uuid.UUID(body.primary_id), uuid.UUID(body.duplicate_id)
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/dedup")
def find_duplicates(
    email: Optional[str] = Query(None),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    threshold: float = Query(0.8, ge=0.1, le=1.0),
    db: Session = Depends(get_db),
):
    return find_duplicate_contacts(
        db,
        email=email,
        first_name=first_name,
        last_name=last_name,
        company_id=uuid.UUID(company_id) if company_id else None,
        threshold=threshold,
    )


@router.get("/export/csv")
def export_contacts_csv_endpoint(db: Session = Depends(get_db)):
    from fastapi.responses import Response
    csv_data = export_contacts_csv(db)
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=contacts.csv"})
