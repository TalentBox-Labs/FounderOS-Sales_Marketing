"""QA crew using BaseCrew pattern."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from crewai import Agent, Task

from src.base_crew import BaseCrew
from src.crew_contract import qa_report_contract_errors, qa_report_meets_contract
from src.tools.csv_reader import get_active_content
from src.tools.runtime_paths import load_runtime_config


class QACrew(BaseCrew):
    """Quality assurance crew for content validation."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize QA crew with standard configuration."""
        super().__init__(
            name="qa",
            agents_yaml_path="src/agents.yaml",
            tasks_yaml_path="src/tasks.yaml",
            repo_root=repo_root,
        )

    def build_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        """Build QA agent and task for content review."""
        active = get_active_content()
        runtime = load_runtime_config()

        # Resolve which markdown file to review
        raw = str(runtime.get("crewai_qa_source", "final")).strip().lower()
        if raw not in ("final", "draft"):
            raw = "final"

        draft_rel = (active.get("draft_path") or runtime.get("draft_path") or "").strip()
        final_rel = (runtime.get("final_path") or "").strip()

        # Determine source file
        if raw == "final" and final_rel:
            cand = self.repo_root / final_rel
            if cand.is_file() and cand.stat().st_size >= 80:
                article_body = self.read_file(final_rel)
                doc_label = f"publish candidate ({Path(final_rel).name})"
            elif draft_rel:
                article_body = self.read_file(draft_rel)
                doc_label = f"working draft ({Path(draft_rel).name}) — final missing/small"
                final_rel = ""
            else:
                raise ValueError("No draft or final path configured")
        elif raw == "draft" and draft_rel:
            article_body = self.read_file(draft_rel)
            doc_label = f"working draft ({Path(draft_rel).name})"
            final_rel = ""
        else:
            raise ValueError("crewai_qa_source misconfigured")

        # Create agent and task
        qa_agent = Agent(
            config=self.agents_config["qa_agent"],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        qa_task = Task(
            config=self.tasks_config["qa_review_task"],
            agent=qa_agent,
            description=f"""
Review this WorkCrew article for structured QA.

Document: {doc_label}
Repository path: {draft_rel if raw == 'draft' else final_rel}

Content ID: {active["content_id"]}
Week: {active.get("week", active["content_id"])}
Title: {active["title"]}
Current Step: {active["current_step"]}

Article markdown:
---
{article_body}
---

Hard failures (## Failed Checks ONLY for these):
- Quote a banned phrase that appears verbatim, OR
- Name a required section that is literally absent, OR
- Quote two identical full sentences (duplication).

If none apply, ## Failed Checks must contain only `- (none)`.

Important rules:
- Use ONLY visible text from the article.
- Never infer prior versions or estimate deleted words.
- For publish candidate (final), base assessment only on that file.
- Never estimate word counts.
- Put subjective notes in ## Observable Issues; hard breaches in ## Failed Checks.
- Use FAIL in ## Final Verdict only when ## Failed Checks is not empty and not just `(none)`.
- Output only the required QA structure.
""",
            expected_output=self.tasks_config["qa_review_task"]["expected_output"],
        )

        return [qa_agent], [qa_task]

    def validate_output(self, output: str) -> tuple[bool, list[str]]:
        """Validate QA output against contract."""
        errors = qa_report_contract_errors(output)
        is_valid = len(errors) == 0
        return is_valid, errors

    def run_qa_agent(self, output_path: str | None = None) -> str:
        """
        Run QA crew and save results.

        Args:
            output_path: Optional path to save output (relative to repo root)

        Returns:
            QA report markdown
        """
        result_text = self.run()

        # Save output
        active = get_active_content()
        target = output_path or active.get("qa_output_path", "output/qa_reports/qa_report.md")
        self.save_file(target, result_text)

        return result_text


if __name__ == "__main__":
    crew = QACrew()
    result = crew.run_qa_agent()
    print("\n" + "=" * 80)
    print(result)
    print("=" * 80)
