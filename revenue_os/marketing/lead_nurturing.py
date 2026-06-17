"""Lead nurturing campaigns and workflow management."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class CampaignStatus(Enum):
    """Campaign status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class NurtureTrack(Enum):
    """Nurture track based on profile."""

    COLD_PROSPECT = "cold_prospect"
    WARM_LEAD = "warm_lead"
    ENGAGED_PROSPECT = "engaged_prospect"
    TRIAL_USER = "trial_user"
    CUSTOMER = "customer"
    EXPANSION = "expansion"
    AT_RISK = "at_risk"


@dataclass
class NurtureCampaign:
    """Lead nurturing campaign."""

    id: str
    name: str
    description: str
    track: NurtureTrack
    sequences: list[str]  # Sequence IDs in order
    enrollment_criteria: dict[str, Any]  # Conditions for auto-enrollment
    status: CampaignStatus = CampaignStatus.DRAFT
    success_criteria: str = ""  # What constitutes success
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    ended_at: datetime | None = None
    enrollments: int = 0
    conversions: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "track": self.track.value,
            "status": self.status.value,
            "sequence_count": len(self.sequences),
            "enrollments": self.enrollments,
            "conversions": self.conversions,
            "conversion_rate": (self.conversions / max(self.enrollments, 1)) * 100,
        }


@dataclass
class SubscriberProfile:
    """Detailed subscriber profile for segmentation."""

    id: str
    email: str
    first_name: str
    last_name: str
    company: str
    job_title: str
    industry: str
    company_size: str
    phone: str | None = None
    current_track: NurtureTrack = NurtureTrack.COLD_PROSPECT
    lead_score: int = 0
    engagement_level: str = "low"  # low, medium, high
    website_visits: int = 0
    email_opens: int = 0
    email_clicks: int = 0
    last_engagement: datetime | None = None
    enrolled_campaigns: list[str] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "name": f"{self.first_name} {self.last_name}",
            "company": self.company,
            "job_title": self.job_title,
            "current_track": self.current_track.value,
            "lead_score": self.lead_score,
            "engagement_level": self.engagement_level,
        }


@dataclass
class PrebuiltSequence:
    """Pre-built email sequence template."""

    id: str
    name: str
    track: NurtureTrack
    steps: list[dict[str, Any]]  # Step definitions
    duration_days: int
    expected_engagement: float  # Expected open rate %
    conversion_rate: float  # Expected conversion %
    description: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "track": self.track.value,
            "step_count": len(self.steps),
            "duration_days": self.duration_days,
            "expected_engagement": self.expected_engagement,
        }


