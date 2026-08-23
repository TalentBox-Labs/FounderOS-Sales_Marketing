"""SaaS S4 — connector credential tenant isolation + webhook tenant binding tests."""

from __future__ import annotations

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
from revenue_os.auth import hash_password
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.credentials_vault import (
    delete_credentials,
    load_credentials,
    save_credentials,
)
from revenue_os.services.integration_tenant_resolution import upsert_n8n_binding
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

ROOT = Path(__file__).resolve().parents[1]
DOCS_S4 = ROOT / "docs" / "saas" / "s4"
_OPERATOR = "Krishna Founder"

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

S4_DOCS = (
    "S4_INTEGRATION_TENANCY_ARCHITECTURE.md",
    "S4_CONNECTOR_CREDENTIAL_OWNERSHIP_CONTRACT.md",
    "S4_CONNECTOR_CREDENTIAL_RESOLUTION_CONTRACT.md",
    "S4_GLOBAL_CREDENTIAL_FALLBACK_CONTRACT.md",
    "S4_WEBHOOK_TENANT_BINDING_CONTRACT.md",
    "S4_INTEGRATION_IDENTITY_CONTRACT.md",
    "S4_INTEGRATION_OBJECT_OWNERSHIP_CONTRACT.md",
    "S4_CROSS_TENANT_INTEGRATION_ATTACK_MATRIX.md",
    "S4_INTEGRATION_AUDIT_PROVENANCE_CONTRACT.md",
    "S4_EDITORIAL_PUBLISHING_SCOPE_ATTESTATION.md",
    "S4_RESIDUAL_INTEGRATION_TENANT_RISK_REGISTER.md",
    "S4_MIGRATION_ATTESTATION.md",
    "S4_KNOWN_EXCEPTION_RECONCILIATION.md",
    "S4_IMPLEMENTATION_MANIFEST.md",
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
    engine = create_engine(f"sqlite:///{tmp_path / 's4_int.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    for mod in (identity_mod, crm_mod, n8n_mod):
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


def test_s4_docs_exist() -> None:
    for name in S4_DOCS:
        assert (DOCS_S4 / name).is_file(), f"missing {name}"


def test_org_a_resolves_own_connector_credential(tenant_db: sessionmaker) -> None:
    org_a = str(_ORG_A)
    org_b = str(_ORG_B)
    save_credentials("linkedin_enrichment", "enrichment", {"api_key": "key-a"}, organization_id=org_a)
    save_credentials("linkedin_enrichment", "enrichment", {"api_key": "key-b"}, organization_id=org_b)
    assert load_credentials("linkedin_enrichment", organization_id=org_a)["api_key"] == "key-a"
    assert load_credentials("linkedin_enrichment", organization_id=org_b)["api_key"] == "key-b"


def test_org_b_cannot_resolve_org_a_credential(tenant_db: sessionmaker) -> None:
    org_a = str(_ORG_A)
    org_b = str(_ORG_B)
    save_credentials("slack", "notifications", {"webhook_url": "https://a"}, organization_id=org_a)
    assert load_credentials("slack", organization_id=org_b, allow_global_fallback=False) is None


def test_connector_name_only_cannot_bypass_org(tenant_db: sessionmaker) -> None:
    org_a = str(_ORG_A)
    save_credentials("email_smtp", "email", {"host": "smtp.a"}, organization_id=org_a)
    assert load_credentials("email_smtp", organization_id=str(_ORG_B)) is None


def test_global_fallback_blocked_for_tenant_request(tenant_db: sessionmaker) -> None:
    save_credentials("whatsapp", "messaging", {"api_key": "global-key"}, organization_id=None)
    assert load_credentials("whatsapp", organization_id=str(_ORG_A), allow_global_fallback=False) is None


def test_configure_connector_scoped_to_tenant(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.post(
        "/api/v1/integrations/connectors/slack/configure",
        json={"webhook_url": "https://hooks.slack.com/a"},
    )
    assert r.status_code == 200, r.text
    assert load_credentials("slack", organization_id=ids["org_a"]) is not None
    assert load_credentials("slack", organization_id=ids["org_b"]) is None


def test_list_connectors_does_not_expose_secrets(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    save_credentials("slack", "notifications", {"webhook_url": "secret-url"}, organization_id=ids["org_a"])
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = client.get("/api/v1/integrations/connectors").json()
    raw = str(body)
    assert "secret-url" not in raw


def test_n8n_webhook_cross_tenant_contact_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], "secret-org-a")
    db = tenant_db()
    try:
        before = db.get(Contact, _CONTACT_B).lead_score
    finally:
        db.close()
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_B)},
        headers={"X-N8N-Secret": "secret-org-a"},
    )
    assert r.status_code == 404
    db = tenant_db()
    try:
        after = db.get(Contact, _CONTACT_B).lead_score
        assert after == before
    finally:
        db.close()


def test_n8n_webhook_same_tenant_contact_allowed(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], "secret-org-a")
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_A)},
        headers={"X-N8N-Secret": "secret-org-a"},
    )
    assert r.status_code == 200, r.text
    db = tenant_db()
    try:
        contact = db.get(Contact, _CONTACT_A)
        assert contact.lead_score == 20
    finally:
        db.close()


def test_n8n_org_not_from_payload_contact_id(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    upsert_n8n_binding(ids["org_a"], "secret-org-a")
    r = client.post(
        "/webhooks/n8n/email.replied",
        json={"contact_id": str(_CONTACT_B), "organization_id": ids["org_b"]},
        headers={"X-N8N-Secret": "secret-org-a"},
    )
    assert r.status_code == 404


def test_crm_isolation_preserved_s4(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    assert client.get(f"/api/v1/crm/contacts/{_CONTACT_B}").status_code == 404


def test_delete_credentials_org_scoped(tenant_db: sessionmaker) -> None:
    org_a = str(_ORG_A)
    save_credentials("google_calendar", "calendar", {"access_token": "t"}, organization_id=org_a)
    assert delete_credentials("google_calendar", organization_id=org_a) is True
    assert load_credentials("google_calendar", organization_id=org_a) is None
