"""Phase 4A sheet_sync dry-run helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.tools import sheet_sync


def test_validate_tracker_columns_ok():
    df = pd.DataFrame(
        columns=list(sheet_sync.TRACKER_REQUIRED_COLUMNS),
        data=[["W01"] + [""] * (len(sheet_sync.TRACKER_REQUIRED_COLUMNS) - 1)],
    )
    sheet_sync.validate_tracker_columns(df)


def test_validate_tracker_columns_missing_raises():
    df = pd.DataFrame(columns=["content_id", "title"])
    with pytest.raises(ValueError, match="missing required"):
        sheet_sync.validate_tracker_columns(df)


def test_compose_sheet_row_minimal(tmp_path: Path):
    (tmp_path / "input" / "W99").mkdir(parents=True)
    row = sheet_sync.compose_sheet_row(
        {
            "content_id": "W99",
            "title": "M1/Wk9",
            "status": "Draft",
            "qa_status": "FAIL",
            "current_step": "A",
            "next_step": "B",
            "draft_path": "input/W99/04_Draft.md",
            "qa_output_path": "",
            "final_output_path": "",
        },
        tmp_path,
    )
    assert row["ID"] == "W99"
    assert row["Month/Week"] == "M1/Wk9"
    assert row["Brief Done"] == "N"
    assert row["Edited"] == "N"
    assert row["SEO Final"] == "N"


def test_authoritative_columns_exclude_analytics():
    assert "Day7 Impr." not in sheet_sync.AUTHORITATIVE_SYNC_HEADERS
    assert len(sheet_sync.authoritative_column_indices()) == len(
        sheet_sync.AUTHORITATIVE_SYNC_HEADERS
    )


def test_validate_sheet_headers_match_ok():
    ok, errs = sheet_sync.validate_sheet_headers_match(list(sheet_sync.SHEET_HEADERS))
    assert ok and errs == []


def test_diff_authoritative_columns():
    b = {k: "" for k in sheet_sync.AUTHORITATIVE_SYNC_HEADERS}
    a = dict(b)
    a["Title"] = "x"
    assert sheet_sync._diff_authoritative_columns(b, a) == ["Title"]


def test_week_id_sort_key_orders_numeric_weeks():
    ids = ["W10", "W02", "W05", "W01"]
    assert sorted(ids, key=sheet_sync._week_id_sort_key) == [
        "W01",
        "W02",
        "W05",
        "W10",
    ]


def test_week_id_sort_key_split_and_sheet_order():
    ids = ["W10", "W05B", "W05", "W09B", "W05A", "W06A", "W09A", "W06B"]
    assert sorted(ids, key=sheet_sync._week_id_sort_key) == [
        "W05",
        "W05A",
        "W05B",
        "W06A",
        "W06B",
        "W09A",
        "W09B",
        "W10",
    ]


def test_compose_sheet_row_artifact_folder_uses_bundle_paths(tmp_path: Path):
    (tmp_path / "input" / "W05").mkdir(parents=True)
    (tmp_path / "input" / "W05" / "05_Final.md").write_text(
        "---\n"
        'article_title: "How to Deal with Candidate Ghosting in Tech Hiring"\n'
        'canonical_url: https://example.com/a\n'
        'primary_keyword: ghosting\n'
        'cta_type: try_workcrew_free\n'
        "---\n\n# H1\n\n## FAQ\n\nx.\n",
        encoding="utf-8",
    )
    row = sheet_sync.compose_sheet_row(
        {
            "content_id": "W05A",
            "title": "M2/Wk5a",
            "status": "QA Passed",
            "qa_status": "PASS",
            "current_step": "x",
            "next_step": "y",
            "draft_path": "",
            "qa_output_path": "",
            "final_output_path": "",
            "artifact_folder": "W05",
        },
        tmp_path,
    )
    assert row["ID"] == "W05A"
    assert row["Month/Week"] == "M2/Wk5a"
    assert row["Title"] == "How to Deal with Candidate Ghosting in Tech Hiring"
    assert row["Published URL"] == "https://example.com/a"
    assert row["Target Keyword"] == "ghosting"


def test_month_week_for_sheet_known_content_ids():
    assert sheet_sync._month_week_for_sheet("W06A", "ignored headline") == "M2/Wk6a"
    assert sheet_sync._month_week_for_sheet("W09B", "") == "M3/Wk9b"
    assert sheet_sync._month_week_for_sheet("W99", "M1/Wk9") == "M1/Wk9"


def test_sheet_display_title_prefers_article_title():
    fm = {"article_title": "From YAML"}
    assert sheet_sync._sheet_display_title("M1/Wk1", fm) == "From YAML"
    assert sheet_sync._sheet_display_title("M1/Wk1", {"article_title": ""}) == "M1/Wk1"


def test_publish_date_for_sheet_prefers_per_content_id_keys():
    fm = {
        "publish_date": "2026-06-09",
        "publish_date_w05a": "2026-06-09",
        "publish_date_w05b": "2026-06-11",
    }
    assert sheet_sync._publish_date_for_sheet("W05A", fm) == "2026-06-09"
    assert sheet_sync._publish_date_for_sheet("W05B", fm) == "2026-06-11"
    assert sheet_sync._publish_date_for_sheet("W06A", fm) == "2026-06-09"


def test_month_week_from_title_accepts_split_suffix():
    assert sheet_sync._month_week_from_title("M2/Wk5a") == "M2/Wk5a"
    assert sheet_sync._month_week_from_title("x M2/Wk7b ") == "M2/Wk7b"
    assert sheet_sync._month_week_from_title("M1/Wk1") == "M1/Wk1"


def test_governance_prefix_warnings_detects_w05a():
    notes = sheet_sync._governance_prefix_warnings(["W05"], {"W05A", "W05B", "W01"})
    assert len(notes) == 1
    assert "W05A" in notes[0] or "W05B" in notes[0]


def test_governance_prefix_warnings_empty_when_no_overlap():
    assert sheet_sync._governance_prefix_warnings(["W05"], {"W04", "W06"}) == []


def test_validate_sheet_headers_mismatch():
    bad = list(sheet_sync.SHEET_HEADERS)
    bad[0] = "Wrong"
    ok, errs = sheet_sync.validate_sheet_headers_match(bad)
    assert not ok
    assert any("Wrong" in e or "ID" in e for e in errs)


def test_compose_sheet_row_with_final(tmp_path: Path):
    inv = tmp_path / "input" / "W98"
    inv.mkdir(parents=True)
    for name in (
        "01_Content_Brief.md",
        "02_SEO_Plan.md",
        "03_Research.md",
        "04_Draft.md",
        "05_Final.md",
        "06_Design_Brief.md",
        "07_Social_Posts.md",
        "08_Email_Copy.md",
        "09_Publish_Checklist.md",
    ):
        text = "# X\n\n" + ("paragraph " * 50) if "07" in name or "08" in name else "# ok\n"
        (inv / name).write_text(text, encoding="utf-8")

    (inv / "05_Final.md").write_text(
        "---\n"
        'article_title: "W98 Display Headline"\n'
        "publish_date: \"2026-06-01\"\n"
        "primary_keyword: test keyword\n"
        "word_count_target: \"1500\"\n"
        "cta_type: try_workcrew_free\n"
        "canonical_url: https://workcrew.com/blog/test\n"
        "seo_status: Approved\n"
        "---\n\n"
        "# Title\n\n## FAQ\n\nx\n",
        encoding="utf-8",
    )

    row = sheet_sync.compose_sheet_row(
        {
            "content_id": "W98",
            "title": "M1/Wk8",
            "status": "QA Passed",
            "qa_status": "PASS",
            "current_step": "Done",
            "next_step": "None",
            "draft_path": "",
            "qa_output_path": "",
            "final_output_path": "",
        },
        tmp_path,
    )
    assert row["Publish Date"] == "2026-06-01"
    assert row["Title"] == "W98 Display Headline"
    assert row["Month/Week"] == "M1/Wk8"
    assert row["Target Keyword"] == "test keyword"
    assert row["Word Count"] == "1500"
    assert row["Brief Done"] == "Y"
    assert row["Assets Done"] == "Y"
    assert row["SEO Final"] == "Approved"
    assert row["CTA"] == "try_workcrew_free"
    assert row["Published URL"].startswith("https://")
