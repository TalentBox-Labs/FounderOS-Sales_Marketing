"""MC06.5 — CommercialOutcome Baseline v1.0 freeze suite."""

from __future__ import annotations

import ast
import inspect

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.commercial_outcome as co_router
import tests.test_mc06_commercial_outcome as mc06
from revenue_os.models.deal import DealStage
from revenue_os.services import commercial_outcome_service as co_svc
from revenue_os.services.commercial_outcome_service import (
    ACTION_ACCEPTED,
    ACTION_HANDOFF,
    ACTION_REJECTED,
    ELIGIBLE_OUTCOME,
    TARGET_TYPE,
    accept_commercial_outcome,
    register_commercial_outcome_handoff,
    reject_commercial_outcome,
)
from revenue_os.services.deal_automation_service import apply_deal_stage_update
from revenue_os.services.mutation_authority import HumanAuthorityError
from runner_api import app

FROZEN_ACTION_TYPES = frozenset(
    {
        "commercial_outcome_handoff",
        "commercial_outcome_accepted",
        "commercial_outcome_rejected",
    }
)

FROZEN_ROUTES = frozenset(
    {
        "/api/v1/sales/commercial-outcome/handoff",
        "/api/v1/revenue/intake/commercial-outcome/accept",
        "/api/v1/revenue/intake/commercial-outcome/reject",
    }
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _service_source() -> str:
    return inspect.getsource(co_svc)


def _no_deal_field_assignment(source: str) -> None:
    tree = ast.parse(source)
    assigned: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "deal"
                    and target.attr in {"stage", "value", "closed_at", "probability", "currency"}
                ):
                    assigned.append(target.attr)
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Attribute):
            if (
                isinstance(node.target.value, ast.Name)
                and node.target.value.id == "deal"
            ):
                assigned.append(node.target.attr)
    assert assigned == []


def test_freeze_eligible_closed_won_handoff() -> None:
    db = mc06._FakeDB(mc06._FakeDeal(DealStage.CLOSED_WON))
    result = register_commercial_outcome_handoff(
        db, mc06._payload(), "Krishna Sales"
    )
    assert result["handoff_registered"] is True
    assert result["deal_mutated"] is False


def test_freeze_ineligible_deal_rejected() -> None:
    db = mc06._FakeDB(mc06._FakeDeal(DealStage.NEGOTIATION))
    with pytest.raises(ValueError, match="closed_won"):
        register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")


def test_freeze_human_sales_handoff_authority() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    result = register_commercial_outcome_handoff(
        db, mc06._payload(), "Krishna Founder"
    )
    assert result["requested_by"] == "Krishna Founder"


def test_freeze_human_revenue_accept() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    result = accept_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue")
    assert result["accepted"] is True
    assert result["commercial_outcome_emitted"] is True


def test_freeze_human_revenue_reject() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    result = reject_commercial_outcome(
        db, mc06._OUTCOME_ID, "Krishna Revenue", "not final"
    )
    assert result["rejected"] is True


def test_freeze_agent_mutation_blocked() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    with pytest.raises(HumanAuthorityError):
        register_commercial_outcome_handoff(db, mc06._payload(), "agent")


def test_freeze_ai_mutation_blocked() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    with pytest.raises(HumanAuthorityError):
        accept_commercial_outcome(db, mc06._OUTCOME_ID, "ai:copilot")


def test_freeze_spoofed_human_blocked(client: TestClient) -> None:
    r = client.post(
        "/api/v1/sales/commercial-outcome/handoff",
        json={
            "outcome_id": mc06._OUTCOME_ID,
            "deal_id": mc06._DEAL_ID,
            "outcome": "closed_won",
            "occurred_at": "2026-08-13T00:00:00Z",
            "requested_by": "system",
        },
    )
    assert r.status_code == 403


def test_freeze_duplicate_safety() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    other = mc06._payload(outcome_id="cccccccc-cccc-cccc-cccc-cccccccccccc")
    with pytest.raises(ValueError, match="already registered"):
        register_commercial_outcome_handoff(db, other, "Krishna Sales")


def test_freeze_idempotent_retry() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    first = accept_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue")
    second = accept_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue")
    assert first["idempotent"] is False
    assert second["idempotent"] is True
    assert len([log for log in db.logs if log.action_type == ACTION_ACCEPTED]) == 1


