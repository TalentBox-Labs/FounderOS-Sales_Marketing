"""Focused tests for Content Studio read-only Kanban (Sprint E4A)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient


MULTI_STATUS_ITEMS = [
    {
        "content_id": "W99",
        "title": "Kanban Alpha",
        "status": "QA Passed",
        "qa_status": "PASS",
        "current_step": "Publish Review",
        "next_step": "None",
        "draft_path": "input/W99/04_Draft.md",
        "qa_output_path": "",
        "final_output_path": "",
        "artifact_folder": "",
        "artifacts": {"draft": True},
    },
    {
        "content_id": "W98",
        "title": "Kanban Beta",
        "status": "draft",
        "qa_status": "",
        "current_step": "Generation",
        "next_step": "QA",
        "draft_path": "input/W98/04_Draft.md",
        "qa_output_path": "",
        "final_output_path": "",
        "artifact_folder": "",
        "artifacts": {"draft": True},
    },
    {
        "content_id": "W97",
        "title": "Odd Status Item",
        "status": "Custom-Raw-Status",
        "qa_status": "",
        "current_step": "—",
        "next_step": "",
        "draft_path": "",
        "qa_output_path": "",
        "final_output_path": "",
        "artifact_folder": "",
        "artifacts": {},
    },
]


@pytest.fixture
def kanban_data(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    monkeypatch.setattr(
        "runner_api_routers.ui.build_content_list",
        lambda: {
            "ok": True,
            "count": len(MULTI_STATUS_ITEMS),
            "items": MULTI_STATUS_ITEMS,
        },
    )
    monkeypatch.setattr(
        "runner_api_routers.ui._load_runtime",
        lambda: {"active_week": "W99"},
    )
    return MULTI_STATUS_ITEMS


class TestContentStudioKanban:
    def test_kanban_renders(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/kanban")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert 'data-testid="kb-board"' in r.text
        assert "Kanban" in r.text

    def test_statuses_map_to_exact_columns(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/kanban")
        # Exact API strings — no invented IDEA/BRIEF/etc.
        assert 'data-status="QA Passed"' in r.text
        assert 'data-status="draft"' in r.text
        assert 'data-status="Custom-Raw-Status"' in r.text
        assert "IDEA" not in r.text
        assert "SCHEDULED" not in r.text
        assert "PUBLISHED" not in r.text

    def test_cards_render_api_data(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/kanban")
        assert "Kanban Alpha" in r.text
        assert "Kanban Beta" in r.text
        assert 'data-content-id="W99"' in r.text
        assert 'data-content-id="W98"' in r.text

    def test_card_links_to_detail(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/kanban")
        assert 'href="/content-studio/W99"' in r.text
        assert 'href="/content-studio/W98"' in r.text
        assert 'data-testid="kb-card"' in r.text

    def test_empty_column_markup_present(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/kanban")
        assert 'data-testid="kb-empty-column"' in r.text

    def test_search_filter_controls(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]]
    ) -> None:
        r = cms_client.get("/content-studio/kanban")
        assert 'data-testid="kb-search"' in r.text
        assert 'data-testid="kb-filter-status"' in r.text
        assert 'data-testid="kb-filter-week"' in r.text
        assert "applyFilters" in r.text

    def test_api_failure_explicit(
        self, cms_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _boom() -> dict[str, Any]:
            raise RuntimeError("kanban api down")

        monkeypatch.setattr("runner_api_routers.ui.build_content_list", _boom)
        monkeypatch.setattr(
            "runner_api_routers.ui._load_runtime",
            lambda: {"active_week": "W01"},
        )
        r = cms_client.get("/content-studio/kanban")
        assert r.status_code == 200
        assert 'data-testid="kb-api-error"' in r.text
        assert "kanban api down" in r.text
        # Board element must be absent (JS may still mention the testid string).
        assert 'class="kb-board"' not in r.text
        assert "No fallback board is shown" in r.text

    def test_blank_status_safe_column(
        self, cms_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        items = [
            {
                "content_id": "W90",
                "title": "No Status",
                "status": "",
                "qa_status": "",
                "current_step": "",
                "next_step": "",
                "draft_path": "",
                "qa_output_path": "",
                "final_output_path": "",
                "artifact_folder": "",
                "artifacts": {},
            }
        ]
        monkeypatch.setattr(
            "runner_api_routers.ui.build_content_list",
            lambda: {"ok": True, "count": 1, "items": items},
        )
        monkeypatch.setattr(
            "runner_api_routers.ui._load_runtime",
            lambda: {"active_week": "W90"},
        )
        r = cms_client.get("/content-studio/kanban")
        assert r.status_code == 200
        assert 'data-status=""' in r.text or "data-status=\"\"" in r.text
        assert "W90" in r.text
        # Display uses em-dash label, not an invented lifecycle name
        assert "IDEA" not in r.text

    def test_no_mutation_requests(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]]
    ) -> None:
        html = cms_client.get("/content-studio/kanban").text
        assert "<form" not in html.lower()
        assert 'method="post"' not in html.lower()
        assert "fetch('/run'" not in html
        assert "fetch('/generate'" not in html
        assert "fetch('/edit'" not in html
        assert "drag" not in html.lower()
        assert "ondrop" not in html.lower()
        assert html.count("apiPost(") == html.count("function apiPost(")

    def test_list_and_detail_unchanged(
        self, cms_client: TestClient, kanban_data: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _detail(content_id: str) -> dict[str, Any]:
            from fastapi import HTTPException

            for item in MULTI_STATUS_ITEMS:
                if item["content_id"] == content_id:
                    return {"ok": True, "item": item}
            raise HTTPException(status_code=404, detail="Content not found")

        monkeypatch.setattr("runner_api_routers.ui.build_content_detail", _detail)
        list_r = cms_client.get("/content-studio")
        detail_r = cms_client.get("/content-studio/W99")
        assert list_r.status_code == 200
        assert 'data-testid="cs-table"' in list_r.text
        assert detail_r.status_code == 200
        assert 'data-testid="cs-detail"' in detail_r.text
        # Kanban route must not steal detail for real ids
        assert cms_client.get("/content-studio/kanban").status_code == 200
