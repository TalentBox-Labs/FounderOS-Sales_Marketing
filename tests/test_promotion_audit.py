"""Promotion audit trail helpers."""

from __future__ import annotations

from pathlib import Path

from src.tools import promotion_audit as pa


def test_compute_file_diffs_phase2b_single_file(monkeypatch, tmp_path):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)

    staging = tmp_path / "gen" / "W01"
    canonical = tmp_path / "input" / "W01"
    staging.mkdir(parents=True)
    canonical.mkdir(parents=True)
    (staging / "05_Final.md").write_text("# Final\n", encoding="utf-8")
    (canonical / "05_Final.md").write_text("# Old\n", encoding="utf-8")

    diff_out = tmp_path / "d"
    full, arts = pa.compute_file_diffs(
        staging,
        canonical,
        audit_prefix="T",
        diff_out_dir=diff_out,
        filenames=pa.PHASE2B_PROMOTION_FILENAMES,
    )
    assert list(full.keys()) == ["05_Final.md"]
    assert arts["05_Final.md"]


def test_parse_validator_verdict_pass_fail():
    assert pa.parse_validator_verdict("## Final Verdict\nPASS\n") == "PASS"
    assert pa.parse_validator_verdict("x\n## Final Verdict\n\nFAIL\n") == "FAIL"
    assert pa.parse_validator_verdict("no verdict") == "UNKNOWN"


def test_compute_file_diffs_creates_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)

    staging = tmp_path / "st"
    canonical = tmp_path / "input" / "W01"
    staging.mkdir(parents=True)
    canonical.mkdir(parents=True)
    (staging / "01_Content_Brief.md").write_text("new brief\n", encoding="utf-8")
    (canonical / "01_Content_Brief.md").write_text("old brief\n", encoding="utf-8")

    diff_out = tmp_path / "audit_diffs"
    full, artifacts = pa.compute_file_diffs(
        staging,
        canonical,
        audit_prefix="T_test_W01",
        diff_out_dir=diff_out,
    )
    assert "01_Content_Brief.md" in full
    assert "--- " in full["01_Content_Brief.md"]
    assert Path(tmp_path / artifacts["01_Content_Brief.md"]).is_file()


def test_write_audit_bundle_json_and_jsonl(monkeypatch, tmp_path):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pa, "AUDIT_DIR", tmp_path / "output" / "promotion_audit")
    monkeypatch.setattr(pa, "HISTORY_JSONL", tmp_path / "output" / "promotion_audit" / "promotion_history.jsonl")

    canon = tmp_path / "input" / "W05"
    canon.mkdir(parents=True)

    path = pa.write_audit_bundle(
        event_ts_slug="20990101T000000Z",
        week_id="W05",
        staging_root="output/generated/W05",
        approver="Test Approver",
        notes="unit test",
        skip_validation=False,
        validator_runs=[{"validator_id": "draft_validator", "verdict": "PASS"}],
        backup_relative="input/W05/.promotion_backup/20990101T000000Z",
        canonical_path=canon,
        diff_artifacts={"01_Content_Brief.md": "output/promotion_audit/x.diff"},
        diff_character_counts={"01_Content_Brief.md": 42},
    )
    assert path.is_file()
    assert pa.HISTORY_JSONL.is_file()
    assert pa.HISTORY_JSONL.read_text().strip()
