"""
Phase 2A — Strategist → SEO → Research → Writer (staged `01`–`04` only).

Writes under ``--staging-root`` (e.g. ``output/generated/W09A``); never writes under ``input/``.
Does not modify ``tracker.csv`` or ``data/runtime_config.json`` (PRD hard boundary).

Suggested flow after a successful run:
``python -m src.tools.validate_staged <staging-root> --week WXX --phase 2a``,
then Phase 2B: ``python -m src.editor_crew --staging-root … --week WXX`` (requires staged ``04_Draft.md`` and QA reports for best results).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crewai import Agent, Crew, Process, Task

from src.crew import BASE_DIR, build_crew_llm, load_yaml, read_file, save_file
from src.editor_crew import _maybe_strip_outer_fence
from src.tools.csv_reader import get_active_content
from src.tools.staging_overlay import warn_if_staging_week_mismatch


def _staging_guard(staging_root: str) -> None:
    norm = staging_root.strip().rstrip("/").replace("\\", "/")
    if norm.startswith("input/") or norm == "input" or "/input/" in f"/{norm}/":
        raise RuntimeError(
            "Phase 2A artifact crew must write to a staging directory outside input/, "
            "e.g. output/generated/W09A. Never target canonical input/ directly."
        )


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


def _week_runtime_excerpt(week_id: str, *, max_chars: int = 12_000) -> str:
    p = BASE_DIR / "data" / "week_runtime" / f"{week_id.upper()}.json"
    if not p.is_file():
        return f"_No `data/week_runtime/{week_id.upper()}.json` — use tracker context only._\n"
    raw = p.read_text(encoding="utf-8")
    if len(raw) > max_chars:
        return raw[:max_chars] + "\n\n... [truncated]\n"
    return raw


def run_phase_2a_artifacts(
    staging_root: str,
    content_id: str | None = None,
) -> dict[str, str]:
    """
    Generate ``01_Content_Brief.md`` … ``04_Draft.md`` under ``staging_root``.

    Returns map of relative path → absolute path written.
    """
    _staging_guard(staging_root)

    active = get_active_content(content_id)
    wid = str(active["content_id"]).upper()
    sr = staging_root.strip().rstrip("/")
    warn_if_staging_week_mismatch(sr, wid)

    agents_y = load_yaml("src/agents_phase2a.yaml")
    tasks_y = load_yaml("src/tasks_phase2a.yaml")
    llm = build_crew_llm()

    rt_excerpt = _week_runtime_excerpt(wid)
    t_strat = tasks_y["strategist_brief_task"]
    desc_brief = f"""{t_strat.get("description", "").strip()}

## Tracker row (read-only)
- content_id: {wid}
- title: {active.get("title")}
- current_step: {active.get("current_step")}
- next_step: {active.get("next_step")}

## Week runtime JSON (read-only; research_gate / validators)
{rt_excerpt}

Instructions:
- Output markdown only. Start with `# Content Brief — {wid}`.
- No fabricated statistics; say "source needed" where evidence is missing.
- Do not mention tracker edits or runtime changes.
"""
    brief_raw = _run_single_task(
        agent_cfg=agents_y["strategist_agent"],
        description=desc_brief,
        expected_output=t_strat["expected_output"],
        llm=llm,
    )
    brief_path = f"{sr}/01_Content_Brief.md"
    save_file(brief_path, _maybe_strip_outer_fence(brief_raw))

    brief_body = read_file(brief_path)
    t_seo = tasks_y["seo_plan_task"]
    desc_seo = f"""{t_seo.get("description", "").strip()}

## Staged content brief
---
{brief_body}
---

Instructions:
- Output markdown only. Start with `# SEO Plan — {wid}`.
- Include the literal gate substrings required by WorkCrew validators: meta description, title tag,
  canonical, h1 tag, frequently asked questions, plus the primary keyword phrase in prose.
- Include a CTA line with try workcrew / try workcrew free / explore workcrew / create your workcrew profile.
"""
    seo_raw = _run_single_task(
        agent_cfg=agents_y["seo_agent"],
        description=desc_seo,
        expected_output=t_seo["expected_output"],
        llm=llm,
    )
    seo_path = f"{sr}/02_SEO_Plan.md"
    save_file(seo_path, _maybe_strip_outer_fence(seo_raw))

    seo_body = read_file(seo_path)
    t_res = tasks_y["research_task"]
    desc_res = f"""{t_res.get("description", "").strip()}

## Staged content brief
---
{brief_body}
---

## Staged SEO plan
---
{seo_body}
---

Instructions:
- Output markdown only. Start with `# Research — {wid}`.
- Use "## Themes for Writer" with subsections; weave in research_gate keywords from JSON when relevant.
- No invented percentages.
"""
    res_raw = _run_single_task(
        agent_cfg=agents_y["research_agent"],
        description=desc_res,
        expected_output=t_res["expected_output"],
        llm=llm,
    )
    research_path = f"{sr}/03_Research.md"
    save_file(research_path, _maybe_strip_outer_fence(res_raw))

    research_body = read_file(research_path)
    t_wr = tasks_y["writer_draft_task"]
    desc_wr = f"""{t_wr.get("description", "").strip()}

## Staged content brief
---
{brief_body}
---

## Staged SEO plan
---
{seo_body}
---

## Staged research
---
{research_body}
---

Instructions:
- Output markdown only. Follow the exact template headings in expected_output.
- week_id in headings must be {wid}.
- Primary keyword for SEO Execution Rules must match the SEO plan primary keyword.
- Internal linking table: include rows with canonical URLs when known from the SEO plan or brief.
"""
    draft_raw = _run_single_task(
        agent_cfg=agents_y["writer_agent"],
        description=desc_wr,
        expected_output=t_wr["expected_output"],
        llm=llm,
    )
    draft_path = f"{sr}/04_Draft.md"
    save_file(draft_path, _maybe_strip_outer_fence(draft_raw))

    written = {
        brief_path: str(BASE_DIR / brief_path),
        seo_path: str(BASE_DIR / seo_path),
        research_path: str(BASE_DIR / research_path),
        draft_path: str(BASE_DIR / draft_path),
    }
    print(
        "\nPhase 2A artifact crew wrote:\n  "
        + "\n  ".join(written.keys())
        + "\n\nNext: python -m src.tools.validate_staged "
        f"{sr} --week {wid} --phase 2a\n"
        f"Then Phase 2B: python -m src.editor_crew --staging-root {sr} --week {wid}\n",
        file=sys.stderr,
    )
    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 2A — generate staged 01–04 markdown via Strategist→Writer crew (CrewAI)."
    )
    parser.add_argument(
        "--staging-root",
        required=True,
        metavar="DIR",
        help="Repo-relative staging dir (e.g. output/generated/W09A). Created implicitly on write.",
    )
    parser.add_argument(
        "--week",
        metavar="WXX",
        help="Tracker content_id; defaults to active_week from runtime config.",
    )
    args = parser.parse_args()
    content_id = args.week.upper() if args.week else None
    try:
        Path(BASE_DIR / args.staging_root.strip().rstrip("/")).mkdir(parents=True, exist_ok=True)
        run_phase_2a_artifacts(args.staging_root, content_id=content_id)
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)
    except (OSError, ValueError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
