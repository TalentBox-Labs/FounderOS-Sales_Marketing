"""Analytics & Attribution and Conversion Rate Optimization (CRO) agents —
both built entirely on real data already computed elsewhere in the platform
(M8's analytics_depth, the CRM's own deal-stage funnel). No heatmap/A-B
test data source exists, so CRO scopes to what's real: pipeline drop-off.
"""

from __future__ import annotations

from typing import Any

AGENT_ANALYTICS = "analytics_attribution_agent"
AGENT_CRO = "cro_agent"


# ── Agent 15: Analytics & Attribution ────────────────────────────────────────


def generate_analytics_report(period: str | None = None, *, organization_id: str) -> dict[str, Any]:
    """Pulls real attribution/LTV/CAC/agent-productivity data (M8) plus SEO
    tracking depth, and synthesizes a founder-readable executive summary.

    Note: M8's analytics_depth functions are global/untenanted today (a
    pre-existing gap, not introduced here) — this report isn't yet
    org-scoped at the metrics layer."""
    from revenue_os.database import SessionLocal
    from revenue_os.models.seo import SEOKeyword
    from revenue_os.services import ai_service
    from revenue_os.services.analytics_depth import (
        compute_agent_productivity,
        compute_attribution,
        compute_cac,
        compute_ltv,
    )

    db = SessionLocal()
    try:
        attribution = compute_attribution(db)
        ltv = compute_ltv(db)
        cac = compute_cac(db, period=period)
        productivity = compute_agent_productivity(db)
        keywords_tracked = db.query(SEOKeyword).count()
    finally:
        db.close()

    metrics_summary = (
        f"Attribution by source: {attribution}. "
        f"LTV: avg ${(ltv.get('avg_ltv') or 0):.0f} across {ltv.get('customers_with_revenue', 0)} customers. "
        f"CAC by channel: {cac}. "
        f"SEO keywords tracked: {keywords_tracked}. "
        f"Active agents: {len(productivity)}."
    )
    summary = ai_service.generate_marketing_exec_summary(metrics_summary)

    return {
        "ok": True, "attribution": attribution, "ltv": ltv, "cac": cac,
        "agent_productivity": productivity, "keywords_tracked": keywords_tracked,
        "executive_summary": summary,
    }


# ── Agent 18: Conversion Rate Optimization ───────────────────────────────────


def analyze_conversion_funnel(*, organization_id: str) -> dict[str, Any]:
    """CRO recommendations from the real deal-stage funnel — the closest
    thing to a conversion funnel this platform actually has data for."""
    from sqlalchemy import func as sa_func

    from revenue_os.database import SessionLocal
    from revenue_os.models.deal import Deal
    from revenue_os.services import ai_service
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    db = SessionLocal()
    try:
        stage_rows = (
            db.query(Deal.stage, sa_func.count(Deal.id))
            .filter(Deal.organization_id == tenant_org_uuid(organization_id))
            .group_by(Deal.stage).all()
        )
    finally:
        db.close()

    funnel = {(stage.value if stage else "unknown"): count for stage, count in stage_rows}
    funnel_summary = ", ".join(f"{k}: {v}" for k, v in funnel.items()) or "No deals in the pipeline yet"
    recommendations = ai_service.generate_cro_recommendations(funnel_summary)

    return {
        "ok": True, "funnel": funnel, "recommendations": recommendations,
        "note": "Based on deal-stage drop-off — no landing-page heatmap or A/B test data source is connected.",
    }
