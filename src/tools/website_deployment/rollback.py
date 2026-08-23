"""Local rollback metadata history (M5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.tools.website_deployment.contract import ROLLBACK_HISTORY_JSONL
from src.tools.website_deployment.manifest import utc_now_iso


def history_path(deploy_root: Path) -> Path:
    return deploy_root / ROLLBACK_HISTORY_JSONL


def read_last_deployment_id(deploy_root: Path) -> str | None:
    path = history_path(deploy_root)
    if not path.is_file():
        return None
    last_id: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        dep = record.get("deployment_id")
        if isinstance(dep, str):
            last_id = dep
    return last_id


def append_rollback_record(deploy_root: Path, record: dict[str, Any]) -> Path:
    deploy_root.mkdir(parents=True, exist_ok=True)
    path = history_path(deploy_root)
    payload = dict(record)
    payload.setdefault("recorded_at", utc_now_iso())
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
    return path
