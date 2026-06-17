"""Scenario planning and what-if analysis engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class Scenario:
    """A what-if scenario for strategic planning."""

    name: str
    description: str
    changes: dict[str, float]  # Variable changes: {"sales_headcount": +2, "conversion_rate": +0.05}
    forecast_impact: float  # Projected impact on annual revenue
    confidence: float  # 0-1 confidence in projection
    assumptions: list[str]  # Key assumptions

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "changes": self.changes,
            "forecast_impact": round(self.forecast_impact, 2),
            "confidence": round(self.confidence, 2),
            "assumptions": self.assumptions,
        }


@dataclass
class ScenarioResult:
    """Result of scenario analysis."""

    scenario: Scenario
    baseline_forecast: float  # Current forecast
    scenario_forecast: float  # Forecast with scenario
    impact: float  # Absolute change
    impact_pct: float  # Percentage change
    roi: float  # Return on investment (if costs provided)
    payback_months: int  # Months to break even
    risk_rating: str  # low, medium, high

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario": self.scenario.to_dict(),
            "baseline_forecast": round(self.baseline_forecast, 2),
            "scenario_forecast": round(self.scenario_forecast, 2),
            "impact": round(self.impact, 2),
            "impact_pct": round(self.impact_pct, 3),
            "roi": round(self.roi, 2),
            "payback_months": self.payback_months,
            "risk_rating": self.risk_rating,
        }


class ScenarioEngine:
    """Plan and analyze strategic scenarios."""

    @classmethod
    def analyze_scenario(
        cls, db: Session, scenario: Scenario, baseline_forecast: float
    ) -> ScenarioResult:
        """
        Analyze impact of a scenario.

        Scenario variables:
        - sales_headcount: Number of sales reps
        - conversion_rate: Deal win rate
        - average_deal_size: ACV
        - sales_cycle: Days from DISCOVERY to CLOSED
        - lead_volume: Leads per month
        - qualification_rate: % of leads that qualify
        - expansion_rate: % of accounts that expand
        """

        # Extract scenario variables
        changes = scenario.changes

        # Calculate impact multipliers
        headcount_impact = 1.0 + changes.get("sales_headcount_change", 0) * 0.15  # +15% ARR per rep
        conversion_impact = 1.0 + changes.get("conversion_rate_change", 0)  # Direct impact
        deal_size_impact = 1.0 + changes.get("average_deal_size_change", 0)
        cycle_impact = 1.0 - changes.get("sales_cycle_reduction_pct", 0) * 0.05  # Cycle reduction
        lead_impact = 1.0 + changes.get("lead_volume_increase_pct", 0)
        qualification_impact = 1.0 + changes.get("qualification_rate_change", 0)
        expansion_impact = 1.0 + changes.get("expansion_rate_change", 0)

        # Combined impact
        total_impact = (
            headcount_impact
            * conversion_impact
            * deal_size_impact
            * cycle_impact
            * lead_impact
            * qualification_impact
            * expansion_impact
        )

        scenario_forecast = baseline_forecast * total_impact
        impact = scenario_forecast - baseline_forecast
        impact_pct = impact / baseline_forecast if baseline_forecast > 0 else 0

        # Calculate ROI (simplified)
        # Assume each sales rep costs $100K/year
        headcount_change = changes.get("sales_headcount_change", 0)
        headcount_cost = headcount_change * 100000

        # Assume lead gen investments cost $50K per 20% increase
        lead_increase = changes.get("lead_volume_increase_pct", 0)
        lead_gen_cost = (lead_increase / 0.2) * 50000 if lead_increase > 0 else 0

        total_cost = headcount_cost + lead_gen_cost
        roi = (impact / total_cost * 100) if total_cost > 0 else 0

        # Payback period in months
        monthly_impact = impact / 12
        payback_months = int((total_cost / monthly_impact)) if monthly_impact > 0 else 0

        # Risk rating
        if len([c for c in changes.values() if c > 0.2]) > 2:
            risk_rating = "high"
        elif len([c for c in changes.values() if c > 0.1]) > 2:
            risk_rating = "medium"
        else:
            risk_rating = "low"

        return ScenarioResult(
            scenario=scenario,
            baseline_forecast=baseline_forecast,
            scenario_forecast=scenario_forecast,
            impact=impact,
            impact_pct=impact_pct,
            roi=roi,
            payback_months=payback_months,
            risk_rating=risk_rating,
        )

    @classmethod
    def get_preset_scenarios(cls) -> list[Scenario]:
        """Get preset scenarios for common strategic decisions."""

        return [
            Scenario(
                name="Add 2 Sales Reps",
                description="Hire 2 additional sales representatives",
                changes={
                    "sales_headcount_change": 2,
                },
                forecast_impact=300000,
                confidence=0.75,
                assumptions=[
                    "Each rep closes $150K ARR",
                    "Ramp-up period: 3 months",
                    "30% quota attainment in year 1",
                ],
            ),
            Scenario(
                name="Increase Lead Generation 50%",
                description="Scale marketing and prospecting to generate 50% more leads",
                changes={
                    "lead_volume_increase_pct": 0.50,
                    "qualification_rate_change": -0.05,  # Quality may decrease
                },
                forecast_impact=200000,
                confidence=0.65,
                assumptions=[
                    "Lead quality decreases slightly with volume",
                    "SDR capacity to handle leads exists",
                    "Conversion rates hold steady",
                ],
            ),
            Scenario(
                name="Improve Sales Cycle 20%",
                description="Streamline sales process to reduce cycle time by 20%",
                changes={
                    "sales_cycle_reduction_pct": 0.20,
                },
                forecast_impact=150000,
                confidence=0.80,
                assumptions=[
                    "Process improvements are implementable",
                    "Sales team adoption is high",
                    "Deal values remain consistent",
                ],
            ),
            Scenario(
                name="Increase Win Rate to 80%",
                description="Improve sales effectiveness (training, process) to reach 80% win rate",
                changes={
                    "conversion_rate_change": 0.10,
                },
                forecast_impact=250000,
                confidence=0.60,
                assumptions=[
                    "Significant sales training investment required",
                    "Sales process redesign",
                    "Timeline: 6 months to see results",
                ],
            ),
            Scenario(
                name="Launch Expansion Program",
                description="Dedicate resources to customer expansion (CSM hiring, upsell)",
                changes={
                    "expansion_rate_change": 0.15,
                },
                forecast_impact=180000,
                confidence=0.70,
                assumptions=[
                    "Existing customer base is healthy",
                    "Expansion opportunities exist",
                    "CSM team can identify opportunities",
                ],
            ),
            Scenario(
                name="Combined Growth (All In)",
                description="Execute all strategies simultaneously: hire sales, scale leads, improve cycle, expand existing",
                changes={
                    "sales_headcount_change": 2,
                    "lead_volume_increase_pct": 0.50,
                    "sales_cycle_reduction_pct": 0.20,
                    "conversion_rate_change": 0.05,
                    "expansion_rate_change": 0.15,
                },
                forecast_impact=1200000,
                confidence=0.45,
                assumptions=[
                    "Execution excellence across all initiatives",
                    "Sufficient capital and resources",
                    "Team capacity to manage growth",
                    "Market conditions remain favorable",
                ],
            ),
        ]

    @classmethod
    def analyze_all_scenarios(
        cls, db: Session, baseline_forecast: float
    ) -> list[ScenarioResult]:
        """Analyze all preset scenarios."""
        scenarios = cls.get_preset_scenarios()
        results = []

        for scenario in scenarios:
            result = cls.analyze_scenario(db, scenario, baseline_forecast)
            results.append(result)

        # Sort by impact (highest first)
        results.sort(key=lambda x: x.impact, reverse=True)

        return results

    @classmethod
    def compare_scenarios(cls, results: list[ScenarioResult]) -> dict[str, Any]:
        """Compare scenarios and provide recommendations."""
        if not results:
            return {}

        # Find best scenario by various metrics
        best_roi = max(results, key=lambda x: x.roi)
        best_impact = max(results, key=lambda x: x.impact)
        best_confidence = max(results, key=lambda x: x.scenario.confidence)
        lowest_risk = min(results, key=lambda x: (1 if x.risk_rating == "high" else 0.5 if x.risk_rating == "medium" else 0))

        return {
            "total_scenarios": len(results),
            "best_roi": best_roi.scenario.name,
            "best_impact": best_impact.scenario.name,
            "highest_confidence": best_confidence.scenario.name,
            "lowest_risk": lowest_risk.scenario.name,
            "total_potential_impact": sum(r.impact for r in results),
            "average_confidence": sum(r.scenario.confidence for r in results) / len(results),
        }
