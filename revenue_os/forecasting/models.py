"""ML models for revenue forecasting and prediction."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of a prediction model."""

    entity_id: str
    entity_type: str  # contact, deal, account
    prediction: float  # 0-1 probability or value
    confidence: float  # 0-1 confidence in prediction
    factors: dict[str, float]  # Contributing factors and their weights
    model_version: str = "v1"
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "prediction": round(self.prediction, 3),
            "confidence": round(self.confidence, 3),
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "model_version": self.model_version,
            "timestamp": self.timestamp,
        }


@dataclass
class ChurnPrediction:
    """Churn prediction for a customer account."""

    account_id: str
    account_name: str
    churn_probability: float  # 0-1, probability of churn
    churn_risk_level: str  # low, medium, high, critical
    confidence: float  # 0-1
    risk_factors: dict[str, float]  # Contributing factors
    recommended_action: str
    days_until_churn: int  # Estimated days before churn

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "churn_probability": round(self.churn_probability, 3),
            "churn_risk_level": self.churn_risk_level,
            "confidence": round(self.confidence, 3),
            "risk_factors": {k: round(v, 3) for k, v in self.risk_factors.items()},
            "recommended_action": self.recommended_action,
            "days_until_churn": self.days_until_churn,
        }


@dataclass
class RevenueForecast:
    """Revenue forecast for future period."""

    period: str  # e.g., "2024-Q3", "2024-06"
    forecast_value: float  # Predicted revenue
    confidence_lower: float  # Lower confidence bound
    confidence_upper: float  # Upper confidence bound
    confidence_level: float  # 0.95 = 95%
    contributing_factors: dict[str, float]
    model_version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "period": self.period,
            "forecast_value": round(self.forecast_value, 2),
            "confidence_lower": round(self.confidence_lower, 2),
            "confidence_upper": round(self.confidence_upper, 2),
            "confidence_level": self.confidence_level,
            "range": round(self.confidence_upper - self.confidence_lower, 2),
            "contributing_factors": {k: round(v, 3) for k, v in contributing_factors.items()},
            "model_version": self.model_version,
        }


