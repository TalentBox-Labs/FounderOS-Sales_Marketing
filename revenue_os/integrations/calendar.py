"""Calendar integration for Google Calendar and Outlook."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CalendarProvider(Enum):
    """Supported calendar providers."""

    GOOGLE = "google"
    OUTLOOK = "outlook"


@dataclass
class CalendarEvent:
    """Calendar event."""

    title: str
    description: str
    start_time: datetime
    end_time: datetime
    attendees: list[str]
    location: str | None = None
    calendar_id: str | None = None
    provider_event_id: str | None = None
    organizer_email: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "attendees": self.attendees,
            "location": self.location,
            "calendar_id": self.calendar_id,
            "provider_event_id": self.provider_event_id,
            "organizer_email": self.organizer_email,
        }


class GoogleCalendarClient:
    """Google Calendar integration."""

    _credentials: dict[str, Any] | None = None
    _calendar_service: Any = None

    @classmethod
    def configure(cls, credentials: dict[str, Any]) -> None:
        """Configure Google Calendar client."""
        cls._credentials = credentials
        logger.info("Google Calendar configured")

    @classmethod
    def create_event(cls, event: CalendarEvent) -> str | None:
        """Create an event on Google Calendar."""
        if not cls._credentials:
            logger.warning("Google Calendar not configured")
            return None

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            credentials = Credentials.from_service_account_info(cls._credentials)
            service = build("calendar", "v3", credentials=credentials)

            body = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "UTC",
                },
                "attendees": [{"email": email} for email in event.attendees],
            }

            if event.location:
                body["location"] = event.location

            calendar_id = event.calendar_id or "primary"
            result = service.events().insert(calendarId=calendar_id, body=body).execute()

            event.provider_event_id = result.get("id")
            logger.info(
                f"Google Calendar event created: {event.provider_event_id}",
                extra={"title": event.title},
            )
            return result.get("id")

        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {str(e)}")
            return None

    @classmethod
    def update_event(cls, event: CalendarEvent) -> bool:
        """Update an event on Google Calendar."""
        if not cls._credentials or not event.provider_event_id:
            logger.warning("Google Calendar not configured or event_id missing")
            return False

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            credentials = Credentials.from_service_account_info(cls._credentials)
            service = build("calendar", "v3", credentials=credentials)

            body = {
                "summary": event.title,
                "description": event.description,
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "UTC",
                },
                "attendees": [{"email": email} for email in event.attendees],
            }

            if event.location:
                body["location"] = event.location

            calendar_id = event.calendar_id or "primary"
            service.events().update(
                calendarId=calendar_id,
                eventId=event.provider_event_id,
                body=body,
            ).execute()

            logger.info(f"Google Calendar event updated: {event.provider_event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {str(e)}")
            return False

    @classmethod
    def delete_event(cls, calendar_id: str, event_id: str) -> bool:
        """Delete an event from Google Calendar."""
        if not cls._credentials:
            logger.warning("Google Calendar not configured")
            return False

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            credentials = Credentials.from_service_account_info(cls._credentials)
            service = build("calendar", "v3", credentials=credentials)

            service.events().delete(calendarId=calendar_id or "primary", eventId=event_id).execute()

            logger.info(f"Google Calendar event deleted: {event_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {str(e)}")
            return False

    @classmethod
    def get_free_slots(cls, calendar_id: str, duration_minutes: int = 60) -> list[tuple[datetime, datetime]]:
        """Get free time slots on calendar."""
        if not cls._credentials:
            logger.warning("Google Calendar not configured")
            return []

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            credentials = Credentials.from_service_account_info(cls._credentials)
            service = build("calendar", "v3", credentials=credentials)

            now = datetime.now(timezone.utc)
            end = now + timedelta(days=7)

            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id or "primary",
                    timeMin=now.isoformat(),
                    timeMax=end.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            busy_slots = []

            for event in events:
                start = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(event["end"]["dateTime"].replace("Z", "+00:00"))
                busy_slots.append((start, end))

            free_slots = []
            current = now
            while current < end:
                slot_end = current + timedelta(minutes=duration_minutes)
                is_free = True

                for busy_start, busy_end in busy_slots:
                    if (current < busy_end and slot_end > busy_start):
                        is_free = False
                        current = busy_end
                        break

                if is_free:
                    free_slots.append((current, slot_end))
                    current = slot_end

            logger.info(f"Found {len(free_slots)} free slots")
            return free_slots

        except Exception as e:
            logger.error(f"Failed to get free slots: {str(e)}")
            return []

    @classmethod
    def has_busy_overlap(
        cls,
        calendar_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """Return True if any event overlaps [start_time, end_time). Fail closed on error."""
        if not cls._credentials:
            raise RuntimeError("Google Calendar not configured — cannot revalidate slot")
        if start_time.tzinfo is None or end_time.tzinfo is None:
            raise ValueError("Slot revalidation requires timezone-aware timestamps")
        if end_time <= start_time:
            raise ValueError("Invalid slot interval for revalidation")

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            credentials = Credentials.from_service_account_info(cls._credentials)
            service = build("calendar", "v3", credentials=credentials)
            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id or "primary",
                    timeMin=start_time.isoformat(),
                    timeMax=end_time.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            for event in events_result.get("items", []):
                raw_start = (event.get("start") or {}).get("dateTime")
                raw_end = (event.get("end") or {}).get("dateTime")
                if not raw_start or not raw_end:
                    return True
                busy_start = datetime.fromisoformat(raw_start.replace("Z", "+00:00"))
                busy_end = datetime.fromisoformat(raw_end.replace("Z", "+00:00"))
                if start_time < busy_end and end_time > busy_start:
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to revalidate Google Calendar slot: {str(e)}")
            raise RuntimeError("Google Calendar slot revalidation failed closed") from e


class OutlookCalendarClient:
    """Outlook/Office 365 Calendar integration."""

    _access_token: str | None = None
    _tenant_id: str | None = None

    @classmethod
    def configure(cls, tenant_id: str, access_token: str) -> None:
        """Configure Outlook Calendar client."""
        cls._tenant_id = tenant_id
        cls._access_token = access_token
        logger.info("Outlook Calendar configured")

    @classmethod
    def create_event(cls, event: CalendarEvent) -> str | None:
        """Create an event on Outlook Calendar."""
        if not cls._access_token:
            logger.warning("Outlook Calendar not configured")
            return None

        try:
            import requests

            headers = {
                "Authorization": f"Bearer {cls._access_token}",
                "Content-Type": "application/json",
            }

            body = {
                "subject": event.title,
                "bodyPreview": event.description,
                "body": {
                    "contentType": "HTML",
                    "content": event.description,
                },
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "UTC",
                },
                "attendees": [
                    {
                        "emailAddress": {"address": email},
                        "type": "required",
                    }
                    for email in event.attendees
                ],
            }

            if event.location:
                body["location"] = {"displayName": event.location}

            response = requests.post(
                "https://graph.microsoft.com/v1.0/me/events",
                headers=headers,
                json=body,
                timeout=10,
            )

            if response.status_code == 201:
                result = response.json()
                event.provider_event_id = result.get("id")
                logger.info(f"Outlook event created: {event.provider_event_id}")
                return result.get("id")
            else:
                logger.error(f"Outlook event creation failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to create Outlook event: {str(e)}")
            return None

    @classmethod
    def update_event(cls, event: CalendarEvent) -> bool:
        """Update an event on Outlook Calendar."""
        if not cls._access_token or not event.provider_event_id:
            logger.warning("Outlook Calendar not configured or event_id missing")
            return False

        try:
            import requests

            headers = {
                "Authorization": f"Bearer {cls._access_token}",
                "Content-Type": "application/json",
            }

            body = {
                "subject": event.title,
                "body": {
                    "contentType": "HTML",
                    "content": event.description,
                },
                "start": {
                    "dateTime": event.start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": event.end_time.isoformat(),
                    "timeZone": "UTC",
                },
                "attendees": [
                    {
                        "emailAddress": {"address": email},
                        "type": "required",
                    }
                    for email in event.attendees
                ],
            }

            response = requests.patch(
                f"https://graph.microsoft.com/v1.0/me/events/{event.provider_event_id}",
                headers=headers,
                json=body,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info(f"Outlook event updated: {event.provider_event_id}")
                return True
            else:
                logger.error(f"Outlook event update failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to update Outlook event: {str(e)}")
            return False

    @classmethod
    def delete_event(cls, event_id: str) -> bool:
        """Delete an event from Outlook Calendar."""
        if not cls._access_token:
            logger.warning("Outlook Calendar not configured")
            return False

        try:
            import requests

            headers = {"Authorization": f"Bearer {cls._access_token}"}

            response = requests.delete(
                f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 204:
                logger.info(f"Outlook event deleted: {event_id}")
                return True
            else:
                logger.error(f"Outlook event deletion failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete Outlook event: {str(e)}")
            return False
