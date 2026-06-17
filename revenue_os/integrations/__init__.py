"""Integration modules for external services."""

from revenue_os.integrations.email import EmailNotifier, EmailTemplate, ScheduledEmailQueue
from revenue_os.integrations.webhooks import WebhookManager, WebhookEventType, WebhookSubscription, WebhookDelivery
from revenue_os.integrations.slack import SlackNotifier, SlackMessage
from revenue_os.integrations.calendar import GoogleCalendarClient, OutlookCalendarClient, CalendarEvent

__all__ = [
    "EmailNotifier",
    "EmailTemplate",
    "ScheduledEmailQueue",
    "WebhookManager",
    "WebhookEventType",
    "WebhookSubscription",
    "WebhookDelivery",
    "SlackNotifier",
    "SlackMessage",
    "GoogleCalendarClient",
    "OutlookCalendarClient",
    "CalendarEvent",
]
