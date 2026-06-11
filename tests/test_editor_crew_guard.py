"""Phase 2B staging path guard."""

from __future__ import annotations

import pytest

from src import editor_crew


def test_staging_guard_rejects_input_paths():
    with pytest.raises(RuntimeError, match="staging directory outside input"):
        editor_crew._staging_guard("input/W05")


def test_staging_guard_allows_output():
    editor_crew._staging_guard("output/generated/W05")
