"""Phase 3 distribution crew using BaseCrew pattern."""

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


class DistributionCrew(BaseCrew):
    """Phase 3: Distribution crew for design, social, email, and publishing artifacts."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize distribution crew."""
        super().__init__(
            name="distribution",
            agents_yaml_path="src/agents_distribution.yaml",
            tasks_yaml_path="src/tasks_distribution.yaml",
            repo_root=repo_root,
        )
        self.content_id: str | None = None
        self.staging_root: str | None = None

    def build_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        """Build distribution crew agents and tasks."""
        active = get_active_content(self.content_id)
        wid = str(active["content_id"])
        sr = self.staging_root.strip().rstrip("/") if self.staging_root else ""

        final_rel = f"{sr}/05_Final.md"

        brief_rel = f"{sr}/01_Content_Brief.md"
        seo_rel = f"{sr}/02_SEO_Plan.md"
        brief_body = (
            self.read_file(brief_rel)
            if (self.repo_root / brief_rel).is_file()
            else "_No staged `01_Content_Brief.md` — infer tone only from the final article._\n"
        )
        seo_body = (
            self.read_file(seo_rel)
            if (self.repo_root / seo_rel).is_file()
            else "_No staged `02_SEO_Plan.md` — use keywords from the final article YAML._\n"
        )
        final_body = self.read_file(final_rel)

        # Create distribution agent
        dist_agent = Agent(
            config=self.agents_config.get("distribution_agent", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

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

        # Design brief task
        t_design = self.tasks_config.get("design_brief_task", {})
        design_task = Task(
            config=t_design,
            agent=dist_agent,
            description=f"{meta}\n\n{t_design.get('description', '')}",
        )

        # Social posts task (depends on design brief)
        t_social = self.tasks_config.get("social_posts_task", {})
        social_task = Task(
            config=t_social,
            agent=dist_agent,
            description=f"""{meta}

## Prior output: design brief (reference only)
---
{self.read_file(f"{sr}/06_Design_Brief.md") if (self.repo_root / f"{sr}/06_Design_Brief.md").is_file() else ""}
---

{t_social.get('description', '')}
""",
        )

        # Email copy task (depends on social posts)
        t_email = self.tasks_config.get("email_copy_task", {})
        email_task = Task(
            config=t_email,
            agent=dist_agent,
            description=f"""{meta}

## Prior: social plan (reference)
---
{self.read_file(f"{sr}/07_Social_Posts.md")[:12_000] if (self.repo_root / f"{sr}/07_Social_Posts.md").is_file() else ""}
---

{t_email.get('description', '')}
""",
        )

        # Publish checklist task (depends on email copy)
        t_checklist = self.tasks_config.get("publish_checklist_task", {})
        checklist_task = Task(
            config=t_checklist,
            agent=dist_agent,
            description=f"""{meta}

## Prior: email copy excerpt (reference)
---
{self.read_file(f"{sr}/08_Email_Copy.md")[:8_000] if (self.repo_root / f"{sr}/08_Email_Copy.md").is_file() else ""}
---

{t_checklist.get('description', '')}
""",
        )

        return [dist_agent], [design_task, social_task, email_task, checklist_task]

    def validate_output(self, output: str) -> tuple[bool, list[str]]:
        """Validate distribution output."""
        errors = []
        if not output or len(output.strip()) < 50:
            errors.append("Distribution output is too short")
        return len(errors) == 0, errors

    def run_phase_3_distribution(
        self,
        staging_root: str,
        content_id: str | None = None,
    ) -> dict[str, str]:
        """
        Run distribution crew and save staged 06–09 markdown files.

        Args:
            staging_root: Staging directory path (repo-relative)
            content_id: Content ID (defaults to active from tracker)

        Returns:
            Mapping of artifact_number → output text (06–09)
        """
        self._staging_guard(staging_root)
        self.content_id = content_id
        self.staging_root = staging_root

        active = get_active_content(content_id)
        wid = str(active["content_id"])
        sr = staging_root.strip().rstrip("/")
        warn_if_staging_week_mismatch(sr, wid)

        final_rel = f"{sr}/05_Final.md"
        if not (self.repo_root / final_rel).is_file():
            raise FileNotFoundError(f"Required {final_rel} not found")

        result_text = self.run()

        # Save distribution artifacts (6 Design Brief, 7 Social, 8 Email, 9 Checklist)
        self.save_file(f"{sr}/06_Design_Brief.md", result_text)
        self.save_file(f"{sr}/07_Social_Posts.md", result_text)
        self.save_file(f"{sr}/08_Email_Copy.md", result_text)
        self.save_file(f"{sr}/09_Publish_Checklist.md", result_text)

        results = {
            "06": result_text,
            "07": result_text,
            "08": result_text,
            "09": result_text,
        }

        logger.info(
            "Wrote phase 3 distribution artifacts",
            extra={"staging_root": sr, "week": wid},
        )

        return results

    @staticmethod
    def _staging_guard(staging_root: str) -> None:
        """Validate that staging_root is outside input/."""
        norm = staging_root.strip().rstrip("/").replace("\\", "/")
        if norm.startswith("input/") or norm == "input" or "/input/" in f"/{norm}/":
            raise RuntimeError(
                "Phase 3 distribution must write to a staging directory outside input/, "
                "e.g. output/generated/W05. Use promote_staged --distribution-only for canonical."
            )


# ── Compatibility exports for tests ──────────────────────────────────────────

def _staging_guard(staging_root: str) -> None:
    """Backward compatibility export."""
    return DistributionCrew._staging_guard(staging_root)


if __name__ == "__main__":
    import argparse

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
        crew = DistributionCrew()
        results = crew.run_phase_3_distribution(args.staging_root, content_id=content_id)
        print("\n" + "=" * 80)
        print("DISTRIBUTION CREW RESULTS")
        print("=" * 80)
        for step in ["06", "07", "08", "09"]:
            print(f"\n{step.upper()}:\n{results.get(step, '')[:200]}...\n")
    except (RuntimeError, FileNotFoundError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)
