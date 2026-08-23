"""Phase 2B editor crew using BaseCrew pattern."""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

from crewai import Agent, Task

from src.base_crew import BaseCrew
from src.tools.csv_reader import get_active_content
from src.tools.staging_overlay import warn_if_staging_week_mismatch

logger = logging.getLogger(__name__)

_QA_MISSING_PREFIX = "_No matching"

_CANONICAL_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\*\*Canonical URL:\*\*\s*`([^`\n]+)`", re.IGNORECASE),
    re.compile(r"Canonical URL:\s*`([^`\n]+)`", re.IGNORECASE),
)


class EditorCrew(BaseCrew):
    """Phase 2B: Editor crew that refines `05_Final.md` from `04_Draft.md` + QA reports."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize editor crew."""
        super().__init__(
            name="editor",
            agents_yaml_path="src/agents_editor.yaml",
            tasks_yaml_path="src/tasks_editor.yaml",
            repo_root=repo_root,
        )
        self.content_id: str | None = None
        self.staging_root: str | None = None

    def build_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        """Build editor crew agents and tasks."""
        active = get_active_content(self.content_id)
        wid = str(active["content_id"])

        sr = self.staging_root.strip().rstrip("/") if self.staging_root else ""
        draft_rel = f"{sr}/04_Draft.md"

        draft_body = self.read_file(draft_rel)
        qa_blob = self._collect_validator_reports(wid)
        if qa_blob.strip().startswith(_QA_MISSING_PREFIX):
            logger.warning("Staging QA context missing; editor quality may be reduced")

        seo_hints = self._seo_canonical_section(sr)
        cta_hints = self._cta_type_hint_section()

        editor_agent = Agent(
            config=self.agents_config.get("editor_agent", {}),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

        task_cfg = self.tasks_config.get("editor_final_task", {})
        description = f"""{task_cfg.get("description", "").strip()}

## Week / tracker context
- content_id: {wid}
- title label: {active.get("title")}
- current_step: {active.get("current_step")}

## Full staged draft (`04_Draft.md`)
---
{draft_body}
---

## Validator and QA reports (use to fix issues; do not invent facts not supported here or in the draft)
---
{qa_blob}
---

{seo_hints}{cta_hints}Instructions:
- Output ONE markdown document only: YAML front matter then article body.
- Front matter values must satisfy metadata checker (no `[PLACEHOLDER]` brackets in values).
- Include required keys: week_id, article_title, primary_keyword, search_intent, funnel_stage,
  status, publish_status, canonical_url (https), cta_type (non-empty).
- Preserve structure required by structure checker (H1, H2s, FAQ section heading).
- Do not mention tooling as ranking guarantees; no fake URLs or statistics.
"""

        editor_task = Task(
            config=task_cfg,
            agent=editor_agent,
            description=description,
        )

        return [editor_agent], [editor_task]

    def validate_output(self, output: str) -> tuple[bool, list[str]]:
        """Validate editor output."""
        errors = []
        if not output or len(output.strip()) < 100:
            errors.append("Edited content is too short")
        if "---" not in output:
            errors.append("Missing YAML front matter (---)")
        return len(errors) == 0, errors

    def run_phase_2b_editor(
        self,
        staging_root: str,
        content_id: str | None = None,
    ) -> str:
        """
        Run editor crew and save final.md to staging directory.

        Args:
            staging_root: Staging directory path (repo-relative)
            content_id: Content ID (defaults to active from tracker)

        Returns:
            Final markdown text
        """
        self._staging_guard(staging_root)
        self.content_id = content_id
        self.staging_root = staging_root

        active = get_active_content(content_id)
        wid = str(active["content_id"])
        sr = staging_root.strip().rstrip("/")
        warn_if_staging_week_mismatch(sr, wid)

        result_text = self.run()

        final_rel = f"{sr}/05_Final.md"
        cleaned = self._maybe_strip_outer_fence(result_text)
        self.save_file(final_rel, cleaned)

        logger.info(
            f"Wrote 05_Final.md",
            extra={"path": final_rel, "week": wid},
        )

        return cleaned

    def _seo_canonical_section(self, staging_root: str) -> str:
        """Deterministic hint block so the Editor copies an approved URL into YAML."""
        root = staging_root.strip().rstrip("/")
        rel = f"{root}/02_SEO_Plan.md"
        path = self.repo_root / rel
        if not path.is_file():
            return (
                "## Canonical URL (from staged SEO plan)\n\n"
                f"No `{rel}` in this staging bundle — set YAML `canonical_url` to a real `https://…` "
                "URL per the brief; never leave bracket placeholders.\n\n"
            )
        raw = path.read_text(encoding="utf-8")
        url = self._extract_canonical_url(raw)
        if not url:
            return (
                "## Canonical URL (from staged SEO plan)\n\n"
                f"`{rel}` has no parseable **Canonical URL** line — read the SEO plan and set "
                "`canonical_url` to the approved https URL with no bracket placeholders.\n\n"
            )
        return (
            "## Canonical URL (from staged SEO plan)\n\n"
            "Use this value for YAML `canonical_url` unless QA explicitly requires a different approved URL:\n\n"
            f"{url}\n\n"
        )

    def _extract_canonical_url(self, text: str) -> str | None:
        """Extract first canonical URL backtick value."""
        for rx in _CANONICAL_URL_PATTERNS:
            m = rx.search(text)
            if m:
                return m.group(1).strip()
        return None

    def _cta_type_hint_section(self) -> str:
        """Snake_case suggestions from canonical runtime `research_gate.cta_variants`."""
        try:
            from src.tools.runtime_paths import load_canonical_runtime_config
            cfg = load_canonical_runtime_config()
        except (OSError, ImportError):
            return ""
        variants = (cfg.get("research_gate") or {}).get("cta_variants") or []
        if not variants:
            return ""
        lines = [
            "## CTA type hint (runtime voice variants)",
            "",
            "Set YAML `cta_type` to one snake_case token aligned with the article's primary CTA, for example:",
        ]
        for v in variants[:8]:
            if not isinstance(v, str) or not v.strip():
                continue
            sug = "_".join(v.lower().replace("-", " ").split())
            lines.append(f"- `{sug}` — voice: {v.strip()}")
        lines.append("")
        return "\n".join(lines)

    def _collect_validator_reports(self, week_id: str, *, max_total_chars: int = 120_000) -> str:
        """Concatenate QA markdown reports for this week (staging reports preferred first)."""
        wid = week_id.upper()
        roots = [
            self.repo_root / "output/qa_reports/staging",
            self.repo_root / "output/qa_reports",
        ]
        parts: list[str] = []
        seen: set[str] = set()
        total = 0

        for root in roots:
            if not root.is_dir():
                continue
            for path in sorted(root.glob(f"{wid}_*.md")):
                if path.name in seen:
                    continue
                seen.add(path.name)
                try:
                    text = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                header = f"### Report file: {path.relative_to(self.repo_root)}\n\n"
                chunk = header + text
                if total + len(chunk) > max_total_chars:
                    remain = max_total_chars - total
                    if remain <= 0:
                        break
                    chunk = chunk[:remain] + "\n\n... [truncated reports]\n"
                    parts.append(chunk)
                    break
                parts.append(chunk)
                total += len(chunk)

        if not parts:
            return (
                "_No matching `WXX_*.md` reports found under output/qa_reports/ or staging/. "
                "Run validators first._\n"
            )

        return "\n".join(parts)

    @staticmethod
    def _maybe_strip_outer_fence(text: str) -> str:
        """Remove a single outer ``` / ```markdown wrapper often emitted by LLMs."""
        t = text.strip()
        if not t.startswith("```"):
            return text
        lines = t.splitlines()
        if not lines:
            return text
        first = lines[0].strip()
        if not first.startswith("```"):
            return text
        lines = lines[1:]
        while lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @staticmethod
    def _staging_guard(staging_root: str) -> None:
        """Validate that staging_root is outside input/."""
        norm = staging_root.strip().rstrip("/").replace("\\", "/")
        if norm.startswith("input/") or norm == "input" or "/input/" in f"/{norm}/":
            raise RuntimeError(
                "Phase 2B editor must write to a staging directory outside input/, "
                "e.g. output/generated/W05. Use promote_staged --final-only for canonical."
            )


# ── Compatibility exports for tests ──────────────────────────────────────────

def _staging_guard(staging_root: str) -> None:
    """Backward compatibility export."""
    return EditorCrew._staging_guard(staging_root)


def extract_canonical_url_from_seo_plan(text: str) -> str | None:
    """Backward compatibility export. Extract first canonical URL backtick value."""
    for rx in _CANONICAL_URL_PATTERNS:
        m = rx.search(text)
        if m:
            return m.group(1).strip()
    return None


def _seo_canonical_section(staging_root: str) -> str:
    """Backward compatibility export."""
    crew = EditorCrew()
    return crew._seo_canonical_section(staging_root)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 2B — generate staged 05_Final.md via Editor agent (CrewAI)."
    )
    parser.add_argument(
        "--staging-root",
        required=True,
        metavar="DIR",
        help="Repo-relative staging dir containing 04_Draft.md (e.g. output/generated/W05).",
    )
    parser.add_argument(
        "--week",
        metavar="WXX",
        help="Tracker content_id; defaults to active_week from runtime config.",
    )
    args = parser.parse_args()
    content_id = args.week.upper() if args.week else None
    try:
        crew = EditorCrew()
        result = crew.run_phase_2b_editor(args.staging_root, content_id=content_id)
        print("\n" + "=" * 80)
        print("EDITOR CREW RESULTS")
        print("=" * 80)
        print(f"\n{result[:500]}...\n")
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)
