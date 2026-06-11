"""Tests for scripts/generate_week_fixtures.py output contracts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_week_fixtures.py"


def test_profile_for_week_has_required_keys():
    """Verify _profile_for_week returns all required config keys."""
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_week_fixtures import _profile_for_week

    profile = _profile_for_week("W01")
    required_keys = {
        "active_week",
        "draft_path",
        "research_path",
        "seo_plan_path",
        "final_path",
        "qa_output_dir",
        "draft_validation_mode",
    }
    assert set(profile.keys()) == required_keys
    assert profile["active_week"] == "W01"
    assert profile["draft_path"] == "input/W01/04_Draft.md"
    assert profile["qa_output_dir"] == "output/qa_reports/"


def test_final_has_required_yaml_frontmatter():
    """Verify _final output contains required YAML front matter keys."""
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_week_fixtures import _final

    content = _final("W05")
    lines = content.split("\n")
    
    # Verify YAML block exists
    assert lines[0].strip() == "---"
    yaml_end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None)
    assert yaml_end is not None, "Missing closing --- for YAML front matter"
    
    yaml_lines = lines[1:yaml_end]
    yaml_text = "\n".join(yaml_lines)
    
    required_fm_keys = {
        "week_id",
        "article_title",
        "primary_keyword",
        "search_intent",
        "funnel_stage",
        "status",
        "publish_status",
        "canonical_url",
        "cta_type",
    }
    for key in required_fm_keys:
        assert f"{key}:" in yaml_text, f"Missing YAML key: {key}"


def test_checklist_has_required_sections():
    """Verify _checklist output contains all required section markers."""
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_week_fixtures import _checklist

    content = _checklist("W03")
    required_sections = [
        "# Content QA",
        "# SEO QA",
        "# Brand QA",
        "# Technical QA",
        "# Final Approval",
    ]
    for section in required_sections:
        assert section in content, f"Missing section: {section}"


def test_verify_mode_exits_zero_when_fixtures_present(tmp_path, monkeypatch):
    """Verify --verify exits 0 when all fixtures exist."""
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_week_fixtures import verify

    # Patch paths to temp dir with fixtures created
    from generate_week_fixtures import (
        PROFILES_DIR as orig_profiles,
        INPUT_DIR as orig_input,
        RUNTIME_CONFIG as orig_config,
    )
    import generate_week_fixtures as gen_mod

    # Create all expected paths
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    config_file = tmp_path / "runtime_config.json"
    config_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(gen_mod, "PROFILES_DIR", profiles)
    monkeypatch.setattr(gen_mod, "INPUT_DIR", input_dir)
    monkeypatch.setattr(gen_mod, "RUNTIME_CONFIG", config_file)

    # Mock tracker to return simple week list
    monkeypatch.setattr(
        gen_mod,
        "_tracker_weeks",
        lambda: ["W01", "W02"],
    )

    # Create fixtures for mocked weeks
    for week in ["W01", "W02"]:
        (profiles / f"{week}.json").write_text("{}", encoding="utf-8")
        week_dir = input_dir / week
        week_dir.mkdir()
        for fname in ["02_SEO_Plan.md", "03_Research.md", "04_Draft.md", "05_Final.md", "09_Publish_Checklist.md"]:
            (week_dir / fname).write_text("", encoding="utf-8")

    # Add legacy W05
    w05_profile = profiles / "W05.json"
    w05_profile.write_text("{}", encoding="utf-8")
    w05_dir = input_dir / "W05"
    w05_dir.mkdir()
    for fname in ["02_SEO_Plan.md", "03_Research.md", "04_Draft.md", "05_Final.md", "09_Publish_Checklist.md"]:
        (w05_dir / fname).write_text("", encoding="utf-8")

    result = verify()
    assert result == 0, "verify() should return 0 when all fixtures present"


def test_verify_mode_via_subprocess():
    """Integration test: --verify flag via subprocess."""
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--verify"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"--verify failed:\n{result.stderr}"


def test_generate_mode_preserves_existing_files(tmp_path, monkeypatch):
    """Verify generate mode without --overwrite preserves existing files."""
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_week_fixtures import generate, _write_if_needed

    # Test the _write_if_needed helper
    test_file = tmp_path / "test.txt"
    original_content = "original"
    test_file.write_text(original_content, encoding="utf-8")

    # Try write without overwrite—should preserve
    changed = _write_if_needed(test_file, "new content", overwrite=False)
    assert not changed
    assert test_file.read_text(encoding="utf-8") == original_content

    # Try with overwrite—should replace
    changed = _write_if_needed(test_file, "new content", overwrite=True)
    assert changed
    assert test_file.read_text(encoding="utf-8") == "new content"
