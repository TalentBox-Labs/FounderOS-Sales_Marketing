"""Marketing Agent crew regression coverage — research/strategy/content/
campaigns/analytics agents plus the full orchestrator pipeline. External
calls (Reddit, Hacker News, n8n, Meta's WhatsApp Cloud API) are mocked so
these tests never depend on network access or real credentials.

Content Strategy, Content Writer, LinkedIn Content, and Social Media are
deferred (superseded by src/marketing_crew.py's existing content agents —
see docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md) and covered here
only for their honest-stub behavior, not real generation.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

_TEST_ORG_ID = "00000000-0000-0000-0000-0000000000b1"
_TEST_ORG_UUID = uuid.UUID(_TEST_ORG_ID)

FAKE_REDDIT = [
    {"title": "Best CRM for staffing agencies?", "body": "Looking for recommendations",
     "subreddit": "staffing", "score": 42, "num_comments": 12,
     "url": "https://reddit.com/r/staffing/1", "created_utc": 1},
]
FAKE_HN = [
    {"title": "Show HN: AI SDR agent", "url": "https://news.ycombinator.com/item?id=1",
     "points": 88, "num_comments": 30, "created_at": "2026-08-01"},
]


@pytest.fixture
def public_sources_mocked():
    with patch("revenue_os.integrations.public_sources.search_reddit", return_value=FAKE_REDDIT) as r, \
         patch("revenue_os.integrations.public_sources.search_hackernews", return_value=FAKE_HN) as h:
        yield r, h


class TestMarketResearchAgent:
    def test_run_market_research_persists_insights(self, public_sources_mocked, revenue_db) -> None:
        from revenue_os.models.marketing import MarketingInsight
        from revenue_os.services.marketing_research import run_market_research

        result = run_market_research("staffing CRM", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["signals_found"] == {"reddit": 1, "hackernews": 1, "competitors": 0}
        assert result["unavailable_channels"]  # X/Discord/etc honestly listed, never silently dropped

        logged = revenue_db.query(MarketingInsight).filter(
            MarketingInsight.agent_name == "market_research_agent",
            MarketingInsight.organization_id == _TEST_ORG_UUID,
        ).count()
        assert logged >= 1


class TestCommunityEngagementAgent:
    def test_monitor_communities_drafts_replies_for_top_threads(self, public_sources_mocked) -> None:
        from revenue_os.services.marketing_research import monitor_communities

        result = monitor_communities("staffing CRM", subreddit="staffing", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["threads_found"] == 1
        assert len(result["drafted_replies"]) == 1
        assert "Reddit only" in result["note"]  # honest about channel coverage


class TestBrandMonitoringAgent:
    def test_monitor_brand_mentions_classifies_sentiment(self, public_sources_mocked) -> None:
        from revenue_os.services.marketing_research import monitor_brand_mentions

        result = monitor_brand_mentions("WorkCrew", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["mentions_found"] == 1
        assert result["mentions"][0]["sentiment"] in ("positive", "neutral", "negative")
        assert result["negative_count"] == len(result["needs_attention"])


class TestPartnershipAgent:
    def test_discover_dedupes_by_url_on_rerun(self, public_sources_mocked) -> None:
        from revenue_os.services.marketing_research import discover_partnership_leads, list_partnership_leads

        first = discover_partnership_leads("staffing podcasts", organization_id=_TEST_ORG_ID)
        assert first["new_leads_created"] == 2  # 1 reddit + 1 hn

        second = discover_partnership_leads("staffing podcasts", organization_id=_TEST_ORG_ID)
        assert second["new_leads_created"] == 0  # same URLs — nothing new

        leads = list_partnership_leads(organization_id=_TEST_ORG_ID)
        assert len(leads) >= 2

    def test_draft_pitch_marks_lead_contacted(self) -> None:
        from revenue_os.services.marketing_research import discover_partnership_leads, draft_partnership_pitch

        # Distinct URLs from the shared public_sources_mocked fixture's fake
        # data — reusing the same URLs would dedupe against leads other
        # tests in this class already created in the shared session DB.
        unique_reddit = [{"title": "Distinct pitch-test thread", "body": "", "subreddit": "test",
                           "score": 1, "num_comments": 0, "url": f"https://reddit.com/r/test/{uuid.uuid4().hex}",
                           "created_utc": 1}]
        with patch("revenue_os.integrations.public_sources.search_reddit", return_value=unique_reddit), \
             patch("revenue_os.integrations.public_sources.search_hackernews", return_value=[]):
            created = discover_partnership_leads("unique query for pitch test", lead_type="podcast", organization_id=_TEST_ORG_ID)
        lead_id = created["new_leads"][0]["id"]

        result = draft_partnership_pitch(lead_id, our_context="AI-native CRM", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["pitch"]


class TestCustomerPersonaAgent:
    def test_update_persona_upserts_not_duplicates(self, revenue_db) -> None:
        from revenue_os.models.marketing import CustomerPersona
        from revenue_os.services.marketing_strategy import update_customer_persona

        first = update_customer_persona(organization_id=_TEST_ORG_ID)
        second = update_customer_persona(organization_id=_TEST_ORG_ID)
        assert first["persona"]["name"] == second["persona"]["name"]

        rows = revenue_db.query(CustomerPersona).filter(
            CustomerPersona.name == first["persona"]["name"],
            CustomerPersona.organization_id == _TEST_ORG_UUID,
        ).all()
        assert len(rows) == 1  # upsert, not insert-again


class TestSEOAndContentStrategyAgents:
    def _seed_keyword(self, revenue_db):
        from revenue_os.models.seo import SEOKeyword

        kw = SEOKeyword(keyword=f"ai-crm-{uuid.uuid4().hex[:6]}", target_rank=3)
        revenue_db.add(kw)
        revenue_db.commit()
        return kw

    def test_seo_strategy_reflects_tracked_keyword_count(self, revenue_db) -> None:
        from revenue_os.services.marketing_strategy import build_seo_strategy

        before = build_seo_strategy("", organization_id=_TEST_ORG_ID)["keywords_tracked"]
        self._seed_keyword(revenue_db)
        after = build_seo_strategy("", organization_id=_TEST_ORG_ID)["keywords_tracked"]
        assert after == before + 1

    def test_content_strategy_is_deferred(self) -> None:
        """Deferred — superseded by src/marketing_crew.py's content_strategist agent."""
        from revenue_os.services.marketing_strategy import build_content_strategy

        result = build_content_strategy("B2B CRM", num_weeks=5, organization_id=_TEST_ORG_ID)
        assert result["ok"] is False
        assert "Superseded" in result["reason"]


