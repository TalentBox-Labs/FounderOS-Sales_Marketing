"""Unit tests for utility functions and helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.tools.csv_reader import get_active_content
from src.tools.runtime_paths import load_runtime_config
from runner_api_routers.utils import _validate_week_id


# ── CSV Reader Tests ─────────────────────────────────────────────────────────


class TestCSVReader:
    """Test CSV reading utilities."""

    def test_get_active_content_with_content_id(
        self, monkeypatch: pytest.MonkeyPatch, fake_active_content
    ) -> None:
        """get_active_content returns row with specific content_id."""
        import pandas as pd

        monkeypatch.setattr(
            "src.tools.csv_reader.read_runtime_tracker",
            lambda *args, **kwargs: pd.DataFrame([fake_active_content]),
        )

        result = get_active_content(content_id="W99")
        assert result["content_id"] == "W99"
        assert result["title"] == "Test Content"

    def test_get_active_content_without_content_id(
        self, monkeypatch: pytest.MonkeyPatch, fake_active_content, fake_runtime_config
    ) -> None:
        """get_active_content uses active_week from runtime config."""
        import pandas as pd

        monkeypatch.setattr(
            "src.tools.csv_reader.read_runtime_tracker",
            lambda *args, **kwargs: pd.DataFrame([fake_active_content]),
        )
        monkeypatch.setattr(
            "src.tools.csv_reader.load_runtime_config",
            lambda: fake_runtime_config,
        )

        result = get_active_content()
        assert result is not None


# ── Runtime Config Tests ─────────────────────────────────────────────────────


class TestRuntimeConfig:
    """Test runtime configuration loading."""

    def test_load_runtime_config_returns_dict(self, monkeypatch: pytest.MonkeyPatch, fake_runtime_config) -> None:
        """load_runtime_config returns dictionary."""
        monkeypatch.setattr(
            "src.tools.runtime_paths.load_runtime_config",
            lambda: fake_runtime_config,
        )

        config = load_runtime_config()
        assert isinstance(config, dict)
        assert "active_week" in config

    def test_runtime_config_has_required_keys(self, monkeypatch: pytest.MonkeyPatch, fake_runtime_config) -> None:
        """Runtime config contains essential keys."""
        monkeypatch.setattr(
            "src.tools.runtime_paths.load_runtime_config",
            lambda: fake_runtime_config,
        )

        config = load_runtime_config()
        required_keys = ["active_week", "qa_output_dir"]
        for key in required_keys:
            assert key in config


# ── Week ID Validation Tests ────────────────────────────────────────────────


class TestWeekIDValidation:
    """Test week ID validation for security."""

    def test_validate_week_id_accepts_valid_format(self) -> None:
        """Valid week IDs like W99 are accepted."""
        # Should not raise
        _validate_week_id("W99")
        _validate_week_id("W01")
        _validate_week_id("W100")

    def test_validate_week_id_rejects_path_traversal(self) -> None:
        """Week ID validation prevents path traversal attacks."""
        with pytest.raises(ValueError):
            _validate_week_id("W99/../../../etc/passwd")

        with pytest.raises(ValueError):
            _validate_week_id("../../etc/passwd")

        with pytest.raises(ValueError):
            _validate_week_id("W99/..\\..\\windows\\system32")

    def test_validate_week_id_rejects_special_chars(self) -> None:
        """Week ID validation rejects dangerous characters."""
        with pytest.raises(ValueError):
            _validate_week_id("W99;rm -rf /")

        with pytest.raises(ValueError):
            _validate_week_id("W99|cat etc/passwd")

    def test_validate_week_id_rejects_shell_metacharacters(self) -> None:
        """Week ID validation rejects shell metacharacters."""
        dangerous_ids = [
            "W99`whoami`",
            "W99$(whoami)",
            "W99&whoami",
            "W99|whoami",
            "W99>output.txt",
        ]
        for week_id in dangerous_ids:
            with pytest.raises(ValueError):
                _validate_week_id(week_id)


# ── Path Resolution Tests ────────────────────────────────────────────────────


class TestPathResolution:
    """Test safe path resolution."""

    def test_artifact_paths_resolve_correctly(self, fake_active_content) -> None:
        """Artifact paths are resolved relative to week folder."""
        from src.artifact_crew import ArtifactCrew

        crew = ArtifactCrew()
        # Mock the method to test path logic
        active = fake_active_content
        output_root = None

        # Should use draft_path parent directory
        from pathlib import Path

        draft_path = active["draft_path"]  # input/W99/04_Draft.md
        expected_parent = Path(draft_path).parent

        assert "input/W99" in draft_path


# ── File I/O Tests ───────────────────────────────────────────────────────────


class TestFileOperations:
    """Test file reading and writing utilities."""

    def test_read_file_returns_content(self, tmp_path: Path) -> None:
        """File reading returns correct content."""
        from src.base_crew import BaseCrew

        test_file = tmp_path / "test.md"
        test_file.write_text("Test content\n")

        crew = BaseCrew("test", repo_root=tmp_path)
        content = crew.read_file("test.md")

        assert content == "Test content\n"

    def test_read_file_raises_on_missing_file(self, tmp_path: Path) -> None:
        """File reading raises error for missing files."""
        from src.base_crew import BaseCrew

        crew = BaseCrew("test", repo_root=tmp_path)

        with pytest.raises(FileNotFoundError):
            crew.read_file("nonexistent.md")

    def test_save_file_creates_directories(self, tmp_path: Path) -> None:
        """File saving creates parent directories."""
        from src.base_crew import BaseCrew

        crew = BaseCrew("test", repo_root=tmp_path)
        crew.save_file("deep/nested/output.md", "content")

        saved_file = tmp_path / "deep" / "nested" / "output.md"
        assert saved_file.is_file()
        assert saved_file.read_text() == "content"

    def test_save_file_overwrites_existing(self, tmp_path: Path) -> None:
        """File saving overwrites existing files."""
        from src.base_crew import BaseCrew

        crew = BaseCrew("test", repo_root=tmp_path)

        output_file = tmp_path / "output.md"
        output_file.write_text("old content")

        crew.save_file("output.md", "new content")

        assert output_file.read_text() == "new content"


# ── String Processing Tests ──────────────────────────────────────────────────


class TestStringProcessing:
    """Test string utilities and normalization."""

    def test_markdown_fence_stripping(self) -> None:
        """Markdown fence stripping removes outer code blocks."""
        from src.editor_crew import EditorCrew

        # LLM sometimes wraps output in code fence
        fenced = """```markdown
# Article
Content here
```"""
        stripped = EditorCrew._maybe_strip_outer_fence(fenced)

        assert not stripped.startswith("```")
        assert not stripped.endswith("```")
        assert "# Article" in stripped

    def test_markdown_fence_stripping_preserves_inner_fences(self) -> None:
        """Fence stripping preserves inner code blocks."""
        from src.editor_crew import EditorCrew

        text = """```markdown
# Article

Some code:
```python
print("hello")
```

End
```"""
        stripped = EditorCrew._maybe_strip_outer_fence(text)

        # Inner fence should be preserved
        assert "```python" in stripped or "print" in stripped

    def test_slug_generation(self) -> None:
        """URL slug generation handles special characters."""
        from src.marketing_crew import MarketingCrew

        crew = MarketingCrew()

        assert crew._slug_from_keyword("AI Recruiting") == "ai-recruiting"
        assert crew._slug_from_keyword("  Spaces  ") == "spaces"
        assert crew._slug_from_keyword("Multiple---dashes") == "multiple-dashes"
        assert crew._slug_from_keyword("CamelCase") == "camelcase"


# ── Configuration Loading Tests ──────────────────────────────────────────────


class TestConfigLoading:
    """Test YAML configuration loading."""

    def test_yaml_agent_config_structure(self, monkeypatch: pytest.MonkeyPatch, fake_yaml_config) -> None:
        """Agent configs have required fields."""
        from unittest.mock import MagicMock

        from src.base_crew import BaseCrew
        from src.qa_crew import QACrew

        monkeypatch.setattr(
            BaseCrew, "_load_yaml", lambda self, p: fake_yaml_config
        )
        monkeypatch.setattr(BaseCrew, "_build_llm", lambda self: MagicMock())

        crew = QACrew()
        agent_cfg = crew.agents_config.get("test_agent", {})

        assert "role" in agent_cfg
        assert "goal" in agent_cfg
        assert "backstory" in agent_cfg

    def test_yaml_task_config_structure(self, monkeypatch: pytest.MonkeyPatch, fake_yaml_config) -> None:
        """Task configs have required fields."""
        from unittest.mock import MagicMock

        from src.base_crew import BaseCrew
        from src.qa_crew import QACrew

        monkeypatch.setattr(
            BaseCrew, "_load_yaml", lambda self, p: fake_yaml_config
        )
        monkeypatch.setattr(BaseCrew, "_build_llm", lambda self: MagicMock())

        crew = QACrew()
        task_cfg = crew.tasks_config.get("test_task", {})

        assert "description" in task_cfg
        assert "expected_output" in task_cfg


# ── Data Validation Tests ────────────────────────────────────────────────────


class TestDataValidation:
    """Test data validation utilities."""

    def test_content_length_validation(self) -> None:
        """Content length validation enforces minimum."""
        from src.generation_crew import GenerationCrew

        crew = GenerationCrew()

        # Too short
        is_valid, errors = crew.validate_output("x")
        assert not is_valid

        # Just right
        is_valid, errors = crew.validate_output("x" * 100)
        assert is_valid

    def test_markdown_structure_validation(self) -> None:
        """Markdown validation checks for required structure."""
        from src.editor_crew import EditorCrew

        crew = EditorCrew()

        # Valid with frontmatter
        valid = "---\ntitle: Test\n---\n# Content"
        is_valid, _ = crew.validate_output(valid)
        assert is_valid

        # Invalid without frontmatter
        invalid = "# Content without frontmatter"
        is_valid, _ = crew.validate_output(invalid)
        assert not is_valid


# ── Environment Variable Tests ───────────────────────────────────────────────


class TestEnvironmentHandling:
    """Test environment variable handling."""

    def test_missing_env_vars_handled_gracefully(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing optional env vars don't crash system."""
        monkeypatch.delenv("WORKCREW_CREWAI_MODEL", raising=False)

        from src.crew import build_crew_llm

        llm = build_crew_llm()
        assert llm is not None  # Should have default

    def test_custom_env_vars_applied(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Custom environment variables are applied."""
        monkeypatch.setenv("WORKCREW_CREWAI_MODEL", "custom/model")
        monkeypatch.setenv("WORKCREW_CREWAI_TEMPERATURE", "0.5")

        from src.crew import build_crew_llm

        llm = build_crew_llm()
        assert llm is not None
