"""Unit tests for BaseCrew and crew implementations."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.base_crew import BaseCrew
from src.qa_crew import QACrew
from src.generation_crew import GenerationCrew
from src.editor_crew import EditorCrew
from src.artifact_crew import ArtifactCrew
from src.distribution_crew import DistributionCrew
from src.marketing_crew import MarketingCrew


# ── BaseCrew Tests ───────────────────────────────────────────────────────────


class TestBaseCrew:
    """Test BaseCrew abstract base class."""

    def test_base_crew_initializes_with_yaml_config(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """BaseCrew loads YAML configs and LLM."""
        fake_config = {"test_agent": {"role": "Test", "goal": "Test", "backstory": "Test"}}

        def fake_load_yaml(self, path):
            return fake_config

        monkeypatch.setattr(BaseCrew, "_load_yaml", fake_load_yaml)
        monkeypatch.setattr(BaseCrew, "_build_llm", lambda self: MagicMock())

        crew = QACrew(repo_root=tmp_path)

        assert crew.name == "qa"
        assert crew.repo_root == tmp_path
        assert crew.llm is not None
        assert crew.agents_config == fake_config
        assert crew.tasks_config == fake_config

    def test_base_crew_read_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """BaseCrew can read files relative to repo_root."""
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")

        monkeypatch.setattr(BaseCrew, "_load_yaml", lambda self, path: {})
        monkeypatch.setattr(BaseCrew, "_build_llm", lambda self: MagicMock())

        crew = QACrew(repo_root=tmp_path)
        content = crew.read_file("test.md")

        assert content == "test content"

    def test_base_crew_save_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """BaseCrew can save files relative to repo_root."""
        monkeypatch.setattr(BaseCrew, "_load_yaml", lambda self, path: {})
        monkeypatch.setattr(BaseCrew, "_build_llm", lambda self: MagicMock())

        crew = QACrew(repo_root=tmp_path)
        crew.save_file("output/test.md", "test content")

        saved_file = tmp_path / "output" / "test.md"
        assert saved_file.is_file()
        assert saved_file.read_text() == "test content"


# ── QACrew Tests ─────────────────────────────────────────────────────────────


class TestQACrew:
    """Test QA crew implementation."""

    def test_qa_crew_validates_output_format(self) -> None:
        """QACrew validates output contains required markdown structure."""
        crew = QACrew()

        # Valid output with required sections
        valid_output = """## Passed Checks
- All headings present

## Failed Checks
- (none)

## Observable Issues
None noted.

## Final Verdict
PASS
"""
        is_valid, errors = crew.validate_output(valid_output)
        assert is_valid is True
        assert len(errors) == 0

    def test_qa_crew_rejects_short_output(self) -> None:
        """QACrew rejects output that's too short."""
        crew = QACrew()

        is_valid, errors = crew.validate_output("too short")
        assert is_valid is False
        assert len(errors) > 0

    def test_qa_crew_builds_agent_and_task(
        self, monkeypatch: pytest.MonkeyPatch, patch_csv_reader, patch_runtime_config, patch_yaml_loader, tmp_path: Path
    ) -> None:
        """QACrew builds a single QA agent and task."""
        # CrewAI Agent accepts str | BaseLLM; MagicMock fails pydantic validation.
        # crewai's native OpenAI routing now validates credentials eagerly at
        # construction (not just at call time), so a real-looking key is
        # needed even though this test never actually calls the LLM.
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
        monkeypatch.setattr(
            "src.base_crew.BaseCrew._build_llm", lambda self: "openai/gpt-4o-mini"
        )

        crew = QACrew(repo_root=tmp_path)
        agents, tasks = crew.build_agents_and_tasks()

        assert len(agents) == 1
        assert len(tasks) == 1
        assert agents[0].llm is not None


# ── GenerationCrew Tests ─────────────────────────────────────────────────────


