from __future__ import annotations

import csv

from src.tools.runtime_paths import TRACKER_PATH, load_runtime_config


def load_tracker():
    if not TRACKER_PATH.is_file():
        raise FileNotFoundError(f"{TRACKER_PATH} not found")

    with TRACKER_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def save_tracker(rows, fieldnames):
    with TRACKER_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_active_content():
    rows = load_tracker()
    preferred = load_runtime_config()["active_week"]
    for row in rows:
        if row.get("content_id") == preferred:
            return row

    for row in rows:
        status = row.get("status", "").strip().lower()
        qa_status = row.get("qa_status", "").strip().lower()

        if status != "published" and qa_status != "pass":
            return row

    return None


def update_content_status(content_id, new_status):
    rows = load_tracker()

    fieldnames = list(rows[0].keys())

    for row in rows:
        if row["content_id"] == content_id:
            row["status"] = new_status

    save_tracker(rows, fieldnames)

    print(f"{content_id} status updated to: {new_status}")


def mark_qa_passed(content_id):
    rows = load_tracker()

    fieldnames = list(rows[0].keys())

    for row in rows:
        if row["content_id"] == content_id:
            row["qa_status"] = "PASS"

    save_tracker(rows, fieldnames)

    print(f"{content_id} QA marked as PASS")


def mark_publish_ready(content_id):
    rows = load_tracker()

    fieldnames = list(rows[0].keys())

    for row in rows:
        if row["content_id"] == content_id:
            row["status"] = "Ready for Publish"

    save_tracker(rows, fieldnames)

    print(f"{content_id} marked Ready for Publish")


if __name__ == "__main__":
    active = get_active_content()

    if active:
        print("ACTIVE CONTENT FOUND")
        print(active)
    else:
        print("No active content found.")
