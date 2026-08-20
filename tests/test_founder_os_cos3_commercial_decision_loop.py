"""COS-3 — Founder OS commercial decision loop (presentation / composition)."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

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
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.commercial_decision_loop import (
    AUTHORITY_COMPLETED,
    AUTHORITY_REQUIRES_FOUNDER,
    compose_commercial_decision_items,
    summarize_decision_loop,
)
from revenue_os.services.founder_ui_read_model import build_command_center_snapshot
from revenue_os.services.marketing_qualified_demand import compose_marketing_qualified_demand
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED,
    ACTION_HANDOFF,
    accept_qualified_demand,
    register_marketing_handoff,
)
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEMAND_A = "11111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_DEMAND_B = "22222222-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
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
    engine = create_engine(f"sqlite:///{tmp_path / 'cos3.db'}")
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


def test_command_center_composes_decision_items(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert snap["decision_items"]
    kinds = {i["kind"] for i in snap["decision_items"]}
    assert "qualified_demand" in kinds
    assert snap["decision_loop"]["requires_founder"] >= 1
    r = client.get("/command")
    assert r.status_code == 200
    assert 'data-testid="command-decision-loop"' in r.text
    assert 'data-testid="command-decision-item"' in r.text
    assert "Needs your decision" in r.text
    assert "Requested a product walkthrough" in r.text


def test_qualified_demand_enters_decision_presentation(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(
        tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com", name="Ada A"
    )
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    qd = [i for i in snap["decision_items"] if i["kind"] == "qualified_demand"]
    assert len(qd) == 1
    assert qd[0]["authority_state"] == AUTHORITY_REQUIRES_FOUNDER
    assert qd[0]["commercial_source"] == "marketing"
    assert qd[0]["href"] == "/demand"
    assert qd[0]["provenance"]["action_type"] == ACTION_HANDOFF


def test_no_new_persistent_sot() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    tables = set(sa_inspect(engine).get_table_names())
    forbidden = {
        "commercial_decision",
        "decision_item",
        "founder_decision",
        "opportunity",
        "lead",
        "audience",
        "campaign",
    }
    assert not (tables & forbidden)
    src = inspect.getsource(
        __import__(
            "revenue_os.services.commercial_decision_loop",
            fromlist=["compose_commercial_decision_items"],
        )
    )
    assert "SessionLocal" not in src
    assert "db.commit" not in src
    assert "db.add" not in src


def test_cross_tenant_decision_isolation(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(
        tenant_db, demand_id=_DEMAND_B, org_id=_ORG_B, email="secret@example.com", name="Secret B"
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    blob = str(snap["decision_items"])
    assert "secret@example.com" not in blob
    assert "Secret B" not in blob
    assert str(_CONTACT_B) not in blob
    r = client.get("/command")
    assert "secret@example.com" not in r.text


def test_missing_tenant_fails_closed(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = build_command_center_snapshot(organization_id=None)
    assert snap["decision_items"] == []
    assert snap["decision_loop"]["total"] == 0
    assert snap["pending_demands"] == []
    assert snap["state"] == "unavailable"
    empty = compose_commercial_decision_items(
        pending_demands=[{"demand_id": _DEMAND_A, "email": "leak@example.com"}],
        organization_id=None,
    )
    assert empty == []


def test_presentation_does_not_bypass_human_authority() -> None:
    loop_src = (_ROOT / "revenue_os/services/commercial_decision_loop.py").read_text()
    assert "accept_qualified_demand" not in loop_src
    assert "reject_qualified_demand" not in loop_src
    assert "approve_request" not in loop_src
    assert "book_meeting" not in loop_src or "booking_eligibility" in loop_src
    assert "send_outreach" not in loop_src
    tpl = (_ROOT / "templates/founder_command.html").read_text()
    assert "contactAction(" not in tpl
    assert "/booking/propose" not in tpl
    assert "approve-btn" not in tpl


def test_presentation_does_not_mutate_contact_or_deal(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        before_contacts = db.query(Contact).count()
        before_logs = db.query(AgentActionLog).count()
    finally:
        db.close()
    build_command_center_snapshot(organization_id=str(_ORG_A))
    db = tenant_db()
    try:
        assert db.query(Contact).count() == before_contacts
        assert db.query(AgentActionLog).count() == before_logs
    finally:
        db.close()


def test_completed_state_from_canonical_evidence(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        accept_qualified_demand(
            db, _DEMAND_A, _OPERATOR, organization_id=str(_ORG_A)
        )
    finally:
        db.close()
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    completed = [
        i for i in snap["decision_items"] if i["authority_state"] == AUTHORITY_COMPLETED
    ]
    assert any(i["provenance"].get("action_type") == ACTION_ACCEPTED for i in completed)
    pending_qd = [i for i in snap["decision_items"] if i["kind"] == "qualified_demand"]
    assert pending_qd == []


def test_company_enrichment_tenant_safe() -> None:
    items = compose_commercial_decision_items(
        pending_demands=[
            {
                "demand_id": _DEMAND_A,
                "name": "Ada",
                "email": "a@example.com",
                "company_hint_name": "Hint Co",
                "why_it_matters": "Fit",
                "human_decision_state": "awaiting_intake",
                "authority_class": "SYSTEM_RECOMMENDED",
            }
        ],
        organization_id=str(_ORG_A),
    )
    assert items[0]["company_label"] == "Hint Co"
    # Composer does not load Company ORM — only passes through already-safe presentation fields.
    assert "SessionLocal" not in inspect.getsource(compose_commercial_decision_items)


def test_governed_routes_remain_authoritative() -> None:
    tpl = (_ROOT / "templates/founder_command.html").read_text()
    assert 'href="/pending-approvals"' in tpl
    assert 'href="/demand"' in tpl
    assert 'href="/activity"' in tpl
    # No direct mutation endpoints in Command Center template.
    assert "/api/v1/operator/actions/qualified-demand/accept" not in tpl
    assert "/api/v1/sales/intake/demand/accept" not in tpl


def test_approval_enters_decision_loop() -> None:
    items = compose_commercial_decision_items(
        pending_approvals=[
            {
                "id": "appr-1",
                "action_type": "book_meeting",
                "title": "Book meeting with Ada",
                "action_label": "Meeting proposed",
                "target_id": str(uuid.uuid4()),
                "created_at": "2026-08-20T00:00:00Z",
            }
        ],
        organization_id=str(_ORG_A),
    )
    assert items[0]["kind"] == "approval"
    assert items[0]["authority_state"] == AUTHORITY_REQUIRES_FOUNDER
    assert items[0]["provenance"]["evidence_type"] == "approval_request"


def test_decision_loop_summary_deterministic() -> None:
    items = compose_commercial_decision_items(
        pending_demands=[{"demand_id": _DEMAND_A, "name": "A"}],
        pending_approvals=[{"id": "1", "action_type": "send_email", "title": "Send"}],
        organization_id=str(_ORG_A),
    )
    summary = summarize_decision_loop(items)
    assert summary["requires_founder"] == 2
    assert summary["total"] == 2
    assert "score" not in summary
    assert "confidence" not in str(items)


def test_command_center_does_not_call_booking_or_send(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    with patch(
        "revenue_os.services.founder_ui_read_model.inspect_booking_eligibility"
    ) as book:
        with patch(
            "revenue_os.services.founder_ui_read_model.inspect_follow_up_eligibility",
            side_effect=Exception("skip"),
        ):
            build_command_center_snapshot(organization_id=str(_ORG_A))
        book.assert_not_called()
