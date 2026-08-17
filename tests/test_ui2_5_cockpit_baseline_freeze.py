"""UI2.5 — Executive Cockpit v1 baseline freeze regression suite."""

from __future__ import annotations

import inspect
from typing import Any

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.cockpit as cockpit_mod
import runner_api_routers.ui as ui_mod
from revenue_os.services.cockpit_read_model import build_cockpit_snapshot

FROZEN_PANELS = frozenset(
    {"attention", "sales", "marketing_seo", "commercial_flow", "governance"}
)

FROZEN_SOURCE_FUNCTIONS = frozenset(
    {
        "_load_pending_qualified_demands",
        "_load_sales_snapshot",
        "build_editorial_pending",
        "list_queue",
        "analyze_site",
        "analyze_technical_site",
    }
)


@pytest.fixture
def client(cms_client: TestClient) -> TestClient:
    return cms_client


def test_freeze_cockpit_route_contract(client: TestClient) -> None:
    r = client.get("/cockpit")
    assert r.status_code == 200
    assert "Executive Cockpit" in r.text
    assert 'extends "base.html"' not in r.text  # rendered HTML


def test_freeze_canonical_jinja_shell(client: TestClient) -> None:
    r = client.get("/cockpit")
    assert "Founder OS" in r.text
    assert 'data-testid="panel-attention"' in r.text


def test_freeze_five_panel_semantic_composition() -> None:
    snap = build_cockpit_snapshot()
    assert set(snap["panels"].keys()) == FROZEN_PANELS


