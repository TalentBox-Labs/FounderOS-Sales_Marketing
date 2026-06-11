from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from revenue_os.auth import get_current_user
from revenue_os.main import app


class _DummyResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user"}
    monkeypatch.setenv("HERMES_AGENT_URL", "https://hermes.local/agent")
    monkeypatch.setenv("ORCHESTRATION_AUDIT_DIR", str(tmp_path / "orchestration_audit"))
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_orchestration_plan_endpoint_returns_strategy(client: TestClient) -> None:
    r = client.post(
        "/api/v1/orchestration/plan",
        json={
            "backend": "hermes",
            "brand": "workcrew",
            "topic": "faster hiring pipeline",
            "keyword": "ai recruiting automation",
            "geo_target": "United States",
            "funnel_stage": "consideration",
            "audience": "recruiters",
            "channels": ["blog", "linkedin", "email"],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    plan = body["plan"]
    assert plan["brand"] == "workcrew"
    assert "content_strategy" in plan["playbooks"]
    assert "email_marketing" in plan["playbooks"]


def test_orchestration_run_with_mocked_backend_and_audit_persistence(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, timeout=45):
        return _DummyResponse({"accepted": True, "provider": "mocked-hermes"})

    monkeypatch.setattr(
        "revenue_os.services.orchestration_runtime.urllib.request.urlopen",
        fake_urlopen,
    )
    monkeypatch.setattr(
        "revenue_os.services.go_to_market_orchestrator.trigger_workflow",
        lambda name, payload: {"workflow": name, "queued": True},
    )

    r = client.post(
        "/api/v1/orchestration/run",
        json={
            "backend": "hermes",
            "brand": "hirestack",
            "topic": "source qualified engineering candidates",
            "keyword": "technical recruiter outreach",
            "geo_target": "India",
            "funnel_stage": "decision",
            "audience": "talent leads",
            "channels": ["blog", "linkedin", "email", "whatsapp"],
            "run_content": False,
            "run_seo": True,
            "run_email": True,
            "run_whatsapp": False,
            "run_prospecting": False,
            "run_voice_qualification": False,
            "run_meeting_booking": False,
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    result = body["result"]
    assert result["backend"] == "hermes"
    assert result["backend_configured"] is True

    executions = result["executions"]
    assert executions["seo_backend"]["status"] == "ok"
    assert executions["email_backend"]["status"] == "ok"
    assert executions["email_n8n"]["triggered"] is True

    audit = result["audit"]
    assert "run_id" in audit
    assert audit["run_file"].endswith(".json")

    logs_resp = client.get("/api/v1/orchestration/logs?limit=5")
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert logs["ok"] is True
    assert len(logs["runs"]) >= 1
    assert logs["runs"][0]["run_id"] == audit["run_id"]
