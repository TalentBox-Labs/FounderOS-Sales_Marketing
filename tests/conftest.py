"""Shared test fixtures and utilities."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from fastapi.testclient import TestClient

# ── FastAPI TestClient Fixture ───────────────────────────────────────────────


@pytest.fixture
def cms_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    """TestClient for FastAPI CMS app with mocked dependencies."""
    from runner_api_routers.utils import _verify_api_key
    from runner_api import app

    # Override API key verification to always pass in tests
    async def mock_verify_api_key(token: str | None = None):
        return "test-key"

    app.dependency_overrides[_verify_api_key] = mock_verify_api_key

    yield TestClient(app)

    app.dependency_overrides.clear()


# ── Mock LLM Fixture ─────────────────────────────────────────────────────────


@pytest.fixture
def mock_llm() -> MagicMock:
    """Mock CrewAI LLM for testing crews without external calls."""
    llm = MagicMock()
    llm.call = MagicMock(return_value="Mock LLM output")
    return llm


# ── Mock Crew Execution ──────────────────────────────────────────────────────


@pytest.fixture
def mock_crew_run(monkeypatch: pytest.MonkeyPatch):
    """Patch crew.kickoff() to return mocked results."""
    def fake_kickoff(self):
        return "# Mock output\nThis is test content."

    # This patches the Crew class's kickoff method globally
    from crewai import Crew
    monkeypatch.setattr(Crew, "kickoff", fake_kickoff)


# ── Test Data Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def fake_active_content() -> dict[str, str]:
    """Fake tracker row for testing."""
    return {
        "content_id": "W99",
        "title": "Test Content",
        "current_step": "Generation",
        "next_step": "QA",
        "draft_path": "input/W99/04_Draft.md",
        "qa_output_path": "output/qa_reports/W99_QA.md",
        "week": "W99",
    }


@pytest.fixture
def fake_runtime_config() -> dict[str, str]:
    """Fake runtime configuration for testing."""
    return {
        "active_week": "W99",
        "crewai_qa_source": "final",
        "final_path": "input/W99/05_Final.md",
        "draft_path": "input/W99/04_Draft.md",
        "qa_output_dir": "output/qa_reports/",
        "enable_crewai_qa": True,
        "validators": [
            "structure_checker",
            "metadata_checker",
            "draft_validator",
        ],
    }


@pytest.fixture
def fake_yaml_config() -> dict[str, dict]:
    """Fake YAML agent/task configuration."""
    return {
        "test_agent": {
            "role": "Test Agent",
            "goal": "Test goal",
            "backstory": "Test backstory",
        },
        "test_task": {
            "description": "Test task description",
            "expected_output": "Test expected output",
        },
    }


# ── Monkeypatch Helpers ──────────────────────────────────────────────────────


@pytest.fixture
def patch_csv_reader(monkeypatch: pytest.MonkeyPatch, fake_active_content):
    """Patch CSV reader to return fake content."""
    def fake_get_active_content(content_id: str | None = None):
        return fake_active_content

    from src.tools import csv_reader
    monkeypatch.setattr(csv_reader, "get_active_content", fake_get_active_content)


@pytest.fixture
def patch_runtime_config(monkeypatch: pytest.MonkeyPatch, fake_runtime_config):
    """Patch runtime config loader."""
    def fake_load_runtime_config():
        return fake_runtime_config

    from src.tools import runtime_paths
    monkeypatch.setattr(runtime_paths, "load_runtime_config", fake_load_runtime_config)


@pytest.fixture
def patch_yaml_loader(monkeypatch: pytest.MonkeyPatch, fake_yaml_config):
    """Patch YAML loader."""
    def fake_load_yaml(path: str):
        return fake_yaml_config

    from src import base_crew
    monkeypatch.setattr(base_crew, "load_yaml", fake_load_yaml)


# ── Temporary Directory Utilities ────────────────────────────────────────────


@pytest.fixture
def staging_dir(tmp_path: Path) -> Path:
    """Create a temporary staging directory structure."""
    staging = tmp_path / "staging" / "W99"
    staging.mkdir(parents=True, exist_ok=True)

    # Create some stub files
    (staging / "00_Generation_Seed.md").write_text("Seed content\n")
    (staging / "04_Draft.md").write_text("# Draft\nDraft content\n")

    return staging


@pytest.fixture
def repo_with_artifacts(tmp_path: Path) -> Path:
    """Create a temporary repo structure with week artifacts."""
    repo = tmp_path / "repo"
    weeks_dir = repo / "input" / "W99"
    weeks_dir.mkdir(parents=True, exist_ok=True)

    # Create week files
    (weeks_dir / "00_Generation_Seed.md").write_text("Seed\n")
    (weeks_dir / "01_Content_Brief.md").write_text("# Brief\n")
    (weeks_dir / "02_SEO_Plan.md").write_text("# SEO\n")
    (weeks_dir / "03_Research.md").write_text("# Research\n")
    (weeks_dir / "04_Draft.md").write_text("# Draft\n")
    (weeks_dir / "05_Final.md").write_text("# Final\n")

    # Create output dirs
    (repo / "output" / "qa_reports").mkdir(parents=True, exist_ok=True)

    return repo
