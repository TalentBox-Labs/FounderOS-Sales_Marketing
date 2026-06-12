from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from revenue_os.auth import get_current_user
from revenue_os.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: {"id": "test-user"}
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_prospecting_plan_endpoint_returns_stage_allocation_and_leads(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROSPECT_FREE_LIMIT", "10")
    monkeypatch.setenv("PROSPECT_SCRAPER_LIMIT", "20")
    monkeypatch.setenv("PROSPECT_MCP_LIMIT", "40")
    monkeypatch.setenv("PROSPECT_GLOBAL_MAX", "200")

    r = client.post(
        "/api/v1/prospecting/plan",
        json={
            "target_count": 50,
            "min_score": 20,
            "statuses": ["lead", "prospect"],
            "allow_scraper": True,
            "allow_mcp": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    plan = body["plan"]
    assert "stages" in plan
    assert len(plan["stages"]) == 3
    assert "selected_existing_linkedin_contacts" in plan
    assert "unfilled_after_limits" in plan


def test_prospecting_plan_validation_error_for_invalid_score(client: TestClient) -> None:
    r = client.post(
        "/api/v1/prospecting/plan",
        json={
            "target_count": 20,
            "min_score": 101,
            "statuses": ["lead"],
            "allow_scraper": True,
            "allow_mcp": False,
        },
    )
    assert r.status_code == 422
