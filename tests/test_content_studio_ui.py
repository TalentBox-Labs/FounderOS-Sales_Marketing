"""Focused tests for Content Studio read-only UI (Sprint E3)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


SAMPLE_ITEMS = [
    {
        "content_id": "W99",
        "title": "Studio UI Week",
        "status": "QA Passed",
        "qa_status": "PASS",
        "current_step": "Publish Review",
        "next_step": "None",
        "draft_path": "input/W99/04_Draft.md",
        "qa_output_path": "",
        "final_output_path": "input/W99/05_Final.md",
        "artifact_folder": "",
        "artifacts": {
            "brief": False,
            "seo": True,
            "research": True,
            "draft": True,
            "final": True,
            "design": False,
            "social": False,
            "email": False,
            "checklist": False,
        },
    },
    {
        "content_id": "W98",
        "title": "Earlier Week",
        "status": "draft",
        "qa_status": "",
        "current_step": "Generation",
        "next_step": "QA",
        "draft_path": "input/W98/04_Draft.md",
        "qa_output_path": "",
        "final_output_path": "",
        "artifact_folder": "",
        "artifacts": {
            "brief": False,
            "seo": False,
            "research": False,
            "draft": True,
            "final": False,
            "design": False,
            "social": False,
            "email": False,
            "checklist": False,
        },
    },
]


@pytest.fixture
def studio_ui_data(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    monkeypatch.setattr(
        "runner_api_routers.ui.build_content_list",
        lambda: {"ok": True, "count": len(SAMPLE_ITEMS), "items": SAMPLE_ITEMS},
    )

    def _detail(content_id: str) -> dict[str, Any]:
        from fastapi import HTTPException

        for item in SAMPLE_ITEMS:
            if item["content_id"] == content_id:
                return {"ok": True, "item": item}
        raise HTTPException(status_code=404, detail="Content not found")

    monkeypatch.setattr("runner_api_routers.ui.build_content_detail", _detail)
    monkeypatch.setattr(
        "runner_api_routers.ui._load_runtime",
        lambda: {"active_week": "W99"},
    )
    return SAMPLE_ITEMS


class TestContentStudioListUI:
    def test_list_page_renders(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "Content Studio" in r.text
        assert 'data-testid="cs-table"' in r.text

    def test_list_api_data_renders(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio")
        assert "W99" in r.text
        assert "Studio UI Week" in r.text
        assert "QA Passed" in r.text
        assert "W98" in r.text

    def test_search_controls_present(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio")
        assert 'data-testid="cs-search"' in r.text
        assert "cs-search" in r.text
        assert "applyFilters" in r.text or "cs-search" in r.text

    def test_filter_controls_present(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio")
        assert 'data-testid="cs-filter-status"' in r.text
        assert 'data-testid="cs-filter-week"' in r.text
        assert "QA Passed" in r.text  # status option from API data
        assert 'value="W99"' in r.text

    def test_empty_state(
        self, cms_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "runner_api_routers.ui.build_content_list",
            lambda: {"ok": True, "count": 0, "items": []},
        )
        monkeypatch.setattr(
            "runner_api_routers.ui._load_runtime",
            lambda: {"active_week": "W01"},
        )
        r = cms_client.get("/content-studio")
        assert r.status_code == 200
        assert 'data-testid="cs-empty"' in r.text
        assert "No content items returned" in r.text

    def test_api_failure_explicit(
        self, cms_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _boom() -> dict[str, Any]:
            raise RuntimeError("simulated API failure")

        monkeypatch.setattr("runner_api_routers.ui.build_content_list", _boom)
        monkeypatch.setattr(
            "runner_api_routers.ui._load_runtime",
            lambda: {"active_week": "W01"},
        )
        r = cms_client.get("/content-studio")
        assert r.status_code == 200
        assert 'data-testid="cs-api-error"' in r.text
        assert "simulated API failure" in r.text
        assert "W99" not in r.text  # no silent fallback demo data


class TestContentStudioDetailUI:
    def test_detail_page_renders(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/W99")
        assert r.status_code == 200
        assert 'data-testid="cs-detail"' in r.text
        assert "Studio UI Week" in r.text
        assert "input/W99/04_Draft.md" in r.text

    def test_detail_artifacts_and_file_preview_links(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/W99")
        assert 'data-testid="cs-artifacts"' in r.text
        assert "/weeks/W99/file/04_Draft.md" in r.text
        assert "/weeks/W99/file/05_Final.md" in r.text
        assert 'data-testid="cs-file-preview"' in r.text

    def test_week_navigation(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/W99")
        assert 'data-testid="cs-week-nav"' in r.text
        # SAMPLE order: W99 then W98 → from W99, next is W98
        assert 'data-testid="cs-next-week"' in r.text
        assert "/content-studio/W98" in r.text
        assert 'data-testid="cs-week-jump"' in r.text

    def test_missing_content_ui_state(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/W97")
        assert r.status_code == 200
        assert 'data-testid="cs-not-found"' in r.text
        assert "Content not found" in r.text


class TestContentStudioUIReadOnlyAndNav:
    def test_no_mutation_requests_in_pages(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        list_src = cms_client.get("/content-studio").text
        detail_src = cms_client.get("/content-studio/W99").text
        for html in (list_src, detail_src):
            assert 'method="post"' not in html.lower()
            assert "<form" not in html.lower()
        # Content Studio page scripts use GET against the E2 API only.
        assert "fetch('/api/v1/content-studio/content', { method: 'GET' })" in list_src
        assert "fetch('/api/v1/content-studio/content', { method: 'GET' })" in detail_src
        for html in (list_src, detail_src):
            assert "fetch('/run'" not in html
            assert "fetch('/generate'" not in html
            assert "fetch('/edit'" not in html
            assert "fetch('/marketing/publish'" not in html
            # Base layout defines apiPost; Content Studio must not call it.
            assert html.count("apiPost(") == html.count("function apiPost(")

    def test_no_side_effect_helpers(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        calls: list[str] = []

        def _forbid(*_a: Any, **_k: Any) -> None:
            calls.append("hit")
            raise AssertionError("mutation helper must not run")

        with patch("runner_api_routers.utils._run", _forbid), patch(
            "runner_api_routers.utils._apply_week_if_set", _forbid
        ):
            assert cms_client.get("/content-studio").status_code == 200
            assert cms_client.get("/content-studio/W99").status_code == 200
        assert calls == []

    def test_existing_navigation_intact(
        self, cms_client: TestClient, studio_ui_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio")
        assert 'href="/weeks"' in r.text
        assert 'href="/pipeline"' in r.text
        assert 'href="/content-studio"' in r.text
        assert "Content Studio" in r.text
        # Existing pages still respond
        assert cms_client.get("/weeks").status_code == 200
        assert cms_client.get("/pipeline").status_code == 200
        assert cms_client.get("/").status_code == 200