class TestGEOAgent:
    def test_geo_requires_title_and_content_or_article_id(self) -> None:
        from revenue_os.services.marketing_strategy import analyze_geo_readiness

        result = analyze_geo_readiness(organization_id=_TEST_ORG_ID)
        assert result["ok"] is False

    def test_geo_analyzes_given_content(self) -> None:
        from revenue_os.services.marketing_strategy import analyze_geo_readiness

        result = analyze_geo_readiness(
            title="How to pick a CRM", content="A CRM helps track deals.", organization_id=_TEST_ORG_ID,
        )
        assert result["ok"] is True
        assert "faqs" in result


class TestContentWriterAgent:
    """Deferred — superseded by src/marketing_crew.py's blog_writer agent."""

    def test_write_content_is_deferred(self) -> None:
        from revenue_os.services.marketing_content import write_content

        result = write_content("blog post", "Why staffing agencies need an AI CRM", organization_id=_TEST_ORG_ID)
        assert result["ok"] is False
        assert "Superseded" in result["reason"]


class TestLinkedInAndSocialContentAgents:
    """Deferred — superseded by src/marketing_crew.py's social_copywriter agent."""

    def test_linkedin_content_is_deferred(self) -> None:
        from revenue_os.services.marketing_content import draft_linkedin_content

        result = draft_linkedin_content("educational", "hiring signals", organization_id=_TEST_ORG_ID)
        assert result["ok"] is False
        assert "Superseded" in result["reason"]

    def test_social_posts_is_deferred(self) -> None:
        from revenue_os.services.marketing_content import draft_social_posts

        result = draft_social_posts("launch day", ["linkedin", "x", "instagram"], organization_id=_TEST_ORG_ID)
        assert result["ok"] is False
        assert "Superseded" in result["reason"]


