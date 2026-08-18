"""REV-ORCH M4 — tenant-scoped deterministic calendar executor.

Loads calendar credentials per organization. No global credential fallback.
AI does not call these functions directly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from revenue_os.integrations.calendar import CalendarEvent, GoogleCalendarClient, OutlookCalendarClient
from revenue_os.services.credentials_vault import load_credentials

logger = logging.getLogger(__name__)

CONNECTOR_GOOGLE = "google_calendar"
CONNECTOR_OUTLOOK = "outlook_calendar"


def resolve_calendar_connector(organization_id: str) -> tuple[str, dict[str, Any]] | None:
    """Resolve tenant-scoped calendar connector. No cross-tenant or global fallback."""
    for name in (CONNECTOR_GOOGLE, CONNECTOR_OUTLOOK):
        config = load_credentials(name, organization_id=organization_id, allow_global_fallback=False)
        if config:
            return name, config
    return None


def get_tenant_availability(
    organization_id: str,
    *,
    duration_minutes: int = 30,
    calendar_id: str | None = None,
) -> dict[str, Any]:
    """Read free slots through tenant-authorized calendar credentials."""
    resolved = resolve_calendar_connector(organization_id)
    if resolved is None:
        return {
            "ok": False,
            "reason": "No tenant-scoped calendar connector configured",
            "slots": [],
        }

    connector_name, config = resolved
    slots: list[tuple[datetime, datetime]] = []

    if connector_name == CONNECTOR_GOOGLE:
        GoogleCalendarClient.configure(config)
        slots = GoogleCalendarClient.get_free_slots(calendar_id or "primary", duration_minutes)
    elif connector_name == CONNECTOR_OUTLOOK:
        OutlookCalendarClient.configure(
            tenant_id=config.get("tenant_id", ""),
            access_token=config.get("access_token", ""),
        )
        slots = []

    normalized = [
        {
            "start": start.astimezone(timezone.utc).isoformat(),
            "end": end.astimezone(timezone.utc).isoformat(),
        }
        for start, end in slots
    ]

    return {
        "ok": True,
        "connector": connector_name,
        "organization_id": organization_id,
        "duration_minutes": duration_minutes,
        "slots": normalized,
    }


def revalidate_provider_slot(
    organization_id: str,
    start_time: datetime,
    end_time: datetime,
    *,
    calendar_id: str | None = None,
) -> dict[str, Any]:
    """Fail closed unless the selected slot is still free at the tenant calendar provider."""
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    start_time = start_time.astimezone(timezone.utc)
    end_time = end_time.astimezone(timezone.utc)
    if end_time <= start_time:
        return {"ok": False, "reason": "Invalid selected slot interval"}
    if start_time <= datetime.now(timezone.utc):
        return {"ok": False, "reason": "Selected slot is in the past — booking blocked"}

    resolved = resolve_calendar_connector(organization_id)
    if resolved is None:
        return {
            "ok": False,
            "reason": "No tenant-scoped calendar connector configured",
        }

    connector_name, config = resolved
    if connector_name == CONNECTOR_GOOGLE:
        GoogleCalendarClient.configure(config)
        try:
            conflict = GoogleCalendarClient.has_busy_overlap(
                calendar_id or "primary", start_time, end_time
            )
        except Exception:
            return {
                "ok": False,
                "reason": "Google Calendar slot revalidation failed closed",
                "connector": connector_name,
            }
        if conflict:
            return {
                "ok": False,
                "reason": "Selected slot is no longer available — booking blocked",
                "connector": connector_name,
            }
        return {"ok": True, "connector": connector_name}

    if connector_name == CONNECTOR_OUTLOOK:
        OutlookCalendarClient.configure(
            tenant_id=config.get("tenant_id", ""),
            access_token=config.get("access_token", ""),
        )
        return {
            "ok": False,
            "reason": (
                "Outlook availability cannot be confirmed at execution time — booking blocked"
            ),
            "connector": connector_name,
        }

    return {"ok": False, "reason": "Unknown calendar connector — booking blocked"}


def create_tenant_calendar_event(
    organization_id: str,
    *,
    title: str,
    description: str,
    start_time: datetime,
    end_time: datetime,
    attendees: list[str],
    location: str | None = None,
    calendar_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Create a calendar event using tenant-scoped credentials only."""
    resolved = resolve_calendar_connector(organization_id)
    if resolved is None:
        return {
            "ok": False,
            "reason": "No tenant-scoped calendar connector configured",
            "provider_event_id": None,
        }

    connector_name, config = resolved
    slot_check = revalidate_provider_slot(
        organization_id,
        start_time,
        end_time,
        calendar_id=calendar_id,
    )
    if not slot_check.get("ok"):
        return {
            "ok": False,
            "reason": slot_check.get("reason", "Selected slot is no longer available"),
            "provider_event_id": None,
            "connector": connector_name,
            "idempotency_key": idempotency_key,
        }

    event = CalendarEvent(
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        location=location,
        calendar_id=calendar_id,
    )

    provider_event_id: str | None = None
    if connector_name == CONNECTOR_GOOGLE:
        GoogleCalendarClient.configure(config)
        provider_event_id = GoogleCalendarClient.create_event(event)
    elif connector_name == CONNECTOR_OUTLOOK:
        OutlookCalendarClient.configure(
            tenant_id=config.get("tenant_id", ""),
            access_token=config.get("access_token", ""),
        )
        provider_event_id = OutlookCalendarClient.create_event(event)

    if provider_event_id is None:
        return {
            "ok": False,
            "reason": "Calendar provider failed to create event",
            "provider_event_id": None,
            "connector": connector_name,
            "idempotency_key": idempotency_key,
        }

    return {
        "ok": True,
        "provider_event_id": provider_event_id,
        "connector": connector_name,
        "organization_id": organization_id,
        "idempotency_key": idempotency_key,
        "meeting_url": event.location,
    }