class NurtureCampaignManager:
    """Manage lead nurturing campaigns."""

    _campaigns: dict[str, NurtureCampaign] = {}
    _subscribers: dict[str, SubscriberProfile] = {}
    _prebuilt_sequences: dict[str, PrebuiltSequence] = {}

    @classmethod
    def create_campaign(
        cls,
        name: str,
        description: str,
        track: NurtureTrack,
        sequences: list[str],
        enrollment_criteria: dict[str, Any] | None = None,
        success_criteria: str = "",
    ) -> NurtureCampaign:
        """Create a nurturing campaign."""
        campaign = NurtureCampaign(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            track=track,
            sequences=sequences,
            enrollment_criteria=enrollment_criteria or {},
            success_criteria=success_criteria,
        )
        cls._campaigns[campaign.id] = campaign
        logger.info(f"Nurture campaign created: {campaign.id} ({name})")
        return campaign

    @classmethod
    def register_subscriber(
        cls,
        email: str,
        first_name: str,
        last_name: str,
        company: str,
        job_title: str,
        industry: str,
        company_size: str,
        custom_fields: dict[str, Any] | None = None,
    ) -> SubscriberProfile:
        """Register a new subscriber."""
        subscriber = SubscriberProfile(
            id=str(uuid.uuid4()),
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
            job_title=job_title,
            industry=industry,
            company_size=company_size,
            custom_fields=custom_fields or {},
        )
        cls._subscribers[subscriber.id] = subscriber
        logger.info(f"Subscriber registered: {subscriber.id} ({email})")
        return subscriber

    @classmethod
    def get_subscriber(cls, subscriber_id: str) -> SubscriberProfile | None:
        """Get subscriber by ID."""
        return cls._subscribers.get(subscriber_id)

    @classmethod
    def update_subscriber_track(cls, subscriber_id: str, new_track: NurtureTrack) -> bool:
        """Update subscriber's nurture track."""
        subscriber = cls.get_subscriber(subscriber_id)
        if subscriber:
            old_track = subscriber.current_track
            subscriber.current_track = new_track
            subscriber.updated_at = datetime.now(timezone.utc)
            logger.info(f"Subscriber track updated: {subscriber_id} ({old_track.value} → {new_track.value})")
            return True
        return False

    @classmethod
    def update_engagement(
        cls,
        subscriber_id: str,
        email_opens: int = 0,
        email_clicks: int = 0,
        website_visits: int = 0,
    ) -> bool:
        """Update engagement metrics."""
        subscriber = cls.get_subscriber(subscriber_id)
        if subscriber:
            subscriber.email_opens += email_opens
            subscriber.email_clicks += email_clicks
            subscriber.website_visits += website_visits
            subscriber.last_engagement = datetime.now(timezone.utc)

            # Update engagement level
            total_engagement = subscriber.email_opens + (subscriber.email_clicks * 2) + (subscriber.website_visits * 3)
            if total_engagement > 10:
                subscriber.engagement_level = "high"
            elif total_engagement > 5:
                subscriber.engagement_level = "medium"
            else:
                subscriber.engagement_level = "low"

            subscriber.updated_at = datetime.now(timezone.utc)
            return True
        return False

    @classmethod
    def assign_campaign(cls, subscriber_id: str, campaign_id: str) -> bool:
        """Assign subscriber to campaign."""
        subscriber = cls.get_subscriber(subscriber_id)
        campaign = cls._campaigns.get(campaign_id)

        if subscriber and campaign:
            if campaign_id not in subscriber.enrolled_campaigns:
                subscriber.enrolled_campaigns.append(campaign_id)
                campaign.enrollments += 1
                logger.info(f"Campaign assigned: {subscriber_id} → {campaign_id}")
            return True
        return False

    @classmethod
    def mark_campaign_converted(cls, subscriber_id: str, campaign_id: str) -> bool:
        """Mark subscriber as converted in campaign."""
        subscriber = cls.get_subscriber(subscriber_id)
        campaign = cls._campaigns.get(campaign_id)

        if subscriber and campaign:
            campaign.conversions += 1
            logger.info(f"Campaign conversion: {subscriber_id} in {campaign_id}")
            return True
        return False

    @classmethod
    def get_campaign_metrics(cls, campaign_id: str) -> dict[str, Any]:
        """Get campaign performance metrics."""
        campaign = cls._campaigns.get(campaign_id)
        if not campaign:
            return {}

        conversion_rate = (campaign.conversions / max(campaign.enrollments, 1)) * 100

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "track": campaign.track.value,
            "enrollments": campaign.enrollments,
            "conversions": campaign.conversions,
            "conversion_rate": conversion_rate,
            "status": campaign.status.value,
        }

    @classmethod
    def register_prebuilt_sequence(cls, sequence: PrebuiltSequence) -> None:
        """Register a pre-built sequence template."""
        cls._prebuilt_sequences[sequence.id] = sequence
        logger.info(f"Prebuilt sequence registered: {sequence.id} ({sequence.name})")

    @classmethod
    def get_prebuilt_sequences(cls, track: NurtureTrack | None = None) -> list[PrebuiltSequence]:
        """Get pre-built sequences by track."""
        sequences = cls._prebuilt_sequences.values()
        if track:
            sequences = [s for s in sequences if s.track == track]
        return list(sequences)


