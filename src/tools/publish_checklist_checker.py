"""Structural validation for 09_Publish_Checklist.md (exists + required QA sections)."""

from __future__ import annotations

from pathlib import Path

from src.tools.runtime_paths import REPO_ROOT, checklist_path_for_week, load_runtime_config


_DEFAULT_SECTION_MARKERS = (
    "# Content QA",
    "# SEO QA",
    "# Brand QA",
    "# Technical QA",
    "# Final Approval",
)


def checklist_section_markers(runtime: dict) -> tuple[str, ...]:
    """Headings required in `09_Publish_Checklist.md` for this active week."""
    custom = runtime.get("publish_checklist_section_markers")
    if custom:
        return tuple(str(x) for x in custom)
    return _DEFAULT_SECTION_MARKERS


def resolve_checklist_path(runtime: dict) -> Path:
    """Canonical `input/WXX/09_...` unless Phase 3 overlay sets `distribution_staging_root`."""
    root = runtime.get("distribution_staging_root")
    if isinstance(root, str) and root.strip():
        return REPO_ROOT / root.strip().rstrip("/") / "09_Publish_Checklist.md"
    bundle = runtime.get("input_bundle")
    if isinstance(bundle, str) and bundle.strip():
        folder = bundle.strip()
    else:
        folder = runtime["active_week"]
    return checklist_path_for_week(folder)


def run_checklist_check() -> None:
    runtime = load_runtime_config()
    active = runtime["active_week"]
    path = resolve_checklist_path(runtime)
    out_dir = REPO_ROOT / Path(runtime["qa_output_dir"].strip("/"))
    output_path = out_dir / f"{active}_Publish_Checklist_Check.md"

    section_markers = checklist_section_markers(runtime)

    passed: list[str] = []
    failed: list[str] = []

    if not path.is_file():
        failed.append(f"- Publish checklist missing: {path}")
        text = ""
    else:
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 50:
            failed.append("- Publish checklist file is unexpectedly short")
        else:
            passed.append("- Publish checklist file exists and has body text")

        for marker in section_markers:
            if marker in text:
                passed.append(f"- Section present: {marker}")
            else:
                failed.append(f"- Missing section heading: {marker}")

    report: list[str] = [f"# {active} Publish Checklist (structure)\n"]
    report.append("## Passed Checks\n")
    report.extend(passed if passed else ["- None"])
    report.append("\n## Failed Checks\n")
    report.extend(failed if failed else ["- None"])
    report.append("\n## Note\n")
    report.append(
        "This gate only verifies the checklist file exists and contains the "
        "expected section headings. Human sign-off on each item is still required "
        "before publish."
    )
    report.append("\n## Final Verdict\n")
    report.append("FAIL" if failed else "PASS")

    final = "\n".join(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final, encoding="utf-8")
    print(final)


if __name__ == "__main__":
    run_checklist_check()
