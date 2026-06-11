"""Build temporary runtime JSON so validators can run against staged Phase 2A / 2B paths."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.tools.runtime_paths import REPO_ROOT, RUNTIME_CONFIG_PATH


def warn_if_staging_week_mismatch(staging_root: str, week_id: str) -> None:
    """Emit stderr warning when folder basename does not match tracker week (catches wrong bundle)."""
    tail = Path(staging_root.strip().rstrip("/")).name.upper()
    wid = week_id.strip().upper()
    if tail != wid:
        print(
            f"WARNING: staging path ends with `{tail}` but week id is `{wid}`. "
            "Confirm --staging-root matches the intended content bundle.",
            file=sys.stderr,
        )


def build_phase2a_overlay_paths(
    staging_root: str,
    week_id: str,
) -> dict:
    """
    Merge canonical runtime with Phase 2A staging paths for draft/research/SEO.

    `staging_root` is repo-relative (e.g. output/generated/W05).
    QA reports go under output/qa_reports/staging/ so promotion validation does not
    overwrite canonical gate reports.
    """
    base = json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8"))
    root = staging_root.strip().rstrip("/")
    wid = week_id.strip().upper()

    base["active_week"] = wid
    base["draft_path"] = f"{root}/04_Draft.md"
    base["research_path"] = f"{root}/03_Research.md"
    base["seo_plan_path"] = f"{root}/02_SEO_Plan.md"
    base["qa_output_dir"] = "output/qa_reports/staging/"
    # Writer output is article-shaped; canonical runtime often defaults to template mode for CMS shells.
    base["draft_validation_mode"] = "article"
    base.setdefault("draft_article_min_words", 900)
    return base


def write_phase2a_overlay_file(staging_root: str, week_id: str, dest: Path | None = None) -> Path:
    """Write overlay JSON under output/.staging_runtime/ unless dest is provided."""
    cfg = build_phase2a_overlay_paths(staging_root, week_id)
    out = dest or (REPO_ROOT / "output" / ".staging_runtime" / f"{week_id.upper()}_phase2a.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return out


def build_phase2b_overlay_paths(staging_root: str, week_id: str) -> dict:
    """
    Overlay for Phase 2B: staged `05_Final.md` plus 01–04 paths for consistency.

    Structure + metadata validators read `final_path`; QA reports under staging/.
    """
    base = json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8"))
    root = staging_root.strip().rstrip("/")
    wid = week_id.strip().upper()

    base["active_week"] = wid
    base["draft_path"] = f"{root}/04_Draft.md"
    base["research_path"] = f"{root}/03_Research.md"
    base["seo_plan_path"] = f"{root}/02_SEO_Plan.md"
    base["final_path"] = f"{root}/05_Final.md"
    base["qa_output_dir"] = "output/qa_reports/staging/"
    return base


def write_phase2b_overlay_file(staging_root: str, week_id: str, dest: Path | None = None) -> Path:
    cfg = build_phase2b_overlay_paths(staging_root, week_id)
    out = dest or (REPO_ROOT / "output" / ".staging_runtime" / f"{week_id.upper()}_phase2b.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return out


def build_phase3_overlay_paths(staging_root: str, week_id: str) -> dict:
    """
    Phase 3 distribution validation: same article paths as 2B plus `distribution_staging_root`
    so checklist / bundle checks resolve `06`–`09` under staging (not only canonical input/).
    """
    base = build_phase2b_overlay_paths(staging_root, week_id)
    root = staging_root.strip().rstrip("/")
    base["distribution_staging_root"] = root
    return base


def write_phase3_overlay_file(staging_root: str, week_id: str, dest: Path | None = None) -> Path:
    cfg = build_phase3_overlay_paths(staging_root, week_id)
    out = dest or (REPO_ROOT / "output" / ".staging_runtime" / f"{week_id.upper()}_phase3.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return out


# Validators that apply to Phase 2A artifacts only (01–04). Not final or checklist.
PHASE2A_PROMOTION_VALIDATORS: tuple[str, ...] = (
    "research_mapper",
    "draft_validator",
)

# Phase 2B: staged article final before canonical promotion.
PHASE2B_PROMOTION_VALIDATORS: tuple[str, ...] = (
    "structure_checker",
    "metadata_checker",
)
