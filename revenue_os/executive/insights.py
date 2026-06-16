"""Strategic insights and recommendations engine for executives."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from revenue_os.services.deal_automation_service import (
    calculate_deal_velocity,
    get_deals_at_risk,
    get_pipeline_health,
)
from revenue_os.services.lead_scoring_service import get_score_distribution

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """An insight or observation about system state."""

    title: str
    description: str
    category: str  # revenue, sales, operations, risk
    priority: str  # critical, high, medium, low
    metrics: dict[str, Any] = None
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "metrics": self.metrics or {},
            "recommendation": self.recommendation,
        }


class InsightEngine:
    """Generate strategic insights from platform data."""

    @classmethod
    def analyze_revenue(cls, db: Session) -> list[Insight]:
        """Analyze revenue metrics and generate insights."""
        insights = []
        health = get_pipeline_health(db)
        velocity = calculate_deal_velocity(db)

        # Forecast vs target
        forecast = health["weighted_forecast"]
        target = 100000.0  # Monthly target
        forecast_pct = (forecast / target) * 100 if target > 0 else 0

        if forecast_pct < 80:
            insights.append(
                Insight(
                    title="⚠️ Revenue Forecast Below Target",
                    description=f"Current weighted forecast is ${forecast:.0f}, which is {forecast_pct:.0f}% of ${target:.0f} target",
                    category="revenue",
                    priority="critical",
                    metrics={"forecast": forecast, "target": target, "pct": forecast_pct},
                    recommendation="Increase deal velocity: accelerate proposal stage, reduce negotiation time, or increase new deal inflow",
                )
            )
        elif forecast_pct > 120:
            insights.append(
                Insight(
                    title="✅ Revenue Forecast Exceeds Target",
                    description=f"Weighted forecast is {forecast_pct:.0f}% of target. Strong pipeline momentum.",
                    category="revenue",
                    priority="medium",
                    metrics={"forecast": forecast, "target": target, "pct": forecast_pct},
                    recommendation="Maintain current pace. Evaluate if sales team is at capacity to handle potential deals.",
                )
            )

        # Win rate analysis
        win_rate = velocity.get("win_rate", 0)
        if win_rate < 0.6:
            insights.append(
                Insight(
                    title="📉 Win Rate Below Benchmark",
                    description=f"Current win rate is {win_rate * 100:.0f}%. Industry benchmark is 70-80%.",
                    category="revenue",
                    priority="high",
                    metrics={"win_rate": win_rate * 100, "benchmark": 75},
                    recommendation="Review lost deals for patterns. Improve proposal quality or deal qualification earlier in pipeline.",
                )
            )

        # Pipeline health
        if health["total_deals"] < 30:
            insights.append(
                Insight(
                    title="⚠️ Thin Pipeline",
                    description=f"Only {health['total_deals']} open deals. Need more deal inflow.",
                    category="revenue",
                    priority="high",
                    metrics={"open_deals": health["total_deals"], "healthy_range": "50-100"},
                    recommendation="Increase lead generation and qualification. Current inflow insufficient to meet revenue targets.",
                )
            )

        return insights

    @classmethod
    def analyze_sales(cls, db: Session) -> list[Insight]:
        """Analyze sales operations and generate insights."""
        insights = []

        health = get_pipeline_health(db)
        at_risk = get_deals_at_risk(db)
        velocity = calculate_deal_velocity(db)

        # At-risk deals
        if len(at_risk) > 0:
            total_at_risk = sum(d["value"] for d in at_risk)
            pct_of_pipeline = (total_at_risk / health["total_pipeline_value"] * 100) if health["total_pipeline_value"] > 0 else 0

            insights.append(
                Insight(
                    title="🔴 Critical: Deals at Risk",
                    description=f"{len(at_risk)} deals totaling ${total_at_risk:.0f} ({pct_of_pipeline:.1f}% of pipeline) are at risk",
                    category="risk",
                    priority="critical",
                    metrics={
                        "count": len(at_risk),
                        "value": total_at_risk,
                        "pct_of_pipeline": pct_of_pipeline,
                    },
                    recommendation="Immediately escalate top 3 at-risk deals. Sales leadership intervention required.",
                )
            )

        # Cycle time
        cycle_time = velocity.get("avg_cycle_time_days", 0)
        if cycle_time > 60:
            insights.append(
                Insight(
                    title="⏱️ Sales Cycle Too Long",
                    description=f"Average cycle time is {cycle_time:.0f} days. Target is 45 days.",
                    category="sales",
                    priority="high",
                    metrics={"actual": cycle_time, "target": 45},
                    recommendation="Identify bottleneck stages. Consider sales training or process improvements to accelerate deals.",
                )
            )

        # Closed deals trend
        closed_this_period = velocity.get("closed_deals", 0)
        if closed_this_period == 0:
            insights.append(
                Insight(
                    title="⚠️ No Deals Closing",
                    description="No deals closed in the last 90 days. Pipeline may be stalled.",
                    category="sales",
                    priority="critical",
                    recommendation="Audit deal pipeline. Some deals should be reaching close stage.",
                )
            )

        return insights

    @classmethod
    def analyze_leads(cls, db: Session) -> list[Insight]:
        """Analyze lead generation and qualification."""
        insights = []

        all_contacts = db.query(Contact).all()
        qualified = [c for c in all_contacts if c.status == ContactStatus.QUALIFIED]
        total = len(all_contacts)

        if total == 0:
            insights.append(
                Insight(
                    title="⚠️ No Leads in System",
                    description="Lead database is empty. Activate lead generation immediately.",
                    category="operations",
                    priority="critical",
                    recommendation="Launch prospecting campaigns. Import existing leads or activate lead sources.",
                )
            )
            return insights

        qualification_rate = (len(qualified) / total * 100) if total > 0 else 0

        # Qualification rate
        if qualification_rate < 5:
            insights.append(
                Insight(
                    title="📊 Low Lead Quality",
                    description=f"Only {qualification_rate:.1f}% of leads are qualified. Target is 10%+.",
                    category="sales",
                    priority="high",
                    metrics={"current": qualification_rate, "target": 10},
                    recommendation="Improve lead scoring model. Review lead sources and import quality.",
                )
            )
        elif qualification_rate > 20:
            insights.append(
                Insight(
                    title="✅ Strong Lead Quality",
                    description=f"Lead qualification rate is {qualification_rate:.1f}%. Well above target.",
                    category="sales",
                    priority="medium",
                    recommendation="Maintain current lead generation approach. Can increase lead volume without sacrificing quality.",
                )
            )

        # Lead velocity
        recent_leads = [c for c in all_contacts if (datetime.now(timezone.utc) - c.created_at).days <= 30]
        if len(recent_leads) == 0:
            insights.append(
                Insight(
                    title="⚠️ No New Lead Inflow",
                    description="No leads added in the last 30 days. Lead generation may have stopped.",
                    category="operations",
                    priority="high",
                    recommendation="Check lead sources. Ensure prospecting campaigns are active.",
                )
            )

        return insights

    @classmethod
    def analyze_operations(cls, db: Session) -> list[Insight]:
        """Analyze operational efficiency."""
        insights = []

        # Lead to opportunity conversion
        all_contacts = db.query(Contact).all()
        qualified = [c for c in all_contacts if c.status == ContactStatus.QUALIFIED]
        deals = db.query(Deal).filter(Deal.closed_at.is_(None)).all()

        conversion_rate = (len(deals) / len(qualified) * 100) if len(qualified) > 0 else 0

        if conversion_rate < 70:
            insights.append(
                Insight(
                    title="📈 Qualified Leads Not Converting to Deals",
                    description=f"Only {conversion_rate:.0f}% of qualified leads have deals. Target is 90%+.",
                    category="operations",
                    priority="high",
                    metrics={"conversion": conversion_rate, "target": 90},
                    recommendation="Automate deal creation for qualified leads. Check if sales team is missing follow-up.",
                )
            )

        return insights

    @classmethod
    def all_insights(cls, db: Session) -> dict[str, list[Insight]]:
        """Generate all insights."""
        return {
            "revenue": cls.analyze_revenue(db),
            "sales": cls.analyze_sales(db),
            "leads": cls.analyze_leads(db),
            "operations": cls.analyze_operations(db),
        }
