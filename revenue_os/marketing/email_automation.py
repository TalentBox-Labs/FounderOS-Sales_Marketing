"""Email marketing automation and lead nurturing system."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable
import uuid

logger = logging.getLogger(__name__)


class EmailSequenceType(Enum):
    """Email sequence types."""

    WELCOME = "welcome"
    NURTURE = "nurture"
    REENGAGEMENT = "reengagement"
    PRODUCT_ONBOARDING = "product_onboarding"
    EXPANSION = "expansion"
    CHURN_PREVENTION = "churn_prevention"
    CUSTOMER_SUCCESS = "customer_success"
    TRIAL_CONVERSION = "trial_conversion"


class EmailStatus(Enum):
    """Email send status."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class EmailTemplate:
    """Email template for sequences."""

    id: str
    name: str
    subject: str
    html_body: str
    text_body: str
    from_name: str = "WorkCrew Team"
    reply_to: str = "hello@workcrew.ai"
    variables: list[str] = field(default_factory=list)  # {{first_name}}, {{company}}, etc.
    cta_url: str | None = None
    cta_text: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "from_name": self.from_name,
            "cta_text": self.cta_text,
            "variables": self.variables,
        }


@dataclass
class EmailSequenceStep:
    """Single step in an email sequence."""

    id: str
    sequence_id: str
    step_number: int
    template_id: str
    delay_hours: int  # Hours after previous step
    conditions: dict[str, Any] = field(default_factory=dict)  # Trigger conditions
    a_b_test: bool = False
    variant_b_template_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "step_number": self.step_number,
            "delay_hours": self.delay_hours,
            "template_id": self.template_id,
            "a_b_test": self.a_b_test,
        }


@dataclass
class EmailSequence:
    """Email sequence for lead nurturing."""

    id: str
    name: str
    sequence_type: EmailSequenceType
    description: str
    steps: list[EmailSequenceStep] = field(default_factory=list)
    target_audience: dict[str, Any] = field(default_factory=dict)  # Segment filters
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success_metric: str = ""  # "demo_booked", "deal_created", etc.

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "sequence_type": self.sequence_type.value,
            "step_count": len(self.steps),
            "enabled": self.enabled,
            "success_metric": self.success_metric,
        }


@dataclass
class SubscriberEmail:
    """Individual email sent to subscriber."""

    id: str
    subscriber_id: str
    sequence_id: str
    step_id: str
    template_id: str
    email_address: str
    subject: str
    status: EmailStatus = EmailStatus.SCHEDULED
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    clicked_url: str | None = None
    bounce_reason: str | None = None
    open_count: int = 0
    click_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "subscriber_id": self.subscriber_id,
            "email_address": self.email_address,
            "status": self.status.value,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "opened": self.opened_at is not None,
            "clicked": self.clicked_at is not None,
            "open_count": self.open_count,
            "click_count": self.click_count,
        }


@dataclass
class LeadScore:
    """Lead scoring for prioritization."""

    subscriber_id: str
    email_score: int = 0  # Email engagement (0-30)
    website_score: int = 0  # Website behavior (0-30)
    firmographic_score: int = 0  # Company fit (0-20)
    temporal_score: int = 0  # Recency (0-20)
    total_score: int = 0  # Total (0-100)
    lead_grade: str = "C"  # A, B, C, D (A=ready to sell)
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subscriber_id": self.subscriber_id,
            "email_score": self.email_score,
            "website_score": self.website_score,
            "firmographic_score": self.firmographic_score,
            "temporal_score": self.temporal_score,
            "total_score": self.total_score,
            "lead_grade": self.lead_grade,
        }


