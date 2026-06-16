"""
Phase 3 — Distribution agent: staged `06`–`09` markdown only.

Reads staged `05_Final.md` (+ optional brief/SEO). Writes under `--staging-root`; never writes to input/.
Does not modify tracker or runtime config.
"""

from __future__ import annotations

import argparse
import sys

from crewai import Agent, Crew, Process, Task

from src.crew import BASE_DIR, build_crew_llm, load_yaml, read_file, save_file
from src.editor_crew import _maybe_strip_outer_fence
from src.tools.csv_reader import get_active_content
from src.tools.staging_overlay import warn_if_staging_week_mismatch


def _staging_guard(staging_root: str) -> None:
    norm = staging_root.strip().rstrip("/").replace("\\", "/")
    if norm.startswith("input/") or norm == "input" or "/input/" in f"/{norm}/":
        raise RuntimeError(
            "Phase 3 distribution must write to a staging directory outside input/, "
            "e.g. output/generated/W05. Use promote_staged --distribution-only for canonical."
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


def run_phase_3_distribution(
    staging_root: str,
    content_id: str | None = None,
) -> dict[str, str]:
    """
    Generate `06_Design_Brief.md` … `09_Publish_Checklist.md` under staging_root.

    Requires `{staging_root}/05_Final.md`. Uses brief/SEO from staging when present.
    """
    _staging_guard(staging_root)

    active = get_active_content(content_id)
    wid = str(active["content_id"])
    sr = staging_root.strip().rstrip("/")
    warn_if_staging_week_mismatch(sr, wid)

    final_rel = f"{sr}/05_Final.md"

    brief_rel = f"{sr}/01_Content_Brief.md"
    seo_rel = f"{sr}/02_SEO_Plan.md"
    brief_body = (
        read_file(brief_rel)
        if (BASE_DIR / brief_rel).is_file()
        else "_No staged `01_Content_Brief.md` — infer tone only from the final article._\n"
    )
    seo_body = (
        read_file(seo_rel)
        if (BASE_DIR / seo_rel).is_file()
        else "_No staged `02_SEO_Plan.md` — use keywords from the final article YAML._\n"
    )
    final_body = read_file(final_rel)

    agents_y = load_yaml("src/agents_distribution.yaml")
    tasks_y = load_yaml("src/tasks_distribution.yaml")
    llm = build_crew_llm()
    agent_cfg = agents_y["distribution_agent"]

    meta = f"""## Week context (read-only)
- content_id: {wid}
- title label: {active.get("title")}
- current_step: {active.get("current_step")}

## Staged final article (`05_Final.md`)
---
{final_body}
---

## Staged content brief (`01_Content_Brief.md`) — optional
---
{brief_body}
---

## Staged SEO plan (`02_SEO_Plan.md`) — optional
---
{seo_body}
---

Hard rules for all outputs:
- Markdown only for each file; no preamble before the first heading.
- Do not invent statistics, testimonials, or URLs not grounded in the article/brief.
- Preserve WorkCrew CTA voice ("Try WorkCrew free" style — never "sign up for free").
"""

    results: dict[str, str] = {}

    # 1) Design brief
    out = _run_single_task(
        agent_cfg=agent_cfg,
        description=f"{meta}\n\n{tasks_y['design_brief_task']['description']}",
        expected_output=tasks_y["design_brief_task"]["expected_output"],
        llm=llm,
    )
    save_file(f"{sr}/06_Design_Brief.md", _maybe_strip_outer_fence(out))
    results["06"] = out

    design_src = read_file(f"{sr}/06_Design_Brief.md")

    # 2) Social
    out = _run_single_task(
        agent_cfg=agent_cfg,
        description=f"""{meta}

## Prior output: design brief (reference only)
---
{design_src}
---

{tasks_y["social_posts_task"]["description"]}
""",
        expected_output=tasks_y["social_posts_task"]["expected_output"],
        llm=llm,
    )
    save_file(f"{sr}/07_Social_Posts.md", _maybe_strip_outer_fence(out))
    results["07"] = out

    social_src = read_file(f"{sr}/07_Social_Posts.md")

    # 3) Email
    out = _run_single_task(
        agent_cfg=agent_cfg,
        description=f"""{meta}

## Prior: social plan (reference)
---
{social_src[:12_000]}
---

{tasks_y["email_copy_task"]["description"]}
""",
        expected_output=tasks_y["email_copy_task"]["expected_output"],
        llm=llm,
    )
    save_file(f"{sr}/08_Email_Copy.md", _maybe_strip_outer_fence(out))
    results["08"] = out

    email_src = read_file(f"{sr}/08_Email_Copy.md")

    # 4) Publish checklist
    out = _run_single_task(
        agent_cfg=agent_cfg,
        description=f"""{meta}

## Prior: email copy excerpt (reference)
---
{email_src[:8_000]}
---

{tasks_y["publish_checklist_task"]["description"]}
""",
        expected_output=tasks_y["publish_checklist_task"]["expected_output"],
        llm=llm,
    )
    save_file(f"{sr}/09_Publish_Checklist.md", _maybe_strip_outer_fence(out))
    results["09"] = out

    print(
        f"\nPhase 3 distribution wrote 06–09 under {sr}/\n"
        f"Next: python -m src.tools.validate_staged {sr} --week {wid} --phase 3\n",
        file=sys.stderr,
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 3 — generate staged 06–09 distribution markdown (CrewAI)."
    )
    parser.add_argument(
        "--staging-root",
        required=True,
        metavar="DIR",
        help="Repo-relative staging dir containing 05_Final.md (e.g. output/generated/W05).",
    )
    parser.add_argument(
        "--week",
        metavar="WXX",
        help="Tracker content_id; defaults to active_week from runtime config.",
    )
    args = parser.parse_args()
    content_id = args.week.upper() if args.week else None
    try:
        run_phase_3_distribution(args.staging_root, content_id=content_id)
    except (RuntimeError, FileNotFoundError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
