from pathlib import Path

from src.tools.runtime_paths import load_runtime_config

REQUIRED_HEADINGS = [
    "#",
    "##",
    "Frequently Asked Questions",
]


FORBIDDEN_PATTERNS = [
    "game-changer",
    "cutting-edge",
    "revolutionary",
    "in today's fast-paced world",
]



def load_content(path):
    return Path(path).read_text(encoding="utf-8")



def validate_headings(content):
    passed = []
    failed = []

    if "# " in content:
        passed.append("- H1 heading detected")
    else:
        failed.append("- Missing H1 heading")

    if "## " in content:
        passed.append("- H2 headings detected")
    else:
        failed.append("- Missing H2 headings")

    if "Frequently Asked Questions" in content:
        passed.append("- FAQ section detected")
    else:
        failed.append("- Missing FAQ section")

    return passed, failed



def validate_banned_phrases(content):
    passed = []
    failed = []

    lowered = content.lower()

    for phrase in FORBIDDEN_PATTERNS:
        if phrase in lowered:
            failed.append(f"- Forbidden phrase detected: {phrase}")
        else:
            passed.append(f"- Forbidden phrase absent: {phrase}")

    return passed, failed



def run_structure_check():
    runtime = load_runtime_config()
    active_week = runtime["active_week"]
    final_path = runtime["final_path"]
    output_path = f"{runtime['qa_output_dir']}{active_week}_Structure_Check.md"

    content = load_content(final_path)

    passed = []
    failed = []

    heading_passed, heading_failed = validate_headings(content)
    banned_passed, banned_failed = validate_banned_phrases(content)

    passed.extend(heading_passed)
    passed.extend(banned_passed)

    failed.extend(heading_failed)
    failed.extend(banned_failed)

    report = []
    report.append(f"# {active_week} Structure Validation\n")

    report.append("## Passed Checks\n")
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
    run_structure_check()