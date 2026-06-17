"""Reporting and analytics API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from revenue_os.database import SessionLocal
from revenue_os.reporting.reports import (
    ReportGenerator,
    ReportTemplate,
    ReportSection,
    ReportType,
    ReportFormat,
    ReportFrequency,
    ReportScheduler,
)
from revenue_os.reporting.delivery import ReportPublisher, ReportDeliveryManager

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reporting", tags=["reporting"])


@router.post("/templates/register", tags=["reporting"])
def register_report_template(
    template_data: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Register a report template."""
    logger.info(f"Registering report template: {template_data.get('name')}")

    try:
        sections = []
        for section_data in template_data.get("sections", []):
            section = ReportSection(
                title=section_data["title"],
                description=section_data["description"],
                data_source=section_data["data_source"],
                visualization=section_data.get("visualization"),
                parameters=section_data.get("parameters", {}),
            )
            sections.append(section)

        template = ReportTemplate(
            name=template_data["name"],
            report_type=ReportType(template_data["report_type"]),
            title=template_data["title"],
            description=template_data["description"],
            sections=sections,
            color_scheme=template_data.get("color_scheme", "professional"),
            logo_url=template_data.get("logo_url"),
            footer_text=template_data.get("footer_text"),
        )

        ReportGenerator.register_template(template)
        return {"ok": True, "message": f"Template '{template.name}' registered"}

    except Exception as e:
        logger.error(f"Failed to register template: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/templates", tags=["reporting"])
def list_report_templates(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all available report templates."""
    logger.info("Listing report templates")

    try:
        templates = ReportGenerator.list_templates()
        return {
            "ok": True,
            "count": len(templates),
            "templates": [t.to_dict() for t in templates],
        }
    except Exception as e:
        logger.error(f"Failed to list templates: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/generate", tags=["reporting"])
def generate_report(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Generate a report from a template."""
    logger.info(f"Generating report: {payload.get('template_name')}")

    try:
        from revenue_os.reporting.reports import ReportExporter

        format_str = payload.get("format", "html")
        format_enum = ReportFormat(format_str)

        report = ReportGenerator.generate_report(
            template_name=payload["template_name"],
            format=format_enum,
            data_context=payload.get("data_context", {}),
        )

        if not report:
            return {"ok": False, "error": "Failed to generate report"}

        # Export to requested format
        if format_enum == ReportFormat.HTML:
            content = ReportExporter.export_html(report)
            report.metadata["content"] = content
        elif format_enum == ReportFormat.CSV:
            content = ReportExporter.export_csv(report)
            report.metadata["content"] = content
        elif format_enum == ReportFormat.JSON:
            content = ReportExporter.export_json(report)
            report.metadata["content"] = content

        return {
            "ok": True,
            "report": report.to_dict(),
            "preview": str(report.metadata.get("content", ""))[:500],
        }

    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/schedules", tags=["reporting"])
def create_report_schedule(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a scheduled report."""
    logger.info(f"Creating report schedule: {payload.get('template_name')}")

    try:
        schedule = ReportScheduler.create_schedule(
            template_name=payload["template_name"],
            frequency=ReportFrequency(payload["frequency"]),
            format=ReportFormat(payload.get("format", "pdf")),
            recipients=payload.get("recipients", []),
            delivery_method=payload.get("delivery_method", "email"),
        )

        return {
            "ok": True,
            "schedule": schedule.to_dict(),
        }

    except Exception as e:
        logger.error(f"Failed to create schedule: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/schedules", tags=["reporting"])
def list_report_schedules(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all scheduled reports."""
    logger.info("Listing report schedules")

    try:
        schedules = ReportScheduler.list_schedules(enabled_only=False)
        return {
            "ok": True,
            "count": len(schedules),
            "schedules": [s.to_dict() for s in schedules],
        }

    except Exception as e:
        logger.error(f"Failed to list schedules: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/schedules/{schedule_id}/enable", tags=["reporting"])
def enable_report_schedule(
    schedule_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Enable a scheduled report."""
    logger.info(f"Enabling schedule: {schedule_id}")

    try:
        success = ReportScheduler.enable_schedule(schedule_id)
        return {
            "ok": success,
            "message": "Schedule enabled" if success else "Schedule not found",
        }

    except Exception as e:
        logger.error(f"Failed to enable schedule: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/schedules/{schedule_id}/disable", tags=["reporting"])
def disable_report_schedule(
    schedule_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Disable a scheduled report."""
    logger.info(f"Disabling schedule: {schedule_id}")

    try:
        success = ReportScheduler.disable_schedule(schedule_id)
        return {
            "ok": success,
            "message": "Schedule disabled" if success else "Schedule not found",
        }

    except Exception as e:
        logger.error(f"Failed to disable schedule: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.delete("/schedules/{schedule_id}", tags=["reporting"])
def delete_report_schedule(
    schedule_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Delete a scheduled report."""
    logger.info(f"Deleting schedule: {schedule_id}")

    try:
        success = ReportScheduler.delete_schedule(schedule_id)
        return {
            "ok": success,
            "message": "Schedule deleted" if success else "Schedule not found",
        }

    except Exception as e:
        logger.error(f"Failed to delete schedule: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/publish", tags=["reporting"])
def publish_report(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Publish a generated report to recipients."""
    logger.info(f"Publishing report: {payload.get('report_id')}")

    try:
        results = ReportPublisher.publish(
            report_id=payload["report_id"],
            recipients=payload.get("recipients", []),
            methods=payload.get("methods", ["email"]),
            html_content=payload.get("html_content", ""),
            pdf_content=payload.get("pdf_content"),
        )

        return {
            "ok": True,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Failed to publish report: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/deliveries/{report_id}", tags=["reporting"])
def get_report_deliveries(
    report_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get delivery status for a report."""
    logger.info(f"Getting deliveries for report: {report_id}")

    try:
        deliveries = ReportDeliveryManager.list_deliveries(report_id=report_id)
        return {
            "ok": True,
            "report_id": report_id,
            "count": len(deliveries),
            "deliveries": [d.to_dict() for d in deliveries],
        }

    except Exception as e:
        logger.error(f"Failed to get deliveries: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/health", tags=["reporting"])
def reporting_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get reporting system health."""
    logger.info("Checking reporting system health")

    templates = len(ReportGenerator.list_templates())
    schedules = len(ReportScheduler.list_schedules())

    return {
        "ok": True,
        "templates": templates,
        "schedules": schedules,
        "export_formats": ["html", "pdf", "csv", "xlsx", "json"],
        "status": "healthy",
    }
