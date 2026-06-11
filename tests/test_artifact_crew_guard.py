"""Guard tests for Phase 2A artifact crew."""

from __future__ import annotations

import pytest

from src import artifact_crew


def test_artifact_crew_staging_guard_rejects_input_path():
    with pytest.raises(RuntimeError, match="Phase 2A"):
        artifact_crew._staging_guard("input/W09A")


def test_artifact_crew_staging_guard_allows_output_generated():
    artifact_crew._staging_guard("output/generated/W09A")


def test_week_runtime_excerpt_missing_week():
    text = artifact_crew._week_runtime_excerpt("W999")
    assert "week_runtime" in text