class EmailSequenceManager:
    """Manage email sequences and nurturing."""

    _templates: dict[str, EmailTemplate] = {}
    _sequences: dict[str, EmailSequence] = {}
    _emails: dict[str, SubscriberEmail] = {}
    _lead_scores: dict[str, LeadScore] = {}

    @classmethod
    def register_template(cls, template: EmailTemplate) -> None:
        """Register an email template."""
        cls._templates[template.id] = template
        logger.info(f"Email template registered: {template.name}")

    @classmethod
    def get_template(cls, template_id: str) -> EmailTemplate | None:
        """Get template by ID."""
        return cls._templates.get(template_id)

    @classmethod
    def create_sequence(
        cls,
        name: str,
        sequence_type: EmailSequenceType,
        description: str,
        target_audience: dict[str, Any] | None = None,
        success_metric: str = "",
    ) -> EmailSequence:
        """Create an email sequence."""
        sequence = EmailSequence(
            id=str(uuid.uuid4()),
            name=name,
            sequence_type=sequence_type,
            description=description,
            target_audience=target_audience or {},
            success_metric=success_metric,
        )
        cls._sequences[sequence.id] = sequence
        logger.info(f"Email sequence created: {sequence.id} ({name})")
        return sequence

    @classmethod
    def add_sequence_step(
        cls,
        sequence_id: str,
        template_id: str,
        delay_hours: int,
        conditions: dict[str, Any] | None = None,
        a_b_test: bool = False,
        variant_b_template_id: str | None = None,
    ) -> EmailSequenceStep | None:
        """Add step to sequence."""
        sequence = cls._sequences.get(sequence_id)
        if not sequence:
            logger.error(f"Sequence not found: {sequence_id}")
            return None

        step = EmailSequenceStep(
            id=str(uuid.uuid4()),
            sequence_id=sequence_id,
            step_number=len(sequence.steps) + 1,
            template_id=template_id,
            delay_hours=delay_hours,
            conditions=conditions or {},
            a_b_test=a_b_test,
            variant_b_template_id=variant_b_template_id,
        )
        sequence.steps.append(step)
        logger.info(f"Step added to sequence: {sequence_id} - Step {step.step_number}")
        return step

    @classmethod
    def get_sequence(cls, sequence_id: str) -> EmailSequence | None:
        """Get sequence by ID."""
        return cls._sequences.get(sequence_id)

    @classmethod
    def enroll_subscriber(
        cls,
        subscriber_id: str,
        sequence_id: str,
        email_address: str,
        context: dict[str, Any] | None = None,
    ) -> list[SubscriberEmail]:
        """Enroll subscriber in sequence (creates all emails)."""
        sequence = cls.get_sequence(sequence_id)
        if not sequence:
            logger.error(f"Sequence not found: {sequence_id}")
            return []

        emails = []
        current_delay = 0

        for step in sequence.steps:
            template = cls.get_template(step.template_id)
            if not template:
                continue

            # Calculate send time
            scheduled_for = datetime.now(timezone.utc) + timedelta(hours=current_delay)

            email = SubscriberEmail(
                id=str(uuid.uuid4()),
                subscriber_id=subscriber_id,
                sequence_id=sequence_id,
                step_id=step.id,
                template_id=step.template_id,
                email_address=email_address,
                subject=template.subject,
                status=EmailStatus.SCHEDULED,
                scheduled_for=scheduled_for,
            )
            cls._emails[email.id] = email
            emails.append(email)

            current_delay += step.delay_hours

        logger.info(f"Subscriber enrolled: {subscriber_id} in sequence {sequence_id}")
        return emails

    @classmethod
    def mark_email_sent(cls, email_id: str, sent_at: datetime | None = None) -> bool:
        """Mark email as sent."""
        email = cls._emails.get(email_id)
        if email:
            email.status = EmailStatus.SENT
            email.sent_at = sent_at or datetime.now(timezone.utc)
            logger.info(f"Email marked sent: {email_id}")
            return True
        return False

    @classmethod
    def mark_email_opened(cls, email_id: str, opened_at: datetime | None = None) -> bool:
        """Mark email as opened."""
        email = cls._emails.get(email_id)
        if email:
            email.status = EmailStatus.OPENED
            email.opened_at = opened_at or datetime.now(timezone.utc)
            email.open_count += 1
            logger.info(f"Email opened: {email_id}")
            return True
        return False

    @classmethod
    def mark_email_clicked(
        cls, email_id: str, url: str, clicked_at: datetime | None = None
    ) -> bool:
        """Mark email link as clicked."""
        email = cls._emails.get(email_id)
        if email:
            email.status = EmailStatus.CLICKED
            email.clicked_at = clicked_at or datetime.now(timezone.utc)
            email.clicked_url = url
            email.click_count += 1
            logger.info(f"Email link clicked: {email_id} - {url}")
            return True
        return False

    @classmethod
    def get_sequence_metrics(cls, sequence_id: str) -> dict[str, Any]:
        """Get performance metrics for sequence."""
        sequence_emails = [e for e in cls._emails.values() if e.sequence_id == sequence_id]

        if not sequence_emails:
            return {}

        sent = [e for e in sequence_emails if e.sent_at]
        opened = [e for e in sequence_emails if e.opened_at]
        clicked = [e for e in sequence_emails if e.clicked_at]

        return {
            "sequence_id": sequence_id,
            "total_emails": len(sequence_emails),
            "sent_count": len(sent),
            "delivered_count": len([e for e in sequence_emails if e.status in (EmailStatus.DELIVERED, EmailStatus.OPENED, EmailStatus.CLICKED)]),
            "open_rate": (len(opened) / max(len(sent), 1)) * 100,
            "click_rate": (len(clicked) / max(len(sent), 1)) * 100,
            "avg_opens_per_email": sum(e.open_count for e in sequence_emails) / max(len(sequence_emails), 1),
            "avg_clicks_per_email": sum(e.click_count for e in sequence_emails) / max(len(sequence_emails), 1),
        }


