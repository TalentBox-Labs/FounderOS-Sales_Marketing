"""Report generation and scheduling system."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Report types."""

    EXECUTIVE_BRIEFING = "executive_briefing"
    SALES_PIPELINE = "sales_pipeline"
    CUSTOMER_HEALTH = "customer_health"
    REVENUE_FORECAST = "revenue_forecast"
    CHURN_RISK = "churn_risk"
    TEAM_PERFORMANCE = "team_performance"
    EXPANSION_OPPORTUNITIES = "expansion_opportunities"
    WEEKLY_DIGEST = "weekly_digest"
    MONTHLY_REVIEW = "monthly_review"
    CUSTOM = "custom"


class ReportFormat(Enum):
    """Output formats."""

    PDF = "pdf"
    HTML = "html"
    CSV = "csv"
    EXCEL = "xlsx"
    JSON = "json"


class ReportFrequency(Enum):
    """Scheduling frequency."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ONCE = "once"


@dataclass
class ReportSection:
    """Report section definition."""

    title: str
    description: str
    data_source: str  # kpi, insight, metric, forecast, etc.
    visualization: str | None = None  # chart, table, list, etc.
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "data_source": self.data_source,
            "visualization": self.visualization,
            "parameters": self.parameters,
        }


@dataclass
class ReportTemplate:
    """Report template definition."""

    name: str
    report_type: ReportType
    title: str
    description: str
    sections: list[ReportSection]
    color_scheme: str = "professional"  # professional, colorful, minimal
    logo_url: str | None = None
    footer_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "report_type": self.report_type.value,
            "title": self.title,
            "description": self.description,
            "sections": [s.to_dict() for s in self.sections],
            "color_scheme": self.color_scheme,
            "logo_url": self.logo_url,
            "footer_text": self.footer_text,
        }


@dataclass
class ScheduledReport:
    """Scheduled report definition."""

    id: str
    template_name: str
    frequency: ReportFrequency
    format: ReportFormat
    recipients: list[str]  # emails or Slack channels
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_sent: datetime | None = None
    next_send: datetime | None = None
    delivery_method: str = "email"  # email, slack, both
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "template_name": self.template_name,
            "frequency": self.frequency.value,
            "format": self.format.value,
            "recipients": self.recipients,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_sent": self.last_sent.isoformat() if self.last_sent else None,
            "next_send": self.next_send.isoformat() if self.next_send else None,
            "delivery_method": self.delivery_method,
        }


@dataclass
class Report:
    """Generated report."""

    id: str
    template_name: str
    report_type: ReportType
    format: ReportFormat
    title: str
    sections: list[dict[str, Any]]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    file_path: str | None = None
    file_size: int | None = None
    s3_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "template_name": self.template_name,
            "report_type": self.report_type.value,
            "format": self.format.value,
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "file_path": self.file_path,
            "file_size": self.file_size,
            "s3_url": self.s3_url,
        }


class ReportGenerator:
    """Generate reports from templates."""

    _templates: dict[str, ReportTemplate] = {}

    @classmethod
    def register_template(cls, template: ReportTemplate) -> None:
        """Register a report template."""
        cls._templates[template.name] = template
        logger.info(f"Report template registered: {template.name}")

    @classmethod
    def get_template(cls, name: str) -> ReportTemplate | None:
        """Get template by name."""
        return cls._templates.get(name)

    @classmethod
    def list_templates(cls) -> list[ReportTemplate]:
        """List all templates."""
        return list(cls._templates.values())

    @classmethod
    def generate_report(
        cls,
        template_name: str,
        format: ReportFormat = ReportFormat.HTML,
        data_context: dict[str, Any] | None = None,
    ) -> Report | None:
        """Generate report from template."""
        template = cls.get_template(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return None

        try:
            sections = []
            for section in template.sections:
                section_data = {
                    "title": section.title,
                    "description": section.description,
                    "data_source": section.data_source,
                    "visualization": section.visualization,
                    "content": cls._fetch_section_data(
                        section.data_source,
                        section.parameters,
                        data_context or {},
                    ),
                }
                sections.append(section_data)

            report = Report(
                id=str(uuid.uuid4()),
                template_name=template_name,
                report_type=template.report_type,
                format=format,
                title=template.title,
                sections=sections,
                metadata={
                    "color_scheme": template.color_scheme,
                    "logo_url": template.logo_url,
                    "footer_text": template.footer_text,
                },
            )

            logger.info(f"Report generated: {report.id}")
            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return None

    @classmethod
    def _fetch_section_data(
        cls,
        data_source: str,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Fetch data for a report section."""
        if data_source == "kpi":
            return cls._get_kpi_data(parameters, context)
        elif data_source == "insight":
            return cls._get_insight_data(parameters, context)
        elif data_source == "metric":
            return cls._get_metric_data(parameters, context)
        elif data_source == "forecast":
            return cls._get_forecast_data(parameters, context)
        elif data_source == "table":
            return cls._get_table_data(parameters, context)
        else:
            return {"error": f"Unknown data source: {data_source}"}

    @classmethod
    def _get_kpi_data(cls, parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Get KPI data."""
        return {
            "kpis": context.get("kpis", []),
            "period": parameters.get("period", "monthly"),
        }

    @classmethod
    def _get_insight_data(
        cls, parameters: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Get insight data."""
        return {
            "insights": context.get("insights", []),
            "category": parameters.get("category", "all"),
        }

    @classmethod
    def _get_metric_data(cls, parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Get metric data."""
        return {
            "metrics": context.get("metrics", []),
            "time_period": parameters.get("time_period", "7d"),
        }

    @classmethod
    def _get_forecast_data(
        cls, parameters: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Get forecast data."""
        return {
            "forecast": context.get("forecast", {}),
            "months": parameters.get("months", 3),
        }

    @classmethod
    def _get_table_data(cls, parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Get table data."""
        return {
            "rows": context.get("rows", []),
            "columns": parameters.get("columns", []),
        }


class ReportScheduler:
    """Manage scheduled reports."""

    _schedules: dict[str, ScheduledReport] = {}

    @classmethod
    def create_schedule(
        cls,
        template_name: str,
        frequency: ReportFrequency,
        format: ReportFormat,
        recipients: list[str],
        delivery_method: str = "email",
    ) -> ScheduledReport:
        """Create a new scheduled report."""
        schedule = ScheduledReport(
            id=str(uuid.uuid4()),
            template_name=template_name,
            frequency=frequency,
            format=format,
            recipients=recipients,
            delivery_method=delivery_method,
        )
        cls._schedules[schedule.id] = schedule
        logger.info(f"Report schedule created: {schedule.id}")
        return schedule

    @classmethod
    def get_schedule(cls, schedule_id: str) -> ScheduledReport | None:
        """Get schedule by ID."""
        return cls._schedules.get(schedule_id)

    @classmethod
    def list_schedules(cls, enabled_only: bool = True) -> list[ScheduledReport]:
        """List all schedules."""
        schedules = cls._schedules.values()
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        return list(schedules)

    @classmethod
    def delete_schedule(cls, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in cls._schedules:
            del cls._schedules[schedule_id]
            logger.info(f"Report schedule deleted: {schedule_id}")
            return True
        return False

    @classmethod
    def enable_schedule(cls, schedule_id: str) -> bool:
        """Enable a schedule."""
        schedule = cls.get_schedule(schedule_id)
        if schedule:
            schedule.enabled = True
            logger.info(f"Report schedule enabled: {schedule_id}")
            return True
        return False

    @classmethod
    def disable_schedule(cls, schedule_id: str) -> bool:
        """Disable a schedule."""
        schedule = cls.get_schedule(schedule_id)
        if schedule:
            schedule.enabled = False
            logger.info(f"Report schedule disabled: {schedule_id}")
            return True
        return False


class ReportExporter:
    """Export reports to different formats."""

    @classmethod
    def export_html(cls, report: Report) -> str | None:
        """Export report to HTML."""
        try:
            html_parts = []
            html_parts.append(f"<!DOCTYPE html>")
            html_parts.append(f"<html><head>")
            html_parts.append(f"<title>{report.title}</title>")
            html_parts.append(f"<style>")
            html_parts.append(cls._get_css_styling(report.metadata.get("color_scheme", "professional")))
            html_parts.append(f"</style>")
            html_parts.append(f"</head><body>")

            if report.metadata.get("logo_url"):
                html_parts.append(f'<img src="{report.metadata["logo_url"]}" class="logo" />')

            html_parts.append(f"<h1>{report.title}</h1>")
            html_parts.append(f"<p class=\"timestamp\">Generated: {report.generated_at.isoformat()}</p>")

            for section in report.sections:
                html_parts.append(f"<section>")
                html_parts.append(f"<h2>{section['title']}</h2>")
                html_parts.append(f"<p>{section['description']}</p>")
                html_parts.append(f"<div class=\"content\">{section['content']}</div>")
                html_parts.append(f"</section>")

            if report.metadata.get("footer_text"):
                html_parts.append(f"<footer>{report.metadata['footer_text']}</footer>")

            html_parts.append(f"</body></html>")
            return "\n".join(html_parts)

        except Exception as e:
            logger.error(f"Failed to export HTML: {str(e)}")
            return None

    @classmethod
    def export_pdf(cls, report: Report, html_content: str) -> bytes | None:
        """Export report to PDF."""
        try:
            from weasyprint import HTML
            import io

            pdf_file = io.BytesIO()
            HTML(string=html_content).write_pdf(pdf_file)
            return pdf_file.getvalue()

        except Exception as e:
            logger.error(f"Failed to export PDF: {str(e)}")
            return None

    @classmethod
    def export_csv(cls, report: Report) -> str | None:
        """Export report to CSV."""
        try:
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow([report.title])
            writer.writerow([f"Generated: {report.generated_at.isoformat()}"])
            writer.writerow([])

            for section in report.sections:
                writer.writerow([section["title"]])
                writer.writerow([section["description"]])
                # Write section content as rows
                if isinstance(section.get("content"), list):
                    for item in section["content"]:
                        writer.writerow([str(item)])
                writer.writerow([])

            return output.getvalue()

        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")
            return None

    @classmethod
    def export_json(cls, report: Report) -> str | None:
        """Export report to JSON."""
        try:
            import json

            data = report.to_dict()
            data["sections"] = report.sections
            return json.dumps(data, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to export JSON: {str(e)}")
            return None

    @classmethod
    def _get_css_styling(cls, scheme: str) -> str:
        """Get CSS styling for color scheme."""
        if scheme == "colorful":
            return """
            body { font-family: Arial, sans-serif; color: #333; background: #f5f5f5; }
            h1 { color: #2196F3; border-bottom: 3px solid #2196F3; padding-bottom: 10px; }
            h2 { color: #1976D2; }
            section { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .timestamp { color: #666; font-size: 12px; }
            .logo { max-width: 200px; margin-bottom: 20px; }
            footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }
            """
        else:  # professional or minimal
            return """
            body { font-family: 'Times New Roman', serif; color: #000; background: white; line-height: 1.6; }
            h1 { color: #000; border-bottom: 1px solid #000; padding-bottom: 10px; }
            h2 { color: #333; margin-top: 30px; }
            section { margin: 30px 0; page-break-inside: avoid; }
            .timestamp { color: #666; font-size: 11px; margin-bottom: 20px; }
            .logo { max-width: 150px; margin-bottom: 30px; }
            footer { margin-top: 60px; padding-top: 10px; border-top: 1px solid #ccc; color: #666; font-size: 10px; }
            """
