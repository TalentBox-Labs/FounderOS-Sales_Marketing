"""Staging overlay paths for Phase 2A promotion."""

from __future__ import annotations

from src.tools.staging_overlay import (
    PHASE2A_PROMOTION_VALIDATORS,
    build_phase2a_overlay_paths,
)


def test_overlay_paths_point_at_staging():
    cfg = build_phase2a_overlay_paths("output/generated/W05", "W05")
    assert cfg["draft_path"] == "output/generated/W05/04_Draft.md"
    assert cfg["research_path"] == "output/generated/W05/03_Research.md"
    assert cfg["seo_plan_path"] == "output/generated/W05/02_SEO_Plan.md"
    assert cfg["qa_output_dir"] == "output/qa_reports/staging/"
    assert cfg["active_week"] == "W05"
    assert cfg["draft_validation_mode"] == "article"
    assert cfg.get("draft_article_min_words") == 900


def test_phase2a_validator_list():
    assert "research_mapper" in PHASE2A_PROMOTION_VALIDATORS
    assert "draft_validator" in PHASE2A_PROMOTION_VALIDATORS
