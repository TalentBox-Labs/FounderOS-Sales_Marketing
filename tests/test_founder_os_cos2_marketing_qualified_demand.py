"""COS-2 — Marketing signal → QualifiedDemand → existing commercial spine."""

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
import runner_api_routers.revenue_orchestration as rev_orch_mod
import runner_api_routers.ui as ui_mod
from revenue_os.agents.orchestration import WorkflowOrchestrator
from revenue_os.auth import hash_password
from revenue_os.models.automation_state import AgentActionLog
from revenue_os.models.base import Base
from revenue_os.models.contact import Company, Contact, ContactSource, ContactStatus
from revenue_os.models.deal import Deal, DealStage, Pipeline, PipelineType
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
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
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_COMPANY_A = uuid.UUID("ca11e001-0000-4000-8000-00000000000a")
_COMPANY_B = uuid.UUID("ca11e001-0000-4000-8000-00000000000b")
_PIPELINE_A = uuid.UUID("f1111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_DEAL_A = uuid.UUID("e1111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_DEMAND_A = "11111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_DEMAND_B = "22222222-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_DEMAND_MISSING = "33333333-cccc-4ccc-8ccc-cccccccccccc"
_OPERATOR = "Krishna Founder"
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()
    WorkflowOrchestrator._workflows.clear()
    WorkflowOrchestrator._executions.clear()
    WorkflowOrchestrator._revenue_workflows_seeded = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 'cos2.db'}")
    Base.metadata.create_all(bind=engine)
    sf = sessionmaker(bind=engine)
    import revenue_os.database as db_mod
    import revenue_os.services.activity_log as al
    import revenue_os.services.approvals as approvals_mod
    import revenue_os.services.founder_ui_read_model as founder_rm
    import revenue_os.services.operator_flow_read_model as of_rm
    import revenue_os.services.revenue_orchestration_service as rev_svc
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
        rev_svc,
        identity_mod,
        rev_orch_mod,
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
                Organization(id=_ORG_A, name="A", slug="org-a", status=OrganizationStatus.ACTIVE),
                Organization(id=_ORG_B, name="B", slug="org-b", status=OrganizationStatus.ACTIVE),
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
        company = Company(id=_COMPANY_A, name="Acme Labs", domain="acme-cos2.demo.local")
        company_b = Company(
            id=_COMPANY_B, name="OtherCo Secret", domain="otherco-cos2.demo.local"
        )
        db.add_all([company, company_b])
        db.flush()
        pipeline = Pipeline(
            id=_PIPELINE_A,
            name="Sales",
            pipeline_type=PipelineType.SALES,
            is_default=1,
        )
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
                    user_id=owner_b.id,
                    organization_id=_ORG_B,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                ),
                Contact(
                    id=_CONTACT_A,
                    first_name="Alice",
                    last_name="A",
                    email="alice@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
                    company_id=company.id,
                    lead_score=70,
                ),
                Contact(
                    id=_CONTACT_B,
                    first_name="Bob",
                    last_name="B",
                    email="bob@example.com",
                    status=ContactStatus.LEAD,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_B,
                    company_id=company_b.id,
                ),
                Deal(
                    id=_DEAL_A,
                    name="Alice deal",
                    stage=DealStage.DISCOVERY,
                    value=1000,
                    organization_id=_ORG_A,
                    contact_id=_CONTACT_A,
                    company_id=company.id,
                    pipeline_id=pipeline.id,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


def _register_org_demand(
    db_factory: sessionmaker,
    *,
    demand_id: str,
    org_id: uuid.UUID,
    email: str,
    name: str,
    source: str,
    qualification: dict | None,
    attribution: dict | None,
    company_hint: dict | None = None,
) -> None:
    db = db_factory()
    try:
        payload = compose_marketing_qualified_demand(
            demand_id=demand_id,
            occurred_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            source=source,
            channel="website",
            person={"email": email, "name": name},
            company_hint=company_hint,
            marketing_qualification=qualification,
            content_attribution=attribution,
        )
        register_marketing_handoff(
            db, payload, _OPERATOR, organization_id=str(org_id)
        )
    finally:
        db.close()


def test_marketing_signal_uses_canonical_qualified_demand(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    before = tenant_db().query(Contact).count()
    _register_org_demand(
        tenant_db,
        demand_id=_DEMAND_A,
        org_id=_ORG_A,
        email="inbound.a@example.com",
        name="Inbound A",
        source="web_form",
        qualification={
            "tier": "mql",
            "score": 81,
            "reason": "Requested a product walkthrough from the website form.",
        },
        attribution={"utm_source": "website", "campaign": "spring-inbound"},
        company_hint={"name": "Inbound Co"},
    )
    db = tenant_db()
    try:
        assert db.query(Contact).count() == before
        handoff = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == ACTION_HANDOFF, AgentActionLog.target_id == _DEMAND_A)
            .one()
        )
        payload = (handoff.detail or {}).get("payload") or {}
        assert payload["source"] == "web_form"
        assert payload["marketing_qualification"]["reason"].startswith("Requested a product")
        assert db.query(Contact).filter(Contact.email == "inbound.a@example.com").first() is None
    finally:
        db.close()


