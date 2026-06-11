"""CrewAI QA input path resolution (final vs draft)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.crew import resolve_crewai_qa_input_paths


def test_resolve_prefers_final_when_present(tmp_path: Path) -> None:
    root = tmp_path
    (root / "input" / "WX").mkdir(parents=True)
    final_p = root / "input" / "WX" / "05_Final.md"
    final_p.write_text("x" * 200, encoding="utf-8")
    draft_p = root / "input" / "WX" / "04_Draft.md"
    draft_p.write_text("# stub", encoding="utf-8")

    rel, label = resolve_crewai_qa_input_paths(
        repo_root=root,
        runtime={"final_path": "input/WX/05_Final.md", "crewai_qa_source": "final"},
        active={"draft_path": "input/WX/04_Draft.md"},
    )
    assert rel == "input/WX/05_Final.md"
    assert "05_Final" in label


def test_resolve_draft_when_source_draft(tmp_path: Path) -> None:
    root = tmp_path
    (root / "input" / "WX").mkdir(parents=True)
    (root / "input" / "WX" / "05_Final.md").write_text("x" * 200, encoding="utf-8")
    (root / "input" / "WX" / "04_Draft.md").write_text("# d", encoding="utf-8")

    rel, label = resolve_crewai_qa_input_paths(
        repo_root=root,
        runtime={
            "final_path": "input/WX/05_Final.md",
            "crewai_qa_source": "draft",
        },
        active={"draft_path": "input/WX/04_Draft.md"},
    )
    assert rel == "input/WX/04_Draft.md"
    assert "04_Draft" in label


def test_resolve_falls_back_when_final_missing(tmp_path: Path, capsys) -> None:
    root = tmp_path
    (root / "input" / "WX").mkdir(parents=True)
    draft_p = root / "input" / "WX" / "04_Draft.md"
    draft_p.write_text("# ok", encoding="utf-8")

    rel, label = resolve_crewai_qa_input_paths(
        repo_root=root,
        runtime={"final_path": "input/WX/05_Final.md", "crewai_qa_source": "final"},
        active={"draft_path": "input/WX/04_Draft.md"},
    )
    assert rel == "input/WX/04_Draft.md"
    assert "final missing" in label.lower() or "too small" in label.lower()
    err = capsys.readouterr().err
    assert "draft fallback" in err


def test_resolve_falls_back_when_final_too_small(tmp_path: Path) -> None:
    root = tmp_path
    (root / "input" / "WX").mkdir(parents=True)
    tiny = root / "input" / "WX" / "05_Final.md"
    tiny.write_text("short", encoding="utf-8")
    (root / "input" / "WX" / "04_Draft.md").write_text("# draft body", encoding="utf-8")

    rel, _ = resolve_crewai_qa_input_paths(
        repo_root=root,
        runtime={"final_path": "input/WX/05_Final.md", "crewai_qa_source": "final"},
        active={"draft_path": "input/WX/04_Draft.md"},
    )
    assert rel == "input/WX/04_Draft.md"


def test_resolve_draft_raises_without_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="draft_path"):
        resolve_crewai_qa_input_paths(
            repo_root=tmp_path,
            runtime={"crewai_qa_source": "draft"},
            active={},
        )


def test_resolve_invalid_source_treated_as_final(tmp_path: Path) -> None:
    root = tmp_path
    (root / "input" / "WX").mkdir(parents=True)
    (root / "input" / "WX" / "05_Final.md").write_text("x" * 100, encoding="utf-8")

    rel, _ = resolve_crewai_qa_input_paths(
        repo_root=root,
        runtime={"final_path": "input/WX/05_Final.md", "crewai_qa_source": "bogus"},
        active={"draft_path": "input/WX/04_Draft.md"},
    )
    assert rel == "input/WX/05_Final.md"