def test_freeze_get_cockpit_no_mutation(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /cockpit must not invoke canonical mutation services."""
    mutations: list[str] = []

    def _block_accept(*_a, **_k):  # noqa: ANN002
        mutations.append("accept")
        raise AssertionError("GET must not accept qualified demand")

    def _block_status(*_a, **_k):  # noqa: ANN002
        mutations.append("status")
        raise AssertionError("GET must not mutate contact status")

    monkeypatch.setattr(cockpit_mod, "accept_qualified_demand", _block_accept)
    monkeypatch.setattr(cockpit_mod, "apply_contact_status_update", _block_status)
    r = client.get("/cockpit")
    assert r.status_code == 200
    assert mutations == []


def test_freeze_snapshot_read_only_api(client: TestClient) -> None:
    r = client.get("/api/v1/cockpit/snapshot")
    assert r.status_code == 200
    assert set(r.json()["panels"].keys()) == FROZEN_PANELS


def test_freeze_cockpit_action_api_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException
    from runner_api_routers.utils import _verify_api_key
    from runner_api import app

    async def strict_auth(credentials=None):  # noqa: ANN001
        raise HTTPException(status_code=401, detail="Unauthorized")

    monkeypatch.setattr("runner_api_routers.utils._get_runner_api_key", lambda: "test-key-required")
    app.dependency_overrides[_verify_api_key] = strict_auth
    try:
        with TestClient(app) as bare:
            r = bare.post(
                "/api/v1/cockpit/actions/qualified-demand/accept",
                json={"demand_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
            )
            assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_freeze_truthful_data_no_fake_metrics_in_source() -> None:
    src = inspect.getsource(build_cockpit_snapshot)
    assert "fake" not in src.lower()
    assert "placeholder_metric" not in src.lower()
    assert "randint" not in src
    assert "random." not in src


def test_freeze_commercial_flow_revenue_honest() -> None:
    snap = build_cockpit_snapshot()
    stages = snap["panels"]["commercial_flow"]["data"]["stages"]
    revenue = next(s for s in stages if "Revenue" in s["label"])
    assert revenue["state"] == "emerging"
    assert "NOT YET ACTIVE" in revenue["detail"]


def test_freeze_degraded_db_unavailable_truthful(monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy.exc import SQLAlchemyError

    class _BrokenSession:
        def query(self, *_a):  # noqa: ANN002
            raise SQLAlchemyError("connection refused")

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        "revenue_os.services.cockpit_read_model.SessionLocal",
        lambda: _BrokenSession(),
    )
    snap = build_cockpit_snapshot()
    assert snap["panels"]["sales"]["state"] == "unavailable"
    assert "unavailable" in snap["panels"]["sales"]["message"].lower()
    assert snap["panels"]["sales"]["data"] == {}


def test_freeze_qualified_demand_accept_uses_trusted_operator(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", "Krishna Founder")
    captured: list[str] = []

    def _accept(db, did, rb, notes=""):  # noqa: ANN001
        captured.append(rb)
        return {"ok": True, "idempotent": True, "demand_id": did}

    monkeypatch.setattr(cockpit_mod, "accept_qualified_demand", _accept)
    monkeypatch.setattr(cockpit_mod, "SessionLocal", lambda: type("DB", (), {"close": lambda s: None})())
    r = client.post(
        "/api/v1/cockpit/actions/qualified-demand/accept",
        json={"demand_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "requested_by": "agent:spoof"},
    )
    assert r.status_code == 200
    assert captured == ["Krishna Founder"]


def test_freeze_contact_status_uses_trusted_operator(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", "Krishna Founder")

    def _apply(db, contact, status, *, requested_by):  # noqa: ANN001
        return {"changed": True, "old_status": "lead", "new_status": status.value}

    monkeypatch.setattr(cockpit_mod, "apply_contact_status_update", _apply)
    monkeypatch.setattr(
        cockpit_mod,
        "SessionLocal",
        lambda: type(
            "DB",
            (),
            {
                "get": lambda s, m, i: type("C", (), {"id": i})(),
                "close": lambda s: None,
            },
        )(),
    )
    r = client.post(
        "/api/v1/cockpit/actions/contact-status",
        json={
            "contact_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "status": "qualified",
            "requested_by": "AI",
        },
    )
    assert r.status_code == 200


def test_freeze_agent_operator_blocked(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", "agent:hermes")
    r = client.post(
        "/api/v1/cockpit/actions/qualified-demand/accept",
        json={"demand_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
    )
    assert r.status_code == 503


def test_freeze_ai_operator_blocked(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", "AI")
    r = client.post(
        "/api/v1/cockpit/actions/contact-status",
        json={"contact_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "status": "qualified"},
    )
    assert r.status_code == 503


def test_freeze_prohibited_mutations_not_in_template(client: TestClient) -> None:
    r = client.get("/cockpit")
    text = r.text.lower()
    assert "reject intake" not in text
    assert "deal stage" not in text or "a3.5" in text  # frozen baseline mention only
    assert 'data-testid="deal-stage' not in text
    assert "editorial approve" not in text
    assert "publishing promote" not in text


def test_freeze_cockpit_router_only_two_mutations() -> None:
    mutation_routes = [
        r.path
        for r in cockpit_mod.router.routes
        if hasattr(r, "methods") and "POST" in r.methods
    ]
    assert sorted(mutation_routes) == [
        "/api/v1/cockpit/actions/contact-status",
        "/api/v1/cockpit/actions/qualified-demand/accept",
    ]


def test_freeze_no_cockpit_sot_module() -> None:
    import importlib.util

    assert importlib.util.find_spec("revenue_os.models.cockpit") is None


def test_freeze_read_model_imports_authoritative_sources() -> None:
    import revenue_os.services.cockpit_read_model as mod

    src = inspect.getsource(mod)
    for fn in ("build_editorial_pending", "analyze_site", "analyze_technical_site", "list_queue"):
        assert fn in src


def test_freeze_page_cockpit_is_read_composition() -> None:
    src = inspect.getsource(ui_mod.page_cockpit)
    assert "build_cockpit_snapshot(" in src
    assert "accept_qualified_demand" not in src
    assert "apply_contact_status_update" not in src


def test_freeze_marketing_seo_social_blocked() -> None:
    snap = build_cockpit_snapshot()
    social = snap["panels"]["marketing_seo"]["data"].get("social", {})
    assert social.get("state") == "blocked"


def test_freeze_governance_authority_pass_marker() -> None:
    snap = build_cockpit_snapshot()
    gov = snap["panels"]["governance"]["data"]
    assert gov.get("authority_remediation") == "PASS"
    assert gov.get("ui1_1_bypasses_closed") == "3/3"
