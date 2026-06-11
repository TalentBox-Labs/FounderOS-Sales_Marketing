"""
Remove data rows on the configured Google Sheet tab whose column A ID is not in
`tracker.csv` (e.g. legacy `W05` after split into `W05A`/`W05B`).

Uses same env as sheet_sync: WORKCREW_GOOGLE_SERVICE_ACCOUNT, WORKCREW_GOOGLE_SHEET_ID,
WORKCREW_GOOGLE_SHEET_TAB (Repo mirror), WORKCREW_GOOGLE_SHEET_HEADER_ROW.

Examples:
  python -m src.tools.sheet_orphan_cleanup              # list orphans, no deletes
  python -m src.tools.sheet_orphan_cleanup --execute    # delete orphan rows
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

from src.tools.google_sheet_sync import (
    SheetEnv,
    build_sheets_service,
    delete_sheet_rows_1based,
    fetch_id_to_row,
    get_sheet_id_for_tab_title,
    load_sa_email,
    load_sheet_env,
)
from src.tools.runtime_paths import REPO_ROOT, TRACKER_PATH

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def tracker_id_set() -> set[str]:
    df = pd.read_csv(TRACKER_PATH)
    return {str(x).strip().upper() for x in df["content_id"].dropna()}


def run(*, execute: bool) -> int:
    allowed = tracker_id_set()
    env = load_sheet_env(require_tab=True)

    try:
        service = build_sheets_service(env.sa_path, readonly=False)
        id_to_row = fetch_id_to_row(service, env)
    except Exception as e:
        print(f"ERROR: Google Sheets API failed: {e}", file=sys.stderr)
        try:
            hint = load_sa_email(env.sa_path)
        except Exception:
            hint = "(set WORKCREW_GOOGLE_SERVICE_ACCOUNT)"
        print(
            f"Hint: Share the spreadsheet with the service account (Editor):\n  {hint}",
            file=sys.stderr,
        )
        return 1

    orphans: list[tuple[str, int]] = []
    for wid, row_num in id_to_row.items():
        key = str(wid).strip().upper()
        if key and key not in allowed:
            orphans.append((str(wid).strip(), row_num))

    if not orphans:
        print(
            f"No orphan IDs on tab {env.tab_title!r} (all column A ids appear in tracker.csv).",
            file=sys.stderr,
        )
        return 0

    orphans.sort(key=lambda x: x[1], reverse=True)
    print(
        f"Orphan row(s) on {env.tab_title!r} (not in tracker.csv): "
        + ", ".join(f"{w}@row{r}" for w, r in orphans),
        file=sys.stderr,
    )

    if not execute:
        print("Dry-run only. Re-run with --execute to delete these rows.", file=sys.stderr)
        return 0

    sheet_id = get_sheet_id_for_tab_title(service, env.spreadsheet_id, env.tab_title)
    delete_sheet_rows_1based(
        service,
        env.spreadsheet_id,
        sheet_id,
        [r for _, r in orphans],
    )
    print(f"Deleted {len(orphans)} orphan row(s).", file=sys.stderr)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete orphan rows (default is dry-run only).",
    )
    args = parser.parse_args()
    raise SystemExit(run(execute=args.execute))


if __name__ == "__main__":
    main()