def test_demand_distinct_from_contact_until_accept(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_org_demand(
        tenant_db,
        demand_id=_DEMAND_A,
        org_id=_ORG_A,
        email="inbound.a@example.com",
        name="Inbound A",
        source="web_form",
        qualification={"reason": "High-intent website form"},
        attribution={"utm_source": "website"},
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    people = client.get("/demand")
    assert people.status_code == 200
    assert "inbound.a@example.com" in people.text
    assert 'data-testid="demand-decision-state"' in people.text
    assert "Needs your decision" in people.text
    assert "Why it matters" in people.text
    assert "High-intent website form" in people.text
    assert "Website form" in people.text
    assert "What happens next" in people.text
    assert "Accepted into People" not in people.text
    alice = client.get(f"/contacts/{_CONTACT_A}")
    assert alice.status_code == 200
    assert "inbound.a@example.com" not in alice.text


def test_accept_uses_existing_spine_reject_does_not(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_org_demand(
        tenant_db,
        demand_id=_DEMAND_A,
        org_id=_ORG_A,
        email="inbound.a@example.com",
        name="Inbound A",
        source="campaign",
        qualification={"reason": "Campaign reply asked for a demo"},
        attribution={"campaign": "spring-inbound"},
    )
    reject_id = "44444444-dddd-4ddd-8ddd-dddddddddddd"
    _register_org_demand(
        tenant_db,
        demand_id=reject_id,
        org_id=_ORG_A,
        email="reject.me@example.com",
        name="Reject Me",
        source="social",
        qualification={"notes": "Weak fit — founder should reject"},
        attribution={"utm_source": "linkedin"},
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    accepted = client.post(
        "/api/v1/operator/actions/qualified-demand/accept",
        json={"demand_id": _DEMAND_A, "notes": "take inbound"},
    )
    assert accepted.status_code == 200
    body = accepted.json()
    assert body.get("contact_id")
    assert body.get("deal_created") is False
    rejected = client.post(
        "/api/v1/operator/actions/qualified-demand/reject",
        json={"demand_id": reject_id, "reason": "not a fit"},
    )
    assert rejected.status_code == 200
    db = tenant_db()
    try:
        created = db.query(Contact).filter(Contact.email == "inbound.a@example.com").one()
        assert created.organization_id == _ORG_A
        assert created.status == ContactStatus.LEAD
        assert db.query(Contact).filter(Contact.email == "reject.me@example.com").first() is None
        assert (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == ACTION_ACCEPTED, AgentActionLog.target_id == _DEMAND_A)
            .first()
            is not None
        )
        assert (
            db.query(AgentActionLog)
            .filter(AgentActionLog.action_type == ACTION_REJECTED, AgentActionLog.target_id == reject_id)
            .first()
            is not None
        )
        deal = db.get(Deal, _DEAL_A)
        assert deal is not None
        assert deal.stage == DealStage.DISCOVERY
    finally:
        db.close()
    people = client.get("/demand")
    assert "inbound.a@example.com" in people.text
    assert "reject.me@example.com" not in people.text
    command = client.get("/command")
    assert command.status_code == 200
    activity = client.get("/activity")
    assert "Demand registered" in activity.text or "qualified_demand_handoff" in activity.text
    assert "system recommended" in activity.text
    assert "human decided" in activity.text


def test_missing_qualification_is_honest(client: TestClient, tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_org_demand(
        tenant_db,
        demand_id=_DEMAND_MISSING,
        org_id=_ORG_A,
        email="bare@example.com",
        name="Bare Demand",
        source="manual",
        qualification=None,
        attribution=None,
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    r = client.get("/demand")
    assert "No extra qualification notes were stored" in r.text
    assert "Why it matters" in r.text
    assert "Needs your decision" in r.text
    assert "Channel: website" in r.text


def test_cross_tenant_demand_and_company_isolated(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_org_demand(
        tenant_db,
        demand_id=_DEMAND_A,
        org_id=_ORG_A,
        email="inbound.a@example.com",
        name="Inbound A",
        source="web_form",
        qualification={"reason": "Org A walkthrough request"},
        attribution={"utm_source": "website"},
    )
    _register_org_demand(
        tenant_db,
        demand_id=_DEMAND_B,
        org_id=_ORG_B,
        email="inbound.b@example.com",
        name="Inbound B",
        source="campaign",
        qualification={"reason": "Org B secret campaign fit"},
        attribution={"campaign": "otherco-secret"},
        company_hint={"name": "OtherCo Secret"},
    )
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    a_page = client.get("/demand")
    assert "inbound.a@example.com" in a_page.text
    assert "Org A walkthrough request" in a_page.text
    assert "inbound.b@example.com" not in a_page.text
    assert "Org B secret campaign fit" not in a_page.text
    assert "otherco-secret" not in a_page.text
    from revenue_os.services.founder_ui_read_model import build_demand_contacts_snapshot

    leaked = {
        "demand_id": _DEMAND_B,
        "name": "Inbound B",
        "email": "inbound.b@example.com",
        "source": "campaign",
        "contact_link": "not_yet_created",
    }
    with patch(
        "revenue_os.services.founder_ui_read_model.build_operator_flow_snapshot",
        return_value={"contacts": [], "pending_demands": [leaked], "deals": []},
    ):
        snap = build_demand_contacts_snapshot(organization_id=str(_ORG_A))
    blob = str(snap["pending_demands"])
    assert "Org B secret campaign fit" not in blob
    assert "OtherCo Secret" not in blob
    assert "otherco-secret" not in blob


def test_unresolved_org_does_not_unscoped_handoff_enrichment(
    tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(tenant_db)
    import revenue_os.services.founder_ui_read_model as founder_rm

    def _must_not_open() -> None:
        raise AssertionError("unscoped AgentActionLog/Contact enrichment")

    monkeypatch.setattr(founder_rm, "SessionLocal", _must_not_open)
    snap = founder_rm.build_demand_contacts_snapshot(organization_id=None)
    assert snap["contacts"] == []
    assert snap["pending_demands"] == []


def test_marketing_slice_does_not_mutate_contact_status_or_deal_stage(
    tenant_db: sessionmaker,
) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        before_status = db.get(Contact, _CONTACT_A).status
        before_stage = db.get(Deal, _DEAL_A).stage
    finally:
        db.close()
    _register_org_demand(
        tenant_db,
        demand_id=_DEMAND_A,
        org_id=_ORG_A,
        email="alice@example.com",
        name="Alice A",
        source="web_form",
        qualification={"reason": "Existing person signal"},
        attribution={"utm_source": "website"},
    )
    db = tenant_db()
    try:
        assert db.get(Contact, _CONTACT_A).status == before_status
        assert db.get(Deal, _DEAL_A).stage == before_stage
    finally:
        db.close()


def test_no_new_crm_sot_and_authority_not_weakened() -> None:
    composer = inspect.getsource(compose_marketing_qualified_demand)
    assert "Contact(" not in composer
    assert "Deal(" not in composer
    assert "apply_contact_status_update" not in composer
    assert "create_tenant_calendar_event" not in composer
    marketing_src = (_ROOT / "revenue_os/services/marketing_qualified_demand.py").read_text()
    assert "SessionLocal" not in marketing_src
    assert "apply_deal_stage_update" not in marketing_src
    approvals = (_ROOT / "templates/founder_approvals.html").read_text()
    assert "JSON.stringify({})" in approvals
    contact = (_ROOT / "templates/founder_contact.html").read_text()
    assert "advisory only" in contact.lower()
    demand = (_ROOT / "templates/founder_demand.html").read_text()
    assert "book_meeting" not in demand.lower()


def test_schema_still_has_no_alias_crm_tables(tenant_db: sessionmaker) -> None:
    db = tenant_db()
    try:
        names = set(sa_inspect(db.get_bind()).get_table_names())
    finally:
        db.close()
    assert "leads" not in names
    assert "opportunities" not in names
    assert "audiences" not in names
    assert "campaigns" not in names
    assert "qualified_demands" not in names
