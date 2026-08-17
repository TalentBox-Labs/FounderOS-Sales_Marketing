"""SaaS S4.5 — Integration Tenant Isolation Baseline v1.0 freeze suite."""

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
import runner_api_routers.crm as crm_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.n8n_webhooks as n8n_mod
import runner_api_routers.integrations as integrations_mod
from revenue_os.auth import hash_password
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.integrations import ConnectorCredentialRecord, OrganizationIntegrationBinding
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.credentials_vault import (
    hydrate_all_connectors,
    load_credentials,
    save_credentials,
)
from revenue_os.services.integration_tenant_resolution import upsert_n8n_binding
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

ROOT = Path(__file__).resolve().parents[1]
DOCS_S4 = ROOT / "docs" / "saas" / "s4"
DOCS_S4_5 = ROOT / "docs" / "saas" / "s4_5"
DOCS_S3_5 = ROOT / "docs" / "saas" / "s3_5"
_OPERATOR = "Krishna Founder"

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

S4_5_REQUIRED_ARTIFACTS = (
    "INTEGRATION_TENANT_ISOLATION_BASELINE_v1.0.md",
    "S4_5_INTEGRATION_TENANCY_TOPOLOGY_v1.0.md",
    "CONNECTOR_CREDENTIAL_OWNERSHIP_CONTRACT_v1.0.md",
    "GLOBAL_CREDENTIAL_FALLBACK_CONTRACT_v1.0.md",
    "S4_5_CONNECTOR_PATH_MANIFEST_v1.0.md",
    "WEBHOOK_TENANT_BINDING_CONTRACT_v1.0.md",
    "INTEGRATION_IDENTITY_AUTHORITY_CONTRACT_v1.0.md",
    "INTEGRATION_AUDIT_PROVENANCE_CONTRACT_v1.0.md",
    "S4_5_CONNECTOR_MIGRATION_ATTESTATION.md",
    "S4_5_RESIDUAL_INTEGRATION_RISK_REGISTER_v1.0.md",
    "S4_5_KNOWN_EXCEPTION_RECONCILIATION.md",
    "S4_5_BASELINE_MANIFEST.md",
)

TENANT_SCOPED_CONNECTOR_PATHS = (
    "load_credentials(org, allow_global_fallback=False)",
    "save_credentials(org from TenantContext)",
    "delete_credentials(org from TenantContext)",
    "list_configured_connectors(org)",
    "integrations configure_connector",
    "integrations remove_connector",
    "integrations list_connectors oauth check",
    "integrations legacy email/slack/calendar configure",
    "whatsapp configure",
    "linkedin_enrichment org-scoped API key",
)

GLOBAL_BY_DESIGN_CONNECTOR_PATHS = (
    "hydrate_all_connectors startup",
    "CONNECTOR_CATALOG env-backed entries",
    "legacy no-session save/load (org=None)",
    "gmail_sync load without org",
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
    engine = create_engine(f"sqlite:///{tmp_path / 's4_5_int.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, crm_mod, n8n_mod, integrations_mod):
        monkeypatch.setattr(mod, "SessionLocal", sf)
    import revenue_os.services.tenant_resolution as tr

    monkeypatch.setattr(tr, "SessionLocal", sf)
    import revenue_os.database as dbmod

    monkeypatch.setattr(dbmod, "SessionLocal", sf)
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
        owner_b = User(
            email="owner-b@example.com",
            hashed_password=hash_password("pass-b"),
            full_name="Owner B",
            role="owner",
            is_active=1,
        )
        db.add_all([org_a, org_b, owner_a, owner_b])
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
                    lead_score=10,
                ),
                Contact(
                    id=_CONTACT_B,
                    first_name="B",
                    last_name="C",
                    email="b@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                    lead_score=20,
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


def _n8n_routes() -> list[tuple[str, str]]:
    src = inspect.getsource(n8n_mod)
    return re.findall(
        r'@router\.(get|post)\("([^"]+)"\)',
        src,
        flags=re.IGNORECASE,
    )


# ── Baseline artifacts ────────────────────────────────────────────────────────


def test_freeze_s4_5_artifacts_exist() -> None:
    for name in S4_5_REQUIRED_ARTIFACTS:
        assert (DOCS_S4_5 / name).is_file(), f"missing {name}"


def test_freeze_baseline_version_frozen() -> None:
    doc = (DOCS_S4_5 / "INTEGRATION_TENANT_ISOLATION_BASELINE_v1.0.md").read_text(encoding="utf-8")
    assert "FROZEN" in doc
    assert "v1.0" in doc


def test_freeze_s4_implementation_artifacts_preserved() -> None:
    assert (DOCS_S4 / "S4_IMPLEMENTATION_MANIFEST.md").is_file()


def test_freeze_s3_5_baseline_immutable() -> None:
    doc = (DOCS_S3_5 / "CRM_RESIDUAL_TENANT_ISOLATION_BASELINE_v1.0.md").read_text(encoding="utf-8")
    assert "FROZEN" in doc


# ── Model / vault contract ────────────────────────────────────────────────────


def test_freeze_connector_model_has_organization_id() -> None:
    cols = {c.name for c in ConnectorCredentialRecord.__table__.columns}
    assert "organization_id" in cols
    assert "connector_name" in cols


def test_freeze_integration_binding_model_exists() -> None:
    assert OrganizationIntegrationBinding.__tablename__ == "organization_integration_bindings"


def test_freeze_vault_default_no_global_fallback() -> None:
    src = inspect.getsource(load_credentials)
    assert "allow_global_fallback: bool = False" in src


def test_freeze_org_owned_credential_resolves(tenant_db: sessionmaker) -> None:
    org_a = str(_ORG_A)
    save_credentials("slack", "notifications", {"webhook_url": "a"}, organization_id=org_a)
    assert load_credentials("slack", organization_id=org_a) is not None


def test_freeze_cross_org_credential_blocked(tenant_db: sessionmaker) -> None:
    org_a = str(_ORG_A)
    save_credentials("email_smtp", "email", {"host": "a"}, organization_id=org_a)
    assert load_credentials("email_smtp", organization_id=str(_ORG_B)) is None


def test_freeze_connector_name_only_bypass_blocked(tenant_db: sessionmaker) -> None:
    save_credentials("whatsapp", "messaging", {"api_key": "g"}, organization_id=None)
    assert load_credentials("whatsapp", organization_id=str(_ORG_A), allow_global_fallback=False) is None


def test_freeze_null_org_only_global_serves_legacy_lookup(tenant_db: sessionmaker) -> None:
    save_credentials("google_calendar", "calendar", {"access_token": "t"}, organization_id=None)
    assert load_credentials("google_calendar", organization_id=None) is not None
    assert load_credentials("google_calendar", organization_id=str(_ORG_A), allow_global_fallback=False) is None


def test_freeze_connector_path_counts_documented() -> None:
    manifest = (DOCS_S4_5 / "S4_5_CONNECTOR_PATH_MANIFEST_v1.0.md").read_text(encoding="utf-8")
    assert str(len(TENANT_SCOPED_CONNECTOR_PATHS)) in manifest or "10" in manifest
    assert "GLOBAL_BY_DESIGN" in manifest


# ── Webhook freeze ────────────────────────────────────────────────────────────


def test_freeze_n8n_route_count() -> None:
    routes = _n8n_routes()
    assert len(routes) == 2


def test_freeze_n8n_post_tenant_binding_in_code() -> None:
    src = inspect.getsource(n8n_mod)
    assert "resolve_n8n_organization_id" in src
    assert "scoped_contact" in src


def test_freeze_cross_tenant_contact_id_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], "freeze-secret-a")
    db = tenant_db()
    try:
        before = db.get(Contact, _CONTACT_B).lead_score
    finally:
        db.close()
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_B), "organization_id": ids["org_b"]},
        headers={"X-N8N-Secret": "freeze-secret-a"},
    )
    assert r.status_code == 404
    db = tenant_db()
    try:
        assert db.get(Contact, _CONTACT_B).lead_score == before
    finally:
        db.close()


