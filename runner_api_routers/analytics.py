"""Analytics and business intelligence API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from revenue_os.analytics.core import (
    AnalyticsEngine,
    AnalyticsMetric,
    Dashboard,
    DashboardType,
    DimensionalAnalytics,
    MetricType,
    ReportFrequency,
    TrendAnalysis,
)
from revenue_os.analytics.dashboards import DashboardBuilder
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


# ── Request/Response Models ──────────────────────────────────────────────────


class MetricDefinition(BaseModel):
    """Define a new metric."""

    name: str = Field(..., description="Metric name")
    metric_type: str = Field(..., description="Type: revenue, count, percentage, time, ratio, custom")
    calculation: str = Field(..., description="Formula or calculation method")
    unit: str = Field(..., description="Unit of measurement ($, %, days, etc.)")
    description: str = Field(..., description="Metric description")
    target_value: float | None = Field(None, description="Target value")


class DataPointRecording(BaseModel):
    """Record a data point."""

    metric_id: str = Field(..., description="Metric ID")
    value: float = Field(..., description="Data value")
    dimension: str | None = Field(None, description="Dimension for grouping")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DashboardDefinition(BaseModel):
    """Define a dashboard."""

    name: str = Field(..., description="Dashboard name")
    dashboard_type: str = Field(..., description="Dashboard type")
    description: str = Field(..., description="Dashboard description")
    owner: str = Field("admin", description="Dashboard owner")


class WidgetDefinition(BaseModel):
    """Add widget to dashboard."""

    metric_id: str = Field(..., description="Metric ID")
    widget_name: str = Field(..., description="Widget name")
    widget_type: str = Field(..., description="Widget type: line_chart, bar_chart, gauge, table, number")
    position: dict[str, int] = Field(..., description="Position: x, y, width, height")


class ReportDefinition(BaseModel):
    """Create analytics report."""

    name: str = Field(..., description="Report name")
    report_type: str = Field(..., description="Report type: pipeline, revenue, customer_health, etc.")
    frequency: str = Field(..., description="Frequency: hourly, daily, weekly, monthly, quarterly, yearly, on_demand")
    recipients: list[str] = Field(..., description="Email recipients")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Metrics to include")


class AggregationRequest(BaseModel):
    """Aggregate data by dimension."""

    metric_id: str = Field(..., description="Metric ID")
    dimension: str = Field(..., description="Dimension to aggregate by")
    aggregation: str = Field("sum", description="Aggregation type: sum, avg, max, min, count")
    start_date: datetime | None = Field(None, description="Start date")
    end_date: datetime | None = Field(None, description="End date")


class ComparisonRequest(BaseModel):
    """Compare two time periods."""

    metric_id: str = Field(..., description="Metric ID")
    current_start: datetime = Field(..., description="Current period start")
    current_end: datetime = Field(..., description="Current period end")
    previous_start: datetime = Field(..., description="Previous period start")
    previous_end: datetime = Field(..., description="Previous period end")


class ForecastRequest(BaseModel):
    """Forecast metric values."""

    metric_id: str = Field(..., description="Metric ID")
    periods_ahead: int = Field(3, description="Number of periods to forecast")
    start_date: datetime | None = Field(None, description="Start date for historical data")
    end_date: datetime | None = Field(None, description="End date for historical data")


# ── Metric Management ────────────────────────────────────────────────────────


@router.post("/metrics", response_model=dict[str, Any])
async def create_metric(
    metric: MetricDefinition,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a new metric."""
    try:
        metric_type = MetricType[metric.metric_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid metric_type: {metric.metric_type}")

    try:
        analytics_metric = AnalyticsMetric(
            id=f"metric_{datetime.now(timezone.utc).timestamp()}",
            name=metric.name,
            metric_type=metric_type,
            calculation=metric.calculation,
            unit=metric.unit,
            description=metric.description,
            target_value=metric.target_value,
        )
        AnalyticsEngine.register_metric(analytics_metric)
        logger.info(f"Metric created: {analytics_metric.id}")
        return {
            "success": True,
            "metric_id": analytics_metric.id,
            "metric": analytics_metric.to_dict(),
        }
    except Exception as e:
        logger.error(f"Error creating metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def list_metrics(
    metric_type: str | None = Query(None, description="Filter by metric type"),
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all metrics."""
    try:
        filter_type = None
        if metric_type:
            try:
                filter_type = MetricType[metric_type.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid metric_type: {metric_type}")

        metrics = AnalyticsEngine.list_metrics(filter_type)
        return {
            "success": True,
            "count": len(metrics),
            "metrics": [m.to_dict() for m in metrics],
        }
    except Exception as e:
        logger.error(f"Error listing metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{metric_id}")
async def get_metric(
    metric_id: str,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get metric by ID."""
    try:
        metric = AnalyticsEngine.get_metric(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {metric_id}")
        return {
            "success": True,
            "metric": metric.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Data Recording ───────────────────────────────────────────────────────────


@router.post("/data-points")
async def record_data_point(
    point: DataPointRecording,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Record a data point for a metric."""
    try:
        metric = AnalyticsEngine.get_metric(point.metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {point.metric_id}")

        data_point = AnalyticsEngine.record_data_point(
            metric_id=point.metric_id,
            value=point.value,
            dimension=point.dimension,
            metadata=point.metadata,
        )
        logger.info(f"Data point recorded for metric: {point.metric_id}")
        return {
            "success": True,
            "data_point": data_point.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording data point: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metric-data/{metric_id}")
async def get_metric_data(
    metric_id: str,
    start_date: datetime | None = Query(None, description="Start date (ISO format)"),
    end_date: datetime | None = Query(None, description="End date (ISO format)"),
    dimension: str | None = Query(None, description="Filter by dimension"),
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get metric data points."""
    try:
        metric = AnalyticsEngine.get_metric(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {metric_id}")

        data = AnalyticsEngine.get_metric_data(
            metric_id=metric_id,
            start_date=start_date,
            end_date=end_date,
            dimension=dimension,
        )
        return {
            "success": True,
            "count": len(data),
            "data_points": [p.to_dict() for p in data],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Dashboard Management ─────────────────────────────────────────────────────


@router.get("/dashboards/templates")
async def get_dashboard_templates(
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get all pre-built dashboard templates."""
    try:
        templates = DashboardBuilder.get_all_dashboard_templates()
        return {
            "success": True,
            "count": len(templates),
            "templates": templates,
        }
    except Exception as e:
        logger.error(f"Error getting dashboard templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboards")
async def create_dashboard(
    dashboard: DashboardDefinition,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a new dashboard."""
    try:
        dashboard_type = DashboardType[dashboard.dashboard_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid dashboard_type: {dashboard.dashboard_type}")

    try:
        dash = AnalyticsEngine.create_dashboard(
            name=dashboard.name,
            dashboard_type=dashboard_type,
            description=dashboard.description,
            owner=dashboard.owner,
        )
        logger.info(f"Dashboard created: {dash.id}")
        return {
            "success": True,
            "dashboard_id": dash.id,
            "dashboard": dash.to_dict(),
        }
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards")
async def list_dashboards(
    dashboard_type: str | None = Query(None, description="Filter by dashboard type"),
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all dashboards."""
    try:
        filter_type = None
        if dashboard_type:
            try:
                filter_type = DashboardType[dashboard_type.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid dashboard_type: {dashboard_type}")

        dashboards = AnalyticsEngine.list_dashboards(filter_type)
        return {
            "success": True,
            "count": len(dashboards),
            "dashboards": [d.to_dict() for d in dashboards],
        }
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get dashboard by ID."""
    try:
        dashboard = AnalyticsEngine.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail=f"Dashboard not found: {dashboard_id}")

        return {
            "success": True,
            "dashboard": dashboard.to_dict(),
            "widget_count": len(dashboard.widgets),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboards/{dashboard_id}/widgets")
async def add_widget(
    dashboard_id: str,
    widget: WidgetDefinition,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Add widget to dashboard."""
    try:
        dashboard = AnalyticsEngine.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail=f"Dashboard not found: {dashboard_id}")

        metric = AnalyticsEngine.get_metric(widget.metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {widget.metric_id}")

        dash_widget = AnalyticsEngine.add_widget_to_dashboard(
            dashboard_id=dashboard_id,
            metric_id=widget.metric_id,
            widget_name=widget.widget_name,
            widget_type=widget.widget_type,
            position=widget.position,
        )

        if not dash_widget:
            raise HTTPException(status_code=500, detail="Failed to add widget")

        logger.info(f"Widget added to dashboard: {dashboard_id}")
        return {
            "success": True,
            "widget_id": dash_widget.id,
            "widget": dash_widget.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Report Management ────────────────────────────────────────────────────────


@router.post("/reports")
async def create_report(
    report: ReportDefinition,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a new analytics report."""
    try:
        frequency = ReportFrequency[report.frequency.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid frequency: {report.frequency}")

    try:
        analytics_report = AnalyticsEngine.create_report(
            name=report.name,
            report_type=report.report_type,
            frequency=frequency,
            recipients=report.recipients,
            metrics=report.metrics,
        )
        logger.info(f"Report created: {analytics_report.id}")
        return {
            "success": True,
            "report_id": analytics_report.id,
            "report": analytics_report.to_dict(),
        }
    except Exception as e:
        logger.error(f"Error creating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def list_reports(
    report_type: str | None = Query(None, description="Filter by report type"),
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all reports."""
    try:
        reports = AnalyticsEngine.list_reports(report_type)
        return {
            "success": True,
            "count": len(reports),
            "reports": [r.to_dict() for r in reports],
        }
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get report by ID."""
    try:
        report = AnalyticsEngine.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

        return {
            "success": True,
            "report": report.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Analytics Operations ─────────────────────────────────────────────────────


@router.post("/aggregate")
async def aggregate_by_dimension(
    request: AggregationRequest,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Aggregate metric data by dimension."""
    try:
        metric = AnalyticsEngine.get_metric(request.metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {request.metric_id}")

        data = AnalyticsEngine.get_metric_data(
            metric_id=request.metric_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        aggregated = DimensionalAnalytics.aggregate_by_dimension(
            data,
            request.dimension,
            request.aggregation,
        )

        logger.info(f"Data aggregated for metric: {request.metric_id}")
        return {
            "success": True,
            "metric_id": request.metric_id,
            "dimension": request.dimension,
            "aggregation": request.aggregation,
            "results": aggregated,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aggregating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-periods")
async def compare_periods(
    request: ComparisonRequest,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Compare metric values across two time periods."""
    try:
        metric = AnalyticsEngine.get_metric(request.metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {request.metric_id}")

        current_data = AnalyticsEngine.get_metric_data(
            metric_id=request.metric_id,
            start_date=request.current_start,
            end_date=request.current_end,
        )

        previous_data = AnalyticsEngine.get_metric_data(
            metric_id=request.metric_id,
            start_date=request.previous_start,
            end_date=request.previous_end,
        )

        comparison = DimensionalAnalytics.compare_periods(current_data, previous_data)

        logger.info(f"Periods compared for metric: {request.metric_id}")
        return {
            "success": True,
            "metric_id": request.metric_id,
            "comparison": comparison,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing periods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{metric_id}")
async def detect_trend(
    metric_id: str,
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Detect trend for metric."""
    try:
        metric = AnalyticsEngine.get_metric(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {metric_id}")

        data = AnalyticsEngine.get_metric_data(
            metric_id=metric_id,
            start_date=start_date,
            end_date=end_date,
        )

        trend = TrendAnalysis.detect_trend(data)

        logger.info(f"Trend detected for metric: {metric_id}")
        return {
            "success": True,
            "metric_id": metric_id,
            "trend": trend,
            "data_points": len(data),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast")
async def forecast_metric(
    request: ForecastRequest,
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Forecast metric values."""
    try:
        metric = AnalyticsEngine.get_metric(request.metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {request.metric_id}")

        data = AnalyticsEngine.get_metric_data(
            metric_id=request.metric_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        forecast = TrendAnalysis.forecast_linear(data, request.periods_ahead)

        logger.info(f"Forecast generated for metric: {request.metric_id}")
        return {
            "success": True,
            "metric_id": request.metric_id,
            "periods_ahead": request.periods_ahead,
            "forecast": forecast,
            "data_points_used": len(data),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forecasting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomalies")
async def detect_anomalies(
    metric_id: str = Query(..., description="Metric ID"),
    threshold_std: float = Query(2.0, description="Standard deviation threshold"),
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Detect anomalies in metric data."""
    try:
        metric = AnalyticsEngine.get_metric(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail=f"Metric not found: {metric_id}")

        data = AnalyticsEngine.get_metric_data(
            metric_id=metric_id,
            start_date=start_date,
            end_date=end_date,
        )

        anomalies = TrendAnalysis.anomaly_detection(data, threshold_std)

        logger.info(f"Anomaly detection completed for metric: {metric_id}")
        return {
            "success": True,
            "metric_id": metric_id,
            "anomaly_count": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies],
            "total_data_points": len(data),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Health Check ─────────────────────────────────────────────────────────────


@router.get("/health")
async def analytics_health(
    api_key: str = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Analytics system health check."""
    try:
        metrics_count = len(AnalyticsEngine.list_metrics())
        dashboards_count = len(AnalyticsEngine.list_dashboards())
        reports_count = len(AnalyticsEngine.list_reports())

        return {
            "success": True,
            "status": "healthy",
            "metrics_registered": metrics_count,
            "dashboards_created": dashboards_count,
            "reports_created": reports_count,
        }
    except Exception as e:
        logger.error(f"Error getting analytics health: {e}")
        raise HTTPException(status_code=500, detail=str(e))
