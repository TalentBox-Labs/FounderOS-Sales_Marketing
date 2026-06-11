#!/usr/bin/env python3
"""Sync Obsidian vault notes from live repo data (tracker + QA reports).

Run any time after a pipeline run to refresh week notes, QA reports,
and the dashboard index.

    python scripts/sync_obsidian_vault.py
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

ROOT  = Path(__file__).resolve().parents[1]
VAULT = ROOT / "obsidian_vault"
TODAY = str(date.today())


def _read_tracker() -> list[dict[str, str]]:
    with (ROOT / "tracker.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _qa_verdict(week_id: str) -> str:
    qa_dir = ROOT / "output" / "qa_reports"
    for fname in [
        f"{week_id}_Draft_Validation.md",
        f"{week_id}_Structure_Check.md",
    ]:
        path = qa_dir / fname
        if not path.is_file():
            continue
        for line in reversed(path.read_text(encoding="utf-8").splitlines()):
            if "PASS" in line:
                return "PASS"
            if "FAIL" in line:
                return "FAIL"
    return "—"


def sync_dashboard(rows: list[dict]) -> None:
    table_rows = "\n".join(
        f"| [[{r['content_id']}]] | {r['title'] or '—'} | {r['status'] or '—'} "
        f"| {r['qa_status'] or '—'} | {r['current_step'] or '—'} |"
        for r in rows
    )
    home = (VAULT / "00 - Dashboard" / "Home.md").read_text(encoding="utf-8")
    # Replace table body between header separator and next section
    import re
    pattern = r"(\| Week \| Title \|.*?\n\|[-| ]+\|\n).*?(\n## )"
    replacement = (
        r"\g<1>"
        + table_rows
        + r"\n\g<2>"
    )
    updated = re.sub(pattern, replacement, home, flags=re.DOTALL)
    (VAULT / "00 - Dashboard" / "Home.md").write_text(updated, encoding="utf-8")
    print(f"  dashboard synced ({len(rows)} rows)")


def sync_week_qa_status(rows: list[dict]) -> None:
    for row in rows:
        wid = row["content_id"].strip().upper()
        week_file = VAULT / "02 - Weeks" / f"{wid}.md"
        if not week_file.is_file():
            continue
        text = week_file.read_text(encoding="utf-8")
        live_qa = _qa_verdict(wid)
        # Update qa_status in frontmatter
        import re
        text = re.sub(r"^qa_status:.*$", f"qa_status: {live_qa}", text, flags=re.MULTILINE)
        week_file.write_text(text, encoding="utf-8")
    print(f"  week QA statuses synced")


def main() -> None:
    rows = _read_tracker()
    print(f"Syncing vault: {len(rows)} tracker rows → {VAULT.name}/")
    sync_dashboard(rows)
    sync_week_qa_status(rows)
    print("Done.")


if __name__ == "__main__":
    main()
