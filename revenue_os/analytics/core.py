"""Data analytics and business intelligence core."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types."""

    REVENUE = "revenue"
    COUNT = "count"
    PERCENTAGE = "percentage"
    TIME = "time"
    RATIO = "ratio"
    CUSTOM = "custom"


class DashboardType(Enum):
    """Dashboard types."""

    EXECUTIVE = "executive"
    SALES = "sales"
    CSM = "csm"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCIAL = "financial"
    CUSTOM = "custom"


class ReportFrequency(Enum):
    """Report generation frequency."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"


@dataclass
class AnalyticsMetric:
    """Single analytics metric."""

    id: str
    name: str
    metric_type: MetricType
    calculation: str  # Formula or query
    unit: str  # "$", "%", "days", etc.
    description: str
    target_value: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "metric_type": self.metric_type.value,
            "unit": self.unit,
            "description": self.description,
            "target_value": self.target_value,
        }


@dataclass
class DashboardWidget:
    """Widget for dashboard."""

    id: str
    name: str
    metric_id: str
    widget_type: str  # "line_chart", "bar_chart", "gauge", "table", "number"
    position: dict[str, int]  # x, y, width, height
    refresh_interval: int = 3600  # seconds
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "metric_id": self.metric_id,
            "widget_type": self.widget_type,
            "position": self.position,
        }


@dataclass
class Dashboard:
    """Analytics dashboard."""

    id: str
    name: str
    dashboard_type: DashboardType
    description: str
    widgets: list[DashboardWidget] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    owner: str = ""
    shared_with: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "dashboard_type": self.dashboard_type.value,
            "widget_count": len(self.widgets),
            "owner": self.owner,
        }


@dataclass
class AnalyticsReport:
    """Generated analytics report."""

    id: str
    name: str
    report_type: str  # "pipeline", "revenue", "customer_health", etc.
    frequency: ReportFrequency
    recipients: list[str]  # emails
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "report_type": self.report_type,
            "frequency": self.frequency.value,
            "generated_at": self.generated_at.isoformat(),
            "metric_count": len(self.metrics),
            "insight_count": len(self.insights),
        }


@dataclass
class DataPoint:
    """Single data point for time series."""

    timestamp: datetime
    metric_id: str
    value: float
    dimension: str | None = None  # For grouping (stage, region, team, etc.)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_id": self.metric_id,
            "value": self.value,
            "dimension": self.dimension,
        }


class AnalyticsEngine:
    """Core analytics engine."""

    _metrics: dict[str, AnalyticsMetric] = {}
    _dashboards: dict[str, Dashboard] = {}
    _reports: dict[str, AnalyticsReport] = {}
    _data_points: list[DataPoint] = []

    @classmethod
    def register_metric(cls, metric: AnalyticsMetric) -> None:
        """Register a metric."""
        cls._metrics[metric.id] = metric
        logger.info(f"Metric registered: {metric.id} ({metric.name})")

    @classmethod
    def get_metric(cls, metric_id: str) -> AnalyticsMetric | None:
        """Get metric by ID."""
        return cls._metrics.get(metric_id)

    @classmethod
    def list_metrics(cls, metric_type: MetricType | None = None) -> list[AnalyticsMetric]:
        """List all metrics."""
        metrics = cls._metrics.values()
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        return list(metrics)

    @classmethod
    def create_dashboard(
        cls,
        name: str,
        dashboard_type: DashboardType,
        description: str,
        owner: str = "admin",
    ) -> Dashboard:
        """Create a dashboard."""
        dashboard = Dashboard(
            id=str(uuid.uuid4()),
            name=name,
            dashboard_type=dashboard_type,
            description=description,
            owner=owner,
        )
        cls._dashboards[dashboard.id] = dashboard
        logger.info(f"Dashboard created: {dashboard.id} ({name})")
        return dashboard

    @classmethod
    def add_widget_to_dashboard(
        cls,
        dashboard_id: str,
        metric_id: str,
        widget_name: str,
        widget_type: str,
        position: dict[str, int],
    ) -> DashboardWidget | None:
        """Add widget to dashboard."""
        dashboard = cls._dashboards.get(dashboard_id)
        if not dashboard:
            logger.error(f"Dashboard not found: {dashboard_id}")
            return None

        widget = DashboardWidget(
            id=str(uuid.uuid4()),
            name=widget_name,
            metric_id=metric_id,
            widget_type=widget_type,
            position=position,
        )
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.now(timezone.utc)
        logger.info(f"Widget added to dashboard: {dashboard_id} - {widget.name}")
        return widget

    @classmethod
    def get_dashboard(cls, dashboard_id: str) -> Dashboard | None:
        """Get dashboard by ID."""
        return cls._dashboards.get(dashboard_id)

    @classmethod
    def list_dashboards(cls, dashboard_type: DashboardType | None = None) -> list[Dashboard]:
        """List dashboards."""
        dashboards = cls._dashboards.values()
        if dashboard_type:
            dashboards = [d for d in dashboards if d.dashboard_type == dashboard_type]
        return list(dashboards)

    @classmethod
    def record_data_point(
        cls,
        metric_id: str,
        value: float,
        dimension: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DataPoint:
        """Record a data point."""
        data_point = DataPoint(
            timestamp=datetime.now(timezone.utc),
            metric_id=metric_id,
            value=value,
            dimension=dimension,
            metadata=metadata or {},
        )
        cls._data_points.append(data_point)
        return data_point

    @classmethod
    def get_metric_data(
        cls,
        metric_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        dimension: str | None = None,
    ) -> list[DataPoint]:
        """Get data points for a metric."""
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        data = [
            p for p in cls._data_points
            if p.metric_id == metric_id
            and start_date <= p.timestamp <= end_date
        ]

        if dimension:
            data = [p for p in data if p.dimension == dimension]

        return data

    @classmethod
    def create_report(
        cls,
        name: str,
        report_type: str,
        frequency: ReportFrequency,
        recipients: list[str],
        metrics: dict[str, Any] | None = None,
    ) -> AnalyticsReport:
        """Create a report."""
        report = AnalyticsReport(
            id=str(uuid.uuid4()),
            name=name,
            report_type=report_type,
            frequency=frequency,
            recipients=recipients,
            metrics=metrics or {},
        )
        cls._reports[report.id] = report
        logger.info(f"Report created: {report.id} ({name})")
        return report

    @classmethod
    def get_report(cls, report_id: str) -> AnalyticsReport | None:
        """Get report by ID."""
        return cls._reports.get(report_id)

    @classmethod
    def list_reports(cls, report_type: str | None = None) -> list[AnalyticsReport]:
        """List reports."""
        reports = cls._reports.values()
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        return list(reports)


class DimensionalAnalytics:
    """Analyze data across dimensions (team, stage, region, etc.)."""

    @classmethod
    def aggregate_by_dimension(
        cls,
        data_points: list[DataPoint],
        dimension: str,
        aggregation: str = "sum",
    ) -> dict[str, float]:
        """Aggregate data points by dimension."""
        result = {}

        for point in data_points:
            if point.dimension:
                dim_value = point.metadata.get(dimension, point.dimension)
                if dim_value not in result:
                    result[dim_value] = []
                result[dim_value].append(point.value)

        # Apply aggregation
        aggregated = {}
        for dim, values in result.items():
            if aggregation == "sum":
                aggregated[dim] = sum(values)
            elif aggregation == "avg":
                aggregated[dim] = sum(values) / len(values)
            elif aggregation == "max":
                aggregated[dim] = max(values)
            elif aggregation == "min":
                aggregated[dim] = min(values)
            elif aggregation == "count":
                aggregated[dim] = len(values)

        return aggregated

    @classmethod
    def compare_periods(
        cls,
        current_data: list[DataPoint],
        previous_data: list[DataPoint],
        aggregation: str = "sum",
    ) -> dict[str, Any]:
        """Compare two time periods."""
        current_sum = sum(p.value for p in current_data)
        previous_sum = sum(p.value for p in previous_data)

        if previous_sum == 0:
            pct_change = 0
        else:
            pct_change = ((current_sum - previous_sum) / previous_sum) * 100

        return {
            "current_period": current_sum,
            "previous_period": previous_sum,
            "absolute_change": current_sum - previous_sum,
            "percent_change": pct_change,
            "trend": "up" if pct_change > 0 else "down" if pct_change < 0 else "flat",
        }

    @classmethod
    def calculate_cohort_metrics(
        cls,
        data_points: list[DataPoint],
        cohort_dimension: str,
    ) -> dict[str, dict[str, float]]:
        """Calculate metrics by cohort."""
        cohorts = {}

        for point in data_points:
            cohort_value = point.metadata.get(cohort_dimension, "unknown")
            if cohort_value not in cohorts:
                cohorts[cohort_value] = {
                    "count": 0,
                    "sum": 0,
                    "max": float('-inf'),
                    "min": float('inf'),
                }

            cohorts[cohort_value]["count"] += 1
            cohorts[cohort_value]["sum"] += point.value
            cohorts[cohort_value]["max"] = max(cohorts[cohort_value]["max"], point.value)
            cohorts[cohort_value]["min"] = min(cohorts[cohort_value]["min"], point.value)

        # Calculate averages
        for cohort in cohorts.values():
            if cohort["count"] > 0:
                cohort["avg"] = cohort["sum"] / cohort["count"]

        return cohorts


class TrendAnalysis:
    """Analyze trends in metrics."""

    @classmethod
    def detect_trend(cls, data_points: list[DataPoint]) -> str:
        """Detect trend (up, down, flat)."""
        if len(data_points) < 2:
            return "insufficient_data"

        # Sort by timestamp
        sorted_data = sorted(data_points, key=lambda x: x.timestamp)

        first_half = sorted_data[:len(sorted_data)//2]
        second_half = sorted_data[len(sorted_data)//2:]

        first_avg = sum(p.value for p in first_half) / len(first_half)
        second_avg = sum(p.value for p in second_half) / len(second_half)

        if second_avg > first_avg * 1.05:
            return "up"
        elif second_avg < first_avg * 0.95:
            return "down"
        else:
            return "flat"

    @classmethod
    def forecast_linear(cls, data_points: list[DataPoint], periods_ahead: int = 1) -> list[float]:
        """Simple linear forecast."""
        if len(data_points) < 2:
            return []

        sorted_data = sorted(data_points, key=lambda x: x.timestamp)
        values = [p.value for p in sorted_data]

        # Simple linear regression
        n = len(values)
        x = list(range(n))
        y = values

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return [y_mean] * periods_ahead

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Forecast
        forecast = []
        for i in range(1, periods_ahead + 1):
            forecast_value = slope * (n + i) + intercept
            forecast.append(max(0, forecast_value))  # No negative values

        return forecast

    @classmethod
    def anomaly_detection(
        cls,
        data_points: list[DataPoint],
        threshold_std: float = 2.0,
    ) -> list[DataPoint]:
        """Detect anomalies using standard deviation."""
        if len(data_points) < 10:
            return []

        values = [p.value for p in data_points]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5

        anomalies = []
        for point in data_points:
            if abs(point.value - mean) > threshold_std * std_dev:
                anomalies.append(point)

        return anomalies
