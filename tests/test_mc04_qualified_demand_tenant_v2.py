"""MC04 tenant-scoped API contract v2 — commercial intake tenant safety."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.cockpit as cockpit_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.manual_demand as mdg_mod
import runner_api_routers.operator_flow as of_router
import runner_api_routers.qualified_demand as qd_router
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
from revenue_os.services.cockpit_read_model import build_cockpit_snapshot
from revenue_os.services.qualified_demand_service import ACTION_HANDOFF
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEMAND_A = "11111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_DEMAND_B = "22222222-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_SHARED_EMAIL = "shared@example.com"
_OPERATOR = "Krishna Founder"
_COMPANY_B_NAME = "Tenant B Co"
_HANDOFF_BODY = {
    "demand_id": _DEMAND_A,
    "occurred_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": "web_form",
    "person": {"email": "a@example.com", "name": "Inbound Lead"},
    "requested_by": _OPERATOR,
}


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'mc04_tenant_v2.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.cockpit_read_model as cockpit_rm
    import revenue_os.services.tenant_resolution as tr

    for mod in (
        db_mod,
        tr,
        cockpit_rm,
        of_router,
        qd_router,
        mdg_mod,
        cockpit_mod,
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


def _handoff(client: TestClient, demand_id: str = _DEMAND_A, email: str = "a@example.com") -> None:
    body = {
        **_HANDOFF_BODY,
        "demand_id": demand_id,
        "person": {"email": email, "name": "Inbound Lead"},
    }
    r = client.post("/api/v1/marketing/qualified-demand/handoff", json=body)
    assert r.status_code == 200, r.text


def test_tenant_scoped_handoff_succeeds(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    _handoff(client)
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


def test_tenant_scoped_accept_succeeds(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    _handoff(client)
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert r.status_code == 200
    assert r.json()["created"] is True


def test_tenant_scoped_reject_succeeds(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    _handoff(client)
    r = client.post(
        "/api/v1/sales/intake/demand/reject",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR, "reason": "ICP mismatch"},
    )
    assert r.status_code == 200
    assert r.json()["rejected"] is True


def test_accept_without_handoff_returns_not_found_with_tenant(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    """Missing handoff under valid tenant → 404 via scoped_demand_handoff (no leak)."""
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert r.status_code == 404
    assert "QualifiedDemand not found" in r.json()["detail"]


def test_tenantless_handoff_fails_closed(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    r = client.post("/api/v1/marketing/qualified-demand/handoff", json=_HANDOFF_BODY)
    assert r.status_code == 403
    db = tenant_db()
    try:
        assert (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == ACTION_HANDOFF)
            .count()
            == 0
        )
    finally:
        db.close()


def test_tenantless_accept_fails_closed(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert r.status_code == 403


def test_tenantless_reject_fails_closed(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    r = client.post(
        "/api/v1/sales/intake/demand/reject",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR, "reason": "nope"},
    )
    assert r.status_code == 403


def test_cross_tenant_accept_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    _handoff(client, demand_id=_DEMAND_B, email="b@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_B},
    )
    assert r.status_code == 404


def test_cross_tenant_reject_blocked(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-b@example.com", "pass-b", str(_ORG_B))
    _handoff(client, demand_id=_DEMAND_B, email="b@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/reject",
        json={"demand_id": _DEMAND_B, "reason": "nope"},
    )
    assert r.status_code == 404


def test_same_email_contacts_isolated(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    _handoff(client, email=_SHARED_EMAIL)
    accept = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_A},
    )
    assert accept.status_code == 200
    assert accept.json()["contact_id"] != str(_CONTACT_B)
    db = tenant_db()
    try:
        b_contact = db.get(Contact, _CONTACT_B)
        assert b_contact is not None
        assert b_contact.company_id is not None
    finally:
        db.close()


def test_direct_intake_no_cross_tenant_contact_id(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    _handoff(client, email=_SHARED_EMAIL)
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert r.status_code == 200
    assert r.json()["contact_id"] != str(_CONTACT_B)


def test_company_cross_tenant_binding_blocked(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    body = {
        **_HANDOFF_BODY,
        "company_hint": {"name": _COMPANY_B_NAME, "domain": "tenantb.example"},
    }
    r = client.post("/api/v1/marketing/qualified-demand/handoff", json=body)
    assert r.status_code == 200
    accept = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert accept.status_code == 200
    db = tenant_db()
    try:
        created = db.get(Contact, uuid.UUID(accept.json()["contact_id"]))
        assert created is not None
        assert created.company_id is None
    finally:
        db.close()


def test_tenantless_mdg_register_fails_closed(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    r = client.post(
        "/api/v1/mdg/manual-demand/register",
        json={"email": "mdg@example.com", "name": "MDG Lead", "source": "manual"},
    )
    assert r.status_code == 403
    db = tenant_db()
    try:
        assert db.query(AgentActionLog).filter(AgentActionLog.action_type == ACTION_HANDOFF).count() == 0
    finally:
        db.close()


def test_cockpit_read_fail_closed_without_org(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        db.add(
            AgentActionLog(
                actor=_OPERATOR,
                action_type=ACTION_HANDOFF,
                target_type="qualified_demand",
                target_id=_DEMAND_A,
                status="completed",
                organization_id=_ORG_A,
                detail={"payload": {"person": {"email": "secret@example.com"}}},
            )
        )
        db.commit()
    finally:
        db.close()
    snap = build_cockpit_snapshot(organization_id=None)
    items = snap["panels"]["attention"]["data"]["items"]
    qd_items = [i for i in items if i.get("kind") == "qualified_demand"]
    assert qd_items == []


def test_mutation_db_resolution_failure_fails_closed(
    monkeypatch: pytest.MonkeyPatch, client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))

    def _boom(*_a, **_k):  # noqa: ANN001
        raise SQLAlchemyError("db down")

    import revenue_os.services.tenant_resolution as tr

    monkeypatch.setattr(tr, "_active_memberships", _boom)
    r = client.post(
        "/api/v1/sales/intake/demand/accept",
        json={"demand_id": _DEMAND_A, "requested_by": _OPERATOR},
    )
    assert r.status_code == 503
    assert "Tenant resolution unavailable" in r.json()["detail"]
