"""
Phase 2B — Editor agent: staged `05_Final.md` only.

Writes under `--staging-root` (e.g. output/generated/WXX); never writes to input/ directly.
Does not modify tracker or runtime config.
"""

from __future__ import annotations

import argparse
import re
import sys

from crewai import Agent, Crew, Process, Task

from src.crew import BASE_DIR, build_crew_llm, load_yaml, read_file, save_file
from src.tools.csv_reader import get_active_content
from src.tools.runtime_paths import load_canonical_runtime_config
from src.tools.staging_overlay import warn_if_staging_week_mismatch

_QA_MISSING_PREFIX = "_No matching"

_CANONICAL_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\*\*Canonical URL:\*\*\s*`([^`\n]+)`", re.IGNORECASE),
    re.compile(r"Canonical URL:\s*`([^`\n]+)`", re.IGNORECASE),
)


def extract_canonical_url_from_seo_plan(text: str) -> str | None:
    """First canonical URL backtick value found in staged `02_SEO_Plan.md` text."""
    for rx in _CANONICAL_URL_PATTERNS:
        m = rx.search(text)
        if m:
            return m.group(1).strip()
    return None


def _seo_canonical_section(staging_root: str) -> str:
    """Deterministic hint block so the Editor copies an approved URL into YAML."""
    root = staging_root.strip().rstrip("/")
    rel = f"{root}/02_SEO_Plan.md"
    path = BASE_DIR / rel
    if not path.is_file():
        return (
            "## Canonical URL (from staged SEO plan)\n\n"
            f"No `{rel}` in this staging bundle — set YAML `canonical_url` to a real `https://…` "
            "URL per the brief; never leave bracket placeholders.\n\n"
        )
    raw = path.read_text(encoding="utf-8")
    url = extract_canonical_url_from_seo_plan(raw)
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


def _cta_type_hint_section() -> str:
    """Snake_case suggestions from canonical runtime `research_gate.cta_variants` (non-authoritative)."""
    try:
        cfg = load_canonical_runtime_config()
    except OSError:
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


def _staging_guard(staging_root: str) -> None:
    norm = staging_root.strip().rstrip("/").replace("\\", "/")
    if norm.startswith("input/") or norm == "input" or "/input/" in f"/{norm}/":
        raise RuntimeError(
            "Phase 2B editor must write to a staging directory outside input/, "
            "e.g. output/generated/W05. Use promote_staged --final-only for canonical."
        )


def collect_validator_reports(week_id: str, *, max_total_chars: int = 120_000) -> str:
    """Concatenate QA markdown reports for this week (staging reports preferred first)."""
    wid = week_id.upper()
    roots = [
        BASE_DIR / "output/qa_reports/staging",
        BASE_DIR / "output/qa_reports",
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
            header = f"### Report file: {path.relative_to(BASE_DIR)}\n\n"
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


def _run_editor_task(
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


def run_phase_2b_editor(
    staging_root: str,
    content_id: str | None = None,
) -> str:
    """
    Generate `05_Final.md` inside staging_root using staged `04_Draft.md` + QA reports.

    Returns full markdown text written to `{staging_root}/05_Final.md`.
    """
    _staging_guard(staging_root)

    active = get_active_content(content_id)
    wid = str(active["content_id"])

    sr = staging_root.strip().rstrip("/")
    warn_if_staging_week_mismatch(sr, wid)
    draft_rel = f"{sr}/04_Draft.md"
    final_rel = f"{sr}/05_Final.md"

    draft_body = read_file(draft_rel)
    qa_blob = collect_validator_reports(wid)
    if qa_blob.strip().startswith(_QA_MISSING_PREFIX):
        print(
            "WARNING: staging QA context missing; editor quality may be reduced",
            file=sys.stderr,
        )

    seo_hints = _seo_canonical_section(sr)
    cta_hints = _cta_type_hint_section()

    agents_y = load_yaml("src/agents_editor.yaml")
    tasks_y = load_yaml("src/tasks_editor.yaml")
    llm = build_crew_llm()

    task_cfg = tasks_y["editor_final_task"]
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

{seo_hints}{cta_hints}
Instructions:
- Output ONE markdown document only: YAML front matter then article body.
- Front matter values must satisfy metadata checker (no `[PLACEHOLDER]` brackets in values).
- Include required keys: week_id, article_title, primary_keyword, search_intent, funnel_stage,
  status, publish_status, canonical_url (https), cta_type (non-empty).
- Preserve structure required by structure checker (H1, H2s, FAQ section heading).
- Do not mention tooling as ranking guarantees; no fake URLs or statistics.
"""

    result = _run_editor_task(
        agent_cfg=agents_y["editor_agent"],
        description=description,
        expected_output=task_cfg["expected_output"],
        llm=llm,
    )

    cleaned = _maybe_strip_outer_fence(result)
    save_file(final_rel, cleaned)
    print(
        f"\nPhase 2B editor wrote {final_rel}\n"
        f"Next: python -m src.tools.validate_staged {sr} --week {wid} --phase 2b\n",
        file=sys.stderr,
    )
    return cleaned


def main() -> None:
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
        run_phase_2b_editor(args.staging_root, content_id=content_id)
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
