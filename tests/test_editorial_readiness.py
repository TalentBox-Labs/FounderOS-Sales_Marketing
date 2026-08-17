"""Focused tests for Editorial Readiness read model (Sprint E6B)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_tree(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    if not root.is_dir():
        return digests
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digests[str(path.relative_to(root))] = _sha256_file(path)
    return digests


def _write_report(qa_dir: Path, content_id: str, suffix: str, verdict: str) -> Path:
    path = qa_dir / f"{content_id}_{suffix}"
    path.write_text(
        f"# {content_id} {suffix}\n\n## Final Verdict\n\n{verdict}\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def readiness_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> dict[str, Any]:
    """Isolated tracker + artifacts + QA reports under tmp_path."""
    qa_dir = tmp_path / "output" / "qa_reports"
    qa_dir.mkdir(parents=True)
    input_root = tmp_path / "input"
    (input_root / "W99").mkdir(parents=True)
    (input_root / "W98").mkdir(parents=True)
    (input_root / "W97").mkdir(parents=True)

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
            "final_output_path": "input/W99/05_Final.md",
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
        {
            "content_id": "W97",
            "title": "Fail Week",
            "status": "QA Passed",
            "qa_status": "FAIL",
            "current_step": "QA",
            "next_step": "Editor",
            "draft_path": "input/W97/04_Draft.md",
            "qa_output_path": "",
            "final_output_path": "input/W97/05_Final.md",
            "artifact_folder": "",
        },
    ]

    def _artifacts(week_id: str) -> dict[str, bool]:
        return {
            "brief": False,
            "seo": week_id == "W99",
            "research": week_id == "W99",
            "draft": week_id in {"W99", "W98", "W97"},
            "final": week_id in {"W99", "W97"},
            "design": False,
            "social": False,
            "email": False,
            "checklist": week_id == "W99",
        }

    # W99: all default reports PASS
    for _, suffix in (
        ("research_mapper", "Research_Map.md"),
        ("draft_validator", "Draft_Validation.md"),
        ("structure_checker", "Structure_Check.md"),
        ("metadata_checker", "Metadata_Check.md"),
        ("publish_checklist_checker", "Publish_Checklist_Check.md"),
    ):
        _write_report(qa_dir, "W99", suffix, "PASS")

    # W97: structure FAIL; others PASS
    for suffix, verdict in (
        ("Research_Map.md", "PASS"),
        ("Draft_Validation.md", "PASS"),
        ("Structure_Check.md", "FAIL"),
        ("Metadata_Check.md", "PASS"),
        ("Publish_Checklist_Check.md", "PASS"),
    ):
        _write_report(qa_dir, "W97", suffix, verdict)

    # Malformed report for optional path coverage via dedicated content id patch in test

    monkeypatch.setattr(
        "runner_api_routers.content_studio._read_tracker",
        lambda: rows,
    )
    monkeypatch.setattr(
        "runner_api_routers.content_studio._week_artifacts",
        _artifacts,
    )
    monkeypatch.setattr(
        "runner_api_routers.editorial.PROJECT_ROOT",
        tmp_path,
    )

    # Mutation sentinels
    tracker = tmp_path / "tracker.csv"
    tracker.write_text("content_id\nW99\n", encoding="utf-8")
    (input_root / "W99" / "04_Draft.md").write_text("# draft\n", encoding="utf-8")

    return {"rows": rows, "qa_dir": qa_dir, "tmp_path": tmp_path, "tracker": tracker}


class TestEditorialReadiness:
    def test_readiness_success(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["content_id"] == "W99"
        assert body["content_studio_path"] == "/content-studio/W99"
        assert body["readiness"]["draft_available"] is True
        assert body["readiness"]["editor_review_available"] is True
        assert body["readiness"]["validation_passed"] is True
        assert body["readiness"]["readiness_summary"] == "all_default_reports_pass"

    def test_content_missing(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W00")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_draft_only(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W98")
        assert r.status_code == 200
        body = r.json()
        assert body["readiness"]["draft_available"] is True
        assert body["readiness"]["editor_review_available"] is False
        assert body["readiness"]["final_artifact_available"] is False
        assert body["readiness"]["validation_passed"] is None
        assert body["readiness"]["readiness_summary"] == "incomplete_evidence"
        assert body["reports"]["draft_validator"]["verdict"] == "missing"

    def test_editor_output_present(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        body = r.json()
        assert body["artifacts"]["final"] is True
        assert body["readiness"]["editor_review_available"] is True

    def test_qa_output_present(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        body = r.json()
        assert body["readiness"]["qa_available"] is True
        assert body["reports"]["draft_validator"]["available"] is True
        assert body["reports"]["draft_validator"]["verdict"] == "PASS"

    def test_validation_pass(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        body = r.json()
        assert body["readiness"]["validation_passed"] is True
        assert body["readiness"]["metadata_valid"] is True
        assert body["readiness"]["structure_valid"] is True

    def test_validation_fail(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W97")
        body = r.json()
        assert body["readiness"]["validation_passed"] is False
        assert body["readiness"]["structure_valid"] is False
        assert body["reports"]["structure_checker"]["verdict"] == "FAIL"
        assert body["readiness"]["readiness_summary"] == "has_failures"

    def test_missing_optional_evidence(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        body = r.json()
        assert body["reports"]["crewai_qa"]["available"] is False
        assert body["reports"]["crewai_qa"]["verdict"] == "missing"
        assert body["reports"]["content_quality_checker"]["verdict"] == "missing"

    def test_malformed_evidence_explicit(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        qa_dir: Path = readiness_env["qa_dir"]
        bad = qa_dir / "W99_Draft_Validation.md"
        bad.write_text("# broken\n\n## Final Verdict\n\nMAYBE\n", encoding="utf-8")
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        assert r.status_code == 200
        body = r.json()
        assert body["reports"]["draft_validator"]["verdict"] == "malformed"
        assert body["readiness"]["validation_passed"] is None
        assert body["readiness"]["readiness_summary"] == "incomplete_evidence"

    def test_no_mutation(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        tmp: Path = readiness_env["tmp_path"]
        tracker: Path = readiness_env["tracker"]
        before_tracker = _sha256_file(tracker)
        before_input = _sha256_tree(tmp / "input")
        before_qa = _sha256_tree(tmp / "output" / "qa_reports")
        assert cms_client.get("/api/v1/editorial/readiness/W99").status_code == 200
        assert _sha256_file(tracker) == before_tracker
        assert _sha256_tree(tmp / "input") == before_input
        assert _sha256_tree(tmp / "output" / "qa_reports") == before_qa

    def test_content_studio_unchanged(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        list_r = cms_client.get("/api/v1/content-studio/content")
        detail_r = cms_client.get("/api/v1/content-studio/content/W99")
        assert list_r.status_code == 200
        assert detail_r.status_code == 200
        assert set(list_r.json().keys()) == {"ok", "count", "items"}
        assert set(detail_r.json().keys()) == {"ok", "item"}
        # No readiness fields leaked into CS contract
        assert "readiness" not in detail_r.json()["item"]

    def test_no_publishing_side_effect(
        self, cms_client: TestClient, readiness_env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[str] = []

        def _boom(*_a: Any, **_k: Any) -> MagicMock:
            calls.append("run")
            raise AssertionError("subprocess should not run")

        monkeypatch.setattr("runner_api_routers.pipeline._run", _boom)
        monkeypatch.setattr("runner_api_routers.utils._run", _boom)
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        assert r.status_code == 200
        assert calls == []
        assert "publish" not in r.json()["readiness"]["readiness_summary"]

    def test_no_crew_execution(
        self, cms_client: TestClient, readiness_env: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _deny(*_a: Any, **_k: Any) -> None:
            raise AssertionError("Crew must not execute")

        monkeypatch.setattr("src.editor_crew.EditorCrew.run", _deny, raising=False)
        monkeypatch.setattr("src.qa_crew.QACrew.run", _deny, raising=False)
        monkeypatch.setattr("src.generation_crew.GenerationCrew.run", _deny, raising=False)
        r = cms_client.get("/api/v1/editorial/readiness/W99")
        assert r.status_code == 200

    def test_malformed_content_id(
        self, cms_client: TestClient, readiness_env: dict[str, Any]
    ) -> None:
        r = cms_client.get("/api/v1/editorial/readiness/.hidden")
        assert r.status_code == 400
