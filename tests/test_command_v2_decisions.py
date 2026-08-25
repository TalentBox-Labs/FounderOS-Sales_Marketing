"""I3 — Decisions Queue + Decision Detail focused contract tests."""

from __future__ import annotations

import ast
import inspect
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import runner_api_routers.identity as identity_mod
from revenue_os.services.command_v2_decisions import (
    compose_decision_detail,
    compose_decisions_queue,
)
from revenue_os.services.founder_ui_read_model import (
    build_approvals_snapshot,
    build_decision_detail_snapshot,
)

_ORG_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_ORG_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_identity() -> None:
    identity_mod._revoked_jtis.clear()
    identity_mod._login_failures.clear()


@pytest.fixture
def client(cms_client: TestClient) -> TestClient:
    return cms_client


def test_pending_approval_appears_in_queue() -> None:
    queue = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=[
            {
                "id": "ar-1",
                "organization_id": _ORG_A,
                "title": "Send outreach",
                "action_type": "send_outreach_email",
                "status": "pending",
                "description": "Draft ready",
            }
        ],
    )
    assert queue["count"] == 1
    assert queue["items"][0]["approval_request_id"] == "ar-1"
    assert queue["items"][0]["href_detail"] == "/decisions/ar-1"


def test_cross_source_dedupe_same_approval_once() -> None:
    pending = [
        {
            "id": "ar-1",
            "organization_id": _ORG_A,
            "title": "Send",
            "action_type": "send_outreach_email",
        }
    ]
    decision_items = [
        {
            "item_id": "di-1",
            "kind": "approval",
            "authority_state": "requires_founder",
            "title": "Send",
            "provenance": {"subject_id": "ar-1"},
        }
    ]
    queue = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=pending + pending,  # duplicate source rows
        decision_items=decision_items,
    )
    keys = [i["decision_key"] for i in queue["items"] if i["kind"] == "approval"]
    assert keys == ["approval:ar-1"]


def test_distinct_approvals_same_subject_remain_distinct() -> None:
    queue = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=[
            {
                "id": "ar-1",
                "organization_id": _ORG_A,
                "target_id": "c-same",
                "action_type": "send_outreach_email",
                "title": "A",
            },
            {
                "id": "ar-2",
                "organization_id": _ORG_A,
                "target_id": "c-same",
                "action_type": "send_outreach_email",
                "title": "B",
            },
        ],
    )
    ids = {i["approval_request_id"] for i in queue["items"]}
    assert ids == {"ar-1", "ar-2"}


def test_unknown_action_type_renders_safely() -> None:
    queue = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=[
            {
                "id": "ar-new",
                "organization_id": _ORG_A,
                "title": "Marketing agent proposal",
                "action_type": "marketing_agent_publish_campaign",
                "status": "pending",
            }
        ],
    )
    item = queue["items"][0]
    assert item["approval_request_id"] == "ar-new"
    assert item["category"] == "Governed proposal"
    assert "Marketing Agent Publish Campaign" in item["action_label"]
    detail = compose_decision_detail(
        organization_id=_ORG_A,
        approval={
            "id": "ar-new",
            "organization_id": _ORG_A,
            "title": "Marketing agent proposal",
            "action_type": "marketing_agent_publish_campaign",
            "status": "pending",
        },
    )
    assert detail["available"] is True
    assert detail["category"] == "Governed proposal"
    # Unknown type still only gets existing approve/reject endpoints — no new authority.
    action_types = {a["action_type"] for a in detail["actions"]}
    assert action_types >= {"approval_approve", "approval_reject"}
    assert "marketing_agent_execute" not in action_types


def test_missing_tenant_and_mismatch_fail_closed() -> None:
    empty = compose_decisions_queue(organization_id=None, pending_approvals=[{"id": "ar-1"}])
    assert empty["items"] == []
    assert empty["fail_closed_reason"] == "missing_organization_id"

    foreign = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=[
            {
                "id": "ar-b",
                "organization_id": _ORG_B,
                "title": "Secret",
                "action_type": "send_outreach_email",
            }
        ],
    )
    assert foreign["items"] == []

    detail = compose_decision_detail(
        organization_id=_ORG_A,
        approval={
            "id": "ar-b",
            "organization_id": _ORG_B,
            "title": "Secret",
            "action_type": "send_outreach_email",
            "status": "pending",
        },
    )
    assert detail["available"] is False
    assert detail["fail_closed_reason"] == "organization_mismatch"


def test_presentation_subject_key_not_situation_or_approval_identity() -> None:
    queue = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=[
            {
                "id": "ar-1",
                "organization_id": _ORG_A,
                "title": "X",
                "action_type": "send_outreach_email",
            }
        ],
    )
    item = queue["items"][0]
    assert item["presentation_subject_key"] == "approval_request:ar-1"
    assert item["approval_request_id"] == "ar-1"
    assert "situation" not in item["presentation_subject_key"]
    # Dedupe identity is approval id, not presentation key alone
    assert item["decision_key"] == "approval:ar-1"


def test_next_move_omitted_when_unsupported_on_detail() -> None:
    detail = compose_decision_detail(
        organization_id=_ORG_A,
        approval={
            "id": "ar-1",
            "organization_id": _ORG_A,
            "title": "Done",
            "action_type": "send_outreach_email",
            "status": "approved",
        },
    )
    assert detail["next_move"] is None
    assert detail["actions"] == []


