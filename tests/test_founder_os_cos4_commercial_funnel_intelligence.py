"""COS-4 — Founder OS commercial funnel & pipeline intelligence."""

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
from revenue_os.models.deal import Deal, DealStage, Pipeline, PipelineType
from revenue_os.models.organization import (
    MembershipStatus,
    Organization,
    OrganizationMembership,
    OrganizationStatus,
)
from revenue_os.models.user import User
from revenue_os.services.commercial_funnel_intelligence import (
    FUNNEL_BAND_DEMAND,
    FUNNEL_BAND_OUTCOME,
    FUNNEL_BAND_PIPELINE,
    REASON_PENDING_QUALIFIED_DEMAND,
    SALES_OPEN_STAGES,
    compose_commercial_funnel_snapshot,
    dedupe_pending_demands,
)
from revenue_os.services.founder_ui_read_model import build_command_center_snapshot
from revenue_os.services.marketing_qualified_demand import compose_marketing_qualified_demand
from revenue_os.services.commercial_outcome_service import (
    ACTION_ACCEPTED as CO_ACCEPTED,
)
from revenue_os.services.commercial_outcome_service import (
    ACTION_HANDOFF as CO_HANDOFF,
)
from revenue_os.services.commercial_outcome_service import (
    ACTION_REJECTED as CO_REJECTED,
)
from revenue_os.services.qualified_demand_service import (
    ACTION_ACCEPTED,
    ACTION_HANDOFF,
    ACTION_REJECTED,
    accept_qualified_demand,
    register_marketing_handoff,
)
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

