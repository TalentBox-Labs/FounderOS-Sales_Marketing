"""Account health tracking and customer success metrics."""

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
class HealthSignal:
    """A signal indicating customer health (positive or negative)."""

    name: str
    value: float  # -100 (critical negative) to +100 (critical positive)
    weight: float  # How much this signal affects overall health
    category: str  # engagement, product_usage, support, payment, expansion
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class AccountHealth:
    """Overall health of a customer account."""

    account_id: str
    account_name: str
    health_score: float  # 0-100, where 100 is healthiest
    health_status: str  # healthy, at_risk, critical
    signals: list[HealthSignal]
    churn_risk_score: float  # 0-100, where 100 is highest churn risk
    expansion_score: float  # 0-100, likelihood of expansion
    last_updated: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "health_score": self.health_score,
            "health_status": self.health_status,
            "signals": [
                {
                    "name": s.name,
                    "value": s.value,
                    "weight": s.weight,
                    "category": s.category,
                }
                for s in self.signals
            ],
            "churn_risk_score": self.churn_risk_score,
            "expansion_score": self.expansion_score,
            "last_updated": self.last_updated,
        }


class HealthCalculator:
    """Calculate customer account health metrics."""

    @classmethod
    def assess_account_health(cls, db: Session, company_id: str) -> AccountHealth:
        """
        Assess overall health of a customer account.

        Factors:
        - Engagement: Recent contact activity
        - Product usage: Deal/activity metrics
        - Support: Support ticket sentiment
        - Payment: Payment history
        - Expansion: Expansion potential
        """
        from revenue_os.models.contact import Company

        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None

        signals = []

        # 1. Engagement signals
        contacts = db.query(Contact).filter(Contact.company_id == company_id).all()
        if contacts:
            active_contacts = [
                c for c in contacts
                if c.last_contacted_at
                and (datetime.now(timezone.utc) - c.last_contacted_at).days <= 30
            ]
            engagement_pct = (len(active_contacts) / len(contacts)) * 100 if contacts else 0

            if engagement_pct > 70:
                signals.append(HealthSignal("High engagement (>70%)", +30, 0.2, "engagement"))
            elif engagement_pct < 20:
                signals.append(HealthSignal("Low engagement (<20%)", -40, 0.3, "engagement"))
            else:
                signals.append(HealthSignal("Moderate engagement", +10, 0.2, "engagement"))

        # 2. Deal/revenue signals
        deals = (
            db.query(Deal)
            .filter(Deal.company_id == company_id)
            .filter(Deal.closed_at.is_(None))
            .all()
        )
        if deals:
            total_value = sum(d.value for d in deals)
            if total_value > 50000:
                signals.append(HealthSignal("High pipeline value", +25, 0.25, "expansion"))
            elif total_value < 5000:
                signals.append(HealthSignal("Low pipeline value", -20, 0.2, "product_usage"))

        # 3. Expansion signals
        expansion_deals = [d for d in deals if d.stage == DealStage.PROPOSAL]
        if expansion_deals:
            signals.append(HealthSignal("Active expansion deals", +35, 0.25, "expansion"))
        elif not deals:
            signals.append(HealthSignal("No active deals", -30, 0.25, "expansion"))

        # 4. Contact quality
        qualified_contacts = [
            c for c in contacts if c.status == ContactStatus.QUALIFIED
        ]
        if len(qualified_contacts) > 3:
            signals.append(HealthSignal("Multiple qualified contacts", +20, 0.15, "engagement"))
        elif len(qualified_contacts) == 0:
            signals.append(HealthSignal("No qualified contacts", -35, 0.2, "engagement"))

        # 5. Account tenure (if available)
        if company.created_at:
            tenure_months = (datetime.now(timezone.utc) - company.created_at).days / 30
            if tenure_months > 12:
                signals.append(HealthSignal("Established account (>1 year)", +15, 0.1, "support"))
            elif tenure_months < 3:
                signals.append(HealthSignal("New account (<3 months)", -10, 0.1, "support"))

        # Calculate overall health score
        health_score = cls._calculate_health_score(signals)

        # Calculate churn risk
        churn_risk = cls._calculate_churn_risk(signals)

        # Calculate expansion score
        expansion_score = cls._calculate_expansion_score(signals)

        # Determine status
        if health_score >= 75:
            status = "healthy"
        elif health_score >= 50:
            status = "at_risk"
        else:
            status = "critical"

        return AccountHealth(
            account_id=str(company_id),
            account_name=company.name,
            health_score=health_score,
            health_status=status,
            signals=signals,
            churn_risk_score=churn_risk,
            expansion_score=expansion_score,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def _calculate_health_score(cls, signals: list[HealthSignal]) -> float:
        """Calculate weighted health score from signals."""
        if not signals:
            return 50.0  # Neutral score

        weighted_sum = sum(s.value * s.weight for s in signals)
        total_weight = sum(s.weight for s in signals)

        if total_weight == 0:
            return 50.0

        # Normalize to 0-100 range
        score = weighted_sum / total_weight
        score = max(0, min(100, score + 50))  # Shift from -100~100 to 0~100

        return round(score, 1)

    @classmethod
    def _calculate_churn_risk(cls, signals: list[HealthSignal]) -> float:
        """Calculate churn risk (0-100, higher = more risk)."""
        # Churn risk is inverse of health
        # Extract negative signals
        churn_signals = [s for s in signals if s.value < 0]

        if not churn_signals:
            return 10.0  # Low risk if no negative signals

        risk = sum(abs(s.value) * s.weight for s in churn_signals)
        risk = min(100, risk)

        return round(risk, 1)

    @classmethod
    def _calculate_expansion_score(cls, signals: list[HealthSignal]) -> float:
        """Calculate expansion potential (0-100, higher = more potential)."""
        expansion_signals = [s for s in signals if "expansion" in s.category]

        if not expansion_signals:
            return 30.0  # Neutral expansion potential

        score = sum(max(0, s.value) * s.weight for s in expansion_signals)
        score = min(100, score)

        return round(score, 1)

    @classmethod
    def assess_all_accounts(cls, db: Session) -> list[AccountHealth]:
        """Assess health of all customer accounts."""
        from revenue_os.models.contact import Company

        companies = db.query(Company).all()
        accounts = []

        for company in companies:
            health = cls.assess_account_health(db, company.id)
            if health:
                accounts.append(health)

        # Sort by churn risk (highest first)
        accounts.sort(key=lambda a: a.churn_risk_score, reverse=True)

        return accounts

    @classmethod
    def get_at_risk_accounts(cls, db: Session, threshold: float = 60.0) -> list[AccountHealth]:
        """Get accounts at risk of churn."""
        accounts = cls.assess_all_accounts(db)
        return [a for a in accounts if a.churn_risk_score >= threshold]

    @classmethod
    def get_expansion_opportunities(cls, db: Session, threshold: float = 60.0) -> list[AccountHealth]:
        """Get accounts with expansion potential."""
        accounts = cls.assess_all_accounts(db)
        return [
            a
            for a in accounts
            if a.expansion_score >= threshold and a.health_status in ("healthy", "at_risk")
        ]
