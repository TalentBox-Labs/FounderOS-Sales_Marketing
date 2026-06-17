"""Pre-built analytics dashboards for different roles."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class ExecutiveDashboard:
    """Executive/CEO dashboard - high-level metrics."""

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Get dashboard configuration."""
        return {
            "name": "Executive Dashboard",
            "dashboard_type": "executive",
            "widgets": [
                {
                    "name": "ARR Growth",
                    "metric_id": "arr_total",
                    "widget_type": "number",
                    "subtitle": "Annual Recurring Revenue",
                    "format": "currency",
                    "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "ARR vs Target",
                    "metric_id": "arr_vs_target",
                    "widget_type": "gauge",
                    "subtitle": "% of annual target",
                    "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Pipeline Value",
                    "metric_id": "pipeline_value",
                    "widget_type": "number",
                    "subtitle": "Total open opportunities",
                    "format": "currency",
                    "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Revenue Trend",
                    "metric_id": "monthly_revenue",
                    "widget_type": "line_chart",
                    "subtitle": "Last 12 months",
                    "position": {"x": 0, "y": 2, "width": 6, "height": 3},
                },
                {
                    "name": "Win Rate",
                    "metric_id": "win_rate",
                    "widget_type": "gauge",
                    "subtitle": "% deals closed",
                    "position": {"x": 6, "y": 2, "width": 3, "height": 2},
                },
                {
                    "name": "Customer Health",
                    "metric_id": "customer_health_score",
                    "widget_type": "gauge",
                    "subtitle": "Average account score",
                    "position": {"x": 9, "y": 2, "width": 3, "height": 2},
                },
                {
                    "name": "Revenue vs Forecast",
                    "metric_id": "revenue_vs_forecast",
                    "widget_type": "bar_chart",
                    "subtitle": "Actual vs predicted",
                    "position": {"x": 0, "y": 5, "width": 6, "height": 3},
                },
                {
                    "name": "Churn Rate",
                    "metric_id": "churn_rate",
                    "widget_type": "number",
                    "subtitle": "% monthly churn",
                    "format": "percentage",
                    "position": {"x": 6, "y": 5, "width": 3, "height": 2},
                },
                {
                    "name": "Top Risks",
                    "metric_id": "at_risk_accounts",
                    "widget_type": "table",
                    "subtitle": "Accounts at risk",
                    "position": {"x": 9, "y": 5, "width": 3, "height": 3},
                },
            ],
        }