class SegmentationEngine:
    """Segment subscribers for targeted campaigns."""

    @classmethod
    def segment_by_track(cls, subscribers: list[SubscriberProfile], track: NurtureTrack) -> list[SubscriberProfile]:
        """Filter subscribers by nurture track."""
        return [s for s in subscribers if s.current_track == track]

    @classmethod
    def segment_by_engagement(cls, subscribers: list[SubscriberProfile], level: str) -> list[SubscriberProfile]:
        """Filter subscribers by engagement level."""
        return [s for s in subscribers if s.engagement_level == level]

    @classmethod
    def segment_by_industry(cls, subscribers: list[SubscriberProfile], industry: str) -> list[SubscriberProfile]:
        """Filter subscribers by industry."""
        return [s for s in subscribers if industry.lower() in s.industry.lower()]

    @classmethod
    def segment_by_company_size(cls, subscribers: list[SubscriberProfile], size_range: tuple[int, int]) -> list[SubscriberProfile]:
        """Filter subscribers by company size."""
        size_map = {
            "1-50": (1, 50),
            "51-200": (51, 200),
            "201-500": (201, 500),
            "501-1000": (501, 1000),
            "1000+": (1000, 999999),
        }
        return [s for s in subscribers if s.company_size in size_range]

    @classmethod
    def segment_by_lead_score(cls, subscribers: list[SubscriberProfile], min_score: int, max_score: int) -> list[SubscriberProfile]:
        """Filter subscribers by lead score range."""
        return [s for s in subscribers if min_score <= s.lead_score <= max_score]

    @classmethod
    def segment_inactive(cls, subscribers: list[SubscriberProfile], days: int = 30) -> list[SubscriberProfile]:
        """Find inactive subscribers (no engagement in N days)."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return [
            s for s in subscribers
            if s.last_engagement is None or s.last_engagement < cutoff
        ]

    @classmethod
    def segment_high_potential(cls, subscribers: list[SubscriberProfile]) -> list[SubscriberProfile]:
        """Find high-potential leads (high engagement + good fit)."""
        return [
            s for s in subscribers
            if s.engagement_level == "high" and s.lead_score >= 60
        ]


class ReengagementCampaignManager:
    """Manage re-engagement for inactive subscribers."""

    @classmethod
    def create_reengagement_plan(
        cls,
        subscriber: SubscriberProfile,
        reason: str = "inactivity",
    ) -> dict[str, Any]:
        """Create re-engagement plan for inactive subscriber."""
        plan = {
            "subscriber_id": subscriber.id,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sequence_type": "reengagement",
            "steps": [
                {
                    "step": 1,
                    "email_type": "win_back",
                    "subject": f"We miss you, {subscriber.first_name}!",
                    "delay_hours": 0,
                },
                {
                    "step": 2,
                    "email_type": "special_offer",
                    "subject": "Special offer just for you",
                    "delay_hours": 72,
                },
                {
                    "step": 3,
                    "email_type": "case_study",
                    "subject": "How companies like yours are using WorkCrew",
                    "delay_hours": 168,
                },
                {
                    "step": 4,
                    "email_type": "final_attempt",
                    "subject": "Last chance: Get back on track",
                    "delay_hours": 240,
                },
            ],
            "success_metric": "re_engagement",
        }
        logger.info(f"Re-engagement plan created for {subscriber.id}")
        return plan

    @classmethod
    def get_reengagement_candidates(
        cls,
        subscribers: list[SubscriberProfile],
        days_inactive: int = 30,
    ) -> list[SubscriberProfile]:
        """Get subscribers eligible for re-engagement."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_inactive)

        candidates = [
            s for s in subscribers
            if (s.last_engagement and s.last_engagement < cutoff)
            and s.email_opens > 0  # Only those who engaged before
        ]
        return candidates
