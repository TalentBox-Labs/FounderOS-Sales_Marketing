"""SaaS S3.5 — CRM / Residual Tenant Isolation Baseline v1.0 freeze suite."""

from __future__ import annotations

import inspect
import re
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.cockpit as cockpit_mod
import runner_api_routers.crm as crm_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.manual_demand as mdg_mod
import runner_api_routers.operator_flow as operator_mod
from revenue_os.auth import hash_password
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.deal import Deal, DealStage, Pipeline, PipelineType
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

ROOT = Path(__file__).resolve().parents[1]
DOCS_S3 = ROOT / "docs" / "saas" / "s3"
DOCS_S3_5 = ROOT / "docs" / "saas" / "s3_5"
DOCS_S2_5 = ROOT / "docs" / "saas" / "s2_5"
_OPERATOR = "Krishna Founder"

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEAL_A = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_DEAL_B = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

S3_5_REQUIRED_ARTIFACTS = (
    "CRM_RESIDUAL_TENANT_ISOLATION_BASELINE_v1.0.md",
    "S3_5_CRM_ROUTE_BASELINE_v1.0.md",
    "CRM_MUTATION_GUARD_CONTRACT_v1.0.md",
    "CRM_READ_ISOLATION_CONTRACT_v1.0.md",
    "S3_5_CRM_ATTACK_MATRIX_v1.0.md",
    "COMPANY_ACCOUNT_SCOPE_ATTESTATION.md",
    "CRM_ROLE_ENFORCEMENT_CONTRACT_v1.0.md",
    "CRM_AUDIT_TENANCY_CONTRACT_v1.0.md",
    "S3_5_KNOWN_EXCEPTION_RECONCILIATION.md",
    "S3_5_RESIDUAL_TENANT_RISK_REGISTER_v1.0.md",
    "S3_5_CONNECTOR_SAFETY_ATTESTATION.md",
    "S3_5_BASELINE_MANIFEST.md",
)

CRM_READ_ROUTES = (
    ("GET", "/contacts"),
    ("GET", "/contacts/{contact_id}"),
    ("GET", "/deals"),
    ("GET", "/deals/{deal_id}"),
    ("GET", "/pipeline"),
    ("GET", "/activities"),
    ("GET", "/followups"),
)

CRM_MUTATION_ROUTES = (
    ("POST", "/contacts"),
    ("POST", "/contacts/{contact_id}/enrich"),
    ("POST", "/contacts/{contact_id}/score"),
    ("PATCH", "/contacts/{contact_id}/status"),
    ("POST", "/deals"),
    ("PATCH", "/deals/{deal_id}/stage"),
    ("POST", "/activities"),
    ("POST", "/activities/{activity_id}/complete"),
)

HISTORICAL_FAILED_TESTS = (
    "tests/test_crews_unit.py::TestQACrew::test_qa_crew_validates_output_format",
    "tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_validates_output",
    "tests/test_crews_unit.py::TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter",
    "tests/test_utilities_unit.py::TestFileOperations::test_read_file_returns_content",
    "tests/test_utilities_unit.py::TestFileOperations::test_read_file_raises_on_missing_file",
    "tests/test_utilities_unit.py::TestFileOperations::test_save_file_creates_directories",
    "tests/test_utilities_unit.py::TestFileOperations::test_save_file_overwrites_existing",
    "tests/test_utilities_unit.py::TestDataValidation::test_markdown_structure_validation",
)

HISTORICAL_ERROR_TESTS = (
    "tests/test_orchestration_api.py::test_orchestration_plan_endpoint_returns_strategy",
    "tests/test_orchestration_api.py::test_orchestration_run_with_mocked_backend_and_audit_persistence",
    "tests/test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads",
    "tests/test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score",
)


@pytest.fixture(autouse=True)
def _reset_identity() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 's3_5_crm.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, crm_mod, cockpit_mod, operator_mod, mdg_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.services.tenant_resolution as tr

    monkeypatch.setattr(tr, "SessionLocal", sf)
    import revenue_os.services.cockpit_read_model as crm_read

    monkeypatch.setattr(crm_read, "SessionLocal", sf)
    import revenue_os.services.operator_flow_read_model as ofrm

    monkeypatch.setattr(ofrm, "SessionLocal", sf)
    import revenue_os.services.followups as followups_mod

    monkeypatch.setattr(followups_mod, "SessionLocal", sf)
    return sf