class LeadScoringEngine:
    """Calculate lead scores for prioritization."""

    @classmethod
    def calculate_email_score(cls, subscriber_id: str, emails: list[SubscriberEmail]) -> int:
        """Calculate email engagement score (0-30)."""
        if not emails:
            return 0

        total_opens = sum(e.open_count for e in emails)
        total_clicks = sum(e.click_count for e in emails)

        # Score: 1 point per open (max 15), 2 points per click (max 15)
        open_score = min(total_opens, 15)
        click_score = min(total_clicks * 2, 15)

        return open_score + click_score

    @classmethod
    def calculate_firmographic_score(cls, company_data: dict[str, Any]) -> int:
        """Calculate company fit score (0-20)."""
        score = 0

        # Company size: target 100-5000 employees
        employees = company_data.get("employees", 0)
        if 100 <= employees <= 5000:
            score += 8
        elif 50 <= employees < 100 or 5000 < employees <= 10000:
            score += 5

        # Industry: SaaS, FinTech, Enterprise
        industry = company_data.get("industry", "").lower()
        if any(x in industry for x in ["saas", "software", "fintech", "finance"]):
            score += 7
        elif any(x in industry for x in ["services", "consulting", "enterprise"]):
            score += 5

        # ARR: higher = better fit
        arr = company_data.get("arr", 0)
        if arr > 1000000:
            score += 5
        elif arr > 100000:
            score += 3

        return min(score, 20)

    @classmethod
    def calculate_temporal_score(cls, last_engagement: datetime) -> int:
        """Calculate recency score (0-20)."""
        if not last_engagement:
            return 0

        days_since = (datetime.now(timezone.utc) - last_engagement).days

        if days_since <= 1:
            return 20
        elif days_since <= 7:
            return 15
        elif days_since <= 30:
            return 10
        elif days_since <= 60:
            return 5
        else:
            return 0

    @classmethod
    def calculate_overall_score(
        cls,
        subscriber_id: str,
        emails: list[SubscriberEmail],
        company_data: dict[str, Any] | None = None,
        last_engagement: datetime | None = None,
    ) -> LeadScore:
        """Calculate overall lead score."""
        email_score = cls.calculate_email_score(subscriber_id, emails)
        firmographic_score = cls.calculate_firmographic_score(company_data or {})
        temporal_score = cls.calculate_temporal_score(last_engagement) if last_engagement else 0

        total = email_score + firmographic_score + temporal_score

        # Determine grade
        if total >= 80:
            grade = "A"
        elif total >= 60:
            grade = "B"
        elif total >= 40:
            grade = "C"
        else:
            grade = "D"

        score = LeadScore(
            subscriber_id=subscriber_id,
            email_score=email_score,
            firmographic_score=firmographic_score,
            temporal_score=temporal_score,
            total_score=total,
            lead_grade=grade,
        )

        return score


class BehaviorTriggerEngine:
    """Trigger actions based on subscriber behavior."""

    _triggers: dict[str, Callable] = {}

    @classmethod
    def register_trigger(cls, trigger_name: str, handler: Callable) -> None:
        """Register a behavior trigger."""
        cls._triggers[trigger_name] = handler
        logger.info(f"Behavior trigger registered: {trigger_name}")

    @classmethod
    def trigger_email_opened(
        cls, subscriber_id: str, email_id: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle email open event."""
        results = []

        # Check all registered triggers
        for trigger_name, handler in cls._triggers.items():
            if "open" in trigger_name.lower():
                try:
                    result = handler(subscriber_id=subscriber_id, event_type="email_opened", context=context)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Trigger {trigger_name} failed: {str(e)}")

        return {
            "event": "email_opened",
            "subscriber_id": subscriber_id,
            "email_id": email_id,
            "triggers_executed": len(results),
        }

    @classmethod
    def trigger_email_clicked(
        cls, subscriber_id: str, email_id: str, url: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle email click event."""
        results = []

        for trigger_name, handler in cls._triggers.items():
            if "click" in trigger_name.lower():
                try:
                    result = handler(
                        subscriber_id=subscriber_id,
                        event_type="email_clicked",
                        url=url,
                        context=context,
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Trigger {trigger_name} failed: {str(e)}")

        return {
            "event": "email_clicked",
            "subscriber_id": subscriber_id,
            "email_id": email_id,
            "url": url,
            "triggers_executed": len(results),
        }

    @classmethod
    def trigger_sequence_completed(
        cls, subscriber_id: str, sequence_id: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle sequence completion."""
        results = []

        for trigger_name, handler in cls._triggers.items():
            if "complete" in trigger_name.lower():
                try:
                    result = handler(
                        subscriber_id=subscriber_id,
                        event_type="sequence_completed",
                        sequence_id=sequence_id,
                        context=context,
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Trigger {trigger_name} failed: {str(e)}")

        return {
            "event": "sequence_completed",
            "subscriber_id": subscriber_id,
            "sequence_id": sequence_id,
            "triggers_executed": len(results),
        }
