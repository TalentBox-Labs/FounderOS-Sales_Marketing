"""Automatic deal creation and lifecycle management from qualified leads."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact, ContactStatus
from revenue_os.models.deal import Deal, DealStage, Pipeline, PipelineType

logger = logging.getLogger(__name__)


def get_or_create_sales_pipeline(db: Session) -> Pipeline:
    """Get default sales pipeline or create if missing."""
    pipeline = db.query(Pipeline).filter(Pipeline.is_default == 1).first()

    if not pipeline:
        pipeline = Pipeline(
            name="Standard Sales Pipeline",
            pipeline_type=PipelineType.SALES,
            stages="discovery,qualified,proposal,negotiation,closed_won,closed_lost",
            is_default=1,
        )
        db.add(pipeline)
        db.commit()

    return pipeline


def create_deal_from_contact(
    db: Session, contact: Contact, value: float = 0.0, owner_id: str | None = None
) -> Deal | None:
    """
    Create a deal from a qualified contact.

    Returns: Created Deal, or None if contact not qualified.
    """
    if contact.status != ContactStatus.QUALIFIED:
        logger.warning(
            "Cannot create deal from non-qualified contact",
            extra={"contact_id": str(contact.id), "status": contact.status},
        )
        return None

    # Check if deal already exists
    existing = (
        db.query(Deal).filter(Deal.contact_id == contact.id).filter(Deal.closed_at.is_(None)).first()
    )
    if existing:
        logger.info(
            "Deal already exists for contact",
            extra={"contact_id": str(contact.id), "deal_id": str(existing.id)},
        )
        return existing

    pipeline = get_or_create_sales_pipeline(db)

    deal = Deal(
        pipeline_id=pipeline.id,
        company_id=contact.company_id,
        contact_id=contact.id,
        name=f"{contact.full_name} - {contact.company.name if contact.company else 'New Prospect'}",
        stage=DealStage.DISCOVERY,
        probability=20,  # 20% for new discovery stage
        value=value or 5000.0,  # Default ACV
        currency="USD",
        description=f"Qualified lead from {contact.source.value}",
        owner_id=owner_id,
        expected_close_date=datetime.now(timezone.utc) + timedelta(days=45),  # 45-day cycle
    )

    db.add(deal)
    db.commit()

    logger.info(
        "Deal created from qualified contact",
        extra={
            "contact_id": str(contact.id),
            "deal_id": str(deal.id),
            "value": value,
            "stage": deal.stage.value,
        },
    )

    return deal


def advance_deal_stage(db: Session, deal: Deal, new_stage: DealStage) -> bool:
    """
    Advance deal to next stage with probability update.

    Probability increases as deal progresses:
    - DISCOVERY: 20%
    - QUALIFIED: 40%
    - PROPOSAL: 60%
    - NEGOTIATION: 80%
    - CLOSED_WON: 100%
    - CLOSED_LOST: 0%
    """
    old_stage = deal.stage

    # Update stage
    deal.stage = new_stage
    deal.updated_at = datetime.now(timezone.utc)

    # Update probability based on stage
    probability_map = {
        DealStage.DISCOVERY: 20,
        DealStage.QUALIFIED: 40,
        DealStage.PROPOSAL: 60,
        DealStage.NEGOTIATION: 80,
        DealStage.CLOSED_WON: 100,
        DealStage.CLOSED_LOST: 0,
    }
    deal.probability = probability_map.get(new_stage, deal.probability)

    # If closed won, set closed_at
    if new_stage == DealStage.CLOSED_WON:
        deal.closed_at = datetime.now(timezone.utc)

    db.add(deal)
    db.commit()

    logger.info(
        "Deal advanced",
        extra={
            "deal_id": str(deal.id),
            "old_stage": old_stage.value,
            "new_stage": new_stage.value,
            "probability": deal.probability,
        },
    )

    return True


def get_pipeline_health(db: Session, pipeline_id: str | None = None) -> dict[str, Any]:
    """Get overall pipeline health metrics."""
    if pipeline_id:
        deals = db.query(Deal).filter(Deal.pipeline_id == pipeline_id).filter(Deal.closed_at.is_(None)).all()
    else:
        deals = db.query(Deal).filter(Deal.closed_at.is_(None)).all()

    if not deals:
        return {
            "total_deals": 0,
            "total_pipeline_value": 0.0,
            "weighted_forecast": 0.0,
            "by_stage": {},
        }

    # Group by stage
    by_stage: dict[str, list[Deal]] = {}
    for deal in deals:
        stage_key = deal.stage.value
        if stage_key not in by_stage:
            by_stage[stage_key] = []
        by_stage[stage_key].append(deal)

    # Calculate metrics per stage
    stage_metrics = {}
    total_value = 0.0
    weighted_forecast = 0.0

    for stage, stage_deals in by_stage.items():
        stage_value = sum(d.value for d in stage_deals)
        stage_probability = sum(d.probability for d in stage_deals) / len(stage_deals)
        stage_forecast = sum(d.value * (d.probability / 100) for d in stage_deals)

        stage_metrics[stage] = {
            "count": len(stage_deals),
            "total_value": stage_value,
            "avg_probability": stage_probability,
            "forecast": stage_forecast,
        }

        total_value += stage_value
        weighted_forecast += stage_forecast

    return {
        "total_deals": len(deals),
        "total_pipeline_value": total_value,
        "weighted_forecast": weighted_forecast,
        "by_stage": stage_metrics,
    }


def calculate_deal_velocity(db: Session, days: int = 90) -> dict[str, Any]:
    """
    Calculate how fast deals move through pipeline.

    Returns stage transition times and velocity.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    closed_deals = db.query(Deal).filter(Deal.closed_at >= cutoff_date).all()

    if not closed_deals:
        return {
            "period_days": days,
            "closed_deals": 0,
            "avg_cycle_time_days": 0,
            "won_vs_lost": {"won": 0, "lost": 0},
        }

    cycle_times = []
    won = 0
    lost = 0

    for deal in closed_deals:
        if deal.created_at and deal.closed_at:
            cycle_days = (deal.closed_at - deal.created_at).days
            cycle_times.append(cycle_days)

        if deal.stage == DealStage.CLOSED_WON:
            won += 1
        elif deal.stage == DealStage.CLOSED_LOST:
            lost += 1

    avg_cycle = sum(cycle_times) / len(cycle_times) if cycle_times else 0
    win_rate = won / (won + lost) if (won + lost) > 0 else 0

    return {
        "period_days": days,
        "closed_deals": len(closed_deals),
        "won_deals": won,
        "lost_deals": lost,
        "win_rate": win_rate,
        "avg_cycle_time_days": avg_cycle,
    }


