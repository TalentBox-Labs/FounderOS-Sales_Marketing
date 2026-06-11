"""Editor output cleanup."""

from __future__ import annotations

from src import editor_crew


def test_strip_markdown_fence():
    raw = "```markdown\n---\nweek_id: W05\n---\n\n# Hi\n```"
    out = editor_crew._maybe_strip_outer_fence(raw)
    assert out.startswith("---")
    assert "```" not in out


def test_strip_fence_noop_when_absent():
    t = "---\nx: y\n---\n\n# Body"
    assert editor_crew._maybe_strip_outer_fence(t) == t
