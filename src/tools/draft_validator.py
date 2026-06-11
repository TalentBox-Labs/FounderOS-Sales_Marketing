import json
import re
from pathlib import Path

from src.tools.runtime_paths import load_runtime_config

REQUIRED_TEMPLATE_SECTIONS = [
    "drafting instructions",
    "writing rules",
    "seo execution rules",
    "cta rules",
    "draft structure",
    "frequently asked questions",
    "internal linking requirements",
    "evidence & validation requirements",
    "draft qa checklist",
]

BANNED_CLAIMS = [
    "best platform in the world",
    "guaranteed hiring",
    "100% success rate",
    "instant hiring",
    "game-changer",
    "cutting-edge",
    "revolutionary",
    "in today's fast-paced world",
]


def load_draft(path):
    return Path(path).read_text(encoding="utf-8")


def count_words(text):
    return len(re.findall(r"\b\w+\b", text))


def check_template_sections(text):
    passed = []
    failed = []
    lowered = text.lower()

    for section in REQUIRED_TEMPLATE_SECTIONS:
        if section in lowered:
            passed.append(f"- Template section present: {section}")
        else:
            failed.append(f"- Missing template section: {section}")

    return passed, failed


def _article_body_for_checks(text: str) -> str:
    if "## Editor Change Log" in text:
        return text.split("## Editor Change Log", 1)[0]
    if "**Editor Change Log**" in text:
        return text.split("**Editor Change Log**", 1)[0]
    return text


def check_article_draft(text, *, article_min_words: int):
    """Validate an editor-approved article draft (not the CMS template shell)."""
    passed = []
    failed = []
    body = _article_body_for_checks(text)
    lowered = body.lower()
    lines = [ln for ln in body.splitlines() if ln.strip()]
    first = lines[0].strip() if lines else ""

    if first.startswith("# ") and len(first) > 2:
        passed.append("- H1 present on first meaningful line")
    else:
        failed.append("- Missing H1 (# title) at start of draft")

    if "frequently asked questions" in lowered:
        passed.append("- FAQ section heading present")
    else:
        failed.append("- Missing FAQ section")

    words = count_words(body)
    if words >= article_min_words:
        passed.append(f"- Word count meets minimum ({words} >= {article_min_words})")
    else:
        failed.append(f"- Word count below minimum ({words} < {article_min_words})")

    return passed, failed


def check_banned_claims(text):
    passed = []
    failed = []
    lowered = text.lower()

    for claim in BANNED_CLAIMS:
        if claim in lowered:
            failed.append(f"- Banned claim found: {claim}")

    if not failed:
        passed.append("- No banned claims found")

    return passed, failed


def run_validator():
    runtime = load_runtime_config()
    active_week = runtime["active_week"]
    draft_path = runtime["draft_path"]
    output_path = f"{runtime['qa_output_dir']}{active_week}_Draft_Validation.md"
    draft_validation_mode = runtime.get("draft_validation_mode", "template")
    article_min_words = int(runtime.get("draft_article_min_words", 900))

    text = load_draft(draft_path)

    passed = []
    failed = []

    if draft_validation_mode == "article":
        p, f = check_article_draft(text, article_min_words=article_min_words)
        passed.extend(p)
        failed.extend(f)
        mode_label = "Article Draft"
    else:
        p, f = check_template_sections(text)
        passed.extend(p)
        failed.extend(f)
        mode_label = "Template Draft"

    p, f = check_banned_claims(text)
    passed.extend(p)
    failed.extend(f)

    passed.append(f"- Word count recorded: {count_words(_article_body_for_checks(text))}")

    report = []
    report.append(f"# {active_week} Draft Validation\n")
    report.append("## Mode\n")
    report.append(mode_label)

    report.append("\n## Passed Checks\n")
    report.extend(passed if passed else ["- None"])

    report.append("\n## Failed Checks\n")
    report.extend(failed if failed else ["- None"])

    report.append("\n## Final Verdict\n")
    report.append("FAIL" if failed else "PASS")

    final = "\n".join(report)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(final, encoding="utf-8")

    print(final)


if __name__ == "__main__":
    run_validator()