def test_freeze_payload_org_does_not_establish_authority(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], "freeze-secret-b")
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_B), "organization_id": ids["org_b"], "tenant_id": ids["org_b"]},
        headers={"X-N8N-Secret": "freeze-secret-b"},
    )
    assert r.status_code == 404


def test_freeze_n8n_same_tenant_allowed(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], "freeze-secret-c")
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_A)},
        headers={"X-N8N-Secret": "freeze-secret-c"},
    )
    assert r.status_code == 200


# ── Identity / audit ──────────────────────────────────────────────────────────


def test_freeze_integration_service_identity_not_human() -> None:
    from revenue_os.services.integration_tenant_resolution import build_integration_tenant_context

    tenant = build_integration_tenant_context(str(_ORG_A))
    assert tenant.identity.is_human is False
    assert tenant.identity.principal_kind.value == "SERVICE"


def test_freeze_n8n_redacts_secrets_in_audit() -> None:
    src = inspect.getsource(n8n_mod)
    assert "_redact_payload" in src


def test_freeze_crm_isolation_preserved(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    assert client.get(f"/api/v1/crm/contacts/{_CONTACT_B}").status_code == 404


def test_freeze_list_connectors_no_secret_exposure(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    save_credentials("slack", "notifications", {"webhook_url": "top-secret"}, organization_id=ids["org_a"])
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = client.get("/api/v1/integrations/connectors").json()
    assert "top-secret" not in str(body)


# ── Migration attestation ─────────────────────────────────────────────────────


def test_freeze_migration_patch_documented() -> None:
    att = (DOCS_S4_5 / "S4_5_CONNECTOR_MIGRATION_ATTESTATION.md").read_text(encoding="utf-8")
    assert "organization_id" in att
    runner_src = (ROOT / "runner_api.py").read_text(encoding="utf-8")
    assert "_migrate_connector_credentials_tenant" in runner_src


def test_freeze_s4_5_no_new_migration_in_manifest() -> None:
    manifest = (DOCS_S4_5 / "S4_5_BASELINE_MANIFEST.md").read_text(encoding="utf-8")
    assert "Database Migrations: 0" in manifest or "Migrations: 0" in manifest.lower()


# ── Known exceptions ──────────────────────────────────────────────────────────


def test_freeze_known_exception_reconciliation() -> None:
    doc = (DOCS_S4_5 / "S4_5_KNOWN_EXCEPTION_RECONCILIATION.md").read_text(encoding="utf-8")
    assert "RECONCILED" in doc or "UNCHANGED" in doc


def test_freeze_historical_failure_identities() -> None:
    doc = (DOCS_S4_5 / "S4_5_KNOWN_EXCEPTION_RECONCILIATION.md").read_text(encoding="utf-8")
    for test_id in HISTORICAL_FAILED_TESTS + HISTORICAL_ERROR_TESTS:
        assert test_id.split("::")[-1] in doc or test_id in doc


def test_freeze_env_connector_residual_documented() -> None:
    reg = (DOCS_S4_5 / "S4_5_RESIDUAL_INTEGRATION_RISK_REGISTER_v1.0.md").read_text(encoding="utf-8")
    assert "env" in reg.lower() or "OpenAI" in reg or "GLOBAL" in reg


def test_freeze_hydrate_global_by_design() -> None:
    src = inspect.getsource(hydrate_all_connectors)
    assert "organization_id=None" in src
