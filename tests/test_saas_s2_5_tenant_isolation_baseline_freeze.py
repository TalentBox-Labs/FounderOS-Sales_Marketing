"""SaaS S2.5 — Organization / Tenant Isolation Baseline v1.0 freeze suite."""

from __future__ import annotations

import inspect
import uuid
from dataclasses import fields as dc_fields
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import revenue_os.models  # noqa: F401
import runner_api_routers.cockpit as cockpit_mod
import runner_api_routers.crm as crm_mod
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
from revenue_os.services.identity_context import (
    MVP_ROLES,
    IdentityContext,
    PrincipalKind,
    bind_requested_by,
    service_identity,
)
from revenue_os.services.mutation_authority import HumanAuthorityError, require_human_mutation_authority
from revenue_os.services.qualified_demand_service import ACTION_HANDOFF as QD_HANDOFF
from revenue_os.services.tenant_bootstrap import bootstrap_organization_for_users
from revenue_os.services.tenant_context import TenantContext, membership_role_allows_mutation
from revenue_os.services.tenant_resolution import ORGANIZATION_COOKIE
from runner_api import app

ROOT = Path(__file__).resolve().parents[1]
DOCS_S2 = ROOT / "docs" / "saas" / "s2"
DOCS_S2_5 = ROOT / "docs" / "saas" / "s2_5"
_OPERATOR = "Krishna Founder"

_ORG_A_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ORG_B_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_CONTACT_A_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT_B_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_DEAL_A_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_DEAL_B_ID = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
_DEMAND_A_ID = "11111111-1111-1111-1111-111111111111"
_DEMAND_B_ID = "22222222-2222-2222-2222-222222222222"
_OUTCOME_A_ID = "44444444-4444-4444-4444-444444444444"
_OUTCOME_B_ID = "33333333-3333-3333-3333-333333333333"