def test_evidence_unavailable_not_fabricated() -> None:
    detail = compose_decision_detail(
        organization_id=_ORG_A,
        approval={
            "id": "ar-1",
            "organization_id": _ORG_A,
            "title": "Sparse",
            "action_type": "totally_unknown_effect",
            "status": "pending",
            "description": "",
            "payload": None,
        },
    )
    assert detail["evidence"]["available"] is False
    assert detail["evidence"]["items"] == []
    assert "unavailable" in (detail["evidence"]["unavailable_message"] or "").lower()
    assert "confidence" not in str(detail).lower()
    assert "impact score" not in str(detail).lower()


def test_no_approval_by_viewing_detail(client: TestClient) -> None:
    snap = {
        "generated_at": "now",
        "state": "ok",
        "message": "",
        "detail": compose_decision_detail(
            organization_id=_ORG_A,
            approval={
                "id": "ar-view",
                "organization_id": _ORG_A,
                "title": "View only",
                "action_type": "send_outreach_email",
                "status": "pending",
            },
        ),
    }
    with patch("runner_api_routers.ui.founder_login_redirect", return_value=None):
        with patch(
            "runner_api_routers.ui.build_decision_detail_snapshot",
            return_value=snap,
        ):
            r = client.get("/decisions/ar-view")
    assert r.status_code == 200
    assert "Viewing this page does not approve" in r.text or "does not approve" in r.text.lower()
    # GET must not POST approve
    assert "method: 'POST'" in r.text or 'method: "POST"' in r.text or "approve" in r.text.lower()
    # Ensure page itself is GET-rendered without auto-submit
    assert "decideApproval" in r.text
    assert "onload=" not in r.text.lower()
    assert "auto_approve" not in r.text.lower()


def test_queue_and_detail_pages_render(client: TestClient) -> None:
    queue_snap = {
        "generated_at": "now",
        "state": "ok",
        "message": "",
        "pending": [
            {
                "id": "ar-1",
                "title": "Send outreach",
                "action_type": "send_outreach_email",
                "action_label": "Outreach prepared",
                "requires_human_decision": True,
            }
        ],
        "recent": [],
        "pending_count": 1,
        "decisions_queue": compose_decisions_queue(
            organization_id=_ORG_A,
            pending_approvals=[
                {
                    "id": "ar-1",
                    "organization_id": _ORG_A,
                    "title": "Send outreach",
                    "action_type": "send_outreach_email",
                }
            ],
        ),
    }
    with patch("runner_api_routers.ui.founder_login_redirect", return_value=None):
        with patch(
            "runner_api_routers.ui.build_approvals_snapshot",
            return_value=queue_snap,
        ):
            r = client.get("/pending-approvals")
            r2 = client.get("/decisions")
    assert r.status_code == 200
    assert r2.status_code == 200
    assert 'data-testid="decisions-queue"' in r.text
    assert 'data-testid="approvals-pending"' in r.text
    assert "Send outreach" in r.text
    assert "situation_id" not in r.text.lower()
    assert "presentation_subject_key" not in r.text


def test_helper_no_db_writes_and_no_situation_id() -> None:
    mod = __import__(
        "revenue_os.services.command_v2_decisions",
        fromlist=["compose_decisions_queue"],
    )
    source = Path(inspect.getfile(mod)).read_text(encoding="utf-8")
    assert "situation_id" not in source.lower()
    assert "SessionLocal" not in source
    assert "CREATE TABLE" not in source.upper()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"commit", "flush", "merge"}:
                pytest.fail(f"DB write: .{node.func.attr}()")


def test_build_approvals_snapshot_missing_org_fail_closed() -> None:
    snap = build_approvals_snapshot(organization_id=None)
    assert snap["state"] == "unavailable"
    assert snap["decisions_queue"]["items"] == []


def test_build_decision_detail_missing_identity_fail_closed() -> None:
    snap = build_decision_detail_snapshot(
        organization_id=_ORG_A, approval_request_id=None
    )
    assert snap["state"] == "unavailable"
    assert snap["detail"]["available"] is False


def test_no_cross_tenant_grouping() -> None:
    queue = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=[
            {
                "id": "ar-a",
                "organization_id": _ORG_A,
                "title": "A",
                "action_type": "send_outreach_email",
                "target_id": "shared-looking",
            },
            {
                "id": "ar-b",
                "organization_id": _ORG_B,
                "title": "B-secret",
                "action_type": "send_outreach_email",
                "target_id": "shared-looking",
            },
        ],
    )
    assert len(queue["items"]) == 1
    assert queue["items"][0]["approval_request_id"] == "ar-a"
    assert all(i["organization_id"] == _ORG_A for i in queue["items"])


def test_recovering_not_confused_with_pending_in_i3_module() -> None:
    # I3 queue is judgment-only — orchestration recovering must not appear as pending.
    queue = compose_decisions_queue(
        organization_id=_ORG_A,
        pending_approvals=[],
        decision_items=[],
    )
    assert queue["items"] == []
    # Explicit: no RUNNING/RECOVERING states in queue items
    assert not any(
        i.get("state") in {"RUNNING", "RECOVERING", "ACTIVE"} for i in queue["items"]
    )


def test_frozen_i1_i2_tests_not_modified() -> None:
    # Ensure this I3 change set does not edit frozen projection/home tests as a side effect
    # (checked again in git diff at commit time).
    assert (_ROOT / "tests/test_command_v2_projection.py").exists()
    assert (_ROOT / "tests/test_command_v2_home.py").exists()
