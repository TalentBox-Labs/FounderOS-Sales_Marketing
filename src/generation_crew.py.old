"""
Phase 2A — Strategist → SEO → Research → Writer.

Writes 01–04 markdown only; does not edit runtime_config.json or tracker.csv.
Paths come from the active tracker row (same week as runtime active_week).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task

from src.crew import BASE_DIR, build_crew_llm, load_yaml, read_file, save_file
from src.tools.csv_reader import get_active_content
from src.tools.runtime_paths import load_runtime_config
from src.tools.staging_overlay import warn_if_staging_week_mismatch


def _week_paths_from_draft(draft_path: str) -> dict[str, str]:
    root = Path(draft_path).parent
    return {
        "brief": str(root / "01_Content_Brief.md"),
        "seo": str(root / "02_SEO_Plan.md"),
        "research": str(root / "03_Research.md"),
        "draft": str(root / "04_Draft.md"),
        "seed": str(root / "00_Generation_Seed.md"),
    }


def _artifact_paths_for_run(
    active: dict,
    output_root: str | None,
) -> dict[str, str]:
    """
    Default: write under input/WXX/ next to `draft_path`.
    If `output_root` is set, write 01–04 under that folder only (keeps validated input/ intact).
    Seed is always read from the real week folder beside `draft_path`.
    """
    base = _week_paths_from_draft(active["draft_path"])
    if not output_root:
        return base
    out = Path(output_root)
    return {
        "brief": str(out / "01_Content_Brief.md"),
        "seo": str(out / "02_SEO_Plan.md"),
        "research": str(out / "03_Research.md"),
        "draft": str(out / "04_Draft.md"),
        "seed": base["seed"],
    }


def _maybe_backup(repo_relative_path: str) -> None:
    if os.environ.get("WORKCREW_GENERATION_BACKUP", "1").lower() in (
        "0",
        "false",
        "no",
    ):
        return
    full = BASE_DIR / repo_relative_path
    if not full.is_file():
        return
    bak = full.with_suffix(full.suffix + ".bak")
    shutil.copy2(full, bak)
    print(f"Backed up -> {bak.relative_to(BASE_DIR)}", file=sys.stderr)


def _load_optional_seed(seed_path: str) -> str:
    full = BASE_DIR / seed_path
    if not full.is_file():
        return ""
    return full.read_text(encoding="utf-8").strip()


def _run_single_task(
    *,
    agent_cfg: dict,
    description: str,
    expected_output: str,
    llm,
) -> str:
    agent = Agent(
        config=agent_cfg,
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
    task = Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    return str(crew.kickoff())


def _direct_input_write_allowed() -> bool:
    return os.environ.get("WORKCREW_ALLOW_DIRECT_INPUT_WRITE", "").lower() in (
        "1",
        "true",
        "yes",
    )


def run_phase_2a_chain(
    content_id: str | None = None,
    output_root: str | None = None,
) -> dict[str, str]:
    """
    Run Strategist → SEO → Research → Writer for one week.

    Returns mapping step_name -> output text (also written to disk).
    """
    if not output_root and not _direct_input_write_allowed():
        raise RuntimeError(
            "Refusing to write into input/WXX/: use --output-root (e.g. "
            "output/generated/W05) for staging generation, or set "
            "WORKCREW_ALLOW_DIRECT_INPUT_WRITE=1 only as an explicit escape hatch. "
            "See docs/Artifact_Promotion_PRD.md."
        )

    cfg_runtime = load_runtime_config()
    active = get_active_content(content_id)
    week = str(active["content_id"])
    paths = _artifact_paths_for_run(active, output_root)
    if output_root:
        print(
            f"Writing artifacts under {output_root} (input/ tree untouched).\n",
            file=sys.stderr,
        )
        warn_if_staging_week_mismatch(output_root, week)

    agents_y = load_yaml("src/agents_generation.yaml")
    tasks_y = load_yaml("src/tasks_generation.yaml")
    llm = build_crew_llm()

    seed_text = _load_optional_seed(paths["seed"])
    seed_block = (
        f"\n\n## Generation seed (optional)\n\n{seed_text}\n"
        if seed_text
        else "\n\n(No 00_Generation_Seed.md — infer topic from tracker title below.)\n"
    )

    meta = f"""Tracker metadata (read-only context):
- content_id: {active.get("content_id")}
- title label: {active.get("title")}
- current_step: {active.get("current_step")}
- next_step: {active.get("next_step")}
{seed_block}
"""

    results: dict[str, str] = {}

    # 1) Strategist
    desc_s = f"""{meta}
Produce the COMPLETE markdown body for `01_Content_Brief.md` for week {week}.

