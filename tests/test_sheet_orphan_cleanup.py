"""sheet_orphan_cleanup tracker helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.tools import sheet_orphan_cleanup as soc


def test_tracker_id_set_reads_content_ids(tmp_path: Path, monkeypatch):
    csv = tmp_path / "tracker.csv"
    csv.write_text(
        "content_id,title\n"
        "W01,M1\n"
        "W05A,M2a\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(soc, "TRACKER_PATH", csv)
    assert soc.tracker_id_set() == {"W01", "W05A"}
