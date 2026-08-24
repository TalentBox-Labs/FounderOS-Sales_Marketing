"""Market Research, Community Engagement, Brand Monitoring, and Partnership
Discovery agents.

Real signals come from Reddit and Hacker News's public, unauthenticated
search APIs (revenue_os.integrations.public_sources) plus the existing
Proxycurl-backed LinkedIn company enrichment for competitor tracking. X/
Twitter, LinkedIn conversations, Discord, Slack, GitHub issues, and Product
Hunt have no compliant free API and are reported as unavailable rather than
silently skipped or faked.

Findings are persisted as MarketingInsight rows so research accumulates
into a real, growing log instead of vanishing after one request/response —
"researches the market daily" means something to look back on.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

AGENT_MARKET_RESEARCH = "market_research_agent"
AGENT_COMMUNITY = "community_engagement_agent"
AGENT_BRAND_MONITOR = "brand_monitoring_agent"
AGENT_PARTNERSHIP = "partnership_influencer_agent"


def _log_insight(
    db: Session, agent_name: str, category: str, title: str, summary: str,
    *, organization_id: str, source_url: str | None = None, sentiment: str | None = None,
) -> None:
    from revenue_os.models.marketing import MarketingInsight
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    db.add(MarketingInsight(
        organization_id=tenant_org_uuid(organization_id), agent_name=agent_name, category=category,
        title=title[:500], summary=summary, source_url=source_url, sentiment=sentiment,
    ))


# ── Agent 1: Market Research ─────────────────────────────────────────────────


def run_market_research(
    query: str, competitor_linkedin_urls: list[str] | None = None, *, organization_id: str,
) -> dict[str, Any]:
    """Pulls real Reddit + Hacker News signals and, if given competitor
    LinkedIn company URLs, real funding/hiring data via the existing
    Proxycurl enrichment. Synthesizes insights + opportunities via LLM
    (or an honest fallback), and logs each as a MarketingInsight."""
    from revenue_os.database import SessionLocal
    from revenue_os.integrations.public_sources import UNAVAILABLE_CHANNELS, search_hackernews, search_reddit
    from revenue_os.services import ai_service

    reddit = search_reddit(query, limit=8)
    hn = search_hackernews(query, limit=8)

    competitors: list[dict[str, Any]] = []
    if competitor_linkedin_urls:
        from revenue_os.services.linkedin_enrichment import enrich_company

        for url in competitor_linkedin_urls[:5]:
            res = enrich_company(url)
            if res.get("ok"):
                p = res["profile"]
                competitors.append({
                    "name": p.get("name"), "hiring_activity_note": "see LinkedIn jobs tab (not returned by this API)",
                    "funding_rounds": [
                        {"type": r.get("funding_type"), "announced": r.get("announced_date")}
                        for r in (p.get("funding_data") or [])
                    ],
                })

    signals = {"reddit": reddit, "hackernews": hn, "competitors": competitors, "unavailable_channels": UNAVAILABLE_CHANNELS}
    result = ai_service.synthesize_market_research(signals, context=query)

    db = SessionLocal()
    try:
        for text in result.get("insights", []):
            _log_insight(db, AGENT_MARKET_RESEARCH, "market_research", query, text, organization_id=organization_id)
        for text in result.get("opportunities", []):
            _log_insight(db, AGENT_MARKET_RESEARCH, "opportunity", query, text, organization_id=organization_id)
        db.commit()
    finally:
        db.close()

    return {
        "ok": True, "query": query,
        "signals_found": {"reddit": len(reddit), "hackernews": len(hn), "competitors": len(competitors)},
        "unavailable_channels": UNAVAILABLE_CHANNELS,
        **result,
    }


# ── Agent 16: Community Engagement ───────────────────────────────────────────


def monitor_communities(
    query: str, subreddit: str | None = None, draft_replies: bool = True, *, organization_id: str,
) -> dict[str, Any]:
    """Reddit only for now — the one community channel with a compliant
    public API. GitHub issues / Discord / Slack / Product Hunt need their
    own configured connector before this agent can cover them."""
    from revenue_os.database import SessionLocal
    from revenue_os.integrations.public_sources import search_reddit
    from revenue_os.services import ai_service

    threads = search_reddit(query, subreddit=subreddit, limit=10)
    drafted = []
    db = SessionLocal()
    try:
        for t in threads:
            _log_insight(
                db, AGENT_COMMUNITY, "community", t["title"],
                f"r/{t['subreddit']} · {t['score']} upvotes, {t['num_comments']} comments",
                organization_id=organization_id, source_url=t["url"],
            )
        db.commit()

        if draft_replies:
            for t in threads[:3]:
                reply = ai_service.draft_community_reply(t["title"], t["body"], context=query)
                drafted.append({"thread": t["title"], "url": t["url"], "draft_reply": reply})
    finally:
        db.close()

    return {"ok": True, "query": query, "threads_found": len(threads), "threads": threads, "drafted_replies": drafted,
            "note": "Covers Reddit only — GitHub/Discord/Slack/Product Hunt need their own configured connector."}


# ── Agent 17: Brand Monitoring ───────────────────────────────────────────────


def monitor_brand_mentions(brand_name: str, *, organization_id: str) -> dict[str, Any]:
    """Searches Reddit for brand mentions and classifies sentiment on each
    — flags negative mentions so they don't sit unnoticed."""
    from revenue_os.database import SessionLocal
    from revenue_os.integrations.public_sources import search_reddit
    from revenue_os.services import ai_service

    mentions = search_reddit(brand_name, limit=15)
    scored = []
    db = SessionLocal()
    try:
        for m in mentions:
            text = f"{m['title']} {m['body']}"
            sentiment = ai_service.classify_sentiment(text)
            scored.append({**m, "sentiment": sentiment})
            _log_insight(
                db, AGENT_BRAND_MONITOR, "brand_mention", m["title"],
                f"r/{m['subreddit']} · sentiment: {sentiment}",
                organization_id=organization_id, source_url=m["url"], sentiment=sentiment,
            )
        db.commit()
    finally:
        db.close()

    negative = [m for m in scored if m["sentiment"] == "negative"]
    return {
        "ok": True, "brand_name": brand_name, "mentions_found": len(scored), "mentions": scored,
        "negative_count": len(negative), "needs_attention": negative,
        "note": "Covers Reddit only — no compliant free API for X/news/review platforms without a configured connector.",
    }