def forecast_close_date(db: Session, deal: Deal) -> datetime:
    """
    Forecast when deal is likely to close based on velocity.

    Simple model: estimate based on stage and historical velocity.
    """
    velocity = calculate_deal_velocity(db)
    avg_cycle = velocity.get("avg_cycle_time_days", 45)

    # Estimate days remaining based on stage progress
    stage_progress = {
        DealStage.DISCOVERY: 0.2,
        DealStage.QUALIFIED: 0.4,
        DealStage.PROPOSAL: 0.6,
        DealStage.NEGOTIATION: 0.85,
        DealStage.CLOSED_WON: 1.0,
        DealStage.CLOSED_LOST: 1.0,
    }

    progress = stage_progress.get(deal.stage, 0.3)
    remaining_days = int(avg_cycle * (1 - progress))

    forecast = datetime.now(timezone.utc) + timedelta(days=remaining_days)
    return forecast


def get_deals_at_risk(db: Session) -> list[dict[str, Any]]:
    """
    Identify deals at risk of being lost.

    Criteria:
    - In negotiation/proposal stage
    - Past expected close date
    - No recent activity
    """
    risk_deals = []

    deals = (
        db.query(Deal)
        .filter(Deal.closed_at.is_(None))
        .filter(Deal.stage.in_([DealStage.NEGOTIATION, DealStage.PROPOSAL]))
        .all()
    )

    now = datetime.now(timezone.utc)

    def _aware(dt: datetime | None) -> datetime | None:
        # SQLite returns naive datetimes; treat stored values as UTC.
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    for deal in deals:
        risk_score = 0
        expected_close = _aware(deal.expected_close_date)
        updated_at = _aware(deal.updated_at)

        # Past expected close date
        if expected_close and expected_close < now:
            days_overdue = (now - expected_close).days
            risk_score += min(30, days_overdue)

        # Old deal (not updated recently)
        if updated_at:
            days_stale = (now - updated_at).days
            if days_stale > 14:
                risk_score += 20

        if risk_score > 0:
            risk_deals.append(
                {
                    "deal_id": str(deal.id),
                    "name": deal.name,
                    "stage": deal.stage.value,
                    "value": deal.value,
                    "risk_score": risk_score,
                    "days_overdue": (now - expected_close).days
                    if expected_close
                    else 0,
                }
            )

    return sorted(risk_deals, key=lambda x: x["risk_score"], reverse=True)
