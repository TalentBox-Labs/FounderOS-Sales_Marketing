"""KPI (Key Performance Indicator) tracking and reporting."""

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
class KPI:
    """A key performance indicator."""

    name: str
    value: float
    target: float | None = None
    unit: str = ""
    trend: str = "stable"  # up, down, stable
    status: str = "healthy"  # healthy, warning, critical

    @property
    def vs_target(self) -> float:
        """Percentage vs target."""
        if not self.target or self.target == 0:
            return 0
        return (self.value / self.target) * 100

    @property
    def status_icon(self) -> str:
        """Visual indicator of status."""
        if self.status == "critical":
            return "🔴"
        elif self.status == "warning":
            return "🟡"
        else:
            return "🟢"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "target": self.target,
            "unit": self.unit,
            "trend": self.trend,
            "status": self.status,
            "vs_target": self.vs_target,
            "status_icon": self.status_icon,
        }


class KPICalculator:
    """Calculate key performance indicators."""

    @classmethod
    def calculate_revenue_kpis(
        cls, db: Session, monthly_target: float = 100000.0
    ) -> dict[str, KPI]:
        """Calculate revenue-related KPIs."""
        health = get_pipeline_health(db)
        velocity = calculate_deal_velocity(db, days=90)

        # Calculate ARR (Annual Recurring Revenue)
        # Simplified: pipeline * win rate * 4 (quarterly to annual)
        arr = health["weighted_forecast"] * velocity.get("win_rate", 0.75) * 4

        # Calculate monthly run rate
        closed_this_month = velocity.get("closed_deals", 0)
        monthly_closed_value = sum(
            d.value
            for d in db.query(Deal)
            .filter(Deal.closed_at >= datetime.now(timezone.utc) - timedelta(days=30))
            .all()
        )

        return {
            "arr": KPI(
                name="Annual Recurring Revenue",
                value=arr,
                target=monthly_target * 12,
                unit="$",
                status="healthy" if arr >= (monthly_target * 12) * 0.8 else "warning",
            ),
            "pipeline": KPI(
                name="Pipeline Value",
                value=health["total_pipeline_value"],
                target=monthly_target * 3,  # 3x monthly target
                unit="$",
            ),
            "forecast": KPI(
                name="Weighted Forecast",
                value=health["weighted_forecast"],
                target=monthly_target,
                unit="$",
            ),
            "monthly_closed": KPI(
                name="Monthly Closed Revenue",
                value=monthly_closed_value,
                target=monthly_target,
                unit="$",
                status="healthy" if monthly_closed_value >= monthly_target * 0.8 else "warning",
            ),
            "win_rate": KPI(
                name="Win Rate",
                value=velocity.get("win_rate", 0.0) * 100,
                target=75.0,
                unit="%",
                status="healthy" if velocity.get("win_rate", 0) >= 0.7 else "warning",
            ),
        }

    @classmethod
    def calculate_sales_kpis(cls, db: Session) -> dict[str, KPI]:
        """Calculate sales team KPIs."""
        health = get_pipeline_health(db)
        velocity = calculate_deal_velocity(db)
        at_risk = get_deals_at_risk(db)

        total_deals = health["total_deals"]
        at_risk_count = len(at_risk)
        at_risk_pct = (at_risk_count / total_deals * 100) if total_deals > 0 else 0

        return {
            "total_deals": KPI(
                name="Total Open Deals",
                value=total_deals,
                target=50.0,
            ),
            "avg_deal_size": KPI(
                name="Average Deal Size",
                value=health["total_pipeline_value"] / total_deals if total_deals > 0 else 0,
                target=5000.0,
                unit="$",
            ),
            "cycle_time": KPI(
                name="Sales Cycle (days)",
                value=velocity.get("avg_cycle_time_days", 0),
                target=45.0,
                unit="days",
                status="healthy" if velocity.get("avg_cycle_time_days", 0) <= 50 else "warning",
            ),
            "at_risk_deals": KPI(
                name="At-Risk Deals",
                value=at_risk_count,
                target=0.0,
                status="critical" if at_risk_pct > 20 else "warning" if at_risk_pct > 10 else "healthy",
            ),
        }

    @classmethod
    def calculate_lead_kpis(cls, db: Session) -> dict[str, KPI]:
        """Calculate lead generation KPIs."""
        all_contacts = db.query(Contact).all()
        qualified = [c for c in all_contacts if c.status == ContactStatus.QUALIFIED]
        prospects = [c for c in all_contacts if c.status == ContactStatus.PROSPECT]

        total = len(all_contacts)
        qualification_rate = (len(qualified) / total * 100) if total > 0 else 0
        prospect_rate = (len(prospects) / total * 100) if total > 0 else 0

        # Average lead score
        avg_score = sum(c.lead_score for c in all_contacts) / total if total > 0 else 0

        return {
            "total_leads": KPI(
                name="Total Leads",
                value=total,
                target=500.0,
                status="healthy" if total >= 500 else "warning",
            ),
            "qualified_leads": KPI(
                name="Qualified Leads",
                value=len(qualified),
                target=50.0,
                status="healthy" if len(qualified) >= 40 else "warning",
            ),
            "qualification_rate": KPI(
                name="Qualification Rate",
                value=qualification_rate,
                target=10.0,
                unit="%",
                status="healthy" if qualification_rate >= 8 else "warning",
            ),
            "avg_lead_score": KPI(
                name="Average Lead Score",
                value=avg_score,
                target=50.0,
                unit="pts",
            ),
        }

    @classmethod
    def calculate_operational_kpis(cls, db: Session) -> dict[str, KPI]:
        """Calculate operational KPIs."""
        # These would come from crew metrics, observability system, etc.
        return {
            "crew_efficiency": KPI(
                name="Crew Efficiency",
                value=85.0,  # Placeholder - would come from metrics
                target=90.0,
                unit="%",
                status="healthy" if 85 >= 80 else "warning",
            ),
            "content_velocity": KPI(
                name="Content Pieces/Week",
                value=12.0,  # Placeholder
                target=10.0,
                status="healthy",
            ),
            "system_uptime": KPI(
                name="System Uptime",
                value=99.8,
                target=99.9,
                unit="%",
                status="healthy" if 99.8 >= 99.5 else "warning",
            ),
        }

    @classmethod
    def all_kpis(cls, db: Session, targets: dict[str, float] | None = None) -> dict[str, dict[str, KPI]]:
        """Get all KPIs."""
        if targets is None:
            targets = {}

        monthly_target = targets.get("monthly_revenue", 100000.0)

        return {
            "revenue": cls.calculate_revenue_kpis(db, monthly_target),
            "sales": cls.calculate_sales_kpis(db),
            "leads": cls.calculate_lead_kpis(db),
            "operations": cls.calculate_operational_kpis(db),
        }
