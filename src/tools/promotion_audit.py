"""Promotion audit trail: history, diffs, validator captures, rollback pointers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any

from src.tools.runtime_paths import REPO_ROOT

AUDIT_DIR = REPO_ROOT / "output" / "promotion_audit"
HISTORY_JSONL = AUDIT_DIR / "promotion_history.jsonl"
SCHEMA_VERSION = 1

PHASE2A_PROMOTION_FILENAMES: tuple[str, ...] = (
    "01_Content_Brief.md",
    "02_SEO_Plan.md",
    "03_Research.md",
    "04_Draft.md",
)

PHASE2B_PROMOTION_FILENAMES: tuple[str, ...] = ("05_Final.md",)

PHASE3_PROMOTION_FILENAMES: tuple[str, ...] = (
    "06_Design_Brief.md",
    "07_Social_Posts.md",
    "08_Email_Copy.md",
    "09_Publish_Checklist.md",
)


def parse_validator_verdict(text: str) -> str:
    """Extract PASS/FAIL from validator stdout (best-effort; uses last Verdict block)."""
    parts = re.split(r"(?i)##\s*Final\s*Verdict\s*", text)
    if len(parts) < 2:
        return "UNKNOWN"
    tail = parts[-1][:800]
    if re.search(r"(?im)^\s*PASS\s*$", tail):
        return "PASS"
    if re.search(r"(?im)^\s*FAIL\s*$", tail):
        return "FAIL"
    return "UNKNOWN"


def _git_head_short() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def compute_file_diffs(
    staging_dir: Path,
    canonical_dir: Path,
    *,
    audit_prefix: str,
    diff_out_dir: Path,
    filenames: tuple[str, ...] | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """
    Unified diff canonical (old) vs staging (new) per file.

    Returns (diff_full_text_by_filename, artifact_relative_path_by_filename).
    Missing canonical side treated as empty file.
    """
    diff_out_dir.mkdir(parents=True, exist_ok=True)
    full_text: dict[str, str] = {}
    artifacts: dict[str, str] = {}

    safe_audit = audit_prefix.replace("/", "_")
    names = filenames if filenames is not None else PHASE2A_PROMOTION_FILENAMES
    for name in names:
        new_p = staging_dir / name
        old_p = canonical_dir / name
        old_lines = (
            old_p.read_text(encoding="utf-8").splitlines(keepends=True)
            if old_p.is_file()
            else []
        )
        new_lines = (
            new_p.read_text(encoding="utf-8").splitlines(keepends=True)
            if new_p.is_file()
            else []
        )
        diff_lines = list(
            unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/input/{canonical_dir.name}/{name}",
                tofile=f"b/{staging_dir.relative_to(REPO_ROOT)}/{name}",
            )
        )
        diff_text = "".join(diff_lines)
        full_text[name] = diff_text

        digest = hashlib.sha256(name.encode()).hexdigest()[:8]
        fname = f"{safe_audit}_diff_{digest}_{name.replace('.', '_')}.unified.txt"
        out_path = diff_out_dir / fname
        out_path.write_text(diff_text if diff_text else f"(no changes or empty)\n", encoding="utf-8")
        artifacts[name] = str(out_path.relative_to(REPO_ROOT))

    return full_text, artifacts


def write_audit_bundle(
    *,
    event_ts_slug: str,
    week_id: str,
    staging_root: str,
    approver: str,
    notes: str,
    skip_validation: bool,
    validator_runs: list[dict[str, Any]],
    backup_relative: str,
    canonical_path: Path,
    diff_artifacts: dict[str, str],
    diff_character_counts: dict[str, int],
    event_name: str = "promotion_phase2a",
) -> Path:
    """
    Write JSON audit record + append JSONL line.

    Pre-copy unified diff files must already exist (see compute_file_diffs).

    Returns path to main audit JSON file.
    """
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    wid = week_id.upper()
    audit_prefix = f"{event_ts_slug}_{wid}"

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event": event_name,
        "utc_timestamp": datetime.now(timezone.utc).isoformat(),
        "week_id": wid,
        "staging_root": staging_root.strip().rstrip("/"),
        "canonical_dir": str(canonical_path.relative_to(REPO_ROOT)),
        "approver": approver,
        "notes": notes or "",
        "skip_validation": skip_validation,
        "validators": validator_runs,
        "rollback_backup_relative": backup_relative,
        "diff_artifacts": diff_artifacts,
        "diff_character_counts": diff_character_counts,
        "git_commit_short": _git_head_short(),
    }

    json_path = AUDIT_DIR / f"{audit_prefix}_audit.json"
    json_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    summary_line = {
        "utc_timestamp": record["utc_timestamp"],
        "week_id": wid,
        "approver": approver,
        "staging_root": record["staging_root"],
        "rollback_backup_relative": backup_relative,
        "audit_json": str(json_path.relative_to(REPO_ROOT)),
        "skip_validation": skip_validation,
    }
    HISTORY_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_JSONL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(summary_line, ensure_ascii=False) + "\n")

    return json_path


def cmd_list(last: int) -> int:
    if not HISTORY_JSONL.is_file():
        print("(no promotion history yet)", file=sys.stderr)
        return 0
    lines = HISTORY_JSONL.read_text(encoding="utf-8").strip().splitlines()
    tail = lines[-last:] if last > 0 else lines
    for ln in tail:
        print(ln)
    return 0


def cmd_show(path: str) -> int:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / path
    if not p.is_file():
        print(f"Not found: {p}", file=sys.stderr)
        return 1
    print(p.read_text(encoding="utf-8"))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Promotion audit trail helpers.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="Print last N lines of promotion_history.jsonl")
    p_list.add_argument("--last", type=int, default=20, help="Number of recent entries")

    p_show = sub.add_parser("show", help="Print one audit JSON file")
    p_show.add_argument("audit_json", help="Path to *_audit.json")

    args = parser.parse_args()
    if args.cmd == "list":
        sys.exit(cmd_list(args.last))
    if args.cmd == "show":
        sys.exit(cmd_show(args.audit_json))
    sys.exit(2)


if __name__ == "__main__":
    main()