class TestGenerationCrew:
    """Test generation crew implementation."""

    def test_generation_crew_validates_output_length(self) -> None:
        """GenerationCrew validates generated content has minimum length."""
        crew = GenerationCrew()

        short_output = "brief"
        is_valid, errors = crew.validate_output(short_output)
        assert is_valid is False
        assert "too short" in errors[0].lower()

        long_output = "# Brief\n" * 100  # Sufficient length
        is_valid, errors = crew.validate_output(long_output)
        assert is_valid is True

    def test_generation_crew_builds_four_agents(
        self, monkeypatch: pytest.MonkeyPatch, patch_csv_reader, patch_runtime_config, patch_yaml_loader, tmp_path: Path
    ) -> None:
        """GenerationCrew builds all four agents (Strategist, SEO, Researcher, Writer)."""
        # CrewAI Agent accepts str | BaseLLM; MagicMock fails pydantic validation.
        # crewai's native OpenAI routing now validates credentials eagerly at
        # construction (not just at call time), so a real-looking key is
        # needed even though this test never actually calls the LLM.
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
        monkeypatch.setattr(
            "src.base_crew.BaseCrew._build_llm", lambda self: "openai/gpt-4o-mini"
        )

        crew = GenerationCrew(repo_root=tmp_path)
        crew.output_root = str(tmp_path / "output")
        crew.content_id = "W99"

        # Create staging directory with seed file
        staging = tmp_path / "output"
        staging.mkdir(exist_ok=True)

        agents, tasks = crew.build_agents_and_tasks()

        assert len(agents) == 4  # Strategist, SEO, Researcher, Writer
        assert len(tasks) == 4
        assert all(a.llm is not None for a in agents)


# ── EditorCrew Tests ─────────────────────────────────────────────────────────


class TestEditorCrew:
    """Test editor crew implementation."""

    def test_editor_crew_validates_output(self) -> None:
        """EditorCrew validates final markdown output."""
        crew = EditorCrew()

        # validate_output() rejects anything under 100 chars as "too short" —
        # padded with real body text so this exercises the frontmatter check,
        # not the length check.
        valid_output = """---
week_id: W99
title: Test Article
---

# Article Content

This is the main article, with enough body text to clear the minimum
length the editor's output-quality check requires."""
        is_valid, errors = crew.validate_output(valid_output)
        assert is_valid is True

    def test_editor_crew_rejects_output_without_frontmatter(self) -> None:
        """EditorCrew requires YAML front matter."""
        crew = EditorCrew()

        output_no_frontmatter = (
            "# Article\nContent without frontmatter, padded with enough body "
            "text to clear the length check so this exercises the frontmatter "
            "check specifically rather than failing for being too short."
        )
        is_valid, errors = crew.validate_output(output_no_frontmatter)
        assert is_valid is False
        assert any("front matter" in e.lower() for e in errors)

    def test_editor_staging_guard_rejects_input_paths(self) -> None:
        """EditorCrew guard rejects input/ directory paths."""
        with pytest.raises(RuntimeError, match="staging directory outside input"):
            EditorCrew._staging_guard("input/W99")

    def test_editor_staging_guard_allows_output_paths(self) -> None:
        """EditorCrew guard allows output/ directory paths."""
        EditorCrew._staging_guard("output/generated/W99")  # Should not raise


# ── ArtifactCrew Tests ───────────────────────────────────────────────────────


class TestArtifactCrew:
    """Test artifact crew implementation."""

    def test_artifact_crew_validates_draft_output(self) -> None:
        """ArtifactCrew validates draft content length."""
        crew = ArtifactCrew()

        valid_output = "# Draft\n" * 50  # Long enough
        is_valid, errors = crew.validate_output(valid_output)
        assert is_valid is True

        short_output = "x"
        is_valid, errors = crew.validate_output(short_output)
        assert is_valid is False

    def test_artifact_staging_guard_rejects_input_paths(self) -> None:
        """ArtifactCrew guard rejects input/ directory."""
        with pytest.raises(RuntimeError, match="Phase 2A"):
            ArtifactCrew._staging_guard("input/W99")

    def test_artifact_staging_guard_allows_output_paths(self) -> None:
        """ArtifactCrew guard allows output/ directory."""
        ArtifactCrew._staging_guard("output/generated/W99")  # Should not raise

    def test_artifact_crew_week_runtime_excerpt_missing(self) -> None:
        """ArtifactCrew handles missing week_runtime gracefully."""
        crew = ArtifactCrew()
        excerpt = crew._week_runtime_excerpt("W999")

        assert "week_runtime" in excerpt
        assert "No" in excerpt or "missing" in excerpt.lower()


