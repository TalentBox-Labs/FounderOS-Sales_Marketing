"""Hermes CRO (Chief Revenue Officer) orchestration and insights."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from revenue_os.database import SessionLocal
from revenue_os.models.contact import ContactStatus
from revenue_os.services.deal_automation_service import (
    calculate_deal_velocity,
    create_deal_from_contact,
    forecast_close_date,
    get_deals_at_risk,
    get_pipeline_health,
)
from revenue_os.services.lead_scoring_service import (
    get_contacts_by_score,
    get_score_distribution,
    score_contact,
    score_contacts_batch,
)
from revenue_os.models.contact import Contact
from src.sdr_crew import SDRCrew

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hermes", tags=["hermes"])


class ScoreContactsRequest(BaseModel):
    """Request to score contacts."""

    contact_ids: list[str] = Field(..., min_items=1, max_items=1000)
    company_context: dict[str, Any] = Field(default_factory=dict)


class QualifyContactsRequest(BaseModel):
    """Request to create deals from qualified contacts."""

    contact_ids: list[str] = Field(..., min_items=1, max_items=500)
    default_value: float = Field(default=5000.0, ge=100.0)


class RevenueMetricsResponse(BaseModel):
    """Revenue metrics response."""

    ok: bool = True
    total_pipeline_value: float
    weighted_forecast: float
    total_deals: int
    by_stage: dict[str, Any]
    velocity: dict[str, Any]
    forecast_accuracy: float


@router.post("/score-contacts", tags=["hermes"])
def score_contacts_endpoint(
    req: ScoreContactsRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Score multiple contacts without mutating Contact.status."""
    logger.info(
        "Scoring contacts",
        extra={"contact_count": len(req.contact_ids)},
    )

    db = SessionLocal()
    try:
        results = score_contacts_batch(db, req.contact_ids, req.company_context)

        return {
            "ok": True,
            "total_scored": results["scored"],
            "suggested_qualified": results["suggested_qualified"],
            "newly_qualified": 0,
            "scores": results["scores"],
        }
    finally:
        db.close()


