"""SaaS S2 — Organization + TenantContext + bounded query isolation tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.cockpit as cockpit_mod
import runner_api_routers.identity as identity_mod
import runner_api_routers.manual_demand as mdg_mod
import runner_api_routers.operator_flow as operator_mod
from revenue_os.auth import hash_password
from revenue_os.models.automation_state import AgentActionLog
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
from revenue_os.services.commercial_outcome_service import ACTION_HANDOFF as CO_HANDOFF
from revenue_os.services.identity_context import PrincipalKind
from revenue_os.services.qualified_demand_service import (
    ACTION_HANDOFF as QD_HANDOFF,
    QualifiedDemandPayload,
    PersonPayload,
    register_marketing_handoff,
)
from revenue_os.services.tenant_bootstrap import bootstrap_organization_for_users
from revenue_os.services.tenant_context import TenantContext
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

ROOT = Path(__file__).resolve().parents[1]
_OPERATOR = "Krishna Founder"

_ORG_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEAL_A_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_DEAL_B_ID = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
_DEMAND_A_ID = "11111111-1111-1111-1111-111111111111"
_DEMAND_B_ID = "22222222-2222-2222-2222-222222222222"
_OUTCOME_B_ID = "33333333-3333-3333-3333-333333333333"


@pytest.fixture(autouse=True)
def _reset_identity_ephemeral() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 's2_tenant.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    for mod in (
        identity_mod,
        cockpit_mod,
        operator_mod,
        mdg_mod,
    ):
        monkeypatch.setattr(mod, "SessionLocal", session_factory)
    import revenue_os.services.tenant_resolution as tr

    monkeypatch.setattr(tr, "SessionLocal", session_factory)
    import revenue_os.services.cockpit_read_model as crm

    monkeypatch.setattr(crm, "SessionLocal", session_factory)
    import revenue_os.services.operator_flow_read_model as ofrm

    monkeypatch.setattr(ofrm, "SessionLocal", session_factory)
    import revenue_os.services.tenant_bootstrap as tb

    monkeypatch.setattr(tb, "SessionLocal", session_factory)
    return session_factory


def _seed_two_orgs(db_factory: sessionmaker) -> dict[str, str]:
    db = db_factory()
    try:
        org_a = Organization(
            id=_ORG_A_ID, name="Org A", slug="org-a", status=OrganizationStatus.ACTIVE
        )
        org_b = Organization(
            id=_ORG_B_ID, name="Org B", slug="org-b", status=OrganizationStatus.ACTIVE
        )
        user_a = User(
            email="member-a@example.com",
            hashed_password=hash_password("pass-a"),
            full_name="Member A",
            role="member",
            is_active=1,
        )
        user_b = User(
            email="member-b@example.com",
            hashed_password=hash_password("pass-b"),
            full_name="Member B",
            role="member",
            is_active=1,
        )
        viewer_a = User(
            email="viewer-a@example.com",
            hashed_password=hash_password("pass-v"),
            full_name="Viewer A",
            role="viewer",
            is_active=1,
        )
        db.add_all([org_a, org_b, user_a, user_b, viewer_a])
        db.flush()
        pipeline = Pipeline(
            name="Default Sales",
            pipeline_type=PipelineType.SALES,
            is_default=1,
        )
        db.add(pipeline)
        db.flush()
        db.add_all(
            [
                OrganizationMembership(
                    user_id=user_a.id,
                    organization_id=org_a.id,
                    role="member",
                    status=MembershipStatus.ACTIVE,
                ),
                OrganizationMembership(
                    user_id=user_b.id,
                    organization_id=org_b.id,
                    role="member",
                    status=MembershipStatus.ACTIVE,
                ),
                OrganizationMembership(
                    user_id=viewer_a.id,
                    organization_id=org_a.id,
                    role="viewer",
                    status=MembershipStatus.ACTIVE,
                ),
            ]
        )
        contact_a = Contact(
            id=_CONTACT_A_ID,
            first_name="A",
            last_name="Contact",
            email="a@example.com",
            status=ContactStatus.LEAD,
            source=ContactSource.MANUAL,
            lead_score=80,
            organization_id=_ORG_A_ID,
        )
        contact_b = Contact(
            id=_CONTACT_B_ID,
            first_name="B",
            last_name="Contact",
            email="b@example.com",
            status=ContactStatus.LEAD,
            source=ContactSource.MANUAL,
            lead_score=75,
            organization_id=_ORG_B_ID,
        )
        deal_a = Deal(
            id=_DEAL_A_ID,
            name="Deal A",
            stage=DealStage.DISCOVERY,
            value=1000,
            contact_id=_CONTACT_A_ID,
            pipeline_id=pipeline.id,
            organization_id=_ORG_A_ID,
        )
        deal_b = Deal(
            id=_DEAL_B_ID,
            name="Deal B",
            stage=DealStage.DISCOVERY,
            value=2000,
            contact_id=_CONTACT_B_ID,
            pipeline_id=pipeline.id,
            organization_id=_ORG_B_ID,
        )
        db.add_all([contact_a, contact_b, deal_a, deal_b])
        db.add(
            AgentActionLog(
                actor="mc04",
                action_type=QD_HANDOFF,
                target_id=_DEMAND_A_ID,
                organization_id=_ORG_A_ID,
                detail={
                    "payload": {
                        "person": {"email": "da@example.com", "name": "Demand A"},
                        "source": "manual",
                    }
                },
            )
        )
        db.add(
            AgentActionLog(
                actor="mc04",
                action_type=QD_HANDOFF,
                target_id=_DEMAND_B_ID,
                organization_id=_ORG_B_ID,
                detail={
                    "payload": {
                        "person": {"email": "db@example.com", "name": "Demand B"},
                        "source": "manual",
                    }
                },
            )
        )
        db.add(
            AgentActionLog(
                actor="mc06",
                action_type=CO_HANDOFF,
                target_id=_OUTCOME_B_ID,
                organization_id=_ORG_B_ID,
                detail={"payload": {"deal_id": str(_DEAL_B_ID)}},
            )
        )
        db.commit()
        return {
            "user_a_id": str(user_a.id),
            "user_b_id": str(user_b.id),
            "viewer_a_id": str(viewer_a.id),
            "org_a": str(_ORG_A_ID),
            "org_b": str(_ORG_B_ID),
        }
    finally:
        db.close()


def _login(
    client: TestClient,
    *,
    email: str,
    password: str,
    org_id: str | None = None,
) -> None:
    r = client.post(
        "/api/v1/identity/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    if org_id is not None:
        client.cookies.set(ORGANIZATION_COOKIE, org_id)


def test_organization_bootstrap_creates_membership(
    tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    db = tenant_db()
    try:
        user = User(
            email="founder@example.com",
            hashed_password=hash_password("x"),
            full_name=_OPERATOR,
            role="owner",
            is_active=1,
        )
        db.add(user)
        db.commit()
        org = bootstrap_organization_for_users(db)
        assert org is not None
        membership = (
            db.query(OrganizationMembership)
            .filter(OrganizationMembership.user_id == user.id)
            .one()
        )
        assert membership.role == "owner"
    finally:
        db.close()


def test_tenant_context_requires_membership(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_b"])
    r = client.get("/api/v1/tenant/me")
    assert r.status_code == 403


def test_tenant_me_returns_context(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    r = client.get("/api/v1/tenant/me")
    assert r.status_code == 200
    tenant = r.json()["tenant"]
    assert tenant["organization_id"] == ids["org_a"]
    assert tenant["membership_role"] == "member"
    assert tenant["is_human"] is True


def test_client_cannot_spoof_org_without_membership(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a")
    r = client.post(
        "/api/v1/tenant/select",
        json={"organization_id": ids["org_b"]},
    )
    assert r.status_code == 403


def test_cross_tenant_contact_mutation_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/contact-status",
        json={"contact_id": str(_CONTACT_B_ID), "status": "prospect"},
    )
    assert r.status_code == 404


def test_same_tenant_contact_mutation_allowed(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/contact-status",
        json={"contact_id": str(_CONTACT_A_ID), "status": "prospect"},
    )
    assert r.status_code == 200, r.text


def test_cross_tenant_deal_stage_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/deal/stage",
        json={"deal_id": str(_DEAL_B_ID), "stage": "qualified"},
    )
    assert r.status_code == 404


def test_cross_tenant_qualified_demand_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/reject",
        json={"demand_id": _DEMAND_B_ID, "reason": "not in tenant"},
    )
    assert r.status_code == 404


def test_cross_tenant_commercial_outcome_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/commercial-outcome/accept",
        json={"outcome_id": _OUTCOME_B_ID, "notes": "accept"},
    )
    assert r.status_code == 404


def test_viewer_mutation_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="viewer-a@example.com", password="pass-v", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/contact-status",
        json={"contact_id": str(_CONTACT_A_ID), "status": "prospect"},
    )
    assert r.status_code == 403
    assert "VIEWER" in r.json()["detail"]


def test_cockpit_snapshot_tenant_filtered(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    snap = client.get("/api/v1/cockpit/snapshot").json()
    sales = snap["panels"]["sales"]["data"]
    assert sales["contact_total"] == 1
    assert sales["deal_total"] == 1


def test_operator_snapshot_tenant_filtered(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-b@example.com", password="pass-b", org_id=ids["org_b"])
    snap = client.get("/api/v1/operator/snapshot").json()
    assert len(snap["contacts"]) == 1
    assert snap["contacts"][0]["email"] == "b@example.com"


def test_manual_demand_stamps_organization(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    demand_id = str(uuid.uuid4())
    r = client.post(
        "/api/v1/mdg/manual-demand/register",
        json={
            "email": "new@example.com",
            "name": "New Lead",
            "source": "manual",
            "demand_id": demand_id,
        },
    )
    assert r.status_code == 200, r.text
    db = tenant_db()
    try:
        row = (
            db.query(AgentActionLog)
            .filter(
                AgentActionLog.action_type == QD_HANDOFF,
                AgentActionLog.target_id == demand_id,
            )
            .one()
        )
        assert str(row.organization_id) == ids["org_a"]
    finally:
        db.close()


def test_tenant_context_dataclass_fields() -> None:
    from revenue_os.services.identity_context import (
        AuthMethod,
        IdentityContext,
    )

    identity = IdentityContext(
        principal_kind=PrincipalKind.HUMAN,
        auth_method=AuthMethod.SESSION,
        is_human=True,
        user_id="u1",
        email="x@example.com",
        display_name="X",
        role="member",
    )
    ctx = TenantContext(
        identity=identity,
        organization_id="o1",
        organization_name="Org",
        organization_slug="org",
        membership_id="m1",
        membership_role="member",
        membership_status="active",
    )
    public = ctx.as_public_dict()
    assert public["organization_id"] == "o1"
    assert public["membership_role"] == "member"
    assert public["is_human"] is True


def test_identity_context_preserved_with_tenant(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a", org_id=ids["org_a"])
    identity = client.get("/api/v1/identity/me").json()["identity"]
    assert identity["principal_kind"] == "HUMAN"
    assert identity["auth_method"] == "session"


def test_login_auto_selects_single_org(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_two_orgs(tenant_db)
    _login(client, email="member-a@example.com", password="pass-a")
    r = client.get("/api/v1/tenant/me")
    assert r.status_code == 200
    assert r.json()["tenant"]["organization_id"] == ids["org_a"]