S2_5_REQUIRED_ARTIFACTS = (
    "S2_5_TENANCY_TOPOLOGY_v1.0.md",
    "CANONICAL_TENANT_CONTRACT_v1.0.md",
    "ORGANIZATION_MEMBERSHIP_CONTRACT_v1.0.md",
    "TENANT_OWNED_ENTITY_MANIFEST_v1.0.md",
    "S2_5_ID_ONLY_MUTATION_RISK_REGISTER_v1.0.md",
    "CROSS_TENANT_ATTACK_MATRIX_v1.0.md",
    "NON_HUMAN_TENANT_AUTHORITY_CONTRACT_v1.0.md",
    "S2_5_KNOWN_EXCEPTION_RECONCILIATION.md",
    "S2_5_RESIDUAL_TENANCY_RISK_REGISTER_v1.0.md",
    "ORGANIZATION_TENANT_ISOLATION_BASELINE_v1.0.md",
    "S2_5_BASELINE_MANIFEST.md",
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
def _reset_identity_ephemeral() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def tenant_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> sessionmaker:
    engine = create_engine(f"sqlite:///{tmp_path / 's2_5_tenant.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    for mod in (identity_mod, cockpit_mod, operator_mod, mdg_mod, crm_mod):
        monkeypatch.setattr(mod, "SessionLocal", session_factory)
    import revenue_os.services.tenant_resolution as tr

    monkeypatch.setattr(tr, "SessionLocal", session_factory)
    import revenue_os.services.cockpit_read_model as crm_read

    monkeypatch.setattr(crm_read, "SessionLocal", session_factory)
    import revenue_os.services.operator_flow_read_model as ofrm

    monkeypatch.setattr(ofrm, "SessionLocal", session_factory)
    import revenue_os.services.tenant_bootstrap as tb

    monkeypatch.setattr(tb, "SessionLocal", session_factory)
    return session_factory


def _seed_attack_matrix(db_factory: sessionmaker) -> dict[str, str]:
    db = db_factory()
    try:
        org_a = Organization(
            id=_ORG_A_ID, name="Org A", slug="org-a", status=OrganizationStatus.ACTIVE
        )
        org_b = Organization(
            id=_ORG_B_ID, name="Org B", slug="org-b", status=OrganizationStatus.ACTIVE
        )
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
                    organization_id=org_a.id,
                    role="owner",
                    status=MembershipStatus.ACTIVE,
                ),
                OrganizationMembership(
                    user_id=viewer_a.id,
                    organization_id=org_a.id,
                    role="viewer",
                    status=MembershipStatus.ACTIVE,
                ),
                OrganizationMembership(
                    user_id=owner_b.id,
                    organization_id=org_b.id,
                    role="owner",
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
        for demand_id, org_id in ((_DEMAND_A_ID, _ORG_A_ID), (_DEMAND_B_ID, _ORG_B_ID)):
            db.add(
                AgentActionLog(
                    actor="mc04",
                    action_type=QD_HANDOFF,
                    target_id=demand_id,
                    organization_id=org_id,
                    detail={"payload": {"person": {"email": f"{demand_id[:4]}@x.com"}}},
                )
            )
        db.add(
            AgentActionLog(
                actor="mc06",
                action_type=CO_HANDOFF,
                target_id=_OUTCOME_A_ID,
                organization_id=_ORG_A_ID,
                detail={"payload": {"deal_id": str(_DEAL_A_ID)}},
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
        return {"org_a": str(_ORG_A_ID), "org_b": str(_ORG_B_ID)}
    finally:
        db.close()


def _login(
    client: TestClient,
    *,
    email: str,
    password: str,
    org_id: str | None = None,
) -> None:
    r = client.post("/api/v1/identity/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    if org_id is not None:
        client.cookies.set(ORGANIZATION_COOKIE, org_id)


# ── Baseline artifact integrity ─────────────────────────────────────────────


def test_freeze_s2_5_required_artifacts_exist() -> None:
    for name in S2_5_REQUIRED_ARTIFACTS:
        assert (DOCS_S2_5 / name).is_file(), f"missing {name}"


def test_freeze_s2_artifacts_preserved() -> None:
    assert (DOCS_S2 / "S2_DATA_CLASSIFICATION.md").is_file()
    assert (DOCS_S2 / "S2_ID_ONLY_MUTATION_RISK_REGISTER.md").is_file()


# ── Organization + membership ───────────────────────────────────────────────


def test_freeze_organization_model_fields() -> None:
    cols = {c.name for c in Organization.__table__.columns}
    assert {"id", "name", "slug", "status", "created_at", "updated_at"} <= cols


def test_freeze_membership_model_fields() -> None:
    cols = {c.name for c in OrganizationMembership.__table__.columns}
    assert {"user_id", "organization_id", "role", "status"} <= cols


def test_freeze_founder_bootstrap_creates_owner_membership(
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
        m = (
            db.query(OrganizationMembership)
            .filter(OrganizationMembership.user_id == user.id)
            .one()
        )
        assert m.role == "owner"
        assert m.status == MembershipStatus.ACTIVE
    finally:
        db.close()


def test_freeze_role_vocabulary_unchanged() -> None:
    assert MVP_ROLES == ("owner", "admin", "member", "viewer")


def test_freeze_viewer_cannot_mutate(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="viewer-a@example.com", password="pass-v", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/contact-status",
        json={"contact_id": str(_CONTACT_A_ID), "status": "prospect"},
    )
    assert r.status_code == 403
    assert membership_role_allows_mutation("viewer") is False


# ── Tenant-owned entity reconciliation (4 identified, 3 scoped) ─────────────


def test_freeze_fourth_tenant_owned_entity_is_organization() -> None:
    manifest = (DOCS_S2_5 / "TENANT_OWNED_ENTITY_MANIFEST_v1.0.md").read_text(encoding="utf-8")
    assert "Organization" in manifest
    assert "Contact" in manifest
    assert "Deal" in manifest
    assert "AgentActionLog" in manifest
    assert "4" in manifest or "four" in manifest.lower()


def test_freeze_three_scoped_data_entities_have_organization_id() -> None:
    for model in (Contact, Deal, AgentActionLog):
        assert "organization_id" in {c.name for c in model.__table__.columns}


def test_freeze_organization_is_tenant_boundary_not_data_scoped_entity() -> None:
    """Organization is the 4th tenant-owned entity; it IS the tenant, not org_id-scoped data."""
    assert Organization.__tablename__ == "organizations"
    assert "organization_id" not in {c.name for c in Organization.__table__.columns}


# ── ID-only risk reconciliation (9 identified, 8/8 critical mitigated) ─────


def test_freeze_ninth_risk_classified_deferred_to_s3() -> None:
    reg = (DOCS_S2_5 / "S2_5_ID_ONLY_MUTATION_RISK_REGISTER_v1.0.md").read_text(encoding="utf-8")
    assert "9" in reg
    assert "DEFERRED_TO_S3" in reg or "OUT_OF_SCOPE" in reg
    assert "crm" in reg.lower()


def test_freeze_eight_critical_risks_have_guards() -> None:
    from revenue_os.services import tenant_mutation_guard as tmg

    src = inspect.getsource(tmg)
    for fn in (
        "scoped_contact",
        "scoped_deal",
        "scoped_demand_handoff",
        "scoped_outcome_handoff",
        "after_demand_register",
    ):
        assert fn in src


# ── Cross-tenant attack matrix ──────────────────────────────────────────────


def test_freeze_cross_tenant_contact_read_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    snap = client.get("/api/v1/operator/snapshot").json()
    emails = {c["email"] for c in snap["contacts"]}
    assert "a@example.com" in emails
    assert "b@example.com" not in emails


def test_freeze_cross_tenant_contact_mutation_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/cockpit/actions/contact-status",
        json={"contact_id": str(_CONTACT_B_ID), "status": "prospect"},
    )
    assert r.status_code == 404


def test_freeze_cross_tenant_deal_read_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    snap = client.get("/api/v1/operator/snapshot").json()
    deal_ids = {d["id"] for d in snap["deals"]}
    assert str(_DEAL_A_ID) in deal_ids
    assert str(_DEAL_B_ID) not in deal_ids


def test_freeze_cross_tenant_deal_mutation_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/deal/stage",
        json={"deal_id": str(_DEAL_B_ID), "stage": "qualified"},
    )
    assert r.status_code == 404


def test_freeze_cross_tenant_qd_action_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/qualified-demand/reject",
        json={"demand_id": _DEMAND_B_ID, "reason": "cross tenant"},
    )
    assert r.status_code == 404


def test_freeze_cross_tenant_co_action_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/commercial-outcome/accept",
        json={"outcome_id": _OUTCOME_B_ID, "notes": "accept"},
    )
    assert r.status_code == 404


def test_freeze_cross_tenant_audit_visibility_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    snap = client.get("/api/v1/cockpit/snapshot").json()
    pending = snap["panels"]["attention"]["data"]["items"]
    demand_ids = {
        item.get("meta", {}).get("demand_id")
        for item in pending
        if item.get("kind") == "qualified_demand"
    }
    assert _DEMAND_A_ID in demand_ids or any(_DEMAND_A_ID[:8] in (item.get("label") or "") for item in pending)
    assert _DEMAND_B_ID not in demand_ids


def test_freeze_spoof_org_via_select_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o")
    r = client.post("/api/v1/tenant/select", json={"organization_id": ids["org_b"]})
    assert r.status_code == 403


def test_freeze_spoof_org_via_cookie_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_b"])
    assert client.get("/api/v1/tenant/me").status_code == 403


def test_freeze_spoof_org_in_mutation_body_ignored(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    r = client.post(
        "/api/v1/operator/actions/contact-status",
        json={
            "contact_id": str(_CONTACT_B_ID),
            "status": "prospect",
            "organization_id": ids["org_b"],
            "tenant_id": ids["org_b"],
        },
    )
    assert r.status_code == 404


# ── Surface isolation ───────────────────────────────────────────────────────


def test_freeze_cockpit_isolation(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    sales = client.get("/api/v1/cockpit/snapshot").json()["panels"]["sales"]["data"]
    assert sales["contact_total"] == 1


def test_freeze_operator_isolation(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-b@example.com", password="pass-b", org_id=ids["org_b"])
    assert len(client.get("/api/v1/operator/snapshot").json()["contacts"]) == 1


def test_freeze_manual_demand_isolation(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    ids = _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o", org_id=ids["org_a"])
    demand_id = str(uuid.uuid4())
    assert client.post(
        "/api/v1/mdg/manual-demand/register",
        json={"email": "mdg@example.com", "source": "manual", "demand_id": demand_id},
    ).status_code == 200
    db = tenant_db()
    try:
        row = (
            db.query(AgentActionLog)
            .filter(AgentActionLog.target_id == demand_id)
            .one()
        )
        assert str(row.organization_id) == ids["org_a"]
    finally:
        db.close()


# ── Non-human identity boundaries ───────────────────────────────────────────


def test_freeze_service_identity_no_human_mutation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RUNNER_API_KEY", "s25-service-key")
    monkeypatch.delenv("FOUNDER_OS_OPERATOR_NAME", raising=False)
    r = client.post(
        "/api/v1/mdg/manual-demand/register",
        json={"email": "svc@example.com", "source": "manual"},
        headers={"Authorization": "Bearer s25-service-key"},
    )
    assert r.status_code == 503
    with pytest.raises(PermissionError):
        bind_requested_by(service_identity())


def test_freeze_agent_identity_no_human_authority() -> None:
    with pytest.raises(HumanAuthorityError):
        require_human_mutation_authority("agent:hermes")


def test_freeze_ai_identity_no_human_authority() -> None:
    with pytest.raises(HumanAuthorityError):
        require_human_mutation_authority("ai:copilot")


def test_freeze_requested_by_spoofing_blocked(
    client: TestClient, tenant_db: sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOUNDER_OS_OPERATOR_NAME", _OPERATOR)
    _seed_attack_matrix(tenant_db)
    _login(client, email="owner-a@example.com", password="pass-o")
    src = inspect.getsource(mdg_mod)
    assert "requested_by" not in mdg_mod.ManualDemandRegisterBody.model_fields


def test_freeze_identity_context_has_no_tenant_fields() -> None:
    names = {f.name for f in dc_fields(IdentityContext)}
    assert "organization_id" not in names
    assert "tenant_id" not in names


def test_freeze_tenant_context_is_separate_layer() -> None:
    names = {f.name for f in dc_fields(TenantContext)}
    assert "organization_id" in names
    assert "membership_role" in names


# ── Residual risks documented ───────────────────────────────────────────────


def test_freeze_crm_api_residual_documented() -> None:
    """S2.5 v1.0 documented CRM as DEFERRED_TO_S3; S3 supersedes with tenant guards."""
    reg = (DOCS_S2_5 / "S2_5_RESIDUAL_TENANCY_RISK_REGISTER_v1.0.md").read_text(encoding="utf-8")
    assert "crm" in reg.lower()
    assert "CRITICAL" in reg or "HIGH" in reg
    s3_reg = (ROOT / "docs" / "saas" / "s3" / "S3_RESIDUAL_TENANCY_RISK_REGISTER.md").read_text(
        encoding="utf-8"
    )
    assert "MITIGATED" in s3_reg
    crm_src = inspect.getsource(crm_mod)
    assert "optional_tenant_mutation" in crm_src
    assert "scoped_contact" in crm_src


def test_freeze_connector_credential_residual_documented() -> None:
    reg = (DOCS_S2_5 / "S2_5_RESIDUAL_TENANCY_RISK_REGISTER_v1.0.md").read_text(encoding="utf-8")
    assert "connector" in reg.lower() or "credential" in reg.lower()


# ── Known exception reconciliation ──────────────────────────────────────────


def test_freeze_known_exception_reconciliation_doc() -> None:
    doc = (DOCS_S2_5 / "S2_5_KNOWN_EXCEPTION_RECONCILIATION.md").read_text(encoding="utf-8")
    assert "CHANGED" in doc
    assert "RECONCILED" in doc or "superseded" in doc.lower()


def test_freeze_historical_failure_identities_preserved() -> None:
    recon = (DOCS_S2_5 / "S2_5_KNOWN_EXCEPTION_RECONCILIATION.md").read_text(encoding="utf-8")
    for test_id in HISTORICAL_FAILED_TESTS:
        assert test_id.split("::")[-1] in recon or test_id in recon
    for test_id in HISTORICAL_ERROR_TESTS:
        assert test_id.split("::")[-1] in recon or test_id in recon


def test_freeze_s1_5_tenant_absence_tests_superseded_not_deleted() -> None:
    s15 = (ROOT / "tests" / "test_saas_s1_5_identity_foundation_baseline_freeze.py").read_text(
        encoding="utf-8"
    )
    assert "test_freeze_s1_5_tenant_boundary_superseded_by_s2" in s15
    assert "test_freeze_s2_tenant_owned_columns_bounded" in s15


# ── Database migration attestation (S2.5 adds none) ───────────────────────────


def test_freeze_no_s2_5_schema_migration_required() -> None:
    attestation = (DOCS_S2_5 / "S2_5_BASELINE_MANIFEST.md").read_text(encoding="utf-8")
    assert "Database Migrations: 0" in attestation or "Migrations: 0" in attestation
