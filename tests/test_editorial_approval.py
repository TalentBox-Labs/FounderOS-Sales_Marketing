"""Focused tests for Editorial Approval Engine (Sprint E7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.tools import editorial_approval as ea
from src.tools.promotion_audit import (
    PHASE2A_PROMOTION_FILENAMES,
    PHASE2B_PROMOTION_FILENAMES,
)


def _write_report(qa_dir: Path, content_id: str, suffix: str, verdict: str) -> None:
    path = qa_dir / f"{content_id}_{suffix}"
    path.write_text(
        f"# {content_id} {suffix}\n\n## Final Verdict\n\n{verdict}\n",
        encoding="utf-8",
    )


def _stage_phase2b(root: Path, week: str) -> Path:
    staging = root / "output" / "generated" / week
    staging.mkdir(parents=True, exist_ok=True)
    for name in PHASE2B_PROMOTION_FILENAMES:
        (staging / name).write_text(f"# staged {name}\n", encoding="utf-8")
    return staging


@pytest.fixture
def approval_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> dict[str, Any]:
    """Isolated tracker, artifacts, QA, staging, and decision store."""
    qa_dir = tmp_path / "output" / "qa_reports"
    qa_dir.mkdir(parents=True)
    input_root = tmp_path / "input"
    (input_root / "W99").mkdir(parents=True)
    (input_root / "W98").mkdir(parents=True)
    (input_root / "W99" / "04_Draft.md").write_text("# draft\n", encoding="utf-8")

    rows = [
        {
            "content_id": "W99",
            "title": "Ready Week",
            "status": "QA Passed",
            "qa_status": "PASS",
            "current_step": "Publish Review",
            "next_step": "None",
            "draft_path": "input/W99/04_Draft.md",
            "qa_output_path": "output/qa_reports/W99_Draft_Validation.md",
            "final_output_path": "",
            "artifact_folder": "",
        },
        {
            "content_id": "W98",
            "title": "Draft Only",
            "status": "draft",
            "qa_status": "",
            "current_step": "Generation",
            "next_step": "QA",
            "draft_path": "input/W98/04_Draft.md",
            "qa_output_path": "",
            "final_output_path": "",
            "artifact_folder": "",
        },
    ]

    def _artifacts(week_id: str) -> dict[str, bool]:
        return {
            "brief": False,
            "seo": week_id == "W99",
            "research": week_id == "W99",
            "draft": week_id in {"W99", "W98"},
            "final": False,
            "design": False,
            "social": False,
            "email": False,
            "checklist": False,
        }

    for _, suffix in (
        ("research_mapper", "Research_Map.md"),
        ("draft_validator", "Draft_Validation.md"),
        ("structure_checker", "Structure_Check.md"),
        ("metadata_checker", "Metadata_Check.md"),
        ("publish_checklist_checker", "Publish_Checklist_Check.md"),
    ):
        _write_report(qa_dir, "W99", suffix, "PASS")

    _stage_phase2b(tmp_path, "W99")

    decisions = tmp_path / "output" / "editorial_decisions"
    decisions.mkdir(parents=True)

    monkeypatch.setattr("runner_api_routers.content_studio._read_tracker", lambda: rows)
    monkeypatch.setattr("runner_api_routers.content_studio._week_artifacts", _artifacts)
    monkeypatch.setattr("runner_api_routers.editorial.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(ea, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ea, "DECISIONS_DIR", decisions)
    monkeypatch.setattr(ea, "HISTORY_JSONL", decisions / "decisions.jsonl")
    monkeypatch.setattr("src.tools.promote_staged.REPO_ROOT", tmp_path)

    promote_mock = MagicMock(return_value=0)
    monkeypatch.setattr(ea, "promote_staged_bundle", promote_mock)

    return {
        "rows": rows,
        "tmp_path": tmp_path,
        "decisions": decisions,
        "promote_mock": promote_mock,
    }


class TestEditorialApprovalAPI:
    def test_pending_queue(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/pending")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["authorizes_publish"] is False
        ids = {i["content_id"] for i in body["items"]}
        assert "W99" in ids
        assert "W98" in ids

    def test_get_item(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/W99")
        assert r.status_code == 200
        body = r.json()
        assert body["content_id"] == "W99"
        assert body["editorial_state"] == ea.STATE_READY
        assert body["phase"] == "2b"
        assert body["staging_available"] is True
        assert body["authorizes_publish"] is False
        assert body["can_approve"] is True

    def test_approve_promotion(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.post(
            "/api/v1/editorial/W99/approve",
            json={"approver": "Krishna Founder", "notes": "Ship phase 2b"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "approve"
        assert body["authorizes_publish"] is False
        assert body["promotion"]["attempted"] is True
        assert body["promotion"]["ok"] is True
        assert body["promotion"]["publishes"] is False
        assert body["editorial_state"] == ea.STATE_APPROVED
        approval_env["promote_mock"].assert_called_once()
        kwargs = approval_env["promote_mock"].call_args.kwargs
        assert kwargs["phase"] == "2b"
        assert kwargs["week_id"] == "W99"
        assert kwargs["approver"] == "Krishna Founder"

        # Audit persisted
        hist = (approval_env["decisions"] / "decisions.jsonl").read_text(encoding="utf-8")
        rec = json.loads(hist.strip().splitlines()[-1])
        assert rec["approver"] == "Krishna Founder"
        assert rec["decision"] == "approve"
        assert rec["phase"] == "2b"
        assert rec["bundle"]
        assert rec["utc_timestamp"]
        assert rec["notes"] == "Ship phase 2b"
        assert rec["authorizes_publish"] is False

    def test_reject(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.post(
            "/api/v1/editorial/W99/reject",
            json={"approver": "Editor One", "notes": "Tone off"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "reject"
        assert body["editorial_state"] == ea.STATE_REJECTED
        approval_env["promote_mock"].assert_not_called()

    def test_request_changes(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.post(
            "/api/v1/editorial/W99/request-changes",
            json={"approver": "Editor One", "notes": "Add examples"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["decision"] == "request_changes"
        assert body["editorial_state"] == ea.STATE_NEEDS_CHANGES
        approval_env["promote_mock"].assert_not_called()

    def test_audit_fields(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        cms_client.post(
            "/api/v1/editorial/W99/reject",
            json={"approver": "Auditor", "notes": "n1", "phase": "2b"},
        )
        r = cms_client.get("/api/v1/editorial/W99")
        audit = r.json()["audit"]
        assert len(audit) == 1
        row = audit[0]
        for key in (
            "approver",
            "utc_timestamp",
            "decision",
            "notes",
            "bundle",
            "phase",
        ):
            assert key in row and row[key] is not None

    def test_permissions_ai_blocked(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.post(
            "/api/v1/editorial/W99/approve",
            json={"approver": "AI", "notes": "auto"},
        )
        assert r.status_code == 403
        approval_env["promote_mock"].assert_not_called()

        r2 = cms_client.post(
            "/api/v1/editorial/W99/reject",
            json={"approver": "crewai", "notes": "x"},
        )
        assert r2.status_code == 403

    def test_permissions_missing_approver(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.post(
            "/api/v1/editorial/W99/approve",
            json={"approver": "", "notes": "x"},
        )
        assert r.status_code == 422

    def test_duplicate_approvals(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        first = cms_client.post(
            "/api/v1/editorial/W99/approve",
            json={"approver": "Human A", "notes": "ok"},
        )
        assert first.status_code == 200
        second = cms_client.post(
            "/api/v1/editorial/W99/approve",
            json={"approver": "Human B", "notes": "again"},
        )
        assert second.status_code == 409
        assert approval_env["promote_mock"].call_count == 1

    def test_invalid_transition_missing_staging(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        # W98 has no staging bundle
        r = cms_client.post(
            "/api/v1/editorial/W98/approve",
            json={"approver": "Human A", "notes": "no stage"},
        )
        assert r.status_code == 400
        assert "staging" in r.json()["detail"].lower()
        approval_env["promote_mock"].assert_not_called()

    def test_invalid_phase(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.post(
            "/api/v1/editorial/W99/approve",
            json={"approver": "Human A", "phase": "9z"},
        )
        assert r.status_code == 400

    def test_readiness_unchanged(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        assert r.status_code == 200
        assert r.json()["readiness"]["readiness_summary"] == "all_default_reports_pass"


class TestEditorialApprovalUI:
    def test_pending_page(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/editorial")
        assert r.status_code == 200
        assert "Pending queue" in r.text
        assert "W99" in r.text

    def test_pending_alias(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/editorial/pending")
        assert r.status_code == 200
        assert 'data-testid="editorial-pending"' in r.text

    def test_detail_page(
        self, cms_client: TestClient, approval_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/editorial/W99")
        assert r.status_code == 200
        assert 'data-testid="editorial-decision"' in r.text
        assert 'data-testid="ea-approve"' in r.text
        assert 'data-testid="editorial-audit"' in r.text


class TestEditorialApprovalUnit:
    def test_derive_states(self) -> None:
        arts = {"draft": True, "final": False}
        assert (
            ea.derive_editorial_state(
                artifacts=arts,
                readiness_summary="incomplete_evidence",
                validation_passed=None,
                last=None,
                phase="2b",
            )
            == ea.STATE_DRAFT
        )
        assert (
            ea.derive_editorial_state(
                artifacts={"draft": True, "final": True},
                readiness_summary="all_default_reports_pass",
                validation_passed=True,
                last=None,
                phase="2b",
            )
            == ea.STATE_READY
        )
        assert (
            ea.derive_editorial_state(
                artifacts=arts,
                readiness_summary="incomplete_evidence",
                validation_passed=None,
                last={
                    "decision": "reject",
                    "phase": "2b",
                    "promotion": {},
                },
                phase="2b",
            )
            == ea.STATE_REJECTED
        )

    def test_is_human_approver(self) -> None:
        assert ea.is_human_approver("Krishna") is True
        assert ea.is_human_approver("AI") is False
        assert ea.is_human_approver("bot") is False
        assert ea.is_human_approver("") is False

    def test_suggest_phase_prefers_staging_2b(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ea, "REPO_ROOT", tmp_path)
        staging = _stage_phase2b(tmp_path, "W50")
        rel = "output/generated/W50"
        assert staging.is_dir()
        assert ea.suggest_phase({"draft": True, "final": False}, rel) == "2b"

    def test_phase2a_files_constant(self) -> None:
        assert "04_Draft.md" in PHASE2A_PROMOTION_FILENAMES