class SalesDashboard:
    """Sales team dashboard - pipeline and deal metrics."""

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Get dashboard configuration."""
        return {
            "name": "Sales Dashboard",
            "dashboard_type": "sales",
            "widgets": [
                {
                    "name": "Pipeline by Stage",
                    "metric_id": "pipeline_by_stage",
                    "widget_type": "bar_chart",
                    "subtitle": "Opportunities in each stage",
                    "position": {"x": 0, "y": 0, "width": 6, "height": 3},
                },
                {
                    "name": "Quota Attainment",
                    "metric_id": "quota_attainment",
                    "widget_type": "table",
                    "subtitle": "% by sales rep",
                    "position": {"x": 6, "y": 0, "width": 6, "height": 3},
                },
                {
                    "name": "Deal Velocity",
                    "metric_id": "sales_cycle_duration",
                    "widget_type": "number",
                    "subtitle": "Avg days to close",
                    "format": "number",
                    "position": {"x": 0, "y": 3, "width": 3, "height": 2},
                },
                {
                    "name": "Win Rate",
                    "metric_id": "win_rate",
                    "widget_type": "gauge",
                    "subtitle": "Deals closed / total",
                    "position": {"x": 3, "y": 3, "width": 3, "height": 2},
                },
                {
                    "name": "Avg Deal Size",
                    "metric_id": "avg_deal_size",
                    "widget_type": "number",
                    "subtitle": "Average ARR value",
                    "format": "currency",
                    "position": {"x": 6, "y": 3, "width": 3, "height": 2},
                },
                {
                    "name": "Pipeline Coverage",
                    "metric_id": "pipeline_coverage",
                    "widget_type": "gauge",
                    "subtitle": "Pipeline / Quota ratio",
                    "position": {"x": 9, "y": 3, "width": 3, "height": 2},
                },
                {
                    "name": "Deals Closing This Month",
                    "metric_id": "deals_closing",
                    "widget_type": "table",
                    "subtitle": "Expected closes",
                    "position": {"x": 0, "y": 5, "width": 6, "height": 3},
                },
                {
                    "name": "Activity Metrics",
                    "metric_id": "activity_metrics",
                    "widget_type": "bar_chart",
                    "subtitle": "Calls, emails, meetings",
                    "position": {"x": 6, "y": 5, "width": 6, "height": 3},
                },
            ],
        }


class CSMDashboard:
    """Customer Success dashboard - health and retention."""

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Get dashboard configuration."""
        return {
            "name": "Customer Success Dashboard",
            "dashboard_type": "csm",
            "widgets": [
                {
                    "name": "Total Customers",
                    "metric_id": "customer_count",
                    "widget_type": "number",
                    "subtitle": "Active accounts",
                    "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Net Retention",
                    "metric_id": "net_retention_rate",
                    "widget_type": "gauge",
                    "subtitle": "% monthly retention",
                    "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Churn Risk",
                    "metric_id": "churn_risk_accounts",
                    "widget_type": "number",
                    "subtitle": "Accounts at risk",
                    "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Expansion Opportunities",
                    "metric_id": "expansion_opportunities",
                    "widget_type": "number",
                    "subtitle": "High-potential accounts",
                    "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Health Score Distribution",
                    "metric_id": "health_score_distribution",
                    "widget_type": "bar_chart",
                    "subtitle": "Accounts by health level",
                    "position": {"x": 0, "y": 2, "width": 6, "height": 3},
                },
                {
                    "name": "At-Risk Accounts",
                    "metric_id": "at_risk_details",
                    "widget_type": "table",
                    "subtitle": "Action required",
                    "position": {"x": 6, "y": 2, "width": 6, "height": 3},
                },
                {
                    "name": "NRR Trend",
                    "metric_id": "nrr_trend",
                    "widget_type": "line_chart",
                    "subtitle": "Last 12 months",
                    "position": {"x": 0, "y": 5, "width": 6, "height": 3},
                },
                {
                    "name": "Expansion Revenue",
                    "metric_id": "expansion_arr",
                    "widget_type": "number",
                    "subtitle": "From existing customers",
                    "format": "currency",
                    "position": {"x": 6, "y": 5, "width": 3, "height": 2},
                },
                {
                    "name": "Engagement Activities",
                    "metric_id": "engagement_activities",
                    "widget_type": "table",
                    "subtitle": "Recent customer touches",
                    "position": {"x": 9, "y": 5, "width": 3, "height": 3},
                },
            ],
        }


