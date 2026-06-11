"""Update tracker.csv for the active content week (from runtime config).

Only ``status`` and ``qa_status`` are written for the matching row(s).
``current_step`` and ``next_step`` are **not** modified here — programme / ops
owns those (e.g. Publish Review → CMS Go-live until a human records go-live).
"""

from __future__ import annotations

import csv

from src.tools.runtime_paths import TRACKER_PATH, load_runtime_config

STATUS = "QA Passed"
QA_STATUS = "PASS"


def _cell(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _row_matches_active_week(row: dict[str, str], active_week: str) -> bool:
    """Match `content_id` or optional `artifact_folder` (split IDs sharing one bundle)."""
    aw = active_week.strip().upper()
    if _cell(row.get("content_id")).upper() == aw:
        return True
    af = _cell(row.get("artifact_folder")).upper()
    return bool(af) and af == aw


def update_tracker(content_id: str | None = None) -> None:
    if content_id is None:
        content_id = load_runtime_config()["active_week"]

    if not TRACKER_PATH.is_file():
        raise FileNotFoundError(f"{TRACKER_PATH} not found")

    rows: list[dict[str, str]] = []

    with TRACKER_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("tracker.csv has no header row")

        required_columns = ("content_id", "status", "qa_status")
        for column in required_columns:
            if column not in fieldnames:
                raise ValueError(f"Missing required column: {column}")

        for row in reader:
            if _row_matches_active_week(row, content_id):
                row["status"] = STATUS
                row["qa_status"] = QA_STATUS
            rows.append(row)

    with TRACKER_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{content_id} updated successfully.")
    print(f"status = {STATUS}")
    print(f"qa_status = {QA_STATUS}")


if __name__ == "__main__":
    update_tracker()
