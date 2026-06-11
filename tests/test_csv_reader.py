"""Tracker resolution for active content (bundle / split ids)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.tools import csv_reader


def test_get_active_content_bundle_folder_w05_picks_w05a(tmp_path, monkeypatch):
    df = pd.DataFrame(
        [
            {
                "content_id": "W05B",
                "title": "b",
                "artifact_folder": "W05",
                "draft_path": "input/W05/04_Draft.md",
            },
            {
                "content_id": "W05A",
                "title": "a",
                "artifact_folder": "W05",
                "draft_path": "input/W05/04_Draft.md",
            },
        ]
    )
    monkeypatch.setattr(csv_reader, "read_runtime_tracker", lambda **_: df)
    monkeypatch.setattr(csv_reader, "load_runtime_config", lambda: {"active_week": "W05"})

    row = csv_reader.get_active_content()
    assert row["content_id"] == "W05A"


def test_get_active_content_exact_id_before_bundle(tmp_path, monkeypatch):
    df = pd.DataFrame(
        [
            {"content_id": "W06A", "artifact_folder": "", "draft_path": "x"},
            {"content_id": "W06B", "artifact_folder": "W06", "draft_path": "y"},
        ]
    )
    monkeypatch.setattr(csv_reader, "read_runtime_tracker", lambda **_: df)
    monkeypatch.setattr(csv_reader, "load_runtime_config", lambda: {"active_week": "W06A"})

    row = csv_reader.get_active_content()
    assert row["content_id"] == "W06A"


def test_get_active_content_raises_when_missing(monkeypatch):
    monkeypatch.setattr(
        csv_reader,
        "read_runtime_tracker",
        lambda **_: pd.DataFrame([{"content_id": "W01", "artifact_folder": ""}]),
    )
    monkeypatch.setattr(csv_reader, "load_runtime_config", lambda: {"active_week": "W99"})

    with pytest.raises(ValueError, match="No tracker row"):
        csv_reader.get_active_content()
