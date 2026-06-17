"""CSM recommendations for account management and expansion."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.customer_success.account_health import HealthCalculator

logger = logging.getLogger(__name__)


@dataclass
class CSMRecommendation:
    """A recommendation for a customer success action."""

    title: str
    description: str
    account_id: str
    account_name: str
    action_type: str  # retention, expansion, engagement, check_in
    priority: str  # critical, high, medium, low
    value: float  # Potential annual value ($)
    estimated_effort: str  # hours required
    specific_steps: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "action_type": self.action_type,
            "priority": self.priority,
            "value": self.value,
            "estimated_effort": self.estimated_effort,
            "specific_steps": self.specific_steps,
        }


class RecommendationEngine:
    """Generate CSM recommendations based on account health."""

    @classmethod
    def generate_recommendations(
        cls, db: Session, account_id: str
    ) -> list[CSMRecommendation]:
        """Generate recommendations for a specific account."""
        health = HealthCalculator.assess_account_health(db, account_id)

        if not health:
            return []

        recommendations = []

        # Churn risk recommendations
        if health.churn_risk_score >= 80:
            recommendations.append(
                CSMRecommendation(
                    title="🔴 Critical: High Churn Risk",
                    description=f"Account {health.account_name} is at critical churn risk ({health.churn_risk_score:.0f}/100)",
                    account_id=health.account_id,
                    account_name=health.account_name,
                    action_type="retention",
                    priority="critical",
                    value=0.0,  # Defensive value
                    estimated_effort="4 hours",
                    specific_steps=[
                        "Schedule executive check-in with customer within 48 hours",
                        "Review contract and renewal date",
                        "Identify specific pain points and concerns",
                        "Develop remediation plan",
                        "Assign dedicated CSM or escalate to management",
                    ],
                )
            )

        elif health.churn_risk_score >= 60:
            recommendations.append(
                CSMRecommendation(
                    title="🟡 Warning: Moderate Churn Risk",
                    description=f"Account {health.account_name} shows signs of disengagement ({health.churn_risk_score:.0f}/100)",
                    account_id=health.account_id,
                    account_name=health.account_name,
                    action_type="retention",
                    priority="high",
                    value=0.0,
                    estimated_effort="2 hours",
                    specific_steps=[
                        "Schedule business review with key contacts",
                        "Assess product adoption and usage",
                        "Identify unmet needs or feature requests",
                        "Create engagement plan",
                        "Schedule follow-up check-in in 2 weeks",
                    ],
                )
            )

        # Expansion recommendations
        if health.expansion_score >= 80:
            recommendations.append(
                CSMRecommendation(
                    title="✨ High Expansion Opportunity",
                    description=f"Account {health.account_name} has strong expansion potential ({health.expansion_score:.0f}/100)",
                    account_id=health.account_id,
                    account_name=health.account_name,
                    action_type="expansion",
                    priority="high",
                    value=25000.0,  # Estimated annual value
                    estimated_effort="8 hours",
                    specific_steps=[
                        "Schedule discovery call with expansion champion",
                        "Understand adjacent use cases and pain points",
                        "Prepare proof-of-concept or expansion proposal",
                        "Present opportunity to customer",
                        "Develop implementation plan and timeline",
                    ],
                )
            )

        elif health.expansion_score >= 60:
            recommendations.append(
                CSMRecommendation(
                    title="📈 Moderate Expansion Opportunity",
                    description=f"Account {health.account_name} could benefit from expansion ({health.expansion_score:.0f}/100)",
                    account_id=health.account_id,
                    account_name=health.account_name,
                    action_type="expansion",
                    priority="medium",
                    value=10000.0,
                    estimated_effort="4 hours",
                    specific_steps=[
                        "Schedule check-in with account to discuss growth",
                        "Identify new use cases or departments",
                        "Share success stories or case studies",
                        "Propose expansion roadmap",
                    ],
                )
            )

        # Engagement recommendations
        if health.health_score < 50:
            recommendations.append(
                CSMRecommendation(
                    title="⚠️ Low Engagement",
                    description=f"Account {health.account_name} is not fully engaged ({health.health_score:.0f}/100 health)",
                    account_id=health.account_id,
                    account_name=health.account_name,
                    action_type="engagement",
                    priority="high",
                    value=0.0,
                    estimated_effort="3 hours",
                    specific_steps=[
                        "Conduct adoption audit to identify gaps",
                        "Provide training or resources for low-adoption features",
                        "Schedule product demo or workshop",
                        "Create 30/60/90 day success milestones",
                        "Establish regular check-in cadence",
                    ],
                )
            )

        # Check-in recommendations
        if health.health_score >= 70 and health.expansion_score < 50:
            recommendations.append(
                CSMRecommendation(
                    title="📅 Quarterly Business Review",
                    description=f"Schedule QBR with {health.account_name} to align on goals and opportunities",
                    account_id=health.account_id,
                    account_name=health.account_name,
                    action_type="check_in",
                    priority="medium",
                    value=5000.0,  # Potential uplift
                    estimated_effort="6 hours",
                    specific_steps=[
                        "Review past quarter metrics and ROI",
                        "Discuss upcoming quarter priorities",
                        "Present new features and roadmap",
                        "Explore expansion opportunities",
                        "Align on success metrics and goals",
                    ],
                )
            )

        return recommendations

    @classmethod
    def get_all_recommendations(cls, db: Session) -> dict[str, list[CSMRecommendation]]:
        """Get recommendations for all accounts."""
        from revenue_os.models.contact import Company

        companies = db.query(Company).all()

        all_recommendations = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        for company in companies:
            recommendations = cls.generate_recommendations(db, str(company.id))
            for rec in recommendations:
                all_recommendations[rec.priority].append(rec)

        return all_recommendations

    @classmethod
    def get_actions_summary(cls, db: Session) -> dict[str, Any]:
        """Get summary of all CSM actions needed."""
        all_recs = cls.get_all_recommendations(db)

        total_value = sum(
            r.value for recs in all_recs.values() for r in recs
        )
        total_effort_hours = sum(
            int(r.estimated_effort.split()[0]) for recs in all_recs.values() for r in recs
        )

        return {
            "total_recommendations": sum(len(recs) for recs in all_recs.values()),
            "by_priority": {
                priority: len(recs) for priority, recs in all_recs.items()
            },
            "total_potential_value": total_value,
            "total_effort_hours": total_effort_hours,
            "critical_actions": len(all_recs["critical"]),
            "expansion_value": sum(
                r.value for recs in all_recs.values() for r in recs if r.action_type == "expansion"
            ),
        }
