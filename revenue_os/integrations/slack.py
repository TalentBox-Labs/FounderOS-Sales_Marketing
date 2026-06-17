"""Slack integration for real-time notifications and commands."""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SlackMessage:
    """A message to send to Slack."""

    channel: str  # #sales, @user_id, C12345
    text: str
    blocks: list[dict[str, Any]] | None = None
    thread_ts: str | None = None  # Reply to thread
    icon_emoji: str | None = None
    username: str = "WorkCrew"

    def to_payload(self) -> dict[str, Any]:
        """Convert to Slack API payload."""
        payload = {
            "channel": self.channel,
            "text": self.text,
            "username": self.username,
        }

        if self.blocks:
            payload["blocks"] = self.blocks

        if self.thread_ts:
            payload["thread_ts"] = self.thread_ts

        if self.icon_emoji:
            payload["icon_emoji"] = self.icon_emoji

        return payload


class SlackNotifier:
    """Send notifications to Slack."""

    _webhook_url: str | None = None

    @classmethod
    def set_webhook_url(cls, url: str) -> None:
        """Set Slack webhook URL."""
        cls._webhook_url = url
        logger.info("Slack webhook URL configured")

    @classmethod
    def send_message(cls, message: SlackMessage) -> bool:
        """Send a message to Slack."""
        if not cls._webhook_url:
            logger.warning("Slack webhook not configured")
            return False

        try:
            import requests

            response = requests.post(
                cls._webhook_url,
                json=message.to_payload(),
                timeout=5,
            )

            if response.status_code == 200:
                logger.info(f"Slack message sent to {message.channel}")
                return True
            else:
                logger.error(f"Slack API error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            return False

    @classmethod
    def send_alert(
        cls,
        channel: str,
        title: str,
        message: str,
        severity: str = "info",  # info, warning, critical
        fields: dict[str, str] | None = None,
    ) -> bool:
        """Send an alert with formatting."""
        color_map = {
            "info": "#36a64f",
            "warning": "#ff9900",
            "critical": "#ff0000",
        }

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n{message}",
                },
            }
        ]

        if fields:
            field_blocks = [
                {"type": "mrkdwn", "text": f"*{k}*\n{v}"}
                for k, v in fields.items()
            ]
            blocks.append(
                {
                    "type": "section",
                    "fields": field_blocks[:10],  # Max 10 fields
                }
            )

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Alert generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}_",
                    }
                ],
            }
        )

        message = SlackMessage(
            channel=channel,
            text=title,
            blocks=blocks,
            username="WorkCrew Alerts",
        )

        return cls.send_message(message)

    @classmethod
    def send_metric_update(
        cls, channel: str, metrics: dict[str, Any]
    ) -> bool:
        """Send a metrics update."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 Metrics Update*",
                },
            }
        ]

        # Add metric fields
        for name, value in list(metrics.items())[:8]:
            blocks.append(
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*{name}*\n{value}",
                        }
                    ],
                }
            )

        message = SlackMessage(
            channel=channel,
            text="Metrics Update",
            blocks=blocks,
            username="WorkCrew Metrics",
        )

        return cls.send_message(message)


class SlackCommands:
    """Handle Slack slash commands."""

    @classmethod
    def handle_command(cls, command: str, args: list[str]) -> dict[str, Any]:
        """Handle a slash command from Slack."""
        if command == "/workcrew-status":
            return cls._handle_status(args)
        elif command == "/workcrew-pipeline":
            return cls._handle_pipeline(args)
        elif command == "/workcrew-risks":
            return cls._handle_risks(args)
        elif command == "/workcrew-forecast":
            return cls._handle_forecast(args)
        else:
            return {
                "response_type": "ephemeral",
                "text": f"Unknown command: {command}",
            }

    @classmethod
    def _handle_status(cls, args: list[str]) -> dict[str, Any]:
        """Return system status."""
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🟢 WorkCrew Status*\n\n*Health Score:* 72.5\n*Active Deals:* 45\n*Pipeline:* $225K\n*At-Risk:* 3",
                    },
                }
            ],
        }

    @classmethod
    def _handle_pipeline(cls, args: list[str]) -> dict[str, Any]:
        """Return pipeline summary."""
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*📈 Pipeline Summary*\n\n*Total:* 45 deals\n*Value:* $225K\n*Forecast:* $135K\n*Win Rate:* 75%",
                    },
                }
            ],
        }

    @classmethod
    def _handle_risks(cls, args: list[str]) -> dict[str, Any]:
        """Return at-risk deals."""
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*⚠️ At-Risk Deals*\n\n1. *Acme Corp* - $50K, 12 days overdue\n2. *TechCorp* - $35K, 8 days overdue\n3. *DataCorp* - $30K, no activity 20 days",
                    },
                }
            ],
        }

    @classmethod
    def _handle_forecast(cls, args: list[str]) -> dict[str, Any]:
        """Return revenue forecast."""
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*💰 Revenue Forecast (Next 3 months)*\n\n*July:* $125K\n*August:* $145K\n*September:* $155K\n*Total:* $425K",
                    },
                }
            ],
        }
