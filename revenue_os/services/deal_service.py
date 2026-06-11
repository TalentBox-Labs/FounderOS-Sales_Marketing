from __future__ import annotations

from sqlalchemy.orm import Session

from revenue_os.models.deal import Deal, Pipeline, PipelineType


def forecast_pipeline(
    db: Session, pipeline_id: str
) -> dict:
    deals = (
        db.query(Deal)
        .filter(Deal.pipeline_id == pipeline_id)
        .all()
    )

    total_value = sum(d.value for d in deals)
    weighted_value = sum(d.value * d.probability / 100 for d in deals)

    stage_breakdown = {}
    for deal in deals:
        stage_key = deal.stage.value
        if stage_key not in stage_breakdown:
            stage_breakdown[stage_key] = {
                "count": 0,
                "value": 0.0,
                "weighted": 0.0,
            }
        stage_breakdown[stage_key]["count"] += 1
        stage_breakdown[stage_key]["value"] += deal.value
        stage_breakdown[stage_key]["weighted"] += (
            deal.value * deal.probability / 100
        )

    return {
        "total_deals": len(deals),
        "total_value": total_value,
        "weighted_value": weighted_value,
        "stage_breakdown": stage_breakdown,
    }


def pipeline_health(db: Session, pipeline_id: str) -> dict:
    forecast = forecast_pipeline(db, pipeline_id)

    won_deals = (
        db.query(Deal)
        .filter(
            Deal.pipeline_id == pipeline_id,
            Deal.stage == "closed_won",
        )
        .count()
    )
    lost_deals = (
        db.query(Deal)
        .filter(
            Deal.pipeline_id == pipeline_id,
            Deal.stage == "closed_lost",
        )
        .count()
    )
    active_deals = forecast["total_deals"] - won_deals - lost_deals

    win_rate = (
        (won_deals / (won_deals + lost_deals) * 100)
        if (won_deals + lost_deals) > 0
        else 0
    )

    return {
        **forecast,
        "active_deals": active_deals,
        "won_deals": won_deals,
        "lost_deals": lost_deals,
        "win_rate": round(win_rate, 1),
    }
