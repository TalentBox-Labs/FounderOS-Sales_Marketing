"""Focused tests for Content Studio read-only JSON API."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

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


@pytest.fixture
def studio_tracker(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Deterministic tracker rows for Content Studio API tests."""
    rows = [
        {
            "content_id": "W99",
            "title": "Studio Test Week",
            "status": "QA Passed",
            "qa_status": "PASS",
            "current_step": "Publish Review",
            "next_step": "None",
            "draft_path": "input/W99/04_Draft.md",
            "qa_output_path": "output/qa_reports/W99_Publish_Checklist_Check.md",
            "final_output_path": "input/W99/05_Final.md",
            "artifact_folder": "",
        },
        {
            "content_id": "W98",
            "title": "Second Week",
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
    monkeypatch.setattr(
        "runner_api_routers.content_studio._read_tracker",
        lambda: rows,
    )
    monkeypatch.setattr(
        "runner_api_routers.content_studio._week_artifacts",
        lambda week_id: {
            "brief": False,
            "seo": True,
            "research": True,
            "draft": True,
            "final": week_id == "W99",
            "design": False,
            "social": False,
            "email": False,
            "checklist": week_id == "W99",
        },
    )
    return rows


class TestContentStudioList:
    """GET /api/v1/content-studio/content"""

    def test_list_success(
        self, cms_client: TestClient, studio_tracker: list[dict[str, str]]
    ) -> None:
        r = cms_client.get("/api/v1/content-studio/content")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["count"] == 2
        assert len(body["items"]) == 2
        assert body["items"][0]["content_id"] == "W99"
        assert body["items"][0]["title"] == "Studio Test Week"
        assert "artifacts" in body["items"][0]
        assert body["items"][0]["artifacts"]["draft"] is True

    def test_list_response_contract(
        self, cms_client: TestClient, studio_tracker: list[dict[str, str]]
    ) -> None:
        r = cms_client.get("/api/v1/content-studio/content")
        body = r.json()
        assert set(body.keys()) == {"ok", "count", "items"}
        item = body["items"][0]
        expected_fields = {
            "content_id",
            "title",
            "status",
            "qa_status",
            "current_step",
            "next_step",
            "draft_path",
            "qa_output_path",
            "final_output_path",
            "artifact_folder",
            "artifacts",
        }
        assert set(item.keys()) == expected_fields
        assert isinstance(item["artifacts"], dict)


class TestContentStudioDetail:
    """GET /api/v1/content-studio/content/{content_id}"""

    def test_detail_success(
        self, cms_client: TestClient, studio_tracker: list[dict[str, str]]
    ) -> None:
        r = cms_client.get("/api/v1/content-studio/content/W99")
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert set(body.keys()) == {"ok", "item"}
        assert body["item"]["content_id"] == "W99"
        assert body["item"]["status"] == "QA Passed"
        assert body["item"]["artifacts"]["final"] is True

    def test_detail_missing_content(
        self, cms_client: TestClient, studio_tracker: list[dict[str, str]]
    ) -> None:
        r = cms_client.get("/api/v1/content-studio/content/W97")
        assert r.status_code == 404
        assert r.json()["detail"] == "Content not found"

    def test_detail_malformed_content_id(self, cms_client: TestClient) -> None:
        # Leading dot is rejected by _validate_week_id (path-safety).
        r = cms_client.get("/api/v1/content-studio/content/.hidden")
        assert r.status_code == 400
        assert "Invalid week ID format" in r.json()["detail"]

    def test_detail_unsupported_path_chars(self, cms_client: TestClient) -> None:
        r = cms_client.get("/api/v1/content-studio/content/W01;rm")
        assert r.status_code == 400
        assert "Invalid week ID format" in r.json()["detail"]


class TestContentStudioReadOnly:
    """Prove list/detail do not mutate Founder SoT or invoke side effects."""

    def test_no_mutation_of_tracker_or_input(
        self, cms_client: TestClient, studio_tracker: list[dict[str, str]]
    ) -> None:
        root = Path(__file__).resolve().parent.parent
        tracker = root / "tracker.csv"
        input_dir = root / "input"
        assert tracker.is_file()
        before_tracker = _sha256_file(tracker)
        before_input = _sha256_tree(input_dir)

        assert cms_client.get("/api/v1/content-studio/content").status_code == 200
        assert cms_client.get("/api/v1/content-studio/content/W99").status_code == 200
        assert cms_client.get("/api/v1/content-studio/content/MISSING").status_code == 404

        assert _sha256_file(tracker) == before_tracker
        assert _sha256_tree(input_dir) == before_input

    def test_no_publish_or_external_side_effects(
        self,
        cms_client: TestClient,
        studio_tracker: list[dict[str, str]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[Any] = []

        def _forbid(*args: Any, **kwargs: Any) -> None:
            calls.append((args, kwargs))
            raise AssertionError("side-effect helper must not be called")

        monkeypatch.setattr("runner_api_routers.utils._run", _forbid)
        monkeypatch.setattr("runner_api_routers.utils._apply_week_if_set", _forbid)

        assert cms_client.get("/api/v1/content-studio/content").status_code == 200
        assert cms_client.get("/api/v1/content-studio/content/W99").status_code == 200
        assert calls == []