# ── DistributionCrew Tests ──────────────────────────────────────────────────


class TestDistributionCrew:
    """Test distribution crew implementation."""

    def test_distribution_crew_validates_output(self) -> None:
        """DistributionCrew validates minimum output length."""
        crew = DistributionCrew()

        valid_output = "# Design Brief\n" * 10
        is_valid, errors = crew.validate_output(valid_output)
        assert is_valid is True

        short_output = "x"
        is_valid, errors = crew.validate_output(short_output)
        assert is_valid is False

    def test_distribution_staging_guard_rejects_input_paths(self) -> None:
        """DistributionCrew guard rejects input/ directory."""
        with pytest.raises(RuntimeError, match="staging directory outside input"):
            DistributionCrew._staging_guard("input/W99")

    def test_distribution_staging_guard_allows_output_paths(self) -> None:
        """DistributionCrew guard allows output/ directory."""
        DistributionCrew._staging_guard("output/generated/W99")  # Should not raise


# ── MarketingCrew Tests ──────────────────────────────────────────────────────


class TestMarketingCrew:
    """Test marketing crew implementation."""

    def test_marketing_crew_validates_output(self) -> None:
        """MarketingCrew validates output."""
        crew = MarketingCrew()

        valid_output = "# Strategy Brief\n" * 10
        is_valid, errors = crew.validate_output(valid_output)
        assert is_valid is True

        short_output = ""
        is_valid, errors = crew.validate_output(short_output)
        assert is_valid is False

    def test_marketing_crew_rejects_invalid_brand(self) -> None:
        """MarketingCrew rejects invalid brand names."""
        crew = MarketingCrew()

        with pytest.raises(ValueError, match="brand must be one of"):
            crew.run_marketing_crew(
                brand="invalid_brand",
                topic="test",
                target_keyword="test",
            )

    def test_marketing_crew_slug_generation(self) -> None:
        """MarketingCrew correctly generates URL slugs."""
        crew = MarketingCrew()

        slug = crew._slug_from_keyword("AI Recruiting Automation")
        assert slug == "ai-recruiting-automation"

        slug = crew._slug_from_keyword("  spaces  and--dashes  ")
        assert slug == "spaces-and-dashes"


# ── Backward Compatibility Tests ─────────────────────────────────────────────


class TestCrewBackwardCompatibility:
    """Test backward-compatible function exports for existing tests."""

    def test_editor_crew_canonical_url_extraction(self) -> None:
        """Test backward-compatible canonical URL extraction."""
        from src.editor_crew import extract_canonical_url_from_seo_plan

        text = "**Canonical URL:** `https://example.com/blog/post`"
        url = extract_canonical_url_from_seo_plan(text)
        assert url == "https://example.com/blog/post"

    def test_editor_crew_guard_function(self) -> None:
        """Test backward-compatible staging guard function."""
        from src.editor_crew import _staging_guard

        with pytest.raises(RuntimeError):
            _staging_guard("input/W99")

    def test_artifact_crew_guard_function(self) -> None:
        """Test backward-compatible artifact crew guard function."""
        from src.artifact_crew import _staging_guard

        with pytest.raises(RuntimeError):
            _staging_guard("input/W99")

    def test_distribution_crew_guard_function(self) -> None:
        """Test backward-compatible distribution crew guard function."""
        from src.distribution_crew import _staging_guard

        with pytest.raises(RuntimeError):
            _staging_guard("input/W99")
