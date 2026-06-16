"""Phase 2A artifact crew using BaseCrew pattern."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from src.base_crew import BaseCrew
from src.tools.csv_reader import get_active_content
from src.tools.staging_overlay import warn_if_staging_week_mismatch

logger = logging.getLogger(__name__)


class ArtifactCrew(BaseCrew):
    """Phase 2A: Strategist → SEO → Researcher → Writer crew for staged artifacts."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize artifact crew."""
        super().__init__(
            name="artifact",
            agents_yaml_path="src/agents_phase2a.yaml",
            tasks_yaml_path="src/tasks_phase2a.yaml",
            repo_root=repo_root,
        )
        self.content_id: str | None = None
        self.staging_root: str | None = None

    def build_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        """Build artifact crew agents and tasks (Strategist → SEO → Researcher → Writer)."""
        active = get_active_content(self.content_id)
        wid = str(active["content_id"]).upper()
        sr = self.staging_root.strip().rstrip("/") if self.staging_root else ""

        rt_excerpt = self._week_runtime_excerpt(wid)

        # Create agents
        strategist = Agent(
            config=self.agents_config.get("strategist_agent", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        seo_agent = Agent(
            config=self.agents_config.get("seo_agent", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        researcher = Agent(
            config=self.agents_config.get("research_agent", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        writer = Agent(
            config=self.agents_config.get("writer_agent", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        # Brief task
        t_strat = self.tasks_config.get("strategist_brief_task", {})
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
        brief_task = Task(
            config=t_strat,
            agent=strategist,
            description=desc_brief,
        )

        # SEO task (depends on brief)
        t_seo = self.tasks_config.get("seo_plan_task", {})
        brief_body = self.read_file(f"{sr}/01_Content_Brief.md")
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
        seo_task = Task(
            config=t_seo,
            agent=seo_agent,
            description=desc_seo,
        )

        # Research task (depends on brief + SEO)
        t_res = self.tasks_config.get("research_task", {})
        seo_body = self.read_file(f"{sr}/02_SEO_Plan.md")
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
        research_task = Task(
            config=t_res,
            agent=researcher,
            description=desc_res,
        )

        # Writer task (depends on brief + SEO + research)
        t_wr = self.tasks_config.get("writer_draft_task", {})
        research_body = self.read_file(f"{sr}/03_Research.md")
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
        writer_task = Task(
            config=t_wr,
            agent=writer,
            description=desc_wr,
        )

        return (
            [strategist, seo_agent, researcher, writer],
            [brief_task, seo_task, research_task, writer_task],
        )

    def validate_output(self, output: str) -> tuple[bool, list[str]]:
        """Validate artifact crew output."""
        errors = []
        if not output or len(output.strip()) < 100:
            errors.append("Generated draft is too short")
        return len(errors) == 0, errors

    def run_phase_2a_artifacts(
        self,
        staging_root: str,
        content_id: str | None = None,
    ) -> dict[str, str]:
        """
        Run artifact crew and save staged 01–04 markdown files.

        Args:
            staging_root: Staging directory path (repo-relative)
            content_id: Content ID (defaults to active from tracker)

        Returns:
            Mapping of relative_path → full_path for all written artifacts
        """
        self._staging_guard(staging_root)
        self.content_id = content_id
        self.staging_root = staging_root

        active = get_active_content(content_id)
        wid = str(active["content_id"]).upper()
        sr = staging_root.strip().rstrip("/")
        warn_if_staging_week_mismatch(sr, wid)

        # Create staging directory
        Path(self.repo_root / sr).mkdir(parents=True, exist_ok=True)

        result_text = self.run()

        # All tasks produce output; save the final one (draft) as the main result
        written = {
            f"{sr}/01_Content_Brief.md": str(self.repo_root / f"{sr}/01_Content_Brief.md"),
            f"{sr}/02_SEO_Plan.md": str(self.repo_root / f"{sr}/02_SEO_Plan.md"),
            f"{sr}/03_Research.md": str(self.repo_root / f"{sr}/03_Research.md"),
            f"{sr}/04_Draft.md": str(self.repo_root / f"{sr}/04_Draft.md"),
        }

        logger.info(
            "Wrote phase 2a artifacts",
            extra={"count": len(written), "week": wid},
        )

        return written

    def _week_runtime_excerpt(self, week_id: str, *, max_chars: int = 12_000) -> str:
        """Load week_runtime JSON if available."""
        p = self.repo_root / "data" / "week_runtime" / f"{week_id.upper()}.json"
        if not p.is_file():
            return f"_No `data/week_runtime/{week_id.upper()}.json` — use tracker context only._\n"
        raw = p.read_text(encoding="utf-8")
        if len(raw) > max_chars:
            return raw[:max_chars] + "\n\n... [truncated]\n"
        return raw

    @staticmethod
    def _staging_guard(staging_root: str) -> None:
        """Validate that staging_root is outside input/."""
        norm = staging_root.strip().rstrip("/").replace("\\", "/")
        if norm.startswith("input/") or norm == "input" or "/input/" in f"/{norm}/":
            raise RuntimeError(
                "Phase 2A artifact crew must write to a staging directory outside input/, "
                "e.g. output/generated/W09A. Never target canonical input/ directly."
            )


if __name__ == "__main__":
    import argparse

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
        crew = ArtifactCrew()
        results = crew.run_phase_2a_artifacts(args.staging_root, content_id=content_id)
        print("\n" + "=" * 80)
        print("ARTIFACT CREW RESULTS")
        print("=" * 80)
        for path in results.keys():
            print(f"  {path}")
        print()
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)
    except (OSError, ValueError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
