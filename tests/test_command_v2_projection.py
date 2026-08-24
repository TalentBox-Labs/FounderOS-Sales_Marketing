"""I1 — Command V2 projection-only composition helper (focused contract tests)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from revenue_os.services import command_v2_projection as mod
from revenue_os.services.command_v2_projection import (
    BUCKET_BLOCKED_OR_DEGRADED,
    BUCKET_NEEDS_YOUR_JUDGMENT,
    BUCKET_RECENTLY_CHANGED,
    BUCKET_RUNNING_WITHOUT_YOU,
    NEXT_EXTERNAL_DEPENDENCY,
    NEXT_HUMAN_DECISION_REQUIRED,
    NEXT_NO_NEXT_ACTION,
    compose_command_v2_projection,
)

_ORG_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_ORG_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _snap(**overrides):
    base = {
        "organization_id": _ORG_A,
        "decision_items": [],
        "pending_approvals": [],
        "agent_orchestration": {},
        "recent_activity": [],
        "meeting_interest": [],
        "errors": [],
    }
    base.update(overrides)
    return base


def test_deterministic_composition_same_input_same_output():
    snap = _snap(
        decision_items=[
            {
                "item_id": "di-1",
                "kind": "approval",
                "title": "Approve outreach",
                "authority_state": "requires_founder",
                "occurred_at": "2026-01-02T00:00:00+00:00",
                "provenance": {"subject_id": "ar-1", "action_type": "send_outreach_email"},
            }
        ],
        agent_orchestration={
            "blocked": [
                {
                    "work_id": "w-blocked",
                    "action_type": "worker_research",
                    "contact_id": "c-1",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ]
        },
    )
    a = compose_command_v2_projection(snap, organization_id=_ORG_A)
    b = compose_command_v2_projection(snap, organization_id=_ORG_A)
    assert a == b
    assert a["persistent"] is False
    assert a["source"] == "command_v2_projection"


def test_tenant_boundary_no_cross_org_grouping():
    snap = _snap(
        decision_items=[
            {
                "item_id": "di-a",
                "kind": "approval",
                "title": "A",
                "authority_state": "requires_founder",
                "provenance": {"subject_id": "ar-shared-contact-shape"},
            }
        ]
    )
    proj_a = compose_command_v2_projection(snap, organization_id=_ORG_A)
    # Foreign org stamp on snapshot must fail closed (no join).
    snap_mismatch = dict(snap)
    snap_mismatch["organization_id"] = _ORG_B
    proj_mismatch = compose_command_v2_projection(snap_mismatch, organization_id=_ORG_A)
    assert proj_mismatch["fail_closed_reason"] == "organization_mismatch"
    assert proj_mismatch["cards"] == []
    assert all(c["organization_id"] == _ORG_A for c in proj_a["cards"])
    for group in proj_a["groups"]:
        assert group["organization_id"] == _ORG_A


def test_missing_org_fails_closed():
    proj = compose_command_v2_projection(_snap(), organization_id=None)
    assert proj["fail_closed_reason"] == "missing_organization_id"
    assert proj["cards"] == []
    assert proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT] == []


def test_approval_request_id_grouping():
    snap = _snap(
        decision_items=[
            {
                "item_id": "di-1",
                "kind": "approval",
                "title": "Approve",
                "authority_state": "requires_founder",
                "provenance": {"subject_id": "ar-99"},
            }
        ]
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    card = proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT][0]
    assert card["subject_kind"] == "approval_request"
    assert card["subject_id"] == "ar-99"
    assert card["presentation_subject_key"] == "approval_request:ar-99"
    assert "situation" not in card["presentation_subject_key"].lower()


def test_demand_id_fallback():
    snap = _snap(
        decision_items=[
            {
                "item_id": "di-qd",
                "kind": "qualified_demand",
                "title": "Intake demand",
                "authority_state": "requires_founder",
                "provenance": {"subject_id": "demand-7"},
            }
        ]
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    card = proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT][0]
    assert card["presentation_subject_key"] == "demand:demand-7"


def test_contact_id_fallback():
    snap = _snap(
        agent_orchestration={
            "blocked": [
                {
                    "work_id": "w1",
                    "action_type": "worker_research",
                    "contact_id": "contact-42",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ]
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    card = proj["buckets"][BUCKET_BLOCKED_OR_DEGRADED][0]
    assert card["presentation_subject_key"] == "contact:contact-42"


def test_no_join_key_singleton():
    snap = _snap(
        agent_orchestration={
            "blocked": [
                {
                    "work_id": "orphan-work",
                    "action_type": "worker_research",
                    # no contact_id
                }
            ]
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    card = proj["buckets"][BUCKET_BLOCKED_OR_DEGRADED][0]
    assert card["presentation_subject_key"] is None
    assert any(g.get("singleton") for g in proj["groups"])


def test_no_fabricated_situation_id():
    proj = compose_command_v2_projection(
        _snap(
            pending_approvals=[{"id": "ar-1", "action_type": "send_outreach_email"}],
        ),
        organization_id=_ORG_A,
    )
    blob = str(proj)
    assert "situation_id" not in blob.lower()
    assert proj["persistent"] is False
    for card in proj["cards"]:
        assert "situation_id" not in card


def test_distinct_approval_requests_remain_distinct():
    snap = _snap(
        pending_approvals=[
            {"id": "ar-1", "target_id": "c-same", "action_type": "send_outreach_email"},
            {"id": "ar-2", "target_id": "c-same", "action_type": "send_outreach_email"},
        ]
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    needs = proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT]
    ids = {c["subject_id"] for c in needs}
    assert ids == {"ar-1", "ar-2"}
    assert len(needs) == 2


def test_eligibility_is_not_pending_approval():
    snap = _snap(
        meeting_interest=[
            {
                "contact_id": "c-1",
                "booking_eligible": True,
                "booking_status": "BOOKING_ELIGIBLE",
                "recommended_next_action": "book_meeting",
            }
        ]
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    assert proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT] == []


def test_pending_approval_request_needs_your_judgment():
    snap = _snap(
        pending_approvals=[
            {
                "id": "ar-pending",
                "action_type": "send_outreach_email",
                "action_label": "Send outreach",
                "target_id": "c-9",
            }
        ]
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    needs = proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT]
    assert len(needs) == 1
    assert needs[0]["next_move"] == NEXT_HUMAN_DECISION_REQUIRED
    assert needs[0]["subject_id"] == "ar-pending"


def test_awaiting_human_excluded_from_running_without_you():
    snap = _snap(
        agent_orchestration={
            "awaiting_human": [
                {
                    "work_id": "wait-1",
                    "action_type": "send_outreach_email",
                    "execution_mode": "HUMAN_REQUIRED",
                    "contact_id": "c-1",
                }
            ]
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    assert proj["buckets"][BUCKET_RUNNING_WITHOUT_YOU] == []
    # awaiting_human alone does not invent Needs Your Judgment without ApprovalRequest
    assert proj["buckets"][BUCKET_NEEDS_YOUR_JUDGMENT] == []


def test_blocked_maps_to_blocked_or_degraded():
    snap = _snap(
        agent_orchestration={
            "blocked": [
                {
                    "work_id": "b1",
                    "action_type": "worker_research",
                    "failure_reason": "policy_blocked",
                }
            ]
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    cards = proj["buckets"][BUCKET_BLOCKED_OR_DEGRADED]
    assert len(cards) == 1
    assert cards[0]["visible_state"] == "BLOCKED"


def test_waiting_on_provider_maps_to_blocked_or_degraded():
    snap = _snap(
        agent_orchestration={
            "waiting_on_provider": [
                {
                    "work_id": "p1",
                    "title": "Outlook unavailable",
                    "reason": "connector_down",
                }
            ]
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    cards = proj["buckets"][BUCKET_BLOCKED_OR_DEGRADED]
    assert len(cards) == 1
    assert cards[0]["visible_state"] == "WAITING_ON_PROVIDER"
    assert cards[0]["next_move"] == NEXT_EXTERNAL_DEPENDENCY


def test_recovering_autonomous_running_without_you_and_remains_recovering():
    snap = _snap(
        agent_orchestration={
            "retryable": [
                {
                    "work_id": "r1",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "recovery_class": "RETRYABLE",
                    "contact_id": "c-1",
                }
            ],
            "pause": {"recovery_execution_allowed": True},
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    running = proj["buckets"][BUCKET_RUNNING_WITHOUT_YOU]
    assert len(running) == 1
    assert running[0]["visible_state"] == "RECOVERING"
    assert running[0]["visible_state"] != "ACTIVE"
    assert running[0]["bucket"] == BUCKET_RUNNING_WITHOUT_YOU


def test_active_autonomous_running_without_you():
    snap = _snap(
        agent_orchestration={
            "running": [
                {
                    "work_id": "run-1",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "state": "running",
                    "contact_id": "c-1",
                }
            ],
            # failed-oriented alias must NOT be treated as running
            "active": [
                {
                    "work_id": "failed-alias",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "state": "failed",
                }
            ],
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    running = proj["buckets"][BUCKET_RUNNING_WITHOUT_YOU]
    assert len(running) == 1
    assert running[0]["source_identity"] == "work:run-1"
    assert running[0]["visible_state"] == "RUNNING"
    assert all(c["source_identity"] != "work:failed-alias" for c in running)


def test_missing_optional_snapshot_fields_do_not_crash():
    proj = compose_command_v2_projection({}, organization_id=_ORG_A)
    assert proj["fail_closed_reason"] is None
    assert proj["cards"] == []
    proj2 = compose_command_v2_projection(
        {"organization_id": _ORG_A, "decision_items": None, "agent_orchestration": None},
        organization_id=_ORG_A,
    )
    assert proj2["cards"] == []


def test_recent_completed_activity_mapping():
    snap = _snap(
        recent_activity=[
            {
                "id": "act-1",
                "label": "Outreach prepared",
                "action_type": "send_outreach_email",
                "contact_id": "c-1",
                "created_at": "2026-01-03T00:00:00+00:00",
            }
        ],
        agent_orchestration={
            "succeeded_recently": [
                {
                    "work_id": "s1",
                    "action_type": "worker_research",
                    "created_at": "2026-01-04T00:00:00+00:00",
                }
            ]
        },
        decision_items=[
            {
                "item_id": "di-done",
                "kind": "outcome",
                "title": "Completed decision",
                "authority_state": "completed",
                "occurred_at": "2026-01-05T00:00:00+00:00",
                "provenance": {"subject_id": "c-9"},
            }
        ],
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    recent = proj["buckets"][BUCKET_RECENTLY_CHANGED]
    keys = {c["card_key"] for c in recent}
    assert "activity:act-1" in keys
    assert "work:s1" in keys
    assert "item:di-done" in keys
    assert all(c["next_move"] == NEXT_NO_NEXT_ACTION for c in recent)


def test_unsupported_next_move_omitted():
    snap = _snap(
        agent_orchestration={
            "blocked": [
                {
                    "work_id": "b-unknown",
                    "action_type": "worker_research",
                    # no explicit next-move provenance
                }
            ]
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    card = proj["buckets"][BUCKET_BLOCKED_OR_DEGRADED][0]
    assert card["next_move"] is None


def test_no_new_persistent_sot_and_helper_performs_no_db_writes():
    source = Path(inspect.getfile(mod)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_names = {
        "SessionLocal",
        "sessionmaker",
        "create_engine",
        "ApprovalRequest",
        "AgentActionLog",
    }
    db_write_attrs = {"commit", "flush", "merge", "execute", "rollback"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # session.add / db.delete style only — not set.add
            if node.func.attr in db_write_attrs:
                pytest.fail(f"DB write call found: .{node.func.attr}()")
            if node.func.attr in {"add", "delete"}:
                owner = node.func.value
                owner_name = None
                if isinstance(owner, ast.Name):
                    owner_name = owner.id
                elif isinstance(owner, ast.Attribute):
                    owner_name = owner.attr
                if owner_name in {"db", "session", "Session", "SessionLocal"}:
                    pytest.fail(f"DB mutation call found: {owner_name}.{node.func.attr}()")
        if isinstance(node, ast.Name) and node.id in forbidden_names:
            pytest.fail(f"Forbidden DB/SoT symbol referenced: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr in forbidden_names:
            pytest.fail(f"Forbidden DB/SoT attribute referenced: {node.attr}")

    assert "situation_id" not in source.lower()
    assert "CREATE TABLE" not in source.upper()

    proj = compose_command_v2_projection(_snap(), organization_id=_ORG_A)
    assert proj["persistent"] is False


def test_failed_retryable_not_mapped_as_blocked_when_recovering():
    """FAILED_RECOVERING / retryable must not sit only in blocked because of prior failure."""
    snap = _snap(
        agent_orchestration={
            "failed": [
                {
                    "work_id": "same",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                }
            ],
            "retryable": [
                {
                    "work_id": "same",
                    "action_type": "worker_research",
                    "execution_mode": "AUTONOMOUS",
                    "recovery_class": "RETRYABLE",
                }
            ],
            "pause": {"recovery_execution_allowed": True},
        }
    )
    proj = compose_command_v2_projection(snap, organization_id=_ORG_A)
    blocked_ids = {c["source_identity"] for c in proj["buckets"][BUCKET_BLOCKED_OR_DEGRADED]}
    running_ids = {c["source_identity"] for c in proj["buckets"][BUCKET_RUNNING_WITHOUT_YOU]}
    assert "work:same" in running_ids
    assert "work:same" not in blocked_ids
