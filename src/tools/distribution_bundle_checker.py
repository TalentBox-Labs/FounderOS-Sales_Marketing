"""
Deterministic gate for staged Phase 3 distribution artifacts (06–09).

Expects `distribution_staging_root` in runtime (set by validate_staged --phase 3 overlay).
"""

from __future__ import annotations

import sys
from pathlib import Path

from src.tools.publish_checklist_checker import checklist_section_markers
from src.tools.promotion_audit import PHASE3_PROMOTION_FILENAMES
from src.tools.runtime_paths import REPO_ROOT, load_runtime_config


_MIN_BODY_CHARS = 80


def run_distribution_bundle_check() -> None:
    runtime = load_runtime_config()
    markers = checklist_section_markers(runtime)
    active = runtime["active_week"]
    root_rel = runtime.get("distribution_staging_root")
    out_dir = REPO_ROOT / Path(runtime["qa_output_dir"].strip("/"))
    output_path = out_dir / f"{active}_Distribution_Bundle_Check.md"

    passed: list[str] = []
    failed: list[str] = []

    if not isinstance(root_rel, str) or not root_rel.strip():
        failed.append(
            "- `distribution_staging_root` missing from runtime — "
            "run via `validate_staged … --phase 3` (staging overlay)."
        )
        text_report = _render_report(active, passed, failed)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text_report, encoding="utf-8")
        print(text_report)
        sys.exit(1)

    bundle_root = REPO_ROOT / root_rel.strip().rstrip("/")

    for name in PHASE3_PROMOTION_FILENAMES:
        p = bundle_root / name
        if not p.is_file():
            failed.append(f"- Missing file: {p.relative_to(REPO_ROOT)}")
            continue
        body = p.read_text(encoding="utf-8")
        if len(body.strip()) < _MIN_BODY_CHARS:
            failed.append(f"- File unexpectedly short ({len(body.strip())} chars): `{name}`")
        else:
            passed.append(f"- `{name}` exists with substantive body")

        if name == "09_Publish_Checklist.md":
            for marker in markers:
                if marker in body:
                    passed.append(f"- Checklist section present: {marker}")
                else:
                    failed.append(f"- Missing checklist heading: {marker}")

    report = _render_report(active, passed, failed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(report)
    sys.exit(1 if failed else 0)


def _render_report(active: str, passed: list[str], failed: list[str]) -> str:
    lines = [
        f"# {active} Distribution bundle (06–09)",
        "",
        "## Passed Checks",
        "",
    ]
    lines.extend(passed if passed else ["- None"])
    lines.extend(["", "## Failed Checks", ""])
    lines.extend(failed if failed else ["- None"])
    lines.extend(
        [
            "",
            "## Final Verdict",
            "",
            "FAIL" if failed else "PASS",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    run_distribution_bundle_check()
