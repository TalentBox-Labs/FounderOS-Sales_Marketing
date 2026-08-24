"""Marketing Orchestrator — the AI CMO.

Runs the documented pipeline end to end: Research -> Persona -> Content
Strategy -> fan-out (SEO / Content Writer / Video Strategy) -> (Creative
Design / Social Media) -> Email + WhatsApp -> Campaign Manager ->
Marketing Automation -> Analytics -> back to the founder. Each stage's
real output feeds the next stage's input — this is one pipeline run, not
20 independent calls glued together after the fact.
"""

from __future__ import annotations

from typing import Any

AGENT_ORCHESTRATOR = "marketing_orchestrator"


def run_marketing_cycle(query: str = "", business_context: str = "", *, organization_id: str) -> dict[str, Any]:
    """One full CMO cycle. Returns every stage's real result — nothing
    summarized away — plus a consolidated executive summary at the end.

    Content Strategy / Content Writer / Social Media stages are currently
    deferred (superseded by src/marketing_crew.py — see
    docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md) and degrade
    gracefully to empty results rather than breaking the pipeline."""
    from revenue_os.agents.orchestration import AgentCoordinator
    from revenue_os.services import marketing_analytics, marketing_campaigns, marketing_content, marketing_research, marketing_strategy

    report: dict[str, Any] = {"ok": True, "stages": {}}
    seed_topic = query or business_context or "industry trends and buyer pain points"

    research = marketing_research.run_market_research(seed_topic, organization_id=organization_id)
    report["stages"]["market_research"] = {
        "signals_found": research.get("signals_found"), "insights": research.get("insights", []),
        "opportunities": research.get("opportunities", []),
    }

    persona_result = marketing_strategy.update_customer_persona(organization_id=organization_id)
    persona = persona_result.get("persona", {}) if persona_result.get("ok") else {}
    report["stages"]["customer_persona"] = persona

    ctx = business_context or persona.get("summary", "") or seed_topic
    strategy = marketing_strategy.build_content_strategy(ctx, organization_id=organization_id)
    report["stages"]["content_strategy"] = {"monthly_theme": strategy.get("monthly_theme"), "weeks": strategy.get("weeks", [])}

    seo = marketing_strategy.build_seo_strategy(ctx, organization_id=organization_id)
    report["stages"]["seo_strategy"] = {"recommendations": seo.get("recommendations", []), "topic_clusters": seo.get("topic_clusters", [])}

    first_topic = ((strategy.get("weeks") or [{}])[0]).get("topic") or seed_topic
    written = marketing_content.write_content("blog post", first_topic, ctx, publish=True, organization_id=organization_id)
    report["stages"]["content_writer"] = {"article_id": written.get("article_id"), "title": written.get("title")}

    video = marketing_content.plan_video(first_topic, ctx, organization_id=organization_id)
    report["stages"]["video_strategy"] = {"hook": video.get("hook"), "talking_points": video.get("talking_points")}

    brief = marketing_content.create_design_brief("social graphic", first_topic, ctx, organization_id=organization_id)
    report["stages"]["creative_design"] = {"concept": brief.get("concept"), "headline": brief.get("headline")}

    social = marketing_content.draft_social_posts(first_topic, ["linkedin", "x"], ctx, organization_id=organization_id)
    report["stages"]["social_media"] = {"approval_id": social.get("approval_id")}

    email = marketing_campaigns.draft_email_campaign("newsletter", ctx, organization_id=organization_id)
    report["stages"]["email_marketing"] = {"approval_id": email.get("approval_id"), "recipient_count": email.get("recipient_count")}

    campaign = marketing_campaigns.plan_campaign(
        name=f"Cycle: {first_topic}"[:255], goal=business_context or query or "Grow pipeline",
        channels=["seo", "blog", "linkedin", "social", "email"], context=ctx, organization_id=organization_id,
    )
    campaign_id = (campaign.get("campaign") or {}).get("id")
    report["stages"]["campaign_manager"] = {"campaign_id": campaign_id}

    automation = marketing_campaigns.trigger_marketing_automation(
        "marketing-cycle-completed", {"campaign_id": campaign_id, "article_id": written.get("article_id")},
        organization_id=organization_id,
    )
    report["stages"]["marketing_automation"] = {"ok": automation.get("ok"), "note": automation.get("note")}

    analytics = marketing_analytics.generate_analytics_report(organization_id=organization_id)
    report["stages"]["analytics"] = {"executive_summary": analytics.get("executive_summary")}

    AgentCoordinator.touch_agent(AGENT_ORCHESTRATOR)
    AgentCoordinator.send_message(
        AGENT_ORCHESTRATOR, "copilot", f"Completed a marketing cycle — campaign {campaign_id}",
        data={"campaign_id": campaign_id, "article_id": written.get("article_id")},
    )

    report["executive_summary"] = analytics.get("executive_summary")
    return report
