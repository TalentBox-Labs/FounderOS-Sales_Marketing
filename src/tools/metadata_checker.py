"""Validate YAML front matter in 05_Final.md (schema lint + structural checks)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from src.tools.final_frontmatter_lint import lint_final_front_matter
from src.tools.runtime_paths import REPO_ROOT, load_runtime_config


def _split_front_matter(text: str) -> Tuple[Optional[dict[str, str]], str]:
    if not text.lstrip().startswith("---"):
        return None, text
    lines = text.splitlines()
    if len(lines) < 2 or lines[0].strip() != "---":
        return None, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    body = "\n".join(lines[end + 1 :])
    fm_lines = lines[1:end]
    data: dict[str, str] = {}
    for raw in fm_lines:
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        data[key] = value
    return data, body


def run_metadata_check() -> None:
    runtime = load_runtime_config()
    active = runtime["active_week"]
    final_rel = runtime["final_path"]
    final_path = REPO_ROOT / final_rel
    out_dir = REPO_ROOT / Path(runtime["qa_output_dir"].strip("/"))
    output_path = out_dir / f"{active}_Metadata_Check.md"

    passed: list[str] = []
    failed: list[str] = []

    if not final_path.is_file():
        failed.append(f"- Final file missing: {final_path}")
    else:
        text = final_path.read_text(encoding="utf-8")
        fm, _ = _split_front_matter(text)
        if fm is None:
            failed.append("- No YAML front matter block (opening --- ... closing ---)")
        else:
            sp, sf = lint_final_front_matter(fm)
            passed.extend(sp)
            failed.extend(sf)

    report: list[str] = [f"# {active} Metadata Validation\n"]
    report.append("## Passed Checks\n")
    report.extend(passed if passed else ["- None"])
    report.append("\n## Failed Checks\n")
    report.extend(failed if failed else ["- None"])
    report.append("\n## Final Verdict\n")
    report.append("FAIL" if failed else "PASS")

    final = "\n".join(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final, encoding="utf-8")
    print(final)


if __name__ == "__main__":
    run_metadata_check()
