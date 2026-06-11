"""Phase 3 distribution bundle deterministic gate."""

from __future__ import annotations

import json

import pytest

from src.tools import distribution_bundle_checker as dbc
from src.tools import promotion_audit as pa
from src.tools import publish_checklist_checker as pcc


def test_phase3_filenames_tuple():
    assert pa.PHASE3_PROMOTION_FILENAMES == (
        "06_Design_Brief.md",
        "07_Social_Posts.md",
        "08_Email_Copy.md",
        "09_Publish_Checklist.md",
    )


def test_bundle_checker_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(dbc, "REPO_ROOT", tmp_path)

    bundle = tmp_path / "output" / "generated" / "W99"
    bundle.mkdir(parents=True)

    filler = "# Section\n\n" + ("paragraph.\n\n" * 30)
    for name in pa.PHASE3_PROMOTION_FILENAMES:
        body = filler
        if name == "09_Publish_Checklist.md":
            body = filler + "\n".join(f"{m}\n- item\n" for m in pcc._DEFAULT_SECTION_MARKERS)
        (bundle / name).write_text(body, encoding="utf-8")

    cfg = tmp_path / "data" / "runtime_config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        json.dumps(
            {
                "active_week": "W99",
                "qa_output_dir": "output/qa_reports/",
                "distribution_staging_root": "output/generated/W99",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(dbc, "load_runtime_config", lambda: json.loads(cfg.read_text()))

    qa_out = tmp_path / "output" / "qa_reports"
    qa_out.mkdir(parents=True)

    with pytest.raises(SystemExit) as exc:
        dbc.run_distribution_bundle_check()
    assert exc.value.code == 0


def test_bundle_checker_custom_checklist_markers(monkeypatch, tmp_path):
    """Phase 3 gate uses `publish_checklist_section_markers` when set (same as main checklist checker)."""
    monkeypatch.setattr(dbc, "REPO_ROOT", tmp_path)

    bundle = tmp_path / "out" / "W97"
    bundle.mkdir(parents=True)
    custom = [
        "## Gate One",
        "## Gate Two",
        "## Gate Three",
        "## Gate Four",
        "## Gate Five",
    ]
    filler = "# x\n\n" + ("body text.\n\n" * 40)
    for name in pa.PHASE3_PROMOTION_FILENAMES:
        if name == "09_Publish_Checklist.md":
            body = "\n".join(f"{m}\n- ok\n" for m in custom) + "\n" + filler
        else:
            body = filler
        (bundle / name).write_text(body, encoding="utf-8")

    cfg = tmp_path / "data" / "runtime_config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        json.dumps(
            {
                "active_week": "W97",
                "qa_output_dir": "output/qa_reports/",
                "distribution_staging_root": "out/W97",
                "publish_checklist_section_markers": custom,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(dbc, "load_runtime_config", lambda: json.loads(cfg.read_text()))
    (tmp_path / "output" / "qa_reports").mkdir(parents=True)

    with pytest.raises(SystemExit) as exc:
        dbc.run_distribution_bundle_check()
    assert exc.value.code == 0


def test_bundle_checker_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(dbc, "REPO_ROOT", tmp_path)

    bundle = tmp_path / "out" / "W98"
    bundle.mkdir(parents=True)
    for name in pa.PHASE3_PROMOTION_FILENAMES[:-1]:
        (bundle / name).write_text("# x\n" * 40, encoding="utf-8")

    cfg = tmp_path / "cfg.json"
    cfg.write_text(
        json.dumps(
            {
                "active_week": "W98",
                "qa_output_dir": "output/qa_reports/",
                "distribution_staging_root": "out/W98",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(dbc, "load_runtime_config", lambda: json.loads(cfg.read_text()))
    (tmp_path / "output" / "qa_reports").mkdir(parents=True)

    with pytest.raises(SystemExit) as exc:
        dbc.run_distribution_bundle_check()
    assert exc.value.code == 1


def test_resolve_checklist_path_staging_overlay():
    from src.tools.publish_checklist_checker import resolve_checklist_path
    from src.tools.runtime_paths import REPO_ROOT

    p = resolve_checklist_path(
        {"active_week": "W05", "distribution_staging_root": "output/generated/W05"}
    )
    assert p == REPO_ROOT / "output/generated/W05/09_Publish_Checklist.md"


def test_resolve_checklist_path_canonical():
    from src.tools.publish_checklist_checker import resolve_checklist_path
    from src.tools.runtime_paths import REPO_ROOT

    p = resolve_checklist_path({"active_week": "W05"})
    assert p == REPO_ROOT / "input/W05/09_Publish_Checklist.md"


def test_resolve_checklist_path_input_bundle():
    from src.tools.publish_checklist_checker import resolve_checklist_path
    from src.tools.runtime_paths import REPO_ROOT

    p = resolve_checklist_path({"active_week": "W05A", "input_bundle": "W05"})
    assert p == REPO_ROOT / "input/W05/09_Publish_Checklist.md"