Hard rules:
- Output markdown ONLY — no preamble, no code fences around the whole file.
- Include these sections with headings (exact names): Brief Summary; Target Audience; Goal & CTA;
  Keyword & SEO Targets; Proposed Outline; Tone & Voice; Research Requirements; Internal Linking Plan.
- No fake metrics. Use `[TBD]` style placeholders when calendar dates or volumes are unknown.
- Do not claim human approval or publish readiness.

Begin the file with a single H1 title line appropriate for the article (after optional front matter if you use none — prefer starting with `# ...`).
"""
    _maybe_backup(paths["brief"])
    out_brief = _run_single_task(
        agent_cfg=agents_y["strategist_agent"],
        description=desc_s,
        expected_output=tasks_y["strategist_task"]["expected_output"],
        llm=llm,
    )
    save_file(paths["brief"], out_brief)
    results["brief"] = out_brief

    brief_src = read_file(paths["brief"])

    # 2) SEO
    desc_seo = f"""You have the approved brief below. Produce the COMPLETE markdown for `02_SEO_Plan.md`.

Hard rules:
- Markdown only; include sections with headings such as: URL slug; Title tag; Meta description;
  H1/H2 structure; Keyword map; Internal links; FAQ schema (outline); Open Graph metadata.
- No fabricated keyword volumes, Ahrefs scores, or ranking promises.

--- BEGIN BRIEF ---
{brief_src}
--- END BRIEF ---
"""
    _maybe_backup(paths["seo"])
    out_seo = _run_single_task(
        agent_cfg=agents_y["seo_agent"],
        description=desc_seo,
        expected_output=tasks_y["seo_task"]["expected_output"],
        llm=llm,
    )
    save_file(paths["seo"], out_seo)
    results["seo"] = out_seo

    seo_src = read_file(paths["seo"])

    # 3) Research
    desc_r = f"""Using the brief and SEO plan below, produce `03_Research.md`.

Hard rules:
- Markdown only. Include sections covering: pricing research (qualitative / placeholders ok);
  competitor comparison (no invented prices); feature validation; recruiter pain points; source references
  (name reputable categories — LinkedIn, Indeed, etc. — without fake URLs).
- Do not invent statistics or paste fictional URLs; describe source types only (e.g. “major job boards”) unless the brief supplies real links.

--- BEGIN BRIEF ---
{brief_src}
--- END BRIEF ---

--- BEGIN SEO PLAN ---
{seo_src}
--- END SEO PLAN ---
"""
    _maybe_backup(paths["research"])
    out_res = _run_single_task(
        agent_cfg=agents_y["research_agent"],
        description=desc_r,
        expected_output=tasks_y["research_task"]["expected_output"],
        llm=llm,
    )
    save_file(paths["research"], out_res)
    results["research"] = out_res

    res_src = read_file(paths["research"])

    # 4) Writer
    desc_w = f"""Write `04_Draft.md` using all prior artifacts.

Hard rules:
- Markdown article body suitable for WorkCrew (recruiter audience).
- Include H1, multiple H2 sections, an FAQ section, two CTA blocks using approved phrasing style from the brief (e.g. "Try WorkCrew free" where appropriate — never "sign up for free").
- Follow keyword / heading themes from the SEO plan without stuffing.
- No fake testimonials, metrics, or invented URLs; link only to placeholders like `[TBD]` if a real URL is required later.

--- BEGIN BRIEF ---
{brief_src}
--- END BRIEF ---

--- BEGIN SEO PLAN ---
{seo_src}
--- END SEO PLAN ---

--- BEGIN RESEARCH ---
{res_src}
--- END RESEARCH ---

Target length guidance: align with the brief word-count target if given; otherwise ~1,500–2,000 words.
"""
    _maybe_backup(paths["draft"])
    out_draft = _run_single_task(
        agent_cfg=agents_y["writer_agent"],
        description=desc_w,
        expected_output=tasks_y["writer_task"]["expected_output"],
        llm=llm,
    )
    save_file(paths["draft"], out_draft)
    results["draft"] = out_draft

    print(
        f"\nPhase 2A complete for {week}. "
        f"runtime active_week in config is still {cfg_runtime.get('active_week')} "
        "(unchanged by design).\n",
        file=sys.stderr,
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 2A — generate 01–04 from Strategist→Writer chain (Ollama/CrewAI)."
    )
    parser.add_argument(
        "--week",
        metavar="WXX",
        help="Optional content_id override (must exist in tracker.csv). "
        "Default: active_week from data/runtime_config.json.",
    )
    parser.add_argument(
        "--output-root",
        metavar="DIR",
        help="Repo-relative directory for 01–04 outputs (recommended). "
        "Omits overwriting input/WXX/ validated files.",
    )
    args = parser.parse_args()
    content_id = args.week.upper() if args.week else None
    try:
        run_phase_2a_chain(content_id=content_id, output_root=args.output_root)
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
