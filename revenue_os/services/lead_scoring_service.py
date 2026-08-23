"""Lead scoring engine for intelligent lead qualification."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.activity import Activity, ActivityType
from revenue_os.models.contact import Contact, ContactSource, ContactStatus

logger = logging.getLogger(__name__)


class LeadScorer:
    """Score contacts based on fit, engagement, and source quality."""

    # Source quality weights (0-30 points)
    SOURCE_WEIGHTS = {
        ContactSource.LINKEDIN: 25,  # High intent, direct
        ContactSource.WEB_FORM: 20,  # Self-identified interest
        ContactSource.REFERRAL: 28,  # Warm introduction
        ContactSource.OUTREACH: 15,  # Cold outreach response
        ContactSource.IMPORT: 10,  # Bulk import, unqualified
        ContactSource.MANUAL: 12,  # Manual entry, low intent
        ContactSource.API: 8,  # Automated source
        ContactSource.N8N: 5,  # Automation tool
    }

    @classmethod
    def calculate_score(cls, contact: Contact, company_context: dict | None = None) -> int:
        """
        Calculate lead score (0-100).

        Score breakdown:
        - Source quality: 0-30 points
        - Engagement signals: 0-40 points
        - Company fit: 0-20 points
        - Timing signals: 0-10 points
        """
        score = 0

        # 1. Source quality (0-30)
        source_score = cls.SOURCE_WEIGHTS.get(contact.source, 5)
        score += source_score

        # 2. Engagement signals (0-40)
        engagement_score = cls._engagement_score(contact)
        score += engagement_score

        # 3. Company fit (0-20)
        company_score = cls._company_fit_score(contact, company_context or {})
        score += company_score

        # 4. Timing signals (0-10)
        timing_score = cls._timing_score(contact)
        score += timing_score

        return max(0, min(100, score))

    @classmethod
    def _engagement_score(cls, contact: Contact) -> int:
        """Score engagement signals (0-40 points)."""
        score = 0

        # Email exists
        if contact.email:
            score += 10

        # LinkedIn profile
        if contact.linkedin_url:
            score += 10

        # Recent engagement
        if contact.last_contacted_at:
            days_since = (datetime.now(timezone.utc) - contact.last_contacted_at).days
            if days_since <= 7:
                score += 15  # Actively engaging
            elif days_since <= 30:
                score += 8  # Recent engagement
            elif days_since <= 90:
                score += 3  # Stale but not cold

        # Status progression (LEAD < PROSPECT < QUALIFIED)
        status_boost = {
            ContactStatus.LEAD: 0,
            ContactStatus.PROSPECT: 5,
            ContactStatus.QUALIFIED: 10,
        }
        score += status_boost.get(contact.status, 0)

        return min(40, score)

    @classmethod
    def _company_fit_score(cls, contact: Contact, company_context: dict) -> int:
        """Score company fit (0-20 points)."""
        score = 0

        if not contact.company:
            return 5  # Minimal score for unknown company

        company = contact.company

        # Company has known revenue (likely established)
        if company.annual_revenue and company.annual_revenue > 1_000_000:
            score += 8

        # Company has funding (actively growing)
        if company.funding_stage in ("Series A", "Series B", "Series C", "Funded"):
            score += 7

        # Hiring activity (expansion signal)
        if company.hiring_activity and "active" in company.hiring_activity.lower():
            score += 5

        return min(20, score)

    @classmethod
    def _timing_score(cls, contact: Contact) -> int:
        """Score timing signals (0-10 points)."""
        if not contact.created_at:
            return 0

        age_days = (datetime.now(timezone.utc) - contact.created_at).days

        if age_days <= 7:
            return 10  # Fresh lead
        elif age_days <= 30:
            return 6  # Recent
        elif age_days <= 90:
            return 2  # Warm
        return 0  # Cold

    @classmethod
    def update_contact_status(cls, contact: Contact, new_score: int) -> str:
        """
        Update contact status based on score.

        Returns: new status value.
        """
        old_status = contact.status

        if new_score >= 70:
            contact.status = ContactStatus.QUALIFIED
        elif new_score >= 40:
            contact.status = ContactStatus.PROSPECT
        else:
            contact.status = ContactStatus.LEAD

        if old_status != contact.status:
            logger.info(
                f"Contact status updated",
                extra={
                    "contact_id": str(contact.id),
                    "score": new_score,
                    "old_status": old_status,
                    "new_status": contact.status,
                },
            )

        return contact.status.value


def score_contact(db: Session, contact: Contact, company_context: dict | None = None) -> int:
    """Score a single contact and update status. Returns new score."""
    score = LeadScorer.calculate_score(contact, company_context)
    contact.lead_score = score
    LeadScorer.update_contact_status(contact, score)
    db.add(contact)
    return score


def score_contacts_batch(
    db: Session, contact_ids: list[str], company_context: dict | None = None
) -> dict[str, Any]:
    """Score multiple contacts in batch."""
    contacts = db.query(Contact).filter(Contact.id.in_(contact_ids)).all()

    results = {
        "total": len(contact_ids),
        "scored": 0,
        "newly_qualified": 0,
        "scores": {},
    }

    for contact in contacts:
        old_status = contact.status
        score = score_contact(db, contact, company_context)
        results["scores"][str(contact.id)] = {"score": score, "status": contact.status.value}

        if contact.status == ContactStatus.QUALIFIED and old_status != ContactStatus.QUALIFIED:
            results["newly_qualified"] += 1

        results["scored"] += 1

    if results["scored"] > 0:
        db.commit()

    return results


def get_contacts_by_score(
    db: Session,
    min_score: int = 0,
    max_score: int = 100,
    statuses: list[ContactStatus] | None = None,
    limit: int = 100,
) -> list[Contact]:
    """Get contacts within score range."""
    query = db.query(Contact).filter(
        Contact.lead_score >= min_score, Contact.lead_score <= max_score
    )

    if statuses:
        query = query.filter(Contact.status.in_(statuses))

    return query.order_by(Contact.lead_score.desc(), Contact.created_at.desc()).limit(limit).all()


def get_score_distribution(db: Session) -> dict[str, int]:
    """Get distribution of lead scores across contacts."""
    contacts = db.query(Contact).all()

    distribution = {
        "0-25": 0,
        "25-50": 0,
        "50-70": 0,
        "70-85": 0,
        "85-100": 0,
    }

    for contact in contacts:
        score = contact.lead_score
        if score < 25:
            distribution["0-25"] += 1
        elif score < 50:
            distribution["25-50"] += 1
        elif score < 70:
            distribution["50-70"] += 1
        elif score < 85:
            distribution["70-85"] += 1
        else:
            distribution["85-100"] += 1

    return distribution
