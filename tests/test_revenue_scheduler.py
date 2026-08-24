"""Heartbeat scheduler and agent registry regression coverage."""

from __future__ import annotations


class TestHeartbeatScheduler:
    def test_initialize_registers_expected_jobs(self) -> None:
        from revenue_os.scheduler import initialize_heartbeat, scheduler

        initialize_heartbeat()  # idempotent — register() upserts
        expected = {
            "score_new_leads", "check_deals_at_risk", "snapshot_pipeline_metrics",
            "hermes_goal_check", "sync_gmail_inbox",
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


class TestAgentRegistry:
    def test_seed_platform_agents_registers_sales_and_platform_agents(self) -> None:
        from revenue_os.agents.orchestration import AgentCoordinator, seed_platform_agents

        seed_platform_agents()  # idempotent — register_agent() upserts
        agents = AgentCoordinator.list_agents()
        names = {a["name"] for a in agents}

        platform = {"heartbeat", "hermes", "copilot", "workflow_engine", "n8n_bridge"}
        sales = {"icp_research_agent", "cold_email_agent", "linkedin_opener_agent",
                 "followup_sequence_agent", "objection_handler_agent"}

        assert platform.issubset(names)
        assert sales.issubset(names)

    def test_list_agents_filters_by_type(self) -> None:
        from revenue_os.agents.orchestration import AgentCoordinator, seed_platform_agents

        seed_platform_agents()
        sdr_agents = AgentCoordinator.list_agents(agent_type="sdr")
        assert len(sdr_agents) == 5
        assert all(a["type"] == "sdr" for a in sdr_agents)

    def test_send_and_read_message(self) -> None:
        from revenue_os.agents.orchestration import AgentCoordinator, seed_platform_agents

        seed_platform_agents()
        sent = AgentCoordinator.send_message("marketing_orchestrator", "copilot", "test handoff", data={"x": 1})
        assert sent is True

        messages = AgentCoordinator.get_messages("copilot", unread_only=True)
        assert any(m["message"] == "test handoff" for m in messages)
