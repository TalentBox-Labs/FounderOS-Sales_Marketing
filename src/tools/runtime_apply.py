"""Apply a saved week profile to data/runtime_config.json (copy-paste helper)."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from src.tools.runtime_paths import REPO_ROOT, RUNTIME_CONFIG_PATH

PROFILES_DIR = REPO_ROOT / "data" / "week_runtime"


def _list_profiles() -> list[str]:
    if not PROFILES_DIR.is_dir():
        return []
    out = []
    for p in sorted(PROFILES_DIR.glob("*.json")):
        out.append(p.stem.upper())
    return out


def apply_profile(week_id: str) -> None:
    week_id = week_id.strip().upper()
    src = PROFILES_DIR / f"{week_id}.json"
    if not src.is_file():
        available = ", ".join(_list_profiles()) or "(none)"
        raise FileNotFoundError(
            f"No profile at {src}. Available: {available}"
        )
    RUNTIME_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, RUNTIME_CONFIG_PATH)
    cfg = json.loads(RUNTIME_CONFIG_PATH.read_text(encoding="utf-8"))
    print(f"Applied {src.name} -> {RUNTIME_CONFIG_PATH}")
    print(f"active_week = {cfg.get('active_week')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy data/week_runtime/WXX.json to data/runtime_config.json"
    )
    parser.add_argument(
        "week_id",
        nargs="?",
        help="Week id, e.g. W01, W05 (omit with --list)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available profile files",
    )
    args = parser.parse_args()

    if args.list:
        for wid in _list_profiles():
            print(wid)
        return

    if not args.week_id:
        parser.error("Provide week_id (e.g. W02) or use --list")
    try:
        apply_profile(args.week_id)
    except FileNotFoundError as err:
        print(err, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
