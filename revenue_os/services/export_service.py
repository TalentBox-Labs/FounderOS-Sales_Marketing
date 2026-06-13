from __future__ import annotations

import csv
import io
from typing import Any

from sqlalchemy.orm import Session


def export_contacts_csv(db: Session) -> str:
    from revenue_os.models.contact import Contact

    contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "first_name", "last_name", "email", "phone", "designation",
        "source", "status", "lead_score", "tags", "linkedin_url", "twitter_url",
        "company_id", "owner_id", "last_contacted_at", "created_at",
    ])
    for c in contacts:
        writer.writerow([
            c.id, c.first_name, c.last_name, c.email or "", c.phone or "",
            c.designation or "", c.source.value if c.source else "",
            c.status.value if c.status else "", c.lead_score,
            c.tags or "", c.linkedin_url or "", c.twitter_url or "",
            c.company_id or "", c.owner_id or "",
            c.last_contacted_at or "", c.created_at,
        ])
    return output.getvalue()


def export_deals_csv(db: Session) -> str:
    from revenue_os.models.deal import Deal

    deals = db.query(Deal).order_by(Deal.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "name", "stage", "value", "currency", "probability",
        "company_id", "contact_id", "pipeline_id",
        "expected_close_date", "closed_at", "description", "tags",
        "owner_id", "created_at",
    ])
    for d in deals:
        writer.writerow([
            d.id, d.name, d.stage.value if d.stage else "", d.value,
            d.currency, d.probability, d.company_id or "",
            d.contact_id or "", d.pipeline_id,
            d.expected_close_date or "", d.closed_at or "",
            d.description or "", d.tags or "", d.owner_id or "",
            d.created_at,
        ])
    return output.getvalue()


def export_companies_csv(db: Session) -> str:
    from revenue_os.models.contact import Company

    companies = db.query(Company).order_by(Company.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "name", "legal_name", "domain", "industry", "employee_count",
        "annual_revenue", "phone", "street", "city", "state", "zip_code", "country",
        "account_type", "account_tier", "lifecycle_stage", "rating",
        "sic_code", "naics_code", "ticker_symbol", "founded_year",
        "linkedin_url", "website_url", "tags", "created_at",
    ])
    for c in companies:
        writer.writerow([
            c.id, c.name, c.legal_name or "", c.domain or "",
            c.industry.value if c.industry else "", c.employee_count or "",
            c.annual_revenue or "", c.phone or "", c.street or "",
            c.city or "", c.state or "", c.zip_code or "", c.country or "",
            c.account_type.value if c.account_type else "",
            c.account_tier.value if c.account_tier else "",
            c.lifecycle_stage.value if c.lifecycle_stage else "",
            c.rating.value if c.rating else "",
            c.sic_code or "", c.naics_code or "", c.ticker_symbol or "",
            c.founded_year or "", c.linkedin_url or "", c.website_url or "",
            c.tags or "", c.created_at,
        ])
    return output.getvalue()
