"""Marketing Agent crew — 20 specialized agents plus the Marketing
Orchestrator (AI CMO). Each endpoint is a thin wrapper around a real
service function in revenue_os.services.marketing_*; see those modules for
what's genuinely automated vs. what's an honest fallback.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from revenue_os.services.tenant_resolution import require_tenant_context
from runner_api_routers.utils import _verify_api_key

router = APIRouter(prefix="/api/v1/marketing-agents", tags=["marketing-agents"])


# ── Request models ────────────────────────────────────────────────────────


class OrchestratorRunRequest(BaseModel):
    query: str = ""
    business_context: str = ""


class MarketResearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    competitor_linkedin_urls: list[str] = Field(default_factory=list)


class CommunityRequest(BaseModel):
    query: str = Field(..., min_length=1)
    subreddit: str | None = None
    draft_replies: bool = True


class BrandMonitorRequest(BaseModel):
    brand_name: str = Field(..., min_length=1)


class PartnershipDiscoverRequest(BaseModel):
    query: str = Field(..., min_length=1)
    lead_type: str = "other"


class PartnershipPitchRequest(BaseModel):
    our_context: str = ""


class PartnershipStatusRequest(BaseModel):
    status: str


class ContentStrategyRequest(BaseModel):
    business_context: str = ""
    num_weeks: int = Field(default=4, ge=1, le=8)


class SEOStrategyRequest(BaseModel):
    business_context: str = ""


class GEORequest(BaseModel):
    article_id: str | None = None
    title: str | None = None
    content: str | None = None


class ContentWriterRequest(BaseModel):
    content_type: str = "blog post"
    topic: str = Field(..., min_length=1)
    context: str = ""
    publish: bool = True


class LinkedInContentRequest(BaseModel):
    post_type: str = "educational"
    topic: str = Field(..., min_length=1)
    context: str = ""


class SocialMediaRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    platforms: list[str] = Field(default_factory=lambda: ["linkedin", "x"])
    context: str = ""


class VideoStrategyRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    context: str = ""


class CreativeDesignRequest(BaseModel):
    asset_type: str = "social graphic"
    topic: str = Field(..., min_length=1)
    context: str = ""


class EmailCampaignRequest(BaseModel):
    campaign_type: str = "newsletter"
    context: str = ""
    audience_status: str | None = None


class WhatsAppCampaignRequest(BaseModel):
    campaign_type: str = "promotional"
    context: str = ""
    tag: str | None = None


class CampaignPlanRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    goal: str = Field(..., min_length=1)
    channels: list[str] = Field(default_factory=list)
    context: str = ""


class CampaignStatusRequest(BaseModel):
    status: str


class AutomationTriggerRequest(BaseModel):
    workflow_name: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class AnalyticsReportRequest(BaseModel):
    period: str | None = None


class ProductMarketingRequest(BaseModel):
    feature: str = Field(..., min_length=1)
    context: str = ""


# ── Marketing Orchestrator ────────────────────────────────────────────────


@router.post("/orchestrator/run")
def run_orchestrator(
    req: OrchestratorRunRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_orchestrator import run_marketing_cycle

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("marketing_orchestrator")
    return run_marketing_cycle(query=req.query, business_context=req.business_context, organization_id=tenant.organization_id)


# ── Agent 1, 16, 17, 19: Research crew ────────────────────────────────────


@router.post("/market-research")
def market_research(
    req: MarketResearchRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_research import run_market_research

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("market_research_agent")
    return run_market_research(req.query, req.competitor_linkedin_urls or None, organization_id=tenant.organization_id)


@router.post("/community-engagement")
def community_engagement(
    req: CommunityRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_research import monitor_communities

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("community_engagement_agent")
    return monitor_communities(req.query, req.subreddit, req.draft_replies, organization_id=tenant.organization_id)


@router.post("/brand-monitoring")
def brand_monitoring(
    req: BrandMonitorRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_research import monitor_brand_mentions

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("brand_monitoring_agent")
    return monitor_brand_mentions(req.brand_name, organization_id=tenant.organization_id)


@router.post("/partnership/discover")
def partnership_discover(
    req: PartnershipDiscoverRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_research import discover_partnership_leads

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("partnership_influencer_agent")
    return discover_partnership_leads(req.query, req.lead_type, organization_id=tenant.organization_id)


@router.get("/partnership/leads")
def partnership_list(
    http_request: Request, status: str | None = Query(None), _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.services.marketing_research import list_partnership_leads

    tenant = require_tenant_context(http_request)
    leads = list_partnership_leads(status, organization_id=tenant.organization_id)
    return {"ok": True, "count": len(leads), "leads": leads}


@router.post("/partnership/leads/{lead_id}/pitch")
def partnership_pitch(
    lead_id: str, req: PartnershipPitchRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.services.marketing_research import draft_partnership_pitch

    tenant = require_tenant_context(http_request)
    return draft_partnership_pitch(lead_id, req.our_context, organization_id=tenant.organization_id)


# ── Agent 2, 3, 4, 5, 20: Strategy crew ───────────────────────────────────


@router.post("/persona/update")
def persona_update(http_request: Request, _: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_strategy import update_customer_persona

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("customer_persona_agent")
    return update_customer_persona(organization_id=tenant.organization_id)


@router.get("/persona/list")
def persona_list(http_request: Request, _: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    from revenue_os.services.marketing_strategy import list_personas

    tenant = require_tenant_context(http_request)
    personas = list_personas(organization_id=tenant.organization_id)
    return {"ok": True, "count": len(personas), "personas": personas}


@router.post("/content-strategy")
def content_strategy(
    req: ContentStrategyRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_strategy import build_content_strategy

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("content_strategy_agent")
    return build_content_strategy(req.business_context, req.num_weeks, organization_id=tenant.organization_id)


@router.post("/seo-strategy")
def seo_strategy(
    req: SEOStrategyRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_strategy import build_seo_strategy

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("seo_strategy_agent")
    return build_seo_strategy(req.business_context, organization_id=tenant.organization_id)


@router.post("/geo")
def geo_analyze(req: GEORequest, http_request: Request, _: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_strategy import analyze_geo_readiness

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("geo_agent")
    return analyze_geo_readiness(req.article_id, req.title, req.content, organization_id=tenant.organization_id)


@router.post("/product-marketing")
def product_marketing(
    req: ProductMarketingRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_strategy import build_product_marketing_kit

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("product_marketing_agent")
    return build_product_marketing_kit(req.feature, req.context, organization_id=tenant.organization_id)


# ── Agent 6, 7, 8, 9, 10: Content crew ─────────────────────────────────────


@router.post("/content-writer")
def content_writer(
    req: ContentWriterRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_content import write_content

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("content_writer_agent")
    return write_content(req.content_type, req.topic, req.context, req.publish, organization_id=tenant.organization_id)


@router.post("/linkedin-content")
def linkedin_content(
    req: LinkedInContentRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_content import draft_linkedin_content

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("linkedin_content_agent")
    return draft_linkedin_content(req.post_type, req.topic, req.context, organization_id=tenant.organization_id)


@router.post("/social-media")
def social_media(
    req: SocialMediaRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_content import draft_social_posts

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("social_media_agent")
    return draft_social_posts(req.topic, req.platforms, req.context, organization_id=tenant.organization_id)


@router.post("/video-strategy")
def video_strategy(
    req: VideoStrategyRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_content import plan_video

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("video_strategy_agent")
    return plan_video(req.topic, req.context, organization_id=tenant.organization_id)


@router.post("/creative-design")
def creative_design(
    req: CreativeDesignRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_content import create_design_brief

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("creative_design_agent")
    return create_design_brief(req.asset_type, req.topic, req.context, organization_id=tenant.organization_id)


# ── Agent 11, 12, 13, 14: Campaign crew ────────────────────────────────────


@router.post("/email-campaign")
def email_campaign(
    req: EmailCampaignRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_campaigns import draft_email_campaign

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("email_marketing_agent")
    return draft_email_campaign(req.campaign_type, req.context, req.audience_status, organization_id=tenant.organization_id)


@router.post("/whatsapp-campaign")
def whatsapp_campaign(
    req: WhatsAppCampaignRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_campaigns import draft_whatsapp_campaign

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("whatsapp_marketing_agent")
    return draft_whatsapp_campaign(req.campaign_type, req.context, req.tag, organization_id=tenant.organization_id)


@router.post("/campaign/plan")
def campaign_plan(
    req: CampaignPlanRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_campaigns import plan_campaign

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("campaign_manager_agent")
    return plan_campaign(req.name, req.goal, req.channels, req.context, organization_id=tenant.organization_id)


@router.get("/campaign/list")
def campaign_list(
    http_request: Request, status: str | None = Query(None), _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.services.marketing_campaigns import list_campaigns

    tenant = require_tenant_context(http_request)
    campaigns = list_campaigns(status, organization_id=tenant.organization_id)
    return {"ok": True, "count": len(campaigns), "campaigns": campaigns}


@router.post("/campaign/{campaign_id}/status")
def campaign_status(
    campaign_id: str, req: CampaignStatusRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.services.marketing_campaigns import update_campaign_status

    tenant = require_tenant_context(http_request)
    return update_campaign_status(campaign_id, req.status, organization_id=tenant.organization_id)


@router.post("/automation/trigger")
def automation_trigger(
    req: AutomationTriggerRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_campaigns import trigger_marketing_automation

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("marketing_automation_agent")
    return trigger_marketing_automation(req.workflow_name, req.payload, organization_id=tenant.organization_id)


# ── Agent 15, 18: Analytics crew ───────────────────────────────────────────


@router.post("/analytics-report")
def analytics_report(
    req: AnalyticsReportRequest, http_request: Request, _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_analytics import generate_analytics_report

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("analytics_attribution_agent")
    return generate_analytics_report(req.period, organization_id=tenant.organization_id)


@router.post("/cro")
def cro_analyze(http_request: Request, _: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services.marketing_analytics import analyze_conversion_funnel

    tenant = require_tenant_context(http_request)
    AgentCoordinator.touch_agent("cro_agent")
    return analyze_conversion_funnel(organization_id=tenant.organization_id)


# ── Shared: research insight log (Agents 1/16/17/20 write to this) ────────


@router.get("/insights")
def list_insights(
    http_request: Request,
    category: str | None = Query(None), agent_name: str | None = Query(None), limit: int = Query(100, le=500),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    from revenue_os.database import SessionLocal
    from revenue_os.models.marketing import MarketingInsight

    tenant = require_tenant_context(http_request)
    db = SessionLocal()
    try:
        q = db.query(MarketingInsight).filter(
            MarketingInsight.organization_id == tenant.organization_id
        ).order_by(MarketingInsight.created_at.desc())
        if category:
            q = q.filter(MarketingInsight.category == category)
        if agent_name:
            q = q.filter(MarketingInsight.agent_name == agent_name)
        rows = q.limit(limit).all()
        return {"ok": True, "count": len(rows), "insights": [
            {"id": str(i.id), "agent_name": i.agent_name, "category": i.category, "title": i.title,
             "summary": i.summary, "source_url": i.source_url, "sentiment": i.sentiment,
             "created_at": i.created_at.isoformat() if i.created_at else None}
            for i in rows
        ]}
    finally:
        db.close()