# ── Agent 19: Partnership & Influencer ───────────────────────────────────────


def discover_partnership_leads(query: str, lead_type: str = "other", *, organization_id: str) -> dict[str, Any]:
    """Searches Reddit/HN for potential partners (communities, newsletters,
    podcasts mentioned in context) and files new ones as PartnershipLead
    rows — deduplicated by URL within the tenant, so re-running doesn't
    create duplicates."""
    from revenue_os.database import SessionLocal
    from revenue_os.integrations.public_sources import search_hackernews, search_reddit
    from revenue_os.models.marketing import PartnershipLead
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    reddit = search_reddit(query, limit=8)
    hn = search_hackernews(query, limit=8)
    candidates = [{"name": r["title"], "url": r["url"], "source": "reddit"} for r in reddit] + \
                 [{"name": h["title"], "url": h["url"], "source": "hackernews"} for h in hn]

    org_uuid = tenant_org_uuid(organization_id)
    db = SessionLocal()
    created = []
    try:
        existing_urls = {
            row.url for row in
            db.query(PartnershipLead.url).filter(PartnershipLead.organization_id == org_uuid).all()
        }
        for c in candidates:
            if c["url"] in existing_urls:
                continue
            lead = PartnershipLead(
                organization_id=org_uuid, name=c["name"][:255], url=c["url"],
                lead_type=lead_type, source=c["source"],
            )
            db.add(lead)
            created.append(lead)
            existing_urls.add(c["url"])
        db.commit()
        result = [{"id": str(l.id), "name": l.name, "url": l.url, "source": l.source} for l in created]
    finally:
        db.close()

    return {"ok": True, "query": query, "candidates_found": len(candidates), "new_leads_created": len(result), "new_leads": result}


def list_partnership_leads(status: str | None = None, *, organization_id: str) -> list[dict[str, Any]]:
    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import PartnershipLead
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    db = SessionLocal()
    try:
        q = db.query(PartnershipLead).filter(
            PartnershipLead.organization_id == tenant_org_uuid(organization_id)
        ).order_by(PartnershipLead.created_at.desc())
        if status:
            q = q.filter(PartnershipLead.status == status)
        return [
            {"id": str(l.id), "name": l.name, "lead_type": l.lead_type, "url": l.url, "status": l.status,
             "notes": l.notes, "source": l.source, "created_at": l.created_at.isoformat() if l.created_at else None}
            for l in q.limit(200).all()
        ]
    finally:
        db.close()


def draft_partnership_pitch(lead_id: str, our_context: str = "", *, organization_id: str) -> dict[str, Any]:
    import uuid as uuid_lib

    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import PartnershipLead
    from revenue_os.services import ai_service
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    db = SessionLocal()
    try:
        try:
            lid = uuid_lib.UUID(lead_id)
        except ValueError:
            return {"ok": False, "reason": "Invalid lead_id"}
        lead = db.query(PartnershipLead).filter(
            PartnershipLead.id == lid, PartnershipLead.organization_id == tenant_org_uuid(organization_id)
        ).first()
        if lead is None:
            return {"ok": False, "reason": "Partnership lead not found"}

        pitch = ai_service.generate_partnership_pitch(lead.name, lead.notes or f"Found via {lead.source}: {lead.url}", our_context)
        lead.status = "contacted" if lead.status == "discovered" else lead.status
        db.add(lead)
        db.commit()
        return {"ok": True, "lead_id": str(lead.id), "name": lead.name, "pitch": pitch}
    finally:
        db.close()
