"""Metrics and observability endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends

from runner_api_routers.utils import _verify_api_key
from src.observability import (
    MetricsCollector,
    CrewMetricsCollector,
    HealthChecker,
    RequestTracer,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics", tags=["metrics"])
def get_metrics(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get current system metrics (counters, gauges, histograms)."""
    logger.info("Fetching system metrics")
    return MetricsCollector.get_snapshot()


@router.get("/metrics/prometheus", tags=["metrics"])
def get_metrics_prometheus(
    _: str | None = Depends(_verify_api_key),
) -> str:
    """Get metrics in Prometheus text format."""
    from src.observability import MetricsExporter

    logger.info("Fetching Prometheus format metrics")
    snapshot = MetricsCollector.get_snapshot()
    return MetricsExporter.to_prometheus_format(snapshot)


# Canonical GET /api/v1/health is owned by ui.api_health (status + service name).
# Observability aggregate/component checks live under /api/v1/system/health*.
@router.get("/system/health", tags=["health"])
def get_system_health() -> dict[str, Any]:
    """Get overall observability health status (component aggregate)."""
    logger.info("Fetching system health status")
    return HealthChecker.get_status()


@router.get("/system/health/{component}", tags=["health"])
def get_component_health(
    component: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get health status for a specific component."""
    logger.info(f"Fetching health status for {component}")
    return HealthChecker.get_status(component)


@router.get("/crew/executions", tags=["metrics"])
def get_crew_executions(
    crew: str | None = None,
    limit: int = 50,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get crew execution history and metrics."""
    logger.info(f"Fetching crew executions", extra={"crew": crew, "limit": limit})

    executions = CrewMetricsCollector.get_executions(crew, limit=limit)
    summary = CrewMetricsCollector.get_summary(crew)

    return {
        "ok": True,
        "crew": crew,
        "summary": summary,
        "executions": [e.to_dict() for e in executions],
    }


@router.get("/crew/summary", tags=["metrics"])
def get_crew_summary(
    crew: str | None = None,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get crew execution summary statistics."""
    logger.info(f"Fetching crew summary", extra={"crew": crew})

    summary = CrewMetricsCollector.get_summary(crew)
    return {
        "ok": True,
        "crew": crew,
        "summary": summary,
    }


@router.get("/trace/info", tags=["tracing"])
def get_trace_info(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get current request trace information."""
    request_id = RequestTracer.get_request_id()
    context = RequestTracer.get_context()
    duration_ms = RequestTracer.get_duration_ms()

    return {
        "ok": True,
        "request_id": request_id,
        "duration_ms": duration_ms,
        "context": context,
    }


@router.post("/metrics/reset", tags=["metrics"])
def reset_metrics(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Reset all metrics (admin operation)."""
    logger.warning("Resetting all metrics")
    MetricsCollector.reset()
    return {
        "ok": True,
        "message": "All metrics reset",
    }


@router.get("/status/summary", tags=["health"])
def get_status_summary(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get comprehensive status summary."""
    logger.info("Fetching comprehensive status summary")

    health = HealthChecker.get_status()
    metrics = MetricsCollector.get_snapshot()
    crew_summary = CrewMetricsCollector.get_summary()

    return {
        "ok": True,
        "timestamp": metrics["timestamp"],
        "uptime_seconds": metrics["uptime_seconds"],
        "health": health,
        "metrics": {
            "counters": metrics["counters"],
            "gauges": metrics["gauges"],
        },
        "crew_activity": crew_summary,
    }
