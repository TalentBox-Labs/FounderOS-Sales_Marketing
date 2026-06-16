"""Phase 2A generation crew using BaseCrew pattern."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from crewai import Agent, Process, Task

from src.base_crew import BaseCrew
from src.tools.csv_reader import get_active_content
from src.tools.runtime_paths import load_runtime_config
from src.tools.staging_overlay import warn_if_staging_week_mismatch

logger = logging.getLogger(__name__)


class GenerationCrew(BaseCrew):
    """Phase 2A: Strategist → SEO → Research → Writer crew."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize generation crew."""
        super().__init__(
            name="generation",
            agents_yaml_path="src/agents_generation.yaml",
            tasks_yaml_path="src/tasks_generation.yaml",
            repo_root=repo_root,
        )
        self.output_root: str | None = None
        self.content_id: str | None = None
        self.active: dict[str, Any] = {}
        self.paths: dict[str, str] = {}

    def build_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        """Build generation crew agents and tasks."""
        # Load content and paths
        self.active = get_active_content(self.content_id)
        week = str(self.active["content_id"])
        self.paths = self._artifact_paths_for_run(self.active, self.output_root)

        if self.output_root:
            logger.info(
                f"Generation artifacts → {self.output_root}",
                extra={"week": week, "output_root": self.output_root},
            )
            warn_if_staging_week_mismatch(self.output_root, week)

        # Load optional seed
        seed_text = self._load_optional_seed(self.paths["seed"])
        seed_block = (
            f"\n\n## Generation seed (optional)\n\n{seed_text}\n" if seed_text else ""
        )

        # Create agents
        strategist = Agent(
            config=self.agents_config.get("strategist", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        seo_specialist = Agent(
            config=self.agents_config.get("seo_specialist", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        researcher = Agent(
            config=self.agents_config.get("researcher", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )
        writer = Agent(
            config=self.agents_config.get("writer", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        # Create tasks
        strategist_task = Task(
            config=self.tasks_config.get("strategist_brief", {}),
            agent=strategist,
            description=f"""Create content brief for: {self.active.get("title", "")}\n{seed_block}""",
        )

        seo_task = Task(
            config=self.tasks_config.get("seo_plan", {}),
            agent=seo_specialist,
            description=f"""Plan SEO for: {self.active.get("title", "")}\n{seed_block}""",
        )

        research_task = Task(
            config=self.tasks_config.get("research", {}),
            agent=researcher,
            description=f"""Research topic: {self.active.get("title", "")}\n{seed_block}""",
        )

        writer_task = Task(
            config=self.tasks_config.get("writer", {}),
            agent=writer,
            description=f"""Write draft for: {self.active.get("title", "")}\n{seed_block}""",
        )

        return (
            [strategist, seo_specialist, researcher, writer],
            [strategist_task, seo_task, research_task, writer_task],
        )

    def validate_output(self, output: str) -> tuple[bool, list[str]]:
        """Validate generation output."""
        # Generation crew output is valid if it contains content
        errors = []
        if not output or len(output.strip()) < 100:
            errors.append("Generated content is too short")
        return len(errors) == 0, errors

    def run_generation(
        self,
        content_id: str | None = None,
        output_root: str | None = None,
        write_direct: bool = False,
    ) -> dict[str, str]:
        """
        Run generation crew and save artifacts.

        Args:
            content_id: Content ID to generate (defaults to active from tracker)
            output_root: Output directory for generated files
            write_direct: If True, write directly to input/ (requires env var)

        Returns:
            Mapping of step_name -> output text
        """
        self.content_id = content_id
        self.output_root = output_root

        # Validate write permissions
        if not output_root and not write_direct:
            raise RuntimeError(
                "Refusing to write into input/WXX/: use output_root or set "
                "WORKCREW_ALLOW_DIRECT_INPUT_WRITE=1"
            )

        # Run the crew
        result_text = self.run()

        # Save artifacts
        steps = [
            ("brief", self.paths["brief"]),
            ("seo", self.paths["seo"]),
            ("research", self.paths["research"]),
            ("draft", self.paths["draft"]),
        ]

        results = {}
        for step_name, output_path in steps:
            # Back up existing file
            self._maybe_backup(output_path)
            # Save generated content
            self.save_file(output_path, result_text)
            results[step_name] = result_text

            logger.info(
                f"Saved {step_name}",
                extra={"path": output_path, "week": self.active.get("content_id")},
            )

        return results

    def _artifact_paths_for_run(
        self, active: dict[str, Any], output_root: str | None
    ) -> dict[str, str]:
        """Determine artifact paths for this run."""
        root = Path(active["draft_path"]).parent
        base = {
            "brief": str(root / "01_Content_Brief.md"),
            "seo": str(root / "02_SEO_Plan.md"),
            "research": str(root / "03_Research.md"),
            "draft": str(root / "04_Draft.md"),
            "seed": str(root / "00_Generation_Seed.md"),
        }

        if not output_root:
            return base

        out = Path(output_root)
        return {
            "brief": str(out / "01_Content_Brief.md"),
            "seo": str(out / "02_SEO_Plan.md"),
            "research": str(out / "03_Research.md"),
            "draft": str(out / "04_Draft.md"),
            "seed": base["seed"],  # Always read seed from original
        }

    def _maybe_backup(self, repo_relative_path: str) -> None:
        """Back up file if WORKCREW_GENERATION_BACKUP is enabled."""
        if os.environ.get("WORKCREW_GENERATION_BACKUP", "1").lower() in (
            "0",
            "false",
            "no",
        ):
            return
        full = self.repo_root / repo_relative_path
        if not full.is_file():
            return
        bak = full.with_suffix(full.suffix + ".bak")
        shutil.copy2(full, bak)
        logger.info(f"Backed up: {bak.relative_to(self.repo_root)}")

    def _load_optional_seed(self, seed_path: str) -> str:
        """Load optional generation seed file."""
        full = self.repo_root / seed_path
        if not full.is_file():
            return ""
        return full.read_text(encoding="utf-8").strip()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Phase 2A generation crew")
    parser.add_argument("topic", nargs="?", default=None, help="Content topic/ID")
    parser.add_argument(
        "--output-root",
        default=None,
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--write-direct",
        action="store_true",
        help="Write directly to input/ (requires WORKCREW_ALLOW_DIRECT_INPUT_WRITE)",
    )
    args = parser.parse_args()

    crew = GenerationCrew()
    results = crew.run_generation(
        content_id=args.topic,
        output_root=args.output_root,
        write_direct=args.write_direct,
    )

    print("\n" + "=" * 80)
    print("GENERATION CREW RESULTS")
    print("=" * 80)
    for step, content in results.items():
        print(f"\n{step.upper()}:\n{content[:200]}...\n")
