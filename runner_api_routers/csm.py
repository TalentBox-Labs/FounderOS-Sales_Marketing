"""Customer Success Manager (CSM) endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from revenue_os.database import SessionLocal
from revenue_os.customer_success.account_health import HealthCalculator
from revenue_os.customer_success.recommendations import RecommendationEngine

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/csm", tags=["csm"])


class AccountReviewRequest(BaseModel):
    """Request to review a customer account."""

    account_id: str
    account_name: str = ""


@router.get("/accounts/health", tags=["csm"])
def get_all_account_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get health assessment for all customer accounts."""
    logger.info("Fetching all account health assessments")

    db = SessionLocal()
    try:
        accounts = HealthCalculator.assess_all_accounts(db)

        # Categorize by health
        healthy = [a for a in accounts if a.health_status == "healthy"]
        at_risk = [a for a in accounts if a.health_status == "at_risk"]
        critical = [a for a in accounts if a.health_status == "critical"]

        return {
            "ok": True,
            "total_accounts": len(accounts),
            "healthy": len(healthy),
            "at_risk": len(at_risk),
            "critical": len(critical),
            "accounts": [a.to_dict() for a in accounts],
        }
    finally:
        db.close()


@router.get("/accounts/{account_id}/health", tags=["csm"])
def get_account_health(
    account_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get health assessment for a specific account."""
    logger.info("Fetching account health", extra={"account_id": account_id})

    db = SessionLocal()
    try:
        health = HealthCalculator.assess_account_health(db, account_id)

        if not health:
            return {"ok": False, "error": "Account not found"}

        return {"ok": True, "account_health": health.to_dict()}
    finally:
        db.close()


@router.get("/accounts/at-risk", tags=["csm"])
def get_at_risk_accounts(
    threshold: float = 60.0,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get accounts at risk of churn."""
    logger.info("Fetching at-risk accounts", extra={"threshold": threshold})

    db = SessionLocal()
    try:
        at_risk = HealthCalculator.get_at_risk_accounts(db, threshold)

        return {
            "ok": True,
            "count": len(at_risk),
            "threshold": threshold,
            "accounts": [a.to_dict() for a in at_risk],
        }
    finally:
        db.close()


@router.get("/accounts/expansion-opportunities", tags=["csm"])
def get_expansion_opportunities(
    threshold: float = 60.0,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get accounts with expansion potential."""
    logger.info("Fetching expansion opportunities", extra={"threshold": threshold})

    db = SessionLocal()
    try:
        opportunities = HealthCalculator.get_expansion_opportunities(db, threshold)

        total_value = sum(a.expansion_score for a in opportunities)

        return {
            "ok": True,
            "count": len(opportunities),
            "threshold": threshold,
            "accounts": [a.to_dict() for a in opportunities],
        }
    finally:
        db.close()


@router.get("/accounts/{account_id}/recommendations", tags=["csm"])
def get_account_recommendations(
    account_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get CSM recommendations for a specific account."""
    logger.info("Fetching CSM recommendations", extra={"account_id": account_id})

    db = SessionLocal()
    try:
        recommendations = RecommendationEngine.generate_recommendations(db, account_id)

        # Categorize by type
        retention = [r for r in recommendations if r.action_type == "retention"]
        expansion = [r for r in recommendations if r.action_type == "expansion"]
        engagement = [r for r in recommendations if r.action_type == "engagement"]

        return {
            "ok": True,
            "account_id": account_id,
            "total_recommendations": len(recommendations),
            "by_type": {
                "retention": len(retention),
                "expansion": len(expansion),
                "engagement": len(engagement),
            },
            "recommendations": [r.to_dict() for r in recommendations],
        }
    finally:
        db.close()


@router.get("/recommendations/all", tags=["csm"])
def get_all_recommendations(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get all CSM recommendations across all accounts."""
    logger.info("Fetching all CSM recommendations")

    db = SessionLocal()
    try:
        all_recs = RecommendationEngine.get_all_recommendations(db)

        # Flatten for display
        flat_recs = []
        for priority, recs in all_recs.items():
            for rec in recs:
                flat_recs.append(rec.to_dict())

        return {
            "ok": True,
            "total": len(flat_recs),
            "by_priority": {
                "critical": len(all_recs["critical"]),
                "high": len(all_recs["high"]),
                "medium": len(all_recs["medium"]),
                "low": len(all_recs["low"]),
            },
            "recommendations": flat_recs,
        }
    finally:
        db.close()


@router.get("/actions-summary", tags=["csm"])
def get_actions_summary(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get summary of all CSM actions needed."""
    logger.info("Fetching CSM actions summary")

    db = SessionLocal()
    try:
        summary = RecommendationEngine.get_actions_summary(db)

        return {
            "ok": True,
            "summary": summary,
        }
    finally:
        db.close()


@router.post("/accounts/{account_id}/review", tags=["csm"])
def review_account(
    account_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Trigger detailed CSM review for an account."""
    logger.info("Triggering account review", extra={"account_id": account_id})

    db = SessionLocal()
    try:
        from revenue_os.models.contact import Company

        company = db.query(Company).filter(Company.id == account_id).first()

        if not company:
            return {"ok": False, "error": "Account not found"}

        # Get account health
        health = HealthCalculator.assess_account_health(db, account_id)

        # Determine adoption stage based on health signals
        if health.health_score >= 80:
            adoption_stage = "Mature"
        elif health.health_score >= 60:
            adoption_stage = "Growing"
        else:
            adoption_stage = "Early"

        # Trigger CSM crew review
        from src.csm_crew import CSMCrew

        csm = CSMCrew()
        result = csm.run_account_review(
            account_name=company.name,
            company_size="Enterprise" if company.employee_count and company.employee_count > 500 else "Mid" if company.employee_count and company.employee_count > 50 else "Small",
            industry=company.industry.value if company.industry else "Other",
            adoption_stage=adoption_stage,
            usage_level="High" if health.expansion_score > 70 else "Medium" if health.health_score > 50 else "Low",
        )

        return {
            "ok": True,
            "account_id": account_id,
            "account_name": company.name,
            "review": result,
        }
    finally:
        db.close()


@router.get("/health", tags=["csm"])
def csm_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get CSM system health and status."""
    logger.info("Checking CSM system health")

    db = SessionLocal()
    try:
        accounts = HealthCalculator.assess_all_accounts(db)
        summary = RecommendationEngine.get_actions_summary(db)

        return {
            "ok": True,
            "total_accounts": len(accounts),
            "critical_accounts": len([a for a in accounts if a.health_status == "critical"]),
            "expansion_opportunities": len([a for a in accounts if a.expansion_score >= 60]),
            "total_expansion_value": summary.get("expansion_value", 0),
            "status": "healthy",
        }
    finally:
        db.close()