class PredictiveModels:
    """ML models for predictions and forecasting."""

    @classmethod
    def predict_churn(cls, db: Session, account_id: str) -> ChurnPrediction:
        """
        Predict probability of customer churn.

        Features:
        - Health score (0-100)
        - Days since last contact
        - Payment history
        - Contract renewal date
        - Deal pipeline value
        """
        from revenue_os.customer_success.account_health import HealthCalculator

        health = HealthCalculator.assess_account_health(db, account_id)

        if not health:
            return None

        # Simple model: combine signals
        # In production: use trained ML model (sklearn, xgboost, etc)

        # Base risk from health score (inverse)
        health_risk = (100 - health.health_score) / 100.0

        # Days since last contact (from signals)
        days_stale = 30  # Placeholder
        contact_risk = min(1.0, days_stale / 90.0)  # Max risk at 90 days

        # Payment risk (simplified)
        payment_risk = 0.0  # Placeholder (assume good payment)

        # Contract renewal risk (simplified)
        renewal_risk = 0.0  # Placeholder

        # Weighted combination
        weights = {
            "health_score": 0.40,
            "contact_frequency": 0.30,
            "payment_history": 0.15,
            "contract_renewal": 0.15,
        }

        churn_prob = (
            health_risk * weights["health_score"]
            + contact_risk * weights["contact_frequency"]
            + payment_risk * weights["payment_history"]
            + renewal_risk * weights["contract_renewal"]
        )

        churn_prob = max(0, min(1.0, churn_prob))  # Clamp 0-1

        # Determine risk level
        if churn_prob > 0.7:
            risk_level = "critical"
            days_until = 30
            action = "Immediate executive intervention required"
        elif churn_prob > 0.5:
            risk_level = "high"
            days_until = 60
            action = "Schedule business review with stakeholders"
        elif churn_prob > 0.3:
            risk_level = "medium"
            days_until = 90
            action = "Increase engagement and check-in frequency"
        else:
            risk_level = "low"
            days_until = 365
            action = "Maintain current engagement"

        # Confidence (lower probability = lower confidence in prediction)
        confidence = 0.85 if churn_prob > 0.3 else 0.7

        return ChurnPrediction(
            account_id=str(account_id),
            account_name=health.account_name,
            churn_probability=churn_prob,
            churn_risk_level=risk_level,
            confidence=confidence,
            risk_factors={
                "health_score": health_risk,
                "contact_frequency": contact_risk,
                "payment_history": payment_risk,
                "contract_renewal": renewal_risk,
            },
            recommended_action=action,
            days_until_churn=days_until,
        )

    @classmethod
    def forecast_revenue(cls, db: Session, months_ahead: int = 3) -> list[RevenueForecast]:
        """
        Forecast revenue for next N months.

        Uses:
        - Historical closed deals
        - Current pipeline
        - Win rates by stage
        - Seasonal adjustments
        """
        from revenue_os.services.deal_automation_service import (
            calculate_deal_velocity,
            get_pipeline_health,
        )

        health = get_pipeline_health(db)
        velocity = calculate_deal_velocity(db, days=90)

        # Historical metrics
        pipeline = health["total_pipeline_value"]
        by_stage = health["by_stage"]
        win_rate = velocity.get("win_rate", 0.75)
        avg_cycle = velocity.get("avg_cycle_time_days", 45)

        forecasts = []

        for month in range(1, months_ahead + 1):
            # Simple forecast: deals likely to close in this month
            # Based on stage progression and historical cycle time

            # Deals in proposal/negotiation stage (60-80% probability)
            proposal_value = by_stage.get("proposal", {}).get("total_value", 0)
            negotiation_value = by_stage.get("negotiation", {}).get("total_value", 0)

            # Probability of closing this month
            # Rough estimate: deals in final stages more likely to close
            late_stage_value = proposal_value + negotiation_value
            month_probability = min(0.5, month / avg_cycle * 30)  # Increase over time

            forecast_value = (
                late_stage_value * month_probability * win_rate
                + pipeline * 0.1 * win_rate  # Some deals from broader pipeline
            )

            # Add seasonal adjustment (simplified)
            # Q4 typically stronger
            now = datetime.now(timezone.utc)
            forecast_month = now + timedelta(days=30 * month)
            quarter = (forecast_month.month - 1) // 3
            seasonal_boost = 1.2 if quarter == 3 else 1.0  # Q4 boost

            forecast_value *= seasonal_boost

            # Confidence intervals (wider for further out)
            # Approximately ±15% for month 1, ±25% for month 3
            confidence_margin = 0.15 + (month - 1) * 0.05
            confidence_lower = forecast_value * (1 - confidence_margin)
            confidence_upper = forecast_value * (1 + confidence_margin)

            period = (now + timedelta(days=30 * month)).strftime("%Y-%m")

            forecasts.append(
                RevenueForecast(
                    period=period,
                    forecast_value=max(0, forecast_value),
                    confidence_lower=max(0, confidence_lower),
                    confidence_upper=confidence_upper,
                    confidence_level=0.85,
                    contributing_factors={
                        "late_stage_deals": late_stage_value,
                        "win_rate": win_rate,
                        "seasonal_adjustment": seasonal_boost,
                        "month_probability": month_probability,
                    },
                )
            )

        return forecasts

    @classmethod
    def predict_deal_win(cls, db: Session, deal_id: str) -> PredictionResult:
        """Predict probability of deal being won."""
        deal = db.query(Deal).filter(Deal.id == deal_id).first()

        if not deal:
            return None

        # Simple model based on stage and other factors
        stage_probability = {
            DealStage.DISCOVERY: 0.10,
            DealStage.QUALIFIED: 0.25,
            DealStage.PROPOSAL: 0.50,
            DealStage.NEGOTIATION: 0.80,
            DealStage.CLOSED_WON: 1.0,
            DealStage.CLOSED_LOST: 0.0,
        }

        base_probability = stage_probability.get(deal.stage, 0.3)

        # Adjust based on deal characteristics
        # Days in current stage (longer = more likely to close)
        if deal.created_at:
            days_in_stage = (datetime.now(timezone.utc) - deal.updated_at).days
            age_factor = min(1.0, days_in_stage / 30.0)  # Normalized to 30 days
            base_probability *= (0.8 + age_factor * 0.4)  # 0.8-1.2x multiplier

        # Deal size (larger deals may have lower win rate)
        if deal.value > 50000:
            base_probability *= 0.9
        elif deal.value > 100000:
            base_probability *= 0.8

        probability = max(0, min(1.0, base_probability))
        confidence = 0.70 if deal.stage in (DealStage.PROPOSAL, DealStage.NEGOTIATION) else 0.60

        return PredictionResult(
            entity_id=str(deal_id),
            entity_type="deal",
            prediction=probability,
            confidence=confidence,
            factors={
                "stage": stage_probability.get(deal.stage, 0),
                "deal_age": min(1.0, days_in_stage / 30.0) if deal.created_at else 0,
                "deal_size_adjustment": 1.0 if deal.value <= 50000 else 0.8,
            },
        )

    @classmethod
    def predict_expansion(cls, db: Session, account_id: str) -> PredictionResult:
        """Predict likelihood of expansion from account."""
        from revenue_os.customer_success.account_health import HealthCalculator

        health = HealthCalculator.assess_account_health(db, account_id)

        if not health:
            return None

        # Expansion prediction based on expansion score and health
        expansion_base = health.expansion_score / 100.0
        health_factor = health.health_score / 100.0

        # Healthy accounts more likely to expand
        expansion_prob = expansion_base * 0.6 + health_factor * 0.4

        confidence = 0.75 if health.expansion_score > 50 else 0.6

        return PredictionResult(
            entity_id=str(account_id),
            entity_type="account",
            prediction=expansion_prob,
            confidence=confidence,
            factors={
                "expansion_potential": expansion_base,
                "account_health": health_factor,
            },
        )
