"""Webhook system for external event subscriptions."""

from __future__ import annotations

import logging
import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Expected by revenue_os.main (include_router). CMS webhook HTTP routes live in
# runner_api_routers/integrations.py; this export unblocks revenue_os.main:app.
router = APIRouter(prefix="/api/v1/integrations/webhooks", tags=["webhooks"])


class WebhookEventType(Enum):
    """Webhook event types."""

    DEAL_CREATED = "deal.created"
    DEAL_UPDATED = "deal.updated"
    DEAL_CLOSED = "deal.closed"
    CONTACT_CREATED = "contact.created"
    CONTACT_UPDATED = "contact.updated"
    CONTACT_SCORED = "contact.scored"
    ACCOUNT_HEALTH_CHANGED = "account.health_changed"
    ACCOUNT_AT_RISK = "account.at_risk"
    FORECAST_UPDATED = "forecast.updated"
    CHURN_PREDICTED = "churn.predicted"


@dataclass
class WebhookSubscription:
    """Webhook subscription."""

    id: str
    url: str
    events: list[WebhookEventType]
    secret: str
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered: datetime | None = None
    failure_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def sign_payload(self, payload: dict[str, Any]) -> str:
        """Create HMAC signature for payload."""
        body = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "events": [e.value for e in self.events],
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "failure_count": self.failure_count,
            "metadata": self.metadata,
        }


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt."""

    id: str
    subscription_id: str
    event_type: WebhookEventType
    payload: dict[str, Any]
    status_code: int | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: datetime | None = None
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "event_type": self.event_type.value,
            "status_code": self.status_code,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "attempts": self.attempts,
        }


class WebhookManager:
    """Manage webhooks and deliveries."""

    _subscriptions: dict[str, WebhookSubscription] = {}
    _deliveries: dict[str, WebhookDelivery] = {}
    _failed_deliveries: list[WebhookDelivery] = []

    @classmethod
    def create_subscription(
        cls,
        url: str,
        events: list[WebhookEventType],
        metadata: dict[str, Any] | None = None,
    ) -> WebhookSubscription:
        """Create a new webhook subscription."""
        subscription = WebhookSubscription(
            id=str(uuid.uuid4()),
            url=url,
            events=events,
            secret=secrets.token_urlsafe(32),
            metadata=metadata or {},
        )
        cls._subscriptions[subscription.id] = subscription
        logger.info(
            f"Webhook subscription created: {subscription.id}",
            extra={"url": url, "events": len(events)},
        )
        return subscription

    @classmethod
    def delete_subscription(cls, subscription_id: str) -> bool:
        """Delete a webhook subscription."""
        if subscription_id in cls._subscriptions:
            del cls._subscriptions[subscription_id]
            logger.info(f"Webhook subscription deleted: {subscription_id}")
            return True
        return False

    @classmethod
    def get_subscription(cls, subscription_id: str) -> WebhookSubscription | None:
        """Get a subscription by ID."""
        return cls._subscriptions.get(subscription_id)

    @classmethod
    def list_subscriptions(cls, active_only: bool = True) -> list[WebhookSubscription]:
        """List all subscriptions."""
        subs = cls._subscriptions.values()
        if active_only:
            subs = [s for s in subs if s.active]
        return list(subs)

    @classmethod
    def dispatch_event(cls, event_type: WebhookEventType, payload: dict[str, Any]) -> list[str]:
        """Dispatch event to matching subscriptions."""
        dispatched = []

        for subscription in cls._subscriptions.values():
            if not subscription.active:
                continue

            if event_type not in subscription.events:
                continue

            delivery = WebhookDelivery(
                id=str(uuid.uuid4()),
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
            )
            cls._deliveries[delivery.id] = delivery
            cls._queue_delivery(delivery, subscription)
            dispatched.append(subscription.id)

        logger.info(
            f"Event dispatched to {len(dispatched)} subscriptions",
            extra={"event_type": event_type.value},
        )
        return dispatched

    @classmethod
    def _queue_delivery(cls, delivery: WebhookDelivery, subscription: WebhookSubscription) -> None:
        """Queue delivery attempt."""
        import threading

        thread = threading.Thread(
            target=cls._deliver_webhook,
            args=(delivery, subscription),
            daemon=True,
        )
        thread.start()

    @classmethod
    def _deliver_webhook(
        cls, delivery: WebhookDelivery, subscription: WebhookSubscription
    ) -> None:
        """Attempt to deliver webhook."""
        import requests
        import time

        max_attempts = 3
        delivery.attempts = 0

        while delivery.attempts < max_attempts:
            delivery.attempts += 1

            try:
                payload = {
                    "event": delivery.event_type.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": delivery.payload,
                    "delivery_id": delivery.id,
                }

                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": subscription.sign_payload(payload),
                    "X-Webhook-ID": subscription.id,
                    "X-Delivery-ID": delivery.id,
                }

                response = requests.post(
                    subscription.url,
                    json=payload,
                    headers=headers,
                    timeout=10,
                )

                delivery.status_code = response.status_code
                if response.status_code in (200, 201, 204):
                    delivery.delivered_at = datetime.now(timezone.utc)
                    subscription.last_triggered = datetime.now(timezone.utc)
                    subscription.failure_count = 0
                    logger.info(
                        f"Webhook delivered successfully",
                        extra={"subscription_id": subscription.id, "delivery_id": delivery.id},
                    )
                    return

                logger.warning(
                    f"Webhook delivery failed",
                    extra={
                        "subscription_id": subscription.id,
                        "status_code": response.status_code,
                        "attempt": delivery.attempts,
                    },
                )

            except Exception as e:
                delivery.error = str(e)
                logger.error(
                    f"Webhook delivery error",
                    extra={
                        "subscription_id": subscription.id,
                        "error": str(e),
                        "attempt": delivery.attempts,
                    },
                )

            if delivery.attempts < max_attempts:
                time.sleep(2 ** delivery.attempts)

        delivery.error = "Max delivery attempts exceeded"
        subscription.failure_count += 1
        cls._failed_deliveries.append(delivery)
        logger.error(
            f"Webhook delivery failed permanently",
            extra={"subscription_id": subscription.id},
        )

    @classmethod
    def get_delivery(cls, delivery_id: str) -> WebhookDelivery | None:
        """Get delivery by ID."""
        return cls._deliveries.get(delivery_id)

    @classmethod
    def get_failed_deliveries(cls) -> list[WebhookDelivery]:
        """Get all failed deliveries."""
        return cls._failed_deliveries.copy()

    @classmethod
    def retry_failed_delivery(cls, delivery_id: str) -> bool:
        """Retry a failed delivery."""
        delivery = cls._deliveries.get(delivery_id)
        subscription = cls._subscriptions.get(delivery.subscription_id) if delivery else None

        if not delivery or not subscription:
            return False

        delivery.attempts = 0
        delivery.delivered_at = None
        delivery.error = None

        cls._queue_delivery(delivery, subscription)
        logger.info(f"Webhook delivery retry queued: {delivery_id}")
        return True
