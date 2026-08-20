"""Tenant-boundary remediation v1 — QualifiedDemand intake tenant safety."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.identity as identity_mod
import runner_api_routers.manual_demand as mdg_mod
import runner_api_routers.operator_flow as of_router
import runner_api_routers.qualified_demand as qd_router
import runner_api_routers.ui as ui_mod
from revenue_os.auth import hash_password
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Company, Contact, ContactSource, ContactStatus
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.founder_ui_read_model import (
    build_command_center_snapshot,
    build_demand_contacts_snapshot,
)
from revenue_os.services.marketing_qualified_demand import compose_marketing_qualified_demand
from revenue_os.services.qualified_demand_service import (
    ACTION_HANDOFF,
    accept_qualified_demand,
    register_marketing_handoff,
    reject_qualified_demand,
)
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEMAND_A = "11111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_DEMAND_B = "22222222-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_SHARED_EMAIL = "shared@example.com"
_OPERATOR = "Krishna Founder"
_COMPANY_B_NAME = "Tenant B Co"


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'tenant_remediation.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.founder_ui_read_model as founder_rm
    import revenue_os.services.operator_flow_read_model as of_rm
    import revenue_os.services.tenant_resolution as tr

    for mod in (
        db_mod,
        tr,
        approvals_mod,
        al,
        ui_mod,
        founder_rm,
        of_rm,
        of_router,
        qd_router,
        mdg_mod,
        identity_mod,
    ):
        if hasattr(mod, "SessionLocal"):
            monkeypatch.setattr(mod, "SessionLocal", sf)
    monkeypatch.setenv("FOUNDER_OS_REQUIRE_LOGIN", "0")
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    return sf


def _login(client: TestClient, email: str, password: str, org_id: str) -> None:
    client.post("/login", data={"email": email, "password": password})
    client.cookies.set(ORGANIZATION_COOKIE, org_id)


def _seed(db_factory: sessionmaker) -> None:
    db = db_factory()
    try:
        db.add_all(
            [
                Organization(id=_ORG_A, name="Org A", slug="org-a", status=OrganizationStatus.ACTIVE),
                Organization(id=_ORG_B, name="Org B", slug="org-b", status=OrganizationStatus.ACTIVE),
            ]
        )
        owner_a = User(
            email="owner-a@example.com",
            hashed_password=hash_password("pass-a"),
            full_name=_OPERATOR,
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
        db.add_all([owner_a, owner_b])
        db.flush()
        company_b = Company(id=uuid.uuid4(), name=_COMPANY_B_NAME, domain="tenantb.example")
        db.add(company_b)
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
                Contact(
                    id=_CONTACT_B,
                    first_name="Bob",
                    last_name="B",
                    email=_SHARED_EMAIL,
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                    company_id=company_b.id,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def _register_demand(
    db_factory: sessionmaker,
    *,
    demand_id: str,
    org_id: uuid.UUID,
    email: str,
    company_hint: dict | None = None,
) -> None:
    db = db_factory()
    try:
        payload = compose_marketing_qualified_demand(
            demand_id=demand_id,
            occurred_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            source="web_form",
            channel="website",
            person={"email": email, "name": "Inbound Lead"},
            company_hint=company_hint,
            marketing_qualification={"reason": "Test qualification"},
            content_attribution={"utm_source": "test"},
        )
        register_marketing_handoff(
            db, payload, _OPERATOR, organization_id=str(org_id)
        )
    finally:
        db.close()


def test_accept_does_not_resolve_other_tenant_contact_by_email(
    tenant_db: sessionmaker,
) -> None:
    _seed(tenant_db)
    _register_demand(
        tenant_db,
        demand_id=_DEMAND_A,
        org_id=_ORG_A,
        email=_SHARED_EMAIL,
        company_hint={"name": _COMPANY_B_NAME, "domain": "tenantb.example"},
    )
    db = tenant_db()
    try:
        result = accept_qualified_demand(
            db,
            _DEMAND_A,
            _OPERATOR,
            organization_id=str(_ORG_A),
        )
        assert result["created"] is True
        assert result["contact_id"] != str(_CONTACT_B)
        created = db.query(Contact).filter(Contact.email == _SHARED_EMAIL).all()
        assert len(created) == 2
        org_a_contact = next(c for c in created if c.organization_id == _ORG_A)
        org_b_contact = next(c for c in created if c.organization_id == _ORG_B)
        assert str(org_a_contact.id) == result["contact_id"]
        assert org_a_contact.company_id is None
        assert org_b_contact.company_id is not None
        assert org_b_contact.notes is None or "MC04 handoff" not in (org_b_contact.notes or "")
    finally:
        db.close()


def test_same_email_across_tenants(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email=_SHARED_EMAIL)
    _register_demand(tenant_db, demand_id=_DEMAND_B, org_id=_ORG_B, email=_SHARED_EMAIL)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    accept_a = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_A},
    )
    assert accept_a.status_code == 200
    assert accept_a.json()["contact_id"] != str(_CONTACT_B)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    accept_b = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_B},
    )
    assert accept_b.status_code == 200
    assert accept_b.json()["merged"] is True
    assert accept_b.json()["contact_id"] == str(_CONTACT_B)


def test_cross_tenant_demand_accept_and_reject_blocked(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _register_demand(tenant_db, demand_id=_DEMAND_B, org_id=_ORG_B, email="b@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    assert client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_B},
    ).status_code == 404
    assert client.post(
        "/api/v1/operator/actions/qualified-demand/reject",
        json={"demand_id": _DEMAND_B, "reason": "nope"},
    ).status_code == 404


def test_direct_intake_requires_tenant_context(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert r.status_code == 403
    assert "Organization context required" in r.json()["detail"]


def test_direct_intake_with_tenant_succeeds(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert r.status_code == 200
    assert r.json()["created"] is True


def test_marketing_handoff_persists_org_atomically(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        row = (
            db.query(AgentActionLog)
            .filter(
                AgentActionLog.action_type == ACTION_HANDOFF,
                AgentActionLog.target_id == _DEMAND_A,
            )
            .one()
        )
        assert row.organization_id == _ORG_A
    finally:
        db.close()


def test_command_center_fail_closed_without_org(
    tenant_db: sessionmaker,
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = build_command_center_snapshot(organization_id=None)
    assert snap["pending_demands"] == []
    assert snap["pending_demand_count"] == 0


def test_demand_snapshot_fail_closed_without_org(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    snap = build_demand_contacts_snapshot(organization_id=None)
    assert snap["pending_demands"] == []
    assert snap["contacts"] == []
    assert snap["state"] == "unavailable"


def test_cross_tenant_demand_not_visible_on_people(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(
        tenant_db,
        demand_id=_DEMAND_B,
        org_id=_ORG_B,
        email="secret@example.com",
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/demand")
    assert r.status_code == 200
    assert "secret@example.com" not in r.text


def test_service_reject_scoped_to_tenant(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_B, org_id=_ORG_B, email="b@example.com")
    db = tenant_db()
    try:
        with pytest.raises(ValueError, match="tenant scope"):
            reject_qualified_demand(
                db,
                _DEMAND_B,
                _OPERATOR,
                "bad",
                organization_id=str(_ORG_A),
            )
    finally:
        db.close()
