"""COS-5 — Founder Command operating surface (inline governed actions)."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.identity as identity_mod
import runner_api_routers.operator_flow as of_router
import runner_api_routers.qualified_demand as qd_router
import runner_api_routers.ui as ui_mod
from revenue_os.auth import hash_password
from revenue_os.models.approvals import ApprovalRequest
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Contact, ContactSource, ContactStatus
from revenue_os.models.deal import Deal, DealStage
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.command_operating_surface import (
    EXEC_INLINE_GOVERNED,
    EXEC_NAVIGATE_GOVERNED,
    actions_for_decision_item,
    assert_no_inline_for_optional_tenant_kinds,
    attach_command_actions,
)
from revenue_os.services.founder_ui_read_model import build_command_center_snapshot
from revenue_os.services.marketing_qualified_demand import compose_marketing_qualified_demand
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED,
    ACTION_HANDOFF,
    ACTION_REJECTED,
    register_marketing_handoff,
)
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEMAND_A = "11111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_DEMAND_B = "22222222-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_APPROVAL_A = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"
_APPROVAL_B = "bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb"
_OPERATOR = "Krishna Founder"
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'cos5.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.commercial_funnel_intelligence as cfi_mod
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
        identity_mod,
        cfi_mod,
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
                    email="bob@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
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
    name: str = "Inbound Lead",
) -> None:
    db = db_factory()
    try:
        payload = compose_marketing_qualified_demand(
            demand_id=demand_id,
            occurred_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            source="web_form",
            channel="website",
            person={"email": email, "name": name},
            marketing_qualification={"reason": "Requested a product walkthrough"},
            content_attribution={"utm_source": "website"},
        )
        register_marketing_handoff(db, payload, _OPERATOR, organization_id=str(org_id))
    finally:
        db.close()


def _add_approval(
    db_factory: sessionmaker,
    *,
    request_id: str,
    org_id: uuid.UUID,
    contact_id: str | None = None,
) -> None:
    db = db_factory()
    try:
        db.add(
            ApprovalRequest(
                id=request_id,
                requested_by="system",
                action_type="send_outreach",
                title="Outreach proposal",
                description="Draft ready",
                target_type="contact",
                target_id=contact_id,
                status="pending",
                payload={"organization_id": str(org_id), "contact_id": contact_id},
            )
        )
        db.commit()
    finally:
        db.close()


# --- Eligibility ---


def test_only_eligible_kinds_get_inline_governed() -> None:
    qd = actions_for_decision_item(
        {
            "kind": "qualified_demand",
            "provenance": {"subject_id": _DEMAND_A},
        }
    )
    assert all(a["execution_mode"] == EXEC_INLINE_GOVERNED for a in qd)
    appr = actions_for_decision_item(
        {
            "kind": "approval",
            "provenance": {"subject_id": _APPROVAL_A},
        }
    )
    assert all(a["execution_mode"] == EXEC_INLINE_GOVERNED for a in appr)
    meeting = actions_for_decision_item(
        {
            "kind": "meeting_interest",
            "provenance": {"subject_id": str(_CONTACT_B)},
        }
    )
    assert meeting and meeting[0]["execution_mode"] == EXEC_NAVIGATE_GOVERNED
    follow = actions_for_decision_item(
        {
            "kind": "follow_up",
            "provenance": {"subject_id": str(_CONTACT_B)},
        }
    )
    assert follow and follow[0]["execution_mode"] == EXEC_NAVIGATE_GOVERNED


def test_optional_tenant_kinds_never_inline() -> None:
    forbidden = assert_no_inline_for_optional_tenant_kinds()
    for kind in forbidden:
        actions = actions_for_decision_item(
            {"kind": kind, "provenance": {"subject_id": "x"}, "href": "/operator"}
        )
        assert not any(a["execution_mode"] == EXEC_INLINE_GOVERNED for a in actions)


def test_missing_tenant_attaches_no_actions(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    empty = attach_command_actions(
        [{"kind": "qualified_demand", "provenance": {"subject_id": _DEMAND_A}}],
        organization_id=None,
    )
    assert empty == []
    snap = build_command_center_snapshot(organization_id=None)
    assert snap["state"] == "unavailable"
    assert snap["decision_items"] == []
    assert snap["command_action_summary"]["total"] == 0


# --- QD inline ---


def test_command_qd_accept_uses_existing_path(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    qd_items = [i for i in snap["decision_items"] if i["kind"] == "qualified_demand"]
    assert qd_items
    accept = next(
        a
        for a in qd_items[0]["command_actions"]
        if a["action_type"] == "qualified_demand_accept"
    )
    assert accept["endpoint"] == "/api/v1/operator/actions/qualified-demand/accept"
    r = client.post(accept["endpoint"], json={"demand_id": _DEMAND_A})
    assert r.status_code == 200, r.text
    db = tenant_db()
    try:
        accepted = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == ACTION_ACCEPTED)
            .filter(AgentActionLog.target_id == _DEMAND_A)
            .count()
        )
        assert accepted == 1
        contacts = (
            db.query(Contact).filter(Contact.organization_id == _ORG_A).count()
        )
        assert contacts >= 1
    finally:
        db.close()


def test_command_qd_reject_uses_existing_path(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/reject",
        json={"demand_id": _DEMAND_A, "reason": "Not a fit"},
    )
    assert r.status_code == 200, r.text
    db = tenant_db()
    try:
        rejected = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == ACTION_REJECTED)
            .filter(AgentActionLog.target_id == _DEMAND_A)
            .count()
        )
        assert rejected == 1
        before = db.query(Contact).filter(Contact.organization_id == _ORG_A).count()
    finally:
        db.close()
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert not any(i["kind"] == "qualified_demand" for i in snap["decision_items"])
    db = tenant_db()
    try:
        assert db.query(Contact).filter(Contact.organization_id == _ORG_A).count() == before
    finally:
        db.close()


def test_tenant_a_cannot_act_on_tenant_b_qd(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(
        tenant_db, demand_id=_DEMAND_B, org_id=_ORG_B, email="secret@example.com", name="Secret"
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert "secret@example.com" not in str(snap["decision_items"])
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_B},
    )
    assert r.status_code in (403, 404, 422)


# --- Approvals inline ---


def test_command_approval_approve_uses_existing_path(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    contact_a = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    db = tenant_db()
    try:
        db.add(
            Contact(
                id=contact_a,
                first_name="Ada",
                last_name="A",
                email="a@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=_ORG_A,
            )
        )
        db.commit()
    finally:
        db.close()
    _add_approval(
        tenant_db, request_id=_APPROVAL_A, org_id=_ORG_A, contact_id=str(contact_a)
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    appr = [i for i in snap["decision_items"] if i["kind"] == "approval"]
    assert appr
    approve = next(
        a for a in appr[0]["command_actions"] if a["action_type"] == "approval_approve"
    )
    assert "/api/v1/approvals/" in approve["endpoint"]
    assert approve["endpoint"].endswith("/approve")
    r = client.post(approve["endpoint"], json={})
    assert r.status_code == 200, r.text
    db = tenant_db()
    try:
        row = db.get(ApprovalRequest, _APPROVAL_A)
        assert row is not None
        assert row.status == "approved"
    finally:
        db.close()


def test_command_approval_reject_uses_existing_path(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    contact_a = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    db = tenant_db()
    try:
        db.add(
            Contact(
                id=contact_a,
                first_name="Ada",
                last_name="A",
                email="a@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=_ORG_A,
            )
        )
        db.commit()
    finally:
        db.close()
    _add_approval(
        tenant_db, request_id=_APPROVAL_A, org_id=_ORG_A, contact_id=str(contact_a)
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.post(f"/api/v1/approvals/{_APPROVAL_A}/reject", json={})
    assert r.status_code == 200, r.text
    db = tenant_db()
    try:
        row = db.get(ApprovalRequest, _APPROVAL_A)
        assert row is not None
        assert row.status == "rejected"
    finally:
        db.close()


def test_tenant_a_cannot_act_on_tenant_b_approval(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _add_approval(
        tenant_db,
        request_id=_APPROVAL_B,
        org_id=_ORG_B,
        contact_id=str(_CONTACT_B),
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert _APPROVAL_B not in str(snap["decision_items"])
    r = client.post(f"/api/v1/approvals/{_APPROVAL_B}/approve", json={})
    assert r.status_code in (403, 404, 409)


def test_already_resolved_approval_is_safe(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    contact_a = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    db = tenant_db()
    try:
        db.add(
            Contact(
                id=contact_a,
                first_name="Ada",
                last_name="A",
                email="a@example.com",
                status=ContactStatus.LEAD,
                source=ContactSource.MANUAL,
                organization_id=_ORG_A,
            )
        )
        db.commit()
    finally:
        db.close()
    _add_approval(
        tenant_db, request_id=_APPROVAL_A, org_id=_ORG_A, contact_id=str(contact_a)
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    assert client.post(f"/api/v1/approvals/{_APPROVAL_A}/approve", json={}).status_code == 200
    r2 = client.post(f"/api/v1/approvals/{_APPROVAL_A}/approve", json={})
    assert r2.status_code in (409, 404)


# --- Exclusions / authority / UI ---


def test_command_ui_exposes_inline_and_nav(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/command")
    assert r.status_code == 200
    assert 'data-testid="command-inline-action"' in r.text
    assert "Accept demand" in r.text
    assert "commandInlineAction" in r.text
    assert "/api/v1/operator/actions/deal/stage" not in r.text
    assert "apply_deal_stage_update" not in r.text
    assert "apply_contact_status_update" not in r.text


def test_presentation_has_no_mutation_primitives() -> None:
    src = (_ROOT / "revenue_os/services/command_operating_surface.py").read_text()
    assert "db.add" not in src
    assert "db.commit" not in src
    assert "db.delete" not in src
    assert "apply_contact_status_update" not in src
    assert "apply_deal_stage_update" not in src
    assert "create_tenant_calendar_event" not in src
    assert "SessionLocal" not in src
    tpl = (_ROOT / "templates/founder_command.html").read_text()
    assert "/actions/deal/stage" not in tpl
    assert "/actions/contact-status" not in tpl
    assert "/actions/commercial-outcome/" not in tpl
    assert "booking/propose" not in tpl or "NAVIGATE" in src


def test_no_new_persistent_sot() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    tables = set(sa_inspect(engine).get_table_names())
    forbidden = {
        "command_action",
        "founder_command_queue",
        "operating_surface",
        "command_decision",
    }
    assert not (tables & forbidden)


def test_booking_and_followup_are_navigate_only(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    items = attach_command_actions(
        [
            {
                "kind": "meeting_interest",
                "provenance": {"subject_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"},
                "authority_state": "ready",
            },
            {
                "kind": "follow_up",
                "provenance": {"subject_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"},
                "authority_state": "ready",
            },
        ],
        organization_id=str(_ORG_A),
    )
    for item in items:
        modes = {a["execution_mode"] for a in item["command_actions"]}
        assert EXEC_INLINE_GOVERNED not in modes
        assert EXEC_NAVIGATE_GOVERNED in modes


def test_compose_does_not_mutate_contact_or_deal(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        before_c = db.query(Contact).count()
        before_d = db.query(Deal).count()
        before_l = db.query(AgentActionLog).count()
    finally:
        db.close()
    build_command_center_snapshot(organization_id=str(_ORG_A))
    db = tenant_db()
    try:
        assert db.query(Contact).count() == before_c
        assert db.query(Deal).count() == before_d
        assert db.query(AgentActionLog).count() == before_l
    finally:
        db.close()


def test_command_refresh_after_accept_clears_pending(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    before = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert any(i["kind"] == "qualified_demand" for i in before["decision_items"])
    assert client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_A},
    ).status_code == 200
    after = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert not any(i["kind"] == "qualified_demand" for i in after["decision_items"])
    assert after["commercial_funnel"]["summary"]["demand_accepted"] >= 1


def test_cos3_and_cos4_still_present(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert snap["decision_items"]
    assert snap["commercial_funnel"]["state"] == "ok"
    assert snap["command_action_summary"]["inline_governed"] >= 1
