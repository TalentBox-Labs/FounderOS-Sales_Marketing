"""Heartbeat scheduler and agent registry regression coverage."""

from __future__ import annotations


class TestHeartbeatScheduler:
    def test_initialize_registers_expected_jobs(self) -> None:
        from revenue_os.scheduler import initialize_heartbeat, scheduler

        initialize_heartbeat()  # idempotent — register() upserts
        expected = {
            "score_new_leads", "check_deals_at_risk", "snapshot_pipeline_metrics",
            "hermes_goal_check", "sync_gmail_inbox", "run_marketing_cycle",
        }
        assert expected.issubset(scheduler.jobs.keys())

    def test_run_job_now_persists_a_heartbeat_run(self) -> None:
        from revenue_os.database import SessionLocal
        from revenue_os.models.automation_state import HeartbeatRun
        from revenue_os.scheduler import initialize_heartbeat, scheduler

        initialize_heartbeat()
        result = scheduler.run_job_now("snapshot_pipeline_metrics")
        assert result["status"] == "completed"

        db = SessionLocal()
        try:
            runs = db.query(HeartbeatRun).filter(HeartbeatRun.job_name == "snapshot_pipeline_metrics").all()
            assert len(runs) >= 1
            assert runs[-1].status == "completed"
        finally:
            db.close()

    def test_run_job_now_unknown_job_raises(self) -> None:
        import pytest

        from revenue_os.scheduler import scheduler

        with pytest.raises(KeyError):
            scheduler.run_job_now("this_job_does_not_exist")

    def test_marketing_cycle_job_is_wired_to_orchestrator(self, monkeypatch, revenue_db) -> None:
        """job_run_marketing_cycle is a governed per-org WorkItem, same
        shape as job_sync_gmail_inbox — verified by asserting it actually
        ran the orchestrator for the allowlisted, ACTIVE org and returned
        its real report shape (an 'ok' key and a 'stages' dict) as the
        per-org result."""
        from unittest.mock import patch

        from revenue_os.models.organization import Organization, OrganizationStatus
        from revenue_os.scheduler import job_run_marketing_cycle

        org = Organization(name="Marketing Cycle Test Org", slug="marketing-cycle-test", status=OrganizationStatus.ACTIVE)
        revenue_db.add(org)
        revenue_db.commit()
        revenue_db.refresh(org)
        org_id = str(org.id)

        monkeypatch.setenv("ACP1_AUTONOMOUS_ORGANIZATION_IDS", org_id)
        with patch("revenue_os.integrations.public_sources.search_reddit", return_value=[]), \
             patch("revenue_os.integrations.public_sources.search_hackernews", return_value=[]), \
             patch("revenue_os.integrations.n8n.trigger_workflow", return_value=None):
            result = job_run_marketing_cycle()
        assert result["ok"] is True
        assert org_id in result["organizations"]
        cycle_result = result["results"][0]["result"]
        assert cycle_result["ok"] is True
        assert "stages" in cycle_result


class TestAgentRegistry:
    def test_seed_platform_agents_registers_all_31(self) -> None:
        from revenue_os.agents.orchestration import AgentCoordinator, seed_platform_agents

        seed_platform_agents()  # idempotent — register_agent() upserts
        agents = AgentCoordinator.list_agents()
        names = {a["name"] for a in agents}

        platform = {"heartbeat", "hermes", "copilot", "workflow_engine", "n8n_bridge"}
        sales = {"icp_research_agent", "cold_email_agent", "linkedin_opener_agent",
                 "followup_sequence_agent", "objection_handler_agent"}
        marketing = {
            "market_research_agent", "customer_persona_agent", "content_strategy_agent",
            "seo_strategy_agent", "geo_agent", "content_writer_agent", "linkedin_content_agent",
            "social_media_agent", "video_strategy_agent", "creative_design_agent",
            "email_marketing_agent", "whatsapp_marketing_agent", "campaign_manager_agent",
            "marketing_automation_agent", "analytics_attribution_agent", "community_engagement_agent",
            "brand_monitoring_agent", "cro_agent", "partnership_influencer_agent", "product_marketing_agent",
        }
        assert len(marketing) == 20
        orchestrator = {"marketing_orchestrator"}

        assert platform.issubset(names)
        assert sales.issubset(names)
        assert marketing.issubset(names)
        assert orchestrator.issubset(names)

    def test_list_agents_filters_by_type(self) -> None:
        from revenue_os.agents.orchestration import AgentCoordinator, seed_platform_agents

        seed_platform_agents()
        sdr_agents = AgentCoordinator.list_agents(agent_type="sdr")
        assert len(sdr_agents) == 5
        assert all(a["type"] == "sdr" for a in sdr_agents)

        marketing_agents = AgentCoordinator.list_agents(agent_type="marketing")
        assert len(marketing_agents) == 20

    def test_send_and_read_message(self) -> None:
        from revenue_os.agents.orchestration import AgentCoordinator, seed_platform_agents

        seed_platform_agents()
        sent = AgentCoordinator.send_message("marketing_orchestrator", "copilot", "test handoff", data={"x": 1})
        assert sent is True

        messages = AgentCoordinator.get_messages("copilot", unread_only=True)
        assert any(m["message"] == "test handoff" for m in messages)
