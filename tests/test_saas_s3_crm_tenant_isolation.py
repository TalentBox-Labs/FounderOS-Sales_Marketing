"""SaaS S3 — CRM API tenant guards + residual read isolation tests."""

from __future__ import annotations

import inspect
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.crm as crm_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.cockpit as cockpit_mod
import runner_api_routers.operator_flow as operator_mod
import runner_api_routers.manual_demand as mdg_mod
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
_OPERATOR = "Krishna Founder"

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEAL_A = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_DEAL_B = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

S3_DOCS = (
    "S3_CRM_API_SURFACE_INVENTORY.md",
    "S3_CRM_TENANT_GUARD_ARCHITECTURE.md",
    "S3_CRM_CROSS_TENANT_ATTACK_MATRIX.md",
    "S3_CRM_READ_ISOLATION.md",
    "S3_EDITORIAL_PUBLISHING_READ_ISOLATION.md",
    "S3_WEBHOOK_TENANT_AUDIT.md",
    "S3_CONNECTOR_CREDENTIAL_BOUNDARY.md",
    "S3_POST_IMPLEMENTATION_QUERY_ISOLATION_AUDIT.md",
    "S3_RESIDUAL_TENANCY_RISK_REGISTER.md",
    "S3_SECURITY_ATTESTATION.md",
    "S3_IMPLEMENTATION_MANIFEST.md",
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
    engine = create_engine(f"sqlite:///{tmp_path / 's3_crm.db'}")
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


def test_s3_docs_exist() -> None:
    for name in S3_DOCS:
        assert (DOCS_S3 / name).is_file(), f"missing {name}"


def test_crm_module_uses_tenant_guards() -> None:
    src = inspect.getsource(crm_mod)
    assert "scoped_contact" in src
    assert "scoped_deal" in src
    assert "apply_contact_org_filter" in src
    assert "resolve_crm_tenant_read" in src


def test_crm_list_contacts_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = client.get("/api/v1/crm/contacts").json()
    assert body["count"] == 1
    assert body["contacts"][0]["email"] == "a@example.com"


def test_crm_get_contact_cross_tenant_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    assert client.get(f"/api/v1/crm/contacts/{_CONTACT_B}").status_code == 404


def test_crm_contact_status_cross_tenant_blocked(
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


def test_crm_viewer_mutation_blocked(
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


def test_crm_list_deals_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    body = client.get("/api/v1/crm/deals").json()
    assert body["count"] == 1
    assert body["deals"][0]["name"] == "Deal B"


def test_crm_deal_stage_cross_tenant_blocked(
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


def test_crm_search_contacts_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    body = client.get("/api/v1/crm/contacts", params={"search": "example"}).json()
    emails = {c["email"] for c in body["contacts"]}
    assert "a@example.com" in emails
    assert "b@example.com" not in emails


def test_crm_pipeline_summary_isolated(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    pipe = client.get("/api/v1/crm/pipeline").json()["pipeline"]
    assert pipe["total_deals"] == 1


def test_crm_create_contact_stamps_org(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    r = client.post(
        "/api/v1/crm/contacts",
        json={
            "first_name": "New",
            "last_name": "Lead",
            "email": "new@example.com",
            "status": "lead",
        },
    )
    assert r.status_code == 200, r.text
    db = tenant_db()
    try:
        row = db.query(Contact).filter(Contact.email == "new@example.com").one()
        assert str(row.organization_id) == ids["org_a"]
    finally:
        db.close()


def test_crm_spoof_org_in_body_ignored(
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


def test_cockpit_isolation_preserved(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-o", ids["org_a"])
    sales = client.get("/api/v1/cockpit/snapshot").json()["panels"]["sales"]["data"]
    assert sales["contact_total"] == 1


def test_operator_isolation_preserved(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", ids["org_b"])
    snap = client.get("/api/v1/operator/snapshot").json()
    assert len(snap["contacts"]) == 1


def test_ninth_crm_risk_mitigated_in_inventory() -> None:
    inv = (DOCS_S3 / "S3_CRM_API_SURFACE_INVENTORY.md").read_text(encoding="utf-8")
    assert "S3_MUST_GUARD" in inv
    assert "DEFERRED_TO_S3" not in inv or "mitigated" in inv.lower()


def test_editorial_deferred_documented() -> None:
    doc = (DOCS_S3 / "S3_EDITORIAL_PUBLISHING_READ_ISOLATION.md").read_text(encoding="utf-8")
    assert "DEFERRED" in doc or "GLOBAL" in doc


def test_webhook_deferred_documented() -> None:
    doc = (DOCS_S3 / "S3_WEBHOOK_TENANT_AUDIT.md").read_text(encoding="utf-8")
    assert "DEFERRED" in doc or "n8n" in doc.lower()


def test_connector_boundary_documented() -> None:
    doc = (DOCS_S3 / "S3_CONNECTOR_CREDENTIAL_BOUNDARY.md").read_text(encoding="utf-8")
    assert "FUTURE" in doc or "global" in doc.lower()