@router.get("/lead-scores", tags=["hermes"])
def get_lead_scores(
    min_score: int = 0,
    max_score: int = 100,
    status: str | None = None,
    limit: int = 50,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get contacts by score range."""
    logger.info(
        "Fetching leads by score",
        extra={"min_score": min_score, "max_score": max_score, "status": status},
    )

    db = SessionLocal()
    try:
        statuses = None
        if status:
            try:
                statuses = [ContactStatus(status)]
            except Exception:
                pass

        contacts = get_contacts_by_score(db, min_score, max_score, statuses, limit)

        return {
            "ok": True,
            "count": len(contacts),
            "contacts": [
                {
                    "id": str(c.id),
                    "name": c.full_name,
                    "email": c.email,
                    "lead_score": c.lead_score,
                    "status": c.status.value,
                    "source": c.source.value,
                    "company": c.company.name if c.company else None,
                }
                for c in contacts
            ],
        }
    finally:
        db.close()


@router.get("/score-distribution", tags=["hermes"])
def score_distribution_endpoint(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get distribution of lead scores across all contacts."""
    logger.info("Fetching score distribution")

    db = SessionLocal()
    try:
        distribution = get_score_distribution(db)

        return {
            "ok": True,
            "distribution": distribution,
        }
    finally:
        db.close()


@router.post("/qualify-contacts", tags=["hermes"])
def qualify_contacts_endpoint(
    req: QualifyContactsRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create deals from qualified contacts."""
    logger.info(
        "Qualifying contacts and creating deals",
        extra={"contact_count": len(req.contact_ids)},
    )

    db = SessionLocal()
    try:
        contacts = db.query(Contact).filter(Contact.id.in_(req.contact_ids)).all()

        created_deals = []
        skipped = []

        for contact in contacts:
            if contact.status != ContactStatus.QUALIFIED:
                skipped.append(
                    {
                        "contact_id": str(contact.id),
                        "reason": f"not qualified (status: {contact.status.value})",
                    }
                )
                continue

            deal = create_deal_from_contact(db, contact, req.default_value)
            if deal:
                created_deals.append(
                    {
                        "deal_id": str(deal.id),
                        "contact_id": str(contact.id),
                        "value": deal.value,
                        "stage": deal.stage.value,
                    }
                )

        return {
            "ok": True,
            "created": len(created_deals),
            "skipped": len(skipped),
            "deals": created_deals,
            "skipped_details": skipped[:10],  # Show first 10
        }
    finally:
        db.close()


@router.get("/pipeline-health", tags=["hermes"])
def pipeline_health_endpoint(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get overall pipeline health and forecast."""
    logger.info("Fetching pipeline health")

    db = SessionLocal()
    try:
        health = get_pipeline_health(db)
        velocity = calculate_deal_velocity(db)

        # Forecast accuracy (how well we predicted close dates historically)
        # For now, simple: if velocity exists, we have data
        forecast_accuracy = 0.75 if velocity.get("closed_deals", 0) > 0 else 0.5

        return {
            "ok": True,
            "total_pipeline_value": health["total_pipeline_value"],
            "weighted_forecast": health["weighted_forecast"],
            "total_deals": health["total_deals"],
            "by_stage": health["by_stage"],
            "velocity": velocity,
            "forecast_accuracy": forecast_accuracy,
        }
    finally:
        db.close()


@router.get("/pipeline-forecast", tags=["hermes"])
def pipeline_forecast_endpoint(
    days: int = 90,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get pipeline forecast for next N days."""
    logger.info("Forecasting pipeline", extra={"days": days})

    db = SessionLocal()
    try:
        health = get_pipeline_health(db)
        velocity = calculate_deal_velocity(db, days)

        # Simple forecast: weighted forecast + growth factor
        base_forecast = health["weighted_forecast"]
        new_deals_estimate = health["total_deals"] * 0.3  # Expect 30% new deals

        return {
            "ok": True,
            "forecast_days": days,
            "current_forecast": base_forecast,
            "new_deals_estimate": new_deals_estimate,
            "total_potential": base_forecast + (new_deals_estimate * 3500),  # Avg deal size
            "by_stage": health["by_stage"],
            "historical_velocity": velocity,
        }
    finally:
        db.close()


@router.get("/deals-at-risk", tags=["hermes"])
def deals_at_risk_endpoint(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get deals at risk of being lost."""
    logger.info("Fetching at-risk deals")

    db = SessionLocal()
    try:
        at_risk = get_deals_at_risk(db)

        total_at_risk_value = sum(d["value"] for d in at_risk)

        return {
            "ok": True,
            "count": len(at_risk),
            "total_value_at_risk": total_at_risk_value,
            "deals": at_risk,
            "recommendation": "Immediately action top 3 deals"
            if len(at_risk) > 0
            else "Pipeline is healthy",
        }
    finally:
        db.close()


@router.get("/revenue-summary", tags=["hermes"])
def revenue_summary_endpoint(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Comprehensive revenue summary for Hermes dashboard."""
    logger.info("Generating revenue summary")

    db = SessionLocal()
    try:
        health = get_pipeline_health(db)
        velocity = calculate_deal_velocity(db)
        at_risk = get_deals_at_risk(db)
        score_dist = get_score_distribution(db)

        # Calculate lead funnel metrics
        total_leads = len(
            db.query(Contact).all()
        )  # Simplified - would query with proper filters
        qualified = len(
            db.query(Contact).filter(Contact.status == ContactStatus.QUALIFIED).all()
        )
        in_deals = health["total_deals"]

        funnel = {
            "total_leads": total_leads,
            "qualified_leads": qualified,
            "deals_created": in_deals,
            "qualification_rate": (qualified / total_leads * 100) if total_leads > 0 else 0,
            "deal_creation_rate": (in_deals / qualified * 100) if qualified > 0 else 0,
        }

        return {
            "ok": True,
            "pipeline": {
                "total_value": health["total_pipeline_value"],
                "forecast": health["weighted_forecast"],
                "deals": health["total_deals"],
            },
            "velocity": {
                "avg_cycle_days": velocity.get("avg_cycle_time_days", 0),
                "win_rate": velocity.get("win_rate", 0),
                "closed_this_period": velocity.get("closed_deals", 0),
            },
            "funnel": funnel,
            "lead_quality": score_dist,
            "at_risk_deals": {
                "count": len(at_risk),
                "total_value": sum(d["value"] for d in at_risk),
            },
        }
    finally:
        db.close()


class SDROutreachRequest(BaseModel):
    """Request to trigger SDR outreach."""

    contact_id: str
    use_llm: bool = False  # If true, use LLM for personalized messages


@router.post("/sdr-outreach", tags=["hermes"])
def sdr_outreach_endpoint(
    req: SDROutreachRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Trigger SDR crew to execute outreach for a qualified lead."""
    logger.info("Triggering SDR outreach", extra={"contact_id": req.contact_id})

    db = SessionLocal()
    try:
        contact = db.query(Contact).filter(Contact.id == req.contact_id).first()
        if not contact:
            return {"ok": False, "error": "Contact not found"}

        if contact.status != ContactStatus.QUALIFIED:
            return {
                "ok": False,
                "error": f"Contact not qualified (status: {contact.status.value})",
            }

        if req.use_llm:
            # Use LLM-powered SDR crew
            sdr = SDRCrew()
            result = sdr.run_sdr_outreach(
                contact_name=contact.full_name,
                company_name=contact.company.name if contact.company else "Unknown",
                role=contact.designation or "Prospect",
                email=contact.email or "",
                linkedin_url=contact.linkedin_url,
            )
            return result
        else:
            # Simple template-based outreach
            return {
                "ok": True,
                "contact_id": req.contact_id,
                "contact_name": contact.full_name,
                "company": contact.company.name if contact.company else "Unknown",
                "status": "ready_for_outreach",
                "recommended_channel": "linkedin" if contact.linkedin_url else "email",
                "message_template": f"Hi {contact.first_name}, I came across your profile at {contact.company.name if contact.company else 'your company'} and would love to connect.",
            }
    finally:
        db.close()
