"""Predictive forecasting and scenario planning endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from revenue_os.database import SessionLocal
from revenue_os.forecasting.models import PredictiveModels
from revenue_os.forecasting.scenarios import ScenarioEngine, Scenario

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


@router.get("/churn-predictions", tags=["forecasting"])
def get_churn_predictions(
    threshold: float = 0.5,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get churn predictions for all accounts."""
    logger.info("Generating churn predictions", extra={"threshold": threshold})

    db = SessionLocal()
    try:
        from revenue_os.models.contact import Company

        companies = db.query(Company).all()

        predictions = []
        high_risk = []

        for company in companies:
            pred = PredictiveModels.predict_churn(db, company.id)
            if pred:
                predictions.append(pred)
                if pred.churn_probability >= threshold:
                    high_risk.append(pred)

        # Sort by churn probability
        high_risk.sort(key=lambda x: x.churn_probability, reverse=True)

        return {
            "ok": True,
            "total_accounts": len(companies),
            "predicted": len(predictions),
            "high_risk_count": len(high_risk),
            "threshold": threshold,
            "high_risk_accounts": [p.to_dict() for p in high_risk],
            "avg_churn_probability": sum(p.churn_probability for p in predictions) / len(predictions)
            if predictions
            else 0,
        }
    finally:
        db.close()


@router.get("/churn-predictions/{account_id}", tags=["forecasting"])
def get_churn_prediction(
    account_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get churn prediction for a specific account."""
    logger.info("Predicting churn", extra={"account_id": account_id})

    db = SessionLocal()
    try:
        prediction = PredictiveModels.predict_churn(db, account_id)

        if not prediction:
            return {"ok": False, "error": "Account not found"}

        return {"ok": True, "prediction": prediction.to_dict()}
    finally:
        db.close()


@router.get("/revenue-forecast", tags=["forecasting"])
def get_revenue_forecast(
    months: int = 3,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get revenue forecast for next N months."""
    logger.info("Generating revenue forecast", extra={"months": months})

    db = SessionLocal()
    try:
        forecasts = PredictiveModels.forecast_revenue(db, months_ahead=min(months, 12))

        total_forecast = sum(f.forecast_value for f in forecasts)
        total_lower = sum(f.confidence_lower for f in forecasts)
        total_upper = sum(f.confidence_upper for f in forecasts)

        return {
            "ok": True,
            "months": len(forecasts),
            "total_forecast": round(total_forecast, 2),
            "forecast_range_lower": round(total_lower, 2),
            "forecast_range_upper": round(total_upper, 2),
            "forecast_confidence": 0.85,
            "forecasts": [f.to_dict() for f in forecasts],
        }
    finally:
        db.close()


@router.get("/deal-win-probability/{deal_id}", tags=["forecasting"])
def get_deal_win_probability(
    deal_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get probability of deal being won."""
    logger.info("Predicting deal win", extra={"deal_id": deal_id})

    db = SessionLocal()
    try:
        prediction = PredictiveModels.predict_deal_win(db, deal_id)

        if not prediction:
            return {"ok": False, "error": "Deal not found"}

        return {"ok": True, "prediction": prediction.to_dict()}
    finally:
        db.close()


@router.get("/expansion-predictions", tags=["forecasting"])
def get_expansion_predictions(
    threshold: float = 0.6,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get expansion probability predictions for all accounts."""
    logger.info("Generating expansion predictions", extra={"threshold": threshold})

    db = SessionLocal()
    try:
        from revenue_os.models.contact import Company

        companies = db.query(Company).all()

        predictions = []
        high_probability = []

        for company in companies:
            pred = PredictiveModels.predict_expansion(db, company.id)
            if pred:
                predictions.append(pred)
                if pred.prediction >= threshold:
                    high_probability.append(pred)

        # Sort by probability
        high_probability.sort(key=lambda x: x.prediction, reverse=True)

        return {
            "ok": True,
            "total_accounts": len(companies),
            "predicted": len(predictions),
            "high_probability_count": len(high_probability),
            "threshold": threshold,
            "high_probability_accounts": [p.to_dict() for p in high_probability],
            "avg_expansion_probability": sum(p.prediction for p in predictions) / len(predictions)
            if predictions
            else 0,
        }
    finally:
        db.close()


@router.get("/scenarios/presets", tags=["forecasting"])
def get_preset_scenarios(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get preset strategic scenarios."""
    logger.info("Fetching preset scenarios")

    scenarios = ScenarioEngine.get_preset_scenarios()

    return {
        "ok": True,
        "count": len(scenarios),
        "scenarios": [s.to_dict() for s in scenarios],
    }


@router.post("/scenarios/analyze", tags=["forecasting"])
def analyze_scenarios(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Analyze all preset scenarios against current forecast."""
    logger.info("Analyzing scenarios")

    db = SessionLocal()
    try:
        from revenue_os.services.deal_automation_service import get_pipeline_health

        health = get_pipeline_health(db)
        baseline_forecast = health["weighted_forecast"] * 4  # Annualize quarterly forecast

        results = ScenarioEngine.analyze_all_scenarios(db, baseline_forecast)
        comparison = ScenarioEngine.compare_scenarios(results)

        return {
            "ok": True,
            "baseline_forecast": round(baseline_forecast, 2),
            "total_scenarios": len(results),
            "scenarios": [r.to_dict() for r in results],
            "comparison": comparison,
        }
    finally:
        db.close()


@router.get("/model-performance", tags=["forecasting"])
def get_model_performance(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get information about the prediction models in use."""
    logger.info("Fetching model performance")

    return {
        "ok": True,
        "models": {
            "churn_prediction": {
                "type": "heuristic",
                "description": "Weighted combination of health score, contact recency, "
                "payment history, and renewal signals.",
                "trained": False,
            },
            "revenue_forecast": {
                "type": "heuristic",
                "description": "Pipeline-stage-weighted projection with seasonal adjustment.",
                "trained": False,
            },
            "deal_win_probability": {
                "type": "heuristic",
                "description": "Stage-based base rate adjusted for deal age and size.",
                "trained": False,
            },
        },
        "note": "These are rule-based heuristic models, not trained ML models. There is no "
        "training pipeline or accuracy-tracking mechanism yet, so accuracy/precision/recall "
        "metrics are not available.",
    }


@router.get("/health", tags=["forecasting"])
def forecasting_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get forecasting system health."""
    logger.info("Checking forecasting system health")

    scenarios = ScenarioEngine.get_preset_scenarios()

    return {
        "ok": True,
        "models_available": [
            "churn_prediction",
            "revenue_forecast",
            "deal_win_probability",
            "expansion_prediction",
        ],
        "scenarios_available": len(scenarios),
        "status": "healthy",
    }
