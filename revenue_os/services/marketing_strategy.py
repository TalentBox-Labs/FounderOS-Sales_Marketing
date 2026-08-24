"""Customer Persona, Content Strategy, SEO Strategy, GEO, and Product
Marketing agents — all grounded in real CRM/SEO/knowledge-base data already
in the platform, not invented from scratch.
"""

from __future__ import annotations

from typing import Any

AGENT_PERSONA = "customer_persona_agent"
AGENT_CONTENT_STRATEGY = "content_strategy_agent"
AGENT_SEO_STRATEGY = "seo_strategy_agent"
AGENT_GEO = "geo_agent"
AGENT_PRODUCT_MARKETING = "product_marketing_agent"


def _persona_dict(p: Any) -> dict[str, Any]:
    return {
        "id": str(p.id), "name": p.name, "summary": p.summary, "pain_points": p.pain_points,
        "motivations": p.motivations, "objections": p.objections, "messaging": p.messaging,
        "based_on": p.based_on, "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


# ── Agent 2: Customer Persona ────────────────────────────────────────────────


def update_customer_persona(*, organization_id: str) -> dict[str, Any]:
    """Aggregates real CRM data — industry mix, company size, closed-won
    count — and refreshes (upserts) the persona it produces."""
    from sqlalchemy import func as sa_func

    from revenue_os.database import SessionLocal
    from revenue_os.models.contact import Company, Contact
    from revenue_os.models.deal import Deal, DealStage
    from revenue_os.models.marketing import CustomerPersona
    from revenue_os.services import ai_service
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    org_uuid = tenant_org_uuid(organization_id)
    db = SessionLocal()
    try:
        total_contacts = db.query(Contact).filter(Contact.organization_id == org_uuid).count()
        won_deals = db.query(Deal).filter(
            Deal.stage == DealStage.CLOSED_WON, Deal.organization_id == org_uuid
        ).count()
        # Company has no organization_id column (global/shared in this codebase today);
        # scope the aggregate through Contact's company relationship instead.
        industry_rows = (
            db.query(Company.industry, sa_func.count(Company.id))
            .join(Contact, Contact.company_id == Company.id)
            .filter(Contact.organization_id == org_uuid)
            .group_by(Company.industry).all()
        )
        industry_mix = {(i.value if i else "unknown"): c for i, c in industry_rows}
        avg_employees = (
            db.query(sa_func.avg(Company.employee_count))
            .join(Contact, Contact.company_id == Company.id)
            .filter(Contact.organization_id == org_uuid)
            .scalar()
        )

        crm_summary = (
            f"{total_contacts} contacts tracked, {won_deals} closed-won deals. "
            f"Industry mix: {industry_mix or 'no company data yet'}. "
            f"Avg company size: {int(avg_employees) if avg_employees else 'unknown'} employees."
        )
        persona_data = ai_service.generate_customer_persona(crm_summary)

        name = persona_data.get("name") or "Primary Buyer"
        row = db.query(CustomerPersona).filter(
            CustomerPersona.name == name, CustomerPersona.organization_id == org_uuid
        ).first()
        if row is None:
            row = CustomerPersona(name=name, organization_id=org_uuid)
        row.summary = persona_data.get("summary", "")
        row.pain_points = persona_data.get("pain_points", "")
        row.motivations = persona_data.get("motivations", "")
        row.objections = persona_data.get("objections", "")
        row.messaging = persona_data.get("messaging", "")
        row.based_on = crm_summary
        db.add(row)
        db.commit()
        db.refresh(row)
        return {"ok": True, "persona": _persona_dict(row)}
    finally:
        db.close()


def list_personas(*, organization_id: str) -> list[dict[str, Any]]:
    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import CustomerPersona
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    db = SessionLocal()
    try:
        return [
            _persona_dict(p) for p in
            db.query(CustomerPersona)
            .filter(CustomerPersona.organization_id == tenant_org_uuid(organization_id))
            .order_by(CustomerPersona.updated_at.desc()).all()
        ]
    finally:
        db.close()


# ── Agent 3: Content Strategy ────────────────────────────────────────────────


def build_content_strategy(business_context: str = "", num_weeks: int = 4, *, organization_id: str) -> dict[str, Any]:
    """Deferred: this crew's Content Strategy agent overlaps the existing
    `content_strategist` agent in src/marketing_crew.py. Not wiring up a
    second, competing content-strategy generator until that dedup is a
    deliberate product decision — see docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md."""
    return {
        "ok": False,
        "reason": "Superseded by src/marketing_crew.py's content_strategist agent — "
                   "see docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md for the dedup decision needed before this ships.",
    }


# ── Agent 4: SEO Strategy ────────────────────────────────────────────────────


def build_seo_strategy(business_context: str = "", *, organization_id: str) -> dict[str, Any]:
    """Gaps/clusters/recommendations from the real tracked keyword set —
    no invented search volumes or difficulty scores."""
    from revenue_os.database import SessionLocal
    from revenue_os.models.seo import SEOKeyword, SEORankCheck
    from revenue_os.services import ai_service

    db = SessionLocal()
    try:
        keywords = db.query(SEOKeyword).all()
        parts = []
        for k in keywords:
            latest = (
                db.query(SEORankCheck).filter(SEORankCheck.keyword_id == k.id)
                .order_by(SEORankCheck.checked_at.desc()).first()
            )
            parts.append(f"{k.keyword} (target rank {k.target_rank or 'unset'}, current {latest.rank if latest else 'unranked'})")
    finally:
        db.close()

    keywords_summary = "; ".join(parts) or "No keywords tracked yet — add some under Marketing > SEO & GEO Tracking."
    strategy = ai_service.generate_seo_strategy(keywords_summary, business_context)
    return {"ok": True, "keywords_tracked": len(keywords), "keywords_summary": keywords_summary, **strategy}


# ── Agent 5: GEO ──────────────────────────────────────────────────────────────


def analyze_geo_readiness(
    article_id: str | None = None, title: str | None = None, content: str | None = None,
    *, organization_id: str,
) -> dict[str, Any]:
    """Evaluates one piece of content (an existing KB article, or arbitrary
    title/content) for AI-answer-engine visibility."""
    if article_id:
        import uuid as uuid_lib

        from revenue_os.database import SessionLocal
        from revenue_os.models.content import KnowledgeBaseArticle

        db = SessionLocal()
        try:
            try:
                aid = uuid_lib.UUID(article_id)
            except ValueError:
                return {"ok": False, "reason": "Invalid article_id"}
            article = db.get(KnowledgeBaseArticle, aid)
            if article is None:
                return {"ok": False, "reason": "Article not found"}
            title, content = article.title, article.content
        finally:
            db.close()

    if not title or not content:
        return {"ok": False, "reason": "Provide article_id, or both title and content"}

    from revenue_os.services import ai_service

    return {"ok": True, "title": title, **ai_service.generate_geo_recommendations(title, content)}


# ── Agent 20: Product Marketing ──────────────────────────────────────────────


def build_product_marketing_kit(feature: str, context: str = "", *, organization_id: str) -> dict[str, Any]:
    """Launch materials for a feature/release — logged as a MarketingInsight
    so past launches stay reviewable."""
    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import MarketingInsight
    from revenue_os.services import ai_service
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    kit = ai_service.generate_product_marketing_kit(feature, context)

    db = SessionLocal()
    try:
        db.add(MarketingInsight(
            organization_id=tenant_org_uuid(organization_id), agent_name=AGENT_PRODUCT_MARKETING,
            category="product_marketing", title=feature[:500], summary=kit.get("announcement", ""),
        ))
        db.commit()
    finally:
        db.close()

    return {"ok": True, "feature": feature, **kit}
