from __future__ import annotations

import src.tools.tracker_updater as tu


def test_update_tracker_matches_artifact_folder_bundle(tmp_path, monkeypatch):
    csv_file = tmp_path / "tracker.csv"
    csv_file.write_text(
        "content_id,title,status,qa_status,artifact_folder\n"
        "W05A,M5a,In Progress,,W05\n"
        "W05B,M5b,In Progress,,W05\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(tu, "TRACKER_PATH", csv_file)
    monkeypatch.setattr(
        tu,
        "load_runtime_config",
        lambda: {"active_week": "W05"},
    )

    tu.update_tracker()

    text = csv_file.read_text(encoding="utf-8")
    assert text.count("QA Passed") == 2
    assert text.count("PASS") == 2


def test_update_tracker_targets_active_week_row(tmp_path, monkeypatch):
    csv_file = tmp_path / "tracker.csv"
    csv_file.write_text(
        "content_id,title,status,qa_status\n"
        "W99,M9,In Progress,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(tu, "TRACKER_PATH", csv_file)
    monkeypatch.setattr(
        tu,
        "load_runtime_config",
        lambda: {"active_week": "W99"},
    )

    tu.update_tracker()

    text = csv_file.read_text(encoding="utf-8")
    assert "W99" in text
    assert "QA Passed" in text
    assert "PASS" in text