def test_freeze_provenance() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    result = accept_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue")
    provenance = result["provenance"]
    assert provenance["deal_id"] == mc06._DEAL_ID
    assert provenance["source_stage"] == "closed_won"
    assert provenance["value_authoritative"] is False


def test_freeze_acceptance_audit() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    accept_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue")
    accepted = [log for log in db.logs if log.action_type == ACTION_ACCEPTED]
    assert len(accepted) == 1
    assert accepted[0].target_type == TARGET_TYPE
    assert accepted[0].target_id == mc06._OUTCOME_ID


def test_freeze_rejection_audit() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    reject_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue", "hold")
    rejected = [log for log in db.logs if log.action_type == ACTION_REJECTED]
    assert len(rejected) == 1
    assert rejected[0].detail["reason"] == "hold"


def test_freeze_sales_state_unchanged() -> None:
    deal = mc06._FakeDeal(DealStage.CLOSED_WON)
    stage, value, closed_at = deal.stage, deal.value, deal.closed_at
    db = mc06._FakeDB(deal)
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    accept_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue")
    assert deal.stage is stage
    assert deal.value == value
    assert deal.closed_at is closed_at


def test_freeze_revenue_boundary_protected() -> None:
    db = mc06._FakeDB(mc06._FakeDeal())
    register_commercial_outcome_handoff(db, mc06._payload(), "Krishna Sales")
    result = accept_commercial_outcome(db, mc06._OUTCOME_ID, "Krishna Revenue")
    assert result["recognized_revenue"] is False
    assert result["billing_created"] is False
    assert result["client_created"] is False
    assert result["project_created"] is False


def test_freeze_no_shared_sot() -> None:
    src = _service_source()
    assert "AgentActionLog" in src
    assert "class CommercialOutcome(" not in src
    assert "from revenue_os.models.project" not in src
    assert "from revenue_os.models.contact" not in src
    imports = [
        node.module
        for node in ast.walk(ast.parse(src))
        if isinstance(node, ast.ImportFrom)
    ]
    assert "revenue_os.models.project" not in imports
    assert "revenue_os.models.contact" not in imports


def test_freeze_no_deal_mutation_in_source() -> None:
    _no_deal_field_assignment(_service_source())


def test_freeze_a3_5_emission_false() -> None:
    deal = mc06._FakeDeal(DealStage.NEGOTIATION)
    result = apply_deal_stage_update(
        mc06._FakeDB(deal), deal, DealStage.CLOSED_WON, requested_by="Krishna Sales"
    )
    assert result["commercial_outcome_emitted"] is False
    a3_src = inspect.getsource(apply_deal_stage_update)
    assert a3_src.count("commercial_outcome_emitted") >= 2
    assert '"commercial_outcome_emitted": False' in a3_src
    assert '"commercial_outcome_emitted": True' not in a3_src


def test_freeze_a4_5_and_mc04_5_preserved() -> None:
    mc06.test_a4_5_contact_status_contract_untouched()
    mc06.test_mc04_5_accept_still_does_not_emit_outcome()


def test_freeze_eligibility_closed_won_only() -> None:
    assert ELIGIBLE_OUTCOME == "closed_won"
    assert ACTION_HANDOFF == "commercial_outcome_handoff"
    assert ACTION_ACCEPTED == "commercial_outcome_accepted"
    assert ACTION_REJECTED == "commercial_outcome_rejected"
    assert FROZEN_ACTION_TYPES == {ACTION_HANDOFF, ACTION_ACCEPTED, ACTION_REJECTED}


def test_freeze_router_contract_and_human_gate() -> None:
    routes = {
        r.path
        for r in co_router.router.routes
        if hasattr(r, "methods") and "POST" in r.methods
    }
    assert routes == FROZEN_ROUTES
    src = inspect.getsource(co_router)
    assert "is_human_approver" in src
    assert "require_human_mutation_authority" not in src or "HumanAuthorityError" in src
    assert src.count("_human_gate") >= 3


def test_freeze_service_human_gate_on_all_mutations() -> None:
    src = _service_source()
    assert src.count("require_human_mutation_authority(") == 3
    assert "AgentActionLog" in inspect.getsource(register_commercial_outcome_handoff)
    assert "AgentActionLog" in inspect.getsource(accept_commercial_outcome)
    assert "AgentActionLog" in inspect.getsource(reject_commercial_outcome)
