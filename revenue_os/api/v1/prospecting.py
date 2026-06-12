from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from revenue_os.database import get_db
from revenue_os.models.contact import ContactStatus
from revenue_os.services.lead_prospecting_service import (
    build_prospecting_plan,
    provider_status,
    prospecting_limits,
)

router = APIRouter(prefix="/prospecting", tags=["prospecting"])


class ProspectingPlanRequest(BaseModel):
    target_count: int = Field(default=50, ge=1, le=5000)
    min_score: int = Field(default=25, ge=0, le=100)
    statuses: list[ContactStatus] = Field(
        default_factory=lambda: [ContactStatus.LEAD, ContactStatus.PROSPECT]
    )
    allow_scraper: bool = True
    allow_mcp: bool = True


@router.get("/providers")
def get_prospecting_providers() -> dict:
    return {
        "ok": True,
        "providers": provider_status(),
        "thresholds": prospecting_limits(),
    }


@router.post("/plan")
def plan_prospecting(body: ProspectingPlanRequest, db: Session = Depends(get_db)) -> dict:
    plan = build_prospecting_plan(
        db,
        target_count=body.target_count,
        min_score=body.min_score,
        statuses=body.statuses,
        allow_scraper=body.allow_scraper,
        allow_mcp=body.allow_mcp,
    )
    return {
        "ok": True,
        "plan": plan,
    }
