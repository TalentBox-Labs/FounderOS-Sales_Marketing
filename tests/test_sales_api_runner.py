from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import runner_api
import runner_api_routers.prospecting as prospecting
from runner_api import app

# Valid UUIDs — OutreachSequence.id / Activity.contact_id are UUID columns.
_SEQ_ID = "11111111-1111-1111-1111-111111111111"
_CONTACT_1 = "22222222-2222-2222-2222-222222222222"
_CONTACT_2 = "33333333-3333-3333-3333-333333333333"


class _DummyDB:
    def close(self):
        return None

    def commit(self):
        return None

    def add(self, _obj):
        return None

    def query(self, _model):
        return _DummyQuery()


class _DummyQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return SimpleNamespace(
            id=UUID(_SEQ_ID),
            name="Default Sequence",
            channel="email",
            steps_count=3,
            is_active=1,
        )

    def all(self):
        return [
            SimpleNamespace(
                id=UUID(_SEQ_ID),
                name="Default Sequence",
                channel="email",
                steps_count=3,
                is_active=1,
            )
        ]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_sales_template_exists() -> None:
    template = Path(__file__).resolve().parent.parent / "templates" / "sales.html"
    text = template.read_text(encoding="utf-8")
    assert "Sales Prospecting" in text
    assert "Outreach Import & Execute" in text
    assert "Lead Filters & Sort" in text


def test_runner_prospecting_plan_proxy_with_mocked_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Plan may be served from runner_api or prospecting router; patch both.
    monkeypatch.setattr(runner_api, "SessionLocal", lambda: _DummyDB())
    monkeypatch.setattr(prospecting, "SessionLocal", lambda: _DummyDB())
    plan = {
        "target_count": 55,
        "thresholds": {"scale_step": 25},
        "providers": {
            "scraper": False,
            "apollo_mcp": False,
            "linkedin_sales_navigator_mcp": False,
        },
        "stages": [
            {"stage": "free_linkedin_existing_data", "cap": 10, "used": 5, "note": "free"},
            {"stage": "scraper_platforms", "cap": 20, "used": 0, "note": "scraper"},
            {"stage": "mcp_providers", "cap": 30, "used": 0, "note": "mcp"},
        ],
        "selected_existing_linkedin_contacts": [
            {"id": _CONTACT_1, "name": "A", "lead_score": 70}
        ],
        "unfilled_after_limits": 0,
        "scale_recommendation": {"next_increment": 25, "message": "ok"},
    }
    monkeypatch.setattr(
        runner_api, "build_prospecting_plan", lambda db, **kwargs: {**plan, "target_count": kwargs["target_count"]}
    )
    monkeypatch.setattr(
        prospecting,
        "build_prospecting_plan",
        lambda db, **kwargs: {**plan, "target_count": kwargs["target_count"]},
    )

    r = client.post(
        "/api/v1/prospecting/plan",
        json={
            "target_count": 55,
            "min_score": 20,
            "statuses": ["lead", "prospect"],
            "allow_scraper": True,
            "allow_mcp": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["plan"]["target_count"] == 55
    assert len(body["plan"]["stages"]) == 3


def test_runner_prospecting_preset_save_and_list(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(runner_api, "_presets_file", lambda: tmp_path / "presets.json")
    monkeypatch.setattr(prospecting, "_presets_file", lambda: tmp_path / "presets.json")

    save_resp = client.post(
        "/api/v1/prospecting/presets/save",
        json={
            "name": "SMB Default",
            "brand": "workcrew",
            "team": "sales",
            "target_count": 40,
            "min_score": 25,
            "statuses": ["lead", "prospect"],
            "allow_scraper": True,
            "allow_mcp": False,
        },
    )
    assert save_resp.status_code == 200
    saved = save_resp.json()
    assert saved["ok"] is True

    list_resp = client.get("/api/v1/prospecting/presets?brand=workcrew&team=sales")
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert payload["ok"] is True
    assert len(payload["presets"]) == 1
    assert payload["presets"][0]["name"] == "SMB Default"


def test_runner_prospecting_import_and_execute(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Active route is runner_api_routers.prospecting (included before runner_api dupes).
    monkeypatch.setattr(prospecting, "SessionLocal", lambda: _DummyDB())
    monkeypatch.setattr(runner_api, "SessionLocal", lambda: _DummyDB())
    monkeypatch.setattr(
        runner_api,
        "_schedule_contact_sequence",
        lambda db, sequence, cid: {"contact_id": cid, "steps": 2},
    )
    plan = {
        "target_count": 10,
        "stages": [
            {"stage": "free_linkedin_existing_data", "cap": 10, "used": 2},
            {"stage": "scraper_platforms", "cap": 5, "used": 0},
            {"stage": "mcp_providers", "cap": 5, "used": 0},
        ],
        "selected_existing_linkedin_contacts": [
            {"id": _CONTACT_1},
            {"id": _CONTACT_2},
        ],
        "unfilled_after_limits": 8,
    }
    monkeypatch.setattr(runner_api, "build_prospecting_plan", lambda db, **_kwargs: plan)
    monkeypatch.setattr(prospecting, "build_prospecting_plan", lambda db, **_kwargs: plan)

    import_resp = client.post(
        "/api/v1/prospecting/import",
        json={"sequence_id": _SEQ_ID, "contact_ids": [_CONTACT_1, _CONTACT_2]},
    )
    assert import_resp.status_code == 200
    import_body = import_resp.json()
    assert import_body["ok"] is True
    assert import_body["contacts_imported"] == 2

    execute_resp = client.post(
        "/api/v1/prospecting/execute",
        json={
            "target_count": 30,
            "min_score": 20,
            "statuses": ["lead", "prospect"],
            "allow_scraper": True,
            "allow_mcp": True,
            "execute_stages": ["free_linkedin_existing_data"],
            "sequence_id": _SEQ_ID,
            "auto_import": True,
            "max_import": 10,
        },
    )
    assert execute_resp.status_code == 200
    execute_body = execute_resp.json()
    assert execute_body["ok"] is True
    assert execute_body["executed_stages"]["free_linkedin_existing_data"]["ok"] is True
    assert execute_body["import_result"]["ok"] is True
