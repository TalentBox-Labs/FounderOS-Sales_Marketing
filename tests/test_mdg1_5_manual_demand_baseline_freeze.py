"""MDG1.5 — Manual Demand Registration Baseline v1.0 freeze suite."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.cockpit as cockpit_mod
import runner_api_routers.manual_demand as mdg
import runner_api_routers.operator_flow as of_router
import runner_api_routers.ui as ui_mod
import tests.test_a3_runner_deal_stage as a3
import tests.test_a4_runner_contact_status as a4
import tests.test_mc04_qualified_demand as mc04
import tests.test_mc06_5_commercial_outcome_baseline_freeze as mc06_5
import tests.test_mdg1_manual_demand_registration as mdg1
import tests.test_of1_5_operator_flow_baseline_freeze as of15
import tests.test_of1_operator_flow as of1
import tests.test_sales_api_runner as a1
import tests.test_ui2_5_cockpit_baseline_freeze as ui25
from runner_api import app

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "marketing" / "mdg1_5"

FROZEN_GET = "/operator/demand/register"
FROZEN_POST = "/api/v1/mdg/manual-demand/register"
FROZEN_MIGRATION_HEAD = "e8278e1169e6_full_schema.py"

A1_5_KNOWN_EXCEPTIONS = (
    "tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads",
    "tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score",
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def operator_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", mdg1._OPERATOR)


def _baseline() -> str:
    return (DOCS / "MANUAL_DEMAND_REGISTRATION_BASELINE_v1.0.md").read_text(encoding="utf-8")


def _proxy_source() -> str:
    return inspect.getsource(mdg)


def test_freeze_registration_get_route(client: TestClient) -> None:
    r = client.get(FROZEN_GET)
    assert r.status_code == 200
    assert "Manual Demand Registration" in r.text
    assert "Founder OS" in r.text
    assert '{% extends "base.html" %}' in (
        ROOT / "templates" / "operator_demand_register.html"
    ).read_text(encoding="utf-8")
    assert "page_manual_demand_register" in inspect.getsource(ui_mod)


def test_freeze_registration_post_route() -> None:
    routes = {
        (
            mdg.router.prefix + route.path
            if not route.path.startswith(mdg.router.prefix)
            else route.path
        )
        for route in mdg.router.routes
        if hasattr(route, "methods") and "POST" in route.methods
    }
    # FastAPI APIRoute.path is relative to prefix
    posts = set()
    for route in mdg.router.routes:
        if hasattr(route, "methods") and "POST" in route.methods:
            path = route.path
            full = path if path.startswith("/api") else f"{mdg.router.prefix}{path}"
            posts.add(full)
    assert FROZEN_POST in posts
    assert posts == {FROZEN_POST}


def test_freeze_trusted_human_can_register(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_valid_manual_demand_registers(client, monkeypatch, operator_env)


def test_freeze_anonymous_public_caller_blocked(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    mdg1.test_no_public_anonymous_path(client, monkeypatch)


def test_freeze_agent_mutation_blocked(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    mdg1.test_agent_mutation_blocked(client, monkeypatch)


def test_freeze_ai_mutation_blocked(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    mdg1.test_ai_mutation_blocked(client, monkeypatch)


def test_freeze_spoofed_human_metadata_blocked(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_spoofed_requested_by_ignored(client, monkeypatch, operator_env)
    assert "requested_by" not in mdg.ManualDemandRegisterBody.model_fields


def test_freeze_direct_bypass_blocked() -> None:
    mdg1.test_direct_service_bypass_still_blocked()


def test_freeze_validation() -> None:
    fields = mdg.ManualDemandRegisterBody.model_fields
    assert "email" in fields and fields["email"].is_required()
    assert "source" in fields
    assert fields["source"].default == "manual"
    src = _proxy_source()
    assert "email_has_at" in src
    assert "source_allowed" in src
    assert "ALLOWED_MANUAL_SOURCES" in src


def test_freeze_mc04_5_handoff_reused(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_reuses_mc04_5_register_path(client, monkeypatch, operator_env)
    assert "register_marketing_handoff" in _proxy_source()
    assert "QualifiedDemandPayload" in _proxy_source()


def test_freeze_no_persistent_demand_sot() -> None:
    assert not (ROOT / "revenue_os" / "models" / "demand.py").exists()
    assert not (ROOT / "revenue_os" / "models" / "manual_demand.py").exists()
    assert not (ROOT / "revenue_os" / "models" / "marketing_signal.py").exists()
    src = _proxy_source()
    assert "Ephemeral form model" in src or "ephemeral" in src.lower()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
            assert "Base" not in bases
            assert "DeclarativeBase" not in bases
    versions = sorted(
        p.name
        for p in (ROOT / "migrations" / "versions").glob("*.py")
        if p.name != "__init__.py"
    )
    assert versions == [FROZEN_MIGRATION_HEAD]


def test_freeze_no_contact_auto_create(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_canonical_contact_only_after_accept(client, monkeypatch, operator_env)
    mdg1.test_mc04_5_accept_still_required(client, monkeypatch, operator_env)


def test_freeze_no_deal_auto_create(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_no_automatic_deal_or_revenue(client, monkeypatch, operator_env)


def test_freeze_no_revenue_mutation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    db = mdg1._db()
    monkeypatch.setattr(mdg, "SessionLocal", lambda: db)
    r = client.post(
        FROZEN_POST,
        json={"email": mdg1._EMAIL, "demand_id": mdg1._DEMAND_ID},
    )
    assert r.status_code == 200
    assert r.json()["revenue_mutated"] is False
    assert r.json()["contact_created"] is False
    assert r.json()["deal_created"] is False
    assert r.json()["public_capture"] is False


def test_freeze_provenance_truthful(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_provenance_truthful_no_fabricated_utm(client, monkeypatch, operator_env)


def test_freeze_missing_attribution_not_fabricated() -> None:
    src = _proxy_source()
    assert "utm_source" not in src
    assert "utm_campaign" not in src
    assert "consent=None" in src.replace(" ", "")
    assert "never invent" in src.lower() or "Never invent" in src or "manually_supplied" in src


def test_freeze_idempotency(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_idempotent_retry(client, monkeypatch, operator_env)


def test_freeze_duplicate_safety(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_idempotent_retry(client, monkeypatch, operator_env)


def test_freeze_of1_5_unchanged() -> None:
    of15.test_freeze_operator_action_route_set_unchanged()
    mdg1.test_of1_5_operator_router_unchanged()
    assert "register_marketing_handoff" not in inspect.getsource(of_router)


def test_freeze_ui2_5_unchanged() -> None:
    ui25.test_freeze_cockpit_router_only_two_mutations()
    mutation_routes = [
        route.path
        for route in cockpit_mod.router.routes
        if hasattr(route, "methods") and "POST" in route.methods
    ]
    assert sorted(mutation_routes) == [
        "/api/v1/cockpit/actions/contact-status",
        "/api/v1/cockpit/actions/qualified-demand/accept",
    ]


def test_freeze_mc04_5_unchanged() -> None:
    mc04.test_register_handoff_does_not_create_contact()
    mc04.test_accept_idempotent()


def test_freeze_mc06_5_unchanged() -> None:
    mc06_5.test_freeze_a3_5_emission_false()
    mc06_5.test_freeze_no_shared_sot()
    mc06_5.test_freeze_eligibility_closed_won_only()


def test_freeze_a4_5_unchanged() -> None:
    a4.test_score_contact_does_not_mutate_status()
    a4.test_apply_contact_status_update_same_status_noop()


def test_freeze_a3_5_unchanged() -> None:
    a3.test_apply_deal_stage_update_rejects_reopen()
    a3.test_apply_deal_stage_update_same_stage_noop()


def test_freeze_a1_5_unchanged() -> None:
    a1.test_sales_template_exists()
    exceptions = (
        ROOT / "docs" / "sales" / "SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md"
    ).read_text(encoding="utf-8")
    for identity in A1_5_KNOWN_EXCEPTIONS:
        assert identity in exceptions
    mdg_exc = (DOCS / "MDG1_5_KNOWN_TEST_EXCEPTIONS.md").read_text(encoding="utf-8")
    for identity in A1_5_KNOWN_EXCEPTIONS:
        assert identity.split("::", 1)[1] in mdg_exc


def test_freeze_public_capture_absent(client: TestClient) -> None:
    html = (ROOT / "templates" / "operator_demand_register.html").read_text(encoding="utf-8")
    assert "No public form" in html or "no public form" in html.lower()
    assert "public_capture" in _proxy_source()
    r = client.get(FROZEN_GET)
    assert "anonymous" not in r.text.lower() or "non-anonymous" in r.text.lower() or "No public" in r.text


def test_freeze_anonymous_ingress_absent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("FOUNDER_OS_OPERATOR_NAME", raising=False)
    r = client.post(FROZEN_POST, json={"email": mdg1._EMAIL})
    assert r.status_code == 503
    assert "_trusted_cockpit_operator" in _proxy_source()


def test_freeze_total_upstream_demand_partial() -> None:
    baseline = _baseline()
    assert "PUBLIC / anonymous Audience → Demand capture" in baseline or "Public / anonymous" in baseline
    assert "NOT IMPLEMENTED" in baseline
    assert "PARTIAL" in baseline
    assert "MANUAL_OPERABLE" in baseline or "**OPERABLE**" in baseline
    neg = (DOCS / "MANUAL_DEMAND_NEGATIVE_SCOPE_v1.0.md").read_text(encoding="utf-8")
    assert "public forms" in neg
    assert "website lead capture" in neg


def test_freeze_manual_registration_operable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, operator_env: None
) -> None:
    mdg1.test_registration_ui_opens(client, operator_env)
    mdg1.test_valid_manual_demand_registers(client, monkeypatch, operator_env)
    baseline = _baseline()
    assert "OPERABLE" in baseline


def test_freeze_saas_forward_compatibility() -> None:
    doc = (DOCS / "MANUAL_DEMAND_SAAS_FORWARD_COMPATIBILITY.md").read_text(encoding="utf-8")
    assert "**PASS**" in doc or "Attestation:** **PASS**" in doc
    assert "Do not freeze HOSTED_SINGLE_USER as permanent" in doc
    assert "register_marketing_handoff" in _proxy_source()


def test_freeze_artifacts_present() -> None:
    required = (
        "MANUAL_DEMAND_REGISTRATION_BASELINE_v1.0.md",
        "MANUAL_DEMAND_REGISTRATION_ROUTE_CONTRACT_v1.0.md",
        "MANUAL_DEMAND_AUTHORITY_CONTRACT_v1.0.md",
        "MANUAL_DEMAND_FIELD_VALIDATION_CONTRACT_v1.0.md",
        "MANUAL_DEMAND_PROVENANCE_CONTRACT_v1.0.md",
        "MANUAL_DEMAND_IDEMPOTENCY_CONTRACT_v1.0.md",
        "MANUAL_DEMAND_NEGATIVE_SCOPE_v1.0.md",
        "MANUAL_DEMAND_SAAS_FORWARD_COMPATIBILITY.md",
        "MDG1_5_KNOWN_TEST_EXCEPTIONS.md",
        "MDG1_5_BASELINE_MANIFEST.md",
    )
    for name in required:
        assert (DOCS / name).is_file(), name


def test_freeze_ui1_1_boundary_unchanged() -> None:
    of1.test_ui1_1_service_bypass_still_blocked()