class MarketingDashboard:
    """Marketing dashboard - lead generation and campaign metrics."""

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Get dashboard configuration."""
        return {
            "name": "Marketing Dashboard",
            "dashboard_type": "marketing",
            "widgets": [
                {
                    "name": "Website Traffic",
                    "metric_id": "website_visitors",
                    "widget_type": "number",
                    "subtitle": "This month",
                    "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Lead Generation",
                    "metric_id": "leads_generated",
                    "widget_type": "number",
                    "subtitle": "New leads this month",
                    "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Lead Quality",
                    "metric_id": "qualified_leads",
                    "widget_type": "gauge",
                    "subtitle": "% qualified",
                    "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Cost per Lead",
                    "metric_id": "cost_per_lead",
                    "widget_type": "number",
                    "subtitle": "Average CAC",
                    "format": "currency",
                    "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Campaign Performance",
                    "metric_id": "campaign_performance",
                    "widget_type": "bar_chart",
                    "subtitle": "By campaign",
                    "position": {"x": 0, "y": 2, "width": 6, "height": 3},
                },
                {
                    "name": "Email Engagement",
                    "metric_id": "email_metrics",
                    "widget_type": "table",
                    "subtitle": "Open rate, CTR",
                    "position": {"x": 6, "y": 2, "width": 6, "height": 3},
                },
                {
                    "name": "Conversion Funnel",
                    "metric_id": "conversion_funnel",
                    "widget_type": "bar_chart",
                    "subtitle": "Visitor → Lead → Demo → Customer",
                    "position": {"x": 0, "y": 5, "width": 6, "height": 3},
                },
                {
                    "name": "Attribution",
                    "metric_id": "attribution_model",
                    "widget_type": "table",
                    "subtitle": "Revenue by source",
                    "position": {"x": 6, "y": 5, "width": 6, "height": 3},
                },
            ],
        }


class OperationsDashboard:
    """Operations dashboard - system health and automation metrics."""

    @staticmethod
    def get_definition() -> dict[str, Any]:
        """Get dashboard configuration."""
        return {
            "name": "Operations Dashboard",
            "dashboard_type": "operations",
            "widgets": [
                {
                    "name": "System Health",
                    "metric_id": "system_uptime",
                    "widget_type": "gauge",
                    "subtitle": "% uptime",
                    "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Automation Tasks",
                    "metric_id": "automation_tasks_completed",
                    "widget_type": "number",
                    "subtitle": "This month",
                    "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Automation Success Rate",
                    "metric_id": "automation_success_rate",
                    "widget_type": "gauge",
                    "subtitle": "% successful",
                    "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Data Freshness",
                    "metric_id": "data_freshness",
                    "widget_type": "number",
                    "subtitle": "Hours since last sync",
                    "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                },
                {
                    "name": "Agent Health",
                    "metric_id": "agent_health",
                    "widget_type": "table",
                    "subtitle": "Agent status",
                    "position": {"x": 0, "y": 2, "width": 6, "height": 3},
                },
                {
                    "name": "Workflow Performance",
                    "metric_id": "workflow_performance",
                    "widget_type": "bar_chart",
                    "subtitle": "Execution time by workflow",
                    "position": {"x": 6, "y": 2, "width": 6, "height": 3},
                },
                {
                    "name": "Data Quality",
                    "metric_id": "data_quality_score",
                    "widget_type": "gauge",
                    "subtitle": "% data completeness",
                    "position": {"x": 0, "y": 5, "width": 3, "height": 2},
                },
                {
                    "name": "Integration Status",
                    "metric_id": "integration_status",
                    "widget_type": "table",
                    "subtitle": "Connected systems",
                    "position": {"x": 3, "y": 5, "width": 3, "height": 2},
                },
                {
                    "name": "Error Log",
                    "metric_id": "error_log",
                    "widget_type": "table",
                    "subtitle": "Recent errors",
                    "position": {"x": 6, "y": 5, "width": 6, "height": 3},
                },
            ],
        }


class DashboardBuilder:
    """Build and deploy dashboards."""

    @staticmethod
    def get_all_dashboard_templates() -> dict[str, dict[str, Any]]:
        """Get all dashboard templates."""
        return {
            "executive": ExecutiveDashboard.get_definition(),
            "sales": SalesDashboard.get_definition(),
            "csm": CSMDashboard.get_definition(),
            "marketing": MarketingDashboard.get_definition(),
            "operations": OperationsDashboard.get_definition(),
        }

    @staticmethod
    def validate_dashboard_definition(definition: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate dashboard definition."""
        errors = []

        if "name" not in definition:
            errors.append("Missing 'name' field")

        if "widgets" not in definition:
            errors.append("Missing 'widgets' field")
        else:
            for i, widget in enumerate(definition["widgets"]):
                if "metric_id" not in widget:
                    errors.append(f"Widget {i}: Missing 'metric_id'")
                if "widget_type" not in widget:
                    errors.append(f"Widget {i}: Missing 'widget_type'")
                if "position" not in widget:
                    errors.append(f"Widget {i}: Missing 'position'")

        return len(errors) == 0, errors