_ORG_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEAL_A = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_DEAL_B = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
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
    engine = create_engine(f"sqlite:///{tmp_path / 'cos4.db'}")
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
        pipeline = Pipeline(
            name="Test Pipeline",
            pipeline_type=PipelineType.SALES,
            stages="discovery,qualified,proposal,negotiation,closed_won,closed_lost",
            is_default=1,
        )
        db.add(pipeline)
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
                    id=_CONTACT_A,
                    first_name="Ada",
                    last_name="A",
                    email="a@example.com",
                    status=ContactStatus.QUALIFIED,
                    source=ContactSource.MANUAL,
                    organization_id=_ORG_A,
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
                Deal(
                    id=_DEAL_A,
                    name="Deal A Open",
                    stage=DealStage.PROPOSAL,
                    value=5000.0,
                    contact_id=_CONTACT_A,
                    pipeline_id=pipeline.id,
                    organization_id=_ORG_A,
                ),
                Deal(
                    id=_DEAL_B,
                    name="Deal B Secret",
                    stage=DealStage.DISCOVERY,
                    value=9000.0,
                    contact_id=_CONTACT_B,
                    pipeline_id=pipeline.id,
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


# --- A. Tenant isolation ---


def test_tenant_a_excludes_tenant_b_deal(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    blob = str(snap)
    assert snap["state"] == "ok"
    assert snap["summary"]["open_deals"] == 1
    assert "Deal B Secret" not in blob
    assert str(_DEAL_B) not in blob


def test_tenant_a_excludes_tenant_b_contact_state(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["people"] == 1
    assert "bob@example.com" not in str(snap)


def test_tenant_a_excludes_tenant_b_agent_log(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(
        tenant_db, demand_id=_DEMAND_B, org_id=_ORG_B, email="secret@example.com", name="Secret B"
    )
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["demand_pending"] == 0
    assert "secret@example.com" not in str(snap)


def test_tenant_a_excludes_tenant_b_pending_approval(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        db.add(
            ApprovalRequest(
                requested_by=_OPERATOR,
                action_type="send_outreach",
                title="Outreach approval B",
                target_type="contact",
                target_id=str(_CONTACT_B),
                status="pending",
                payload={"organization_id": str(_ORG_B), "contact_id": str(_CONTACT_B)},
            )
        )
        db.commit()
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["approvals_pending"] == 0


def test_missing_organization_id_fails_closed(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = compose_commercial_funnel_snapshot(organization_id=None)
    assert snap["state"] == "unavailable"
    assert snap["funnel"] == {}
    cmd = build_command_center_snapshot(organization_id=None)
    assert cmd["state"] == "unavailable"
    assert cmd.get("commercial_funnel", {}) == {}


# --- B. Read-only authority ---


def test_compose_creates_no_contact(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        before = db.query(Contact).count()
    finally:
        db.close()
    compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    db = tenant_db()
    try:
        assert db.query(Contact).count() == before
    finally:
        db.close()


def test_compose_creates_no_deal(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        before = db.query(Deal).count()
    finally:
        db.close()
    compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    db = tenant_db()
    try:
        assert db.query(Deal).count() == before
    finally:
        db.close()


def test_compose_creates_no_agent_log(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        before = db.query(AgentActionLog).count()
    finally:
        db.close()
    compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    db = tenant_db()
    try:
        assert db.query(AgentActionLog).count() == before
    finally:
        db.close()


def test_compose_creates_no_approval_request(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        before = db.query(ApprovalRequest).count()
    finally:
        db.close()
    compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    db = tenant_db()
    try:
        assert db.query(ApprovalRequest).count() == before
    finally:
        db.close()


def test_compose_commits_no_mutation(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        before_deals = {d.id: d.stage for d in db.query(Deal).all()}
        before_contacts = db.query(Contact).count()
        before_logs = db.query(AgentActionLog).count()
    finally:
        db.close()
    compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    build_command_center_snapshot(organization_id=str(_ORG_A))
    db = tenant_db()
    try:
        after_deals = {d.id: d.stage for d in db.query(Deal).all()}
        assert before_deals == after_deals
        assert db.query(Contact).count() == before_contacts
        assert db.query(AgentActionLog).count() == before_logs
    finally:
        db.close()


# --- C. Funnel correctness ---


def test_demand_band_maps_pending_handoff(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    demand = snap["funnel"]["demand"]
    assert demand["band"] == FUNNEL_BAND_DEMAND
    assert demand["pending_intake"] == 1
    assert any("pending" in s for s in demand["states_included"])
    assert any("accepted" in s for s in demand["states_included"])


def test_pipeline_band_maps_open_deal_stage(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    pipeline = snap["funnel"]["pipeline"]
    assert pipeline["band"] == FUNNEL_BAND_PIPELINE
    assert pipeline["open_deals"] == 1
    assert pipeline["by_stage"].get("proposal") == 1


def test_outcome_band_maps_closed_won_deal(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        deal = db.get(Deal, _DEAL_A)
        assert deal is not None
        deal.stage = DealStage.CLOSED_WON
        deal.closed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    outcome = snap["funnel"]["outcome"]
    assert outcome["band"] == FUNNEL_BAND_OUTCOME
    assert outcome["deals_closed_won"] == 1
    assert snap["summary"]["open_deals"] == 0


def test_accepted_demand_increments_outcome_count(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        accept_qualified_demand(
            db, _DEMAND_A, _OPERATOR, organization_id=str(_ORG_A)
        )
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["demand_accepted"] == 1
    assert snap["summary"]["demand_pending"] == 0


def test_recruitment_stage_not_in_open_pipeline_band(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        deal = db.get(Deal, _DEAL_A)
        assert deal is not None
        deal.stage = DealStage.SOURCING
        db.commit()
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["pipeline"]["open_count"] == 0
    assert "sourcing" not in snap["pipeline"]["by_stage"]
    assert snap["pipeline"]["ignored_non_sales"] == 1


# --- D. Attention correctness ---


def test_pending_demand_produces_attention_reason(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    codes = [i["reason_code"] for i in snap["attention"]["entries"]]
    assert REASON_PENDING_QUALIFIED_DEMAND in codes


def test_accepted_demand_not_falsely_actionable(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        accept_qualified_demand(
            db, _DEMAND_A, _OPERATOR, organization_id=str(_ORG_A)
        )
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    codes = [i["reason_code"] for i in snap["attention"]["entries"]]
    assert REASON_PENDING_QUALIFIED_DEMAND not in codes


def test_attention_has_no_numeric_score(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    for item in snap["attention"]["entries"]:
        assert "score" not in item
        assert "priority" not in item
        assert "reason_code" in item


# --- E. Company safety ---


def test_no_company_model_in_composer_source() -> None:
    src = (_ROOT / "revenue_os/services/commercial_funnel_intelligence.py").read_text()
    assert "from revenue_os.models.contact import Company" not in src
    assert "db.query(Company" not in src
    assert "Company(" not in src
    assert "company_id" not in src


def test_no_global_company_lookup_at_runtime(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    with patch("revenue_os.models.contact.Company") as mock_company:
        mock_company.query.side_effect = AssertionError("Company lookup forbidden")
        snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
        assert snap["state"] == "ok"


# --- F. Integration / UI ---


def test_command_center_includes_commercial_funnel(
    client: TestClient, tenant_db: sessionmaker
) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _login(client, "owner-a@example.com", "pass-a", str(_ORG_A))
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert snap["commercial_funnel"]["state"] == "ok"
    assert snap["commercial_funnel"]["summary"]["demand_pending"] == 1
    r = client.get("/command")
    assert r.status_code == 200
    assert 'data-testid="command-commercial-funnel"' in r.text
    assert "Commercial funnel" in r.text
    assert "ARR" not in r.text
    assert "MRR" not in r.text


def test_no_new_persistent_sot() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    tables = set(sa_inspect(engine).get_table_names())
    forbidden = {
        "commercial_funnel",
        "funnel_snapshot",
        "pipeline_intelligence",
        "revenue_intelligence",
        "founder_metrics",
    }
    assert not (tables & forbidden)
    src = inspect.getsource(
        __import__(
            "revenue_os.services.commercial_funnel_intelligence",
            fromlist=["compose_commercial_funnel_snapshot"],
        )
    )
    assert "db.add" not in src
    assert "db.delete" not in src
    assert "db.commit" not in src
    tpl = (_ROOT / "templates/founder_command.html").read_text()
    assert "ARR" not in tpl
    assert "MRR" not in tpl


def test_cos3_decision_items_still_present(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    snap = build_command_center_snapshot(organization_id=str(_ORG_A))
    assert snap["decision_items"]
    assert snap["commercial_funnel"]["summary"]["decision_items_total"] == len(
        snap["decision_items"]
    )


# --- G. Semantic correction v1 ---


def _add_log(
    db_factory: sessionmaker,
    *,
    action_type: str,
    target_id: str,
    org_id: uuid.UUID,
    detail: dict | None = None,
) -> None:
    db = db_factory()
    try:
        db.add(
            AgentActionLog(
                actor=_OPERATOR,
                action_type=action_type,
                target_type="test",
                target_id=target_id,
                status="completed",
                detail=detail or {},
                organization_id=org_id,
            )
        )
        db.commit()
    finally:
        db.close()


def test_duplicate_qd_handoff_does_not_inflate_pending(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _add_log(
        tenant_db,
        action_type=ACTION_HANDOFF,
        target_id=_DEMAND_A,
        org_id=_ORG_A,
        detail={"payload": {"person": {"email": "a@example.com"}}},
    )
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["demand_pending"] == 1
    assert snap["funnel"]["demand"]["event_counts"]["handoff_events"] >= 2


def test_duplicate_qd_accept_does_not_inflate_accepted(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        accept_qualified_demand(db, _DEMAND_A, _OPERATOR, organization_id=str(_ORG_A))
    finally:
        db.close()
    _add_log(tenant_db, action_type=ACTION_ACCEPTED, target_id=_DEMAND_A, org_id=_ORG_A)
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["demand_accepted"] == 1
    assert snap["funnel"]["demand"]["event_counts"]["accepted_events"] >= 2


def test_duplicate_qd_reject_does_not_inflate_rejected(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    _add_log(tenant_db, action_type=ACTION_REJECTED, target_id=_DEMAND_A, org_id=_ORG_A)
    _add_log(tenant_db, action_type=ACTION_REJECTED, target_id=_DEMAND_A, org_id=_ORG_A)
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["demand_rejected"] == 1
    assert snap["summary"]["demand_pending"] == 0
    assert snap["funnel"]["demand"]["event_counts"]["rejected_events"] >= 2


def test_accepted_rejected_removed_from_pending(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    _register_demand(tenant_db, demand_id=_DEMAND_A, org_id=_ORG_A, email="a@example.com")
    db = tenant_db()
    try:
        accept_qualified_demand(db, _DEMAND_A, _OPERATOR, organization_id=str(_ORG_A))
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["demand_pending"] == 0
    assert snap["summary"]["demand_accepted"] == 1
    rows = dedupe_pending_demands(
        [{"demand_id": _DEMAND_A}, {"demand_id": _DEMAND_A}],
        accepted_ids={_DEMAND_A},
        rejected_ids=set(),
    )
    assert rows == []


def test_duplicate_co_handoff_does_not_inflate_unique_outcomes(
    tenant_db: sessionmaker,
) -> None:
    _seed(tenant_db)
    outcome_id = "33333333-cccc-4ccc-8ccc-cccccccccccc"
    _add_log(
        tenant_db,
        action_type=CO_HANDOFF,
        target_id=outcome_id,
        org_id=_ORG_A,
        detail={"deal_id": str(_DEAL_A)},
    )
    _add_log(
        tenant_db,
        action_type=CO_HANDOFF,
        target_id=outcome_id,
        org_id=_ORG_A,
        detail={"deal_id": str(_DEAL_A)},
    )
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["outcomes"]["commercial_outcome_accepted"] == 0
    assert snap["outcomes"]["commercial_outcome_rejected"] == 0
    assert snap["outcomes"]["event_counts"]["handoff_events"] == 2
    assert "handoff_events" in snap["funnel"]["outcome"]["event_counts"]


def test_co_accepted_rejected_reconciles_to_one_outcome(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    outcome_id = "44444444-dddd-4ddd-8ddd-dddddddddddd"
    _add_log(tenant_db, action_type=CO_HANDOFF, target_id=outcome_id, org_id=_ORG_A)
    _add_log(tenant_db, action_type=CO_ACCEPTED, target_id=outcome_id, org_id=_ORG_A)
    _add_log(tenant_db, action_type=CO_ACCEPTED, target_id=outcome_id, org_id=_ORG_A)
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["outcomes"]["commercial_outcome_accepted"] == 1
    assert snap["outcomes"]["event_counts"]["accepted_events"] >= 2
    assert snap["funnel"]["outcome"]["commercial_outcome_accepted"] == 1
    assert snap["funnel"]["outcome"]["event_counts"]["handoff_events"] >= 1


def test_unknown_deal_stage_is_not_open(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    snap = compose_commercial_funnel_snapshot(
        organization_id=str(_ORG_A),
        operator_flow={
            "deals": [
                {
                    "id": str(_DEAL_A),
                    "name": "Weird",
                    "stage": "not_a_real_stage",
                    "terminal": False,
                }
            ],
            "contacts": [],
            "pending_demands": [],
            "outcomes": {"pending_handoff": [], "pending_revenue": []},
        },
        pending_demands=[],
    )
    assert snap["pipeline"]["open_count"] == 0
    assert snap["pipeline"]["ignored_unknown"] == 1
    assert snap["summary"]["open_deals"] == 0


def test_recruitment_placed_not_open_commercial_pipeline(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        deal = db.get(Deal, _DEAL_A)
        assert deal is not None
        deal.stage = DealStage.PLACED
        db.commit()
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["pipeline"]["open_count"] == 0
    assert snap["summary"]["deals_closed_won"] == 0
    assert snap["pipeline"]["ignored_non_sales"] == 1


def test_canonical_sales_open_stage_is_open(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["pipeline"]["open_count"] == 1
    assert snap["pipeline"]["by_stage"].get("proposal") == 1
    assert "proposal" in SALES_OPEN_STAGES


def test_closed_won_is_won(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        deal = db.get(Deal, _DEAL_A)
        assert deal is not None
        deal.stage = DealStage.CLOSED_WON
        deal.closed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["deals_closed_won"] == 1
    assert snap["summary"]["open_deals"] == 0


def test_closed_lost_is_lost(tenant_db: sessionmaker) -> None:
    _seed(tenant_db)
    db = tenant_db()
    try:
        deal = db.get(Deal, _DEAL_A)
        assert deal is not None
        deal.stage = DealStage.CLOSED_LOST
        deal.closed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()
    snap = compose_commercial_funnel_snapshot(organization_id=str(_ORG_A))
    assert snap["summary"]["deals_closed_lost"] == 1
    assert snap["summary"]["open_deals"] == 0
    assert snap["summary"]["deals_closed_won"] == 0