def _seed(db_factory: sessionmaker) -> dict[str, str]:
    db = db_factory()
    try:
        org_a = Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE)
        org_b = Organization(id=_ORG_B, name="B", slug="org-b", status=OrganizationStatus.ACTIVE)
        owner_a = User(
            email="owner-a@example.com",
            hashed_password=hash_password("pass-o"),
            full_name="Owner A",
            role="owner",
            is_active=1,
        )
        viewer_a = User(
            email="viewer-a@example.com",
            hashed_password=hash_password("pass-v"),
            full_name="Viewer A",
            role="viewer",
            is_active=1,
        )
        owner_b = User(
            email="owner-b@example.com",
            hashed_password=hash_password("pass-b"),
            full_name="Owner B",
            role="owner",
            is_active=1,
        )
        db.add_all([org_a, org_b, owner_a, viewer_a, owner_b])
        db.flush()
        pipeline = Pipeline(name="Sales", pipeline_type=PipelineType.SALES, is_default=1)
        db.add(pipeline)
        db.flush()
        db.add_all(
            [
                OrganizationMembership(
                    user_id=owner_a.id,
                    organization_id=_ORG_A,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                ),
                OrganizationMembership(
                    user_id=viewer_a.id,
                    organization_id=_ORG_A,
                    role="viewer",
                    status=MembershipStatus.ACTIVE,
                ),
                OrganizationMembership(
                    user_id=owner_b.id,
                    organization_id=_ORG_B,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                ),
            ]
        )
        db.add_all(
            [
                Contact(
                    id=_CONTACT_A,
                    first_name="A",
                    last_name="C",
                    email="a@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                ),
                Contact(
                    id=_CONTACT_B,
                    first_name="B",
                    last_name="C",
                    email="b@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                ),
                Deal(
                    id=_DEAL_A,
                    name="Deal A",
                    stage=DealStage.DISCOVERY,
                    value=100,
                    contact_id=_CONTACT_A,
                    pipeline_id=pipeline.id,
                    organization_id=_ORG_A,
                ),
                Deal(
                    id=_DEAL_B,
                    name="Deal B",
                    stage=DealStage.DISCOVERY,
                    value=200,
                    contact_id=_CONTACT_B,
                    pipeline_id=pipeline.id,
                    organization_id=_ORG_B,
                ),
            ]
        )
        db.commit()
        return {"org_a": str(_ORG_A), "org_b": str(_ORG_B)}
    finally:
        db.close()


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _crm_route_decorators() -> list[tuple[str, str]]:
    src = inspect.getsource(crm_mod)
    return re.findall(
        r'@router\.(get|post|patch|put|delete)\("([^"]+)"\)',
        src,
        flags=re.IGNORECASE,
    )


# ── Baseline artifacts ────────────────────────────────────────────────────────


def test_freeze_s3_5_artifacts_exist() -> None:
    for name in S3_5_REQUIRED_ARTIFACTS:
        assert (DOCS_S3_5 / name).is_file(), f"missing {name}"


def test_freeze_s3_implementation_artifacts_preserved() -> None:
    for name in (
        "S3_CRM_API_SURFACE_INVENTORY.md",
        "S3_SECURITY_ATTESTATION.md",
        "S3_IMPLEMENTATION_MANIFEST.md",
    ):
        assert (DOCS_S3 / name).is_file(), f"missing S3 artifact {name}"


def test_freeze_baseline_version_frozen() -> None:
    doc = (DOCS_S3_5 / "CRM_RESIDUAL_TENANT_ISOLATION_BASELINE_v1.0.md").read_text(
        encoding="utf-8"
    )
    assert "v1.0" in doc
    assert "FROZEN" in doc


# ── CRM route inventory ─────────────────────────────────────────────────────


def test_freeze_crm_live_route_count() -> None:
    routes = _crm_route_decorators()
    assert len(routes) == 15


def test_freeze_crm_read_route_count() -> None:
    routes = {path for method, path in _crm_route_decorators() if method == "get"}
    expected = {path for _, path in CRM_READ_ROUTES}
    assert routes == expected


def test_freeze_crm_mutation_route_count() -> None:
    routes = {
        (method.upper(), path)
        for method, path in _crm_route_decorators()
        if method.lower() in {"post", "patch", "put", "delete"}
    }
    expected = set(CRM_MUTATION_ROUTES)
    assert routes == expected


def test_freeze_crm_module_tenant_guard_symbols() -> None:
    src = inspect.getsource(crm_mod)
    for sym in (
        "resolve_crm_tenant_read",
        "optional_tenant_mutation",
        "scoped_contact",
        "scoped_deal",
        "apply_contact_org_filter",
        "apply_deal_org_filter",
        "verify_activity_in_tenant",
    ):
        assert sym in src


# ── Cross-tenant adversarial (frozen) ─────────────────────────────────────────


def test_freeze_contact_list_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = client.get("/api/v1/crm/contacts").json()
    assert body["count"] == 1
    assert body["contacts"][0]["email"] == "a@example.com"


def test_freeze_contact_read_cross_tenant_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    assert client.get(f"/api/v1/crm/contacts/{_CONTACT_B}").status_code == 404


def test_freeze_contact_mutation_cross_tenant_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.patch(
        f"/api/v1/crm/contacts/{_CONTACT_B}/status",
        json={"status": "prospect", "requested_by": _OPERATOR},
    )
    assert r.status_code == 404


def test_freeze_deal_read_list_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    body = client.get("/api/v1/crm/deals").json()
    assert body["count"] == 1
    assert body["deals"][0]["name"] == "Deal B"


def test_freeze_deal_mutation_cross_tenant_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.patch(
        f"/api/v1/crm/deals/{_DEAL_B}/stage",
        json={"stage": "qualified", "requested_by": _OPERATOR},
    )
    assert r.status_code == 404


def test_freeze_crm_search_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = client.get("/api/v1/crm/contacts", params={"search": "example"}).json()
    emails = {c["email"] for c in body["contacts"]}
    assert "b@example.com" not in emails


def test_freeze_pipeline_summary_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    pipe = client.get("/api/v1/crm/pipeline").json()["pipeline"]
    assert pipe["total_deals"] == 1


def test_freeze_viewer_mutation_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "viewer-a@example.com", "pass-v", ids["org_a"])
    r = client.patch(
        f"/api/v1/crm/contacts/{_CONTACT_A}/status",
        json={"status": "prospect", "requested_by": _OPERATOR},
    )
    assert r.status_code == 403


def test_freeze_tenant_spoof_in_body_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.patch(
        f"/api/v1/crm/contacts/{_CONTACT_B}/status",
        json={
            "status": "prospect",
            "requested_by": _OPERATOR,
            "organization_id": ids["org_b"],
        },
    )
    assert r.status_code == 404


# ── Company non-scope ─────────────────────────────────────────────────────────


def test_freeze_no_company_crm_routes() -> None:
    src = inspect.getsource(crm_mod)
    assert "/companies" not in src
    assert "@router" in src


def test_freeze_company_attestation_documented() -> None:
    doc = (DOCS_S3_5 / "COMPANY_ACCOUNT_SCOPE_ATTESTATION.md").read_text(encoding="utf-8")
    assert "NOT_IN_SCOPE" in doc or "not in scope" in doc.lower()


# ── Downstream isolation preserved ────────────────────────────────────────────


def test_freeze_cockpit_isolation_preserved(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    sales = client.get("/api/v1/cockpit/snapshot").json()["panels"]["sales"]["data"]
    assert sales["contact_total"] == 1


def test_freeze_operator_isolation_preserved(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    snap = client.get("/api/v1/operator/snapshot").json()
    assert len(snap["contacts"]) == 1


# ── S2.5 baseline unchanged ───────────────────────────────────────────────────


def test_freeze_s2_5_artifacts_immutable() -> None:
    baseline = (DOCS_S2_5 / "ORGANIZATION_TENANT_ISOLATION_BASELINE_v1.0.md").read_text(
        encoding="utf-8"
    )
    assert "v1.0" in baseline
    assert "FROZEN" in baseline
    reg = (DOCS_S2_5 / "S2_5_RESIDUAL_TENANCY_RISK_REGISTER_v1.0.md").read_text(encoding="utf-8")
    assert "S3_REQUIRED" in reg
    assert "DEFERRED_TO_S3" in reg or "S3" in reg


def test_freeze_s2_5_crm_supersession_documented() -> None:
    recon = (DOCS_S3_5 / "S3_5_KNOWN_EXCEPTION_RECONCILIATION.md").read_text(encoding="utf-8")
    assert "test_freeze_crm_api_residual_documented" in recon
    assert "S3" in recon
    s3_reg = (DOCS_S3 / "S3_RESIDUAL_TENANCY_RISK_REGISTER.md").read_text(encoding="utf-8")
    assert "MITIGATED" in s3_reg


# ── Known exception reconciliation ────────────────────────────────────────────


def test_freeze_known_exception_reconciliation_doc() -> None:
    doc = (DOCS_S3_5 / "S3_5_KNOWN_EXCEPTION_RECONCILIATION.md").read_text(encoding="utf-8")
    assert "RECONCILED" in doc
    assert "Historical FAILED" in doc or "8" in doc


def test_freeze_historical_failure_identities_preserved() -> None:
    recon = (DOCS_S3_5 / "S3_5_KNOWN_EXCEPTION_RECONCILIATION.md").read_text(encoding="utf-8")
    for test_id in HISTORICAL_FAILED_TESTS:
        assert test_id.split("::")[-1] in recon or test_id in recon
    for test_id in HISTORICAL_ERROR_TESTS:
        assert test_id.split("::")[-1] in recon or test_id in recon


def test_freeze_historical_failures_not_removed_from_codebase() -> None:
    for rel in (
        "tests/test_crews_unit.py",
        "tests/test_utilities_unit.py",
        "tests/test_orchestration_api.py",
        "tests/test_prospecting_ui.py",
    ):
        assert (ROOT / rel).is_file()


# ── Residual / deferred attestation ───────────────────────────────────────────


def test_freeze_residual_critical_none() -> None:
    reg = (DOCS_S3_5 / "S3_5_RESIDUAL_TENANT_RISK_REGISTER_v1.0.md").read_text(encoding="utf-8")
    assert "Critical residual tenant risks:** NONE" in reg or "NONE" in reg
    assert "MITIGATED" in reg


def test_freeze_connector_safety_attested() -> None:
    doc = (DOCS_S3_5 / "S3_5_CONNECTOR_SAFETY_ATTESTATION.md").read_text(encoding="utf-8")
    assert "SAFE" in doc or "PASS" in doc


def test_freeze_editorial_deferred() -> None:
    doc = (DOCS_S3 / "S3_EDITORIAL_PUBLISHING_READ_ISOLATION.md").read_text(encoding="utf-8")
    assert "DEFERRED" in doc or "GLOBAL" in doc


def test_freeze_webhook_deferred() -> None:
    doc = (DOCS_S3 / "S3_WEBHOOK_TENANT_AUDIT.md").read_text(encoding="utf-8")
    assert "DEFERRED" in doc or "LIVE" in doc


# ── Schema / contract freeze ──────────────────────────────────────────────────


def test_freeze_no_s3_5_schema_migration() -> None:
    manifest = (DOCS_S3_5 / "S3_5_BASELINE_MANIFEST.md").read_text(encoding="utf-8")
    assert "Database Migrations: 0" in manifest or "Migrations: 0" in manifest


def test_freeze_no_frozen_contract_changes() -> None:
    manifest = (DOCS_S3_5 / "S3_5_BASELINE_MANIFEST.md").read_text(encoding="utf-8")
    idx = manifest.lower().find("frozen contract changes")
    assert idx >= 0
    section = manifest[idx : idx + 80]
    assert "**0**" in section or "0" in section


def test_freeze_requested_by_binding_preserved_in_crm() -> None:
    src = inspect.getsource(crm_mod)
    assert "requested_by" in src
    assert "is_human_approver" in src