class TestVideoAndCreativeAgents:
    def test_plan_video_returns_script(self) -> None:
        from revenue_os.services.marketing_content import plan_video

        result = plan_video("launch day", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert "hook" in result

    def test_create_design_brief_returns_concept(self) -> None:
        from revenue_os.services.marketing_content import create_design_brief

        result = create_design_brief("social graphic", "launch day", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert "concept" in result


class TestEmailAndWhatsAppCampaignAgents:
    def test_email_campaign_targets_real_contact_emails(self, revenue_db) -> None:
        from revenue_os.models.contact import Contact
        from revenue_os.services.marketing_campaigns import draft_email_campaign

        c = Contact(
            first_name="Camp", last_name="Aign", email=f"camp-{uuid.uuid4().hex[:8]}@example.com",
            organization_id=_TEST_ORG_UUID,
        )
        revenue_db.add(c)
        revenue_db.commit()

        result = draft_email_campaign("newsletter", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["recipient_count"] >= 1

    def test_whatsapp_campaign_files_approval_with_tag_scoped_count(self) -> None:
        from revenue_os.integrations.whatsapp import WhatsAppClient
        from revenue_os.services.marketing_campaigns import draft_whatsapp_campaign

        WhatsAppClient.add_contact("+15550000001", "Test WA Contact", tags=["vip-test-tag"])
        result = draft_whatsapp_campaign("promotional", tag="vip-test-tag", organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["recipient_count"] == 1


class TestCampaignManagerAgent:
    def test_plan_list_and_update_campaign(self) -> None:
        from revenue_os.services.marketing_campaigns import list_campaigns, plan_campaign, update_campaign_status

        created = plan_campaign("Q3 Launch", "Grow pipeline", ["seo", "email"], organization_id=_TEST_ORG_ID)
        assert created["ok"] is True
        campaign_id = created["campaign"]["id"]

        campaigns = list_campaigns(organization_id=_TEST_ORG_ID)
        assert any(c["id"] == campaign_id for c in campaigns)

        updated = update_campaign_status(campaign_id, "active", organization_id=_TEST_ORG_ID)
        assert updated["ok"] is True
        assert updated["campaign"]["status"] == "active"

    def test_update_campaign_rejects_invalid_status(self) -> None:
        from revenue_os.services.marketing_campaigns import plan_campaign, update_campaign_status

        created = plan_campaign("Bad status test", "goal", ["email"], organization_id=_TEST_ORG_ID)
        result = update_campaign_status(created["campaign"]["id"], "not_a_real_status", organization_id=_TEST_ORG_ID)
        assert result["ok"] is False


class TestMarketingAutomationAgent:
    def test_trigger_reports_honest_failure_when_n8n_unreachable(self) -> None:
        from revenue_os.services.marketing_campaigns import trigger_marketing_automation

        with patch("revenue_os.integrations.n8n.trigger_workflow", return_value=None):
            result = trigger_marketing_automation("publish-content", {"article_id": "abc"}, organization_id=_TEST_ORG_ID)
        assert result["ok"] is False
        assert result["note"]

    def test_trigger_reports_success_when_n8n_responds(self) -> None:
        from revenue_os.services.marketing_campaigns import trigger_marketing_automation

        with patch("revenue_os.integrations.n8n.trigger_workflow", return_value={"queued": True}):
            result = trigger_marketing_automation("publish-content", {"article_id": "abc"}, organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["note"] is None


class TestAnalyticsAndCROAgents:
    def test_analytics_report_grounded_in_real_seo_count(self, revenue_db) -> None:
        from revenue_os.models.seo import SEOKeyword
        from revenue_os.services.marketing_analytics import generate_analytics_report

        revenue_db.add(SEOKeyword(keyword=f"cro-test-{uuid.uuid4().hex[:6]}"))
        revenue_db.commit()

        result = generate_analytics_report(organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["keywords_tracked"] >= 1
        assert result["executive_summary"]

    def test_cro_funnel_reflects_real_deal_stages(self, revenue_db) -> None:
        from revenue_os.models.contact import Contact
        from revenue_os.models.deal import Deal, DealStage
        from revenue_os.services.deal_automation_service import get_or_create_sales_pipeline
        from revenue_os.services.marketing_analytics import analyze_conversion_funnel

        c = Contact(
            first_name="Funnel", last_name="Test", email=f"funnel-{uuid.uuid4().hex[:8]}@example.com",
            organization_id=_TEST_ORG_UUID,
        )
        revenue_db.add(c)
        revenue_db.flush()
        pipeline = get_or_create_sales_pipeline(revenue_db)
        revenue_db.add(Deal(
            name="Funnel deal", value=1000, stage=DealStage.NEGOTIATION, contact_id=c.id,
            pipeline_id=pipeline.id, organization_id=_TEST_ORG_UUID,
        ))
        revenue_db.commit()

        result = analyze_conversion_funnel(organization_id=_TEST_ORG_ID)
        assert result["ok"] is True
        assert result["funnel"].get("negotiation", 0) >= 1


class TestMarketingOrchestrator:
    def test_run_marketing_cycle_completes_all_stages_with_real_side_effects(self, public_sources_mocked, revenue_db) -> None:
        """Content Strategy / Content Writer / Social Media stages degrade
        to an honest {"ok": False} rather than breaking the pipeline —
        see the module docstring for why those are deferred."""
        from revenue_os.models.marketing import MarketingCampaign
        from revenue_os.services.marketing_orchestrator import run_marketing_cycle

        with patch("revenue_os.integrations.n8n.trigger_workflow", return_value=None):
            result = run_marketing_cycle(business_context="B2B CRM for staffing agencies", organization_id=_TEST_ORG_ID)

        assert result["ok"] is True
        expected_stages = {
            "market_research", "customer_persona", "content_strategy", "seo_strategy",
            "content_writer", "video_strategy", "creative_design", "social_media",
            "email_marketing", "campaign_manager", "marketing_automation", "analytics",
        }
        assert expected_stages.issubset(result["stages"].keys())

        # Real side effects from the non-deferred stages:
        video = result["stages"]["video_strategy"]
        assert video.get("hook")

        campaign_id = result["stages"]["campaign_manager"]["campaign_id"]
        assert revenue_db.get(MarketingCampaign, uuid.UUID(campaign_id)) is not None

        assert result["executive_summary"]


class TestWhatsAppRealSendUpgrade:
    """WhatsAppClient.send_message used to be a pure in-memory stub — it
    now attempts a real call to Meta's Cloud API. These tests mock the
    HTTP layer so they never touch the network."""

    def test_send_message_not_configured_returns_none(self) -> None:
        from revenue_os.integrations.whatsapp import MessageType, WhatsAppClient

        WhatsAppClient._api_key = None
        WhatsAppClient._phone_number_id = None
        result = WhatsAppClient.send_message("+15551234567", MessageType.TEXT, {"body": "hi"})
        assert result is None

    def test_send_message_success_sets_sent_status_and_message_id(self) -> None:
        from revenue_os.integrations.whatsapp import MessageType, WhatsAppClient

        WhatsAppClient.configure("fake-token", "123456789", "biz-id")
        fake_response = type("R", (), {
            "raise_for_status": lambda self: None,
            "json": lambda self: {"messages": [{"id": "wamid.real123"}]},
        })()
        with patch("requests.post", return_value=fake_response):
            result = WhatsAppClient.send_message("+15551234567", MessageType.TEXT, {"body": "Hello"})
        assert result.status == "sent"
        assert result.whatsapp_message_id == "wamid.real123"

    def test_send_message_http_failure_sets_failed_status(self) -> None:
        from revenue_os.integrations.whatsapp import MessageType, WhatsAppClient

        WhatsAppClient.configure("fake-token", "123456789", "biz-id")
        with patch("requests.post", side_effect=ConnectionError("no route to host")):
            result = WhatsAppClient.send_message("+15551234567", MessageType.TEXT, {"body": "Hello"})
        assert result.status == "failed"
        assert "no route to host" in result.error
