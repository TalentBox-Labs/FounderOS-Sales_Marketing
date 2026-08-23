"""Deployment manifest and rollback metadata (M5)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.tools.website_deployment.contract import MANIFEST_FILENAME

SCHEMA_VERSION = "1.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


@dataclass
class DeploymentManifest:
    schema_version: str
    deployment_id: str
    created_at: str
    source_root: str
    package_root: str
    files: list[dict[str, Any]]
    public_file_count: int
    provider_target: str
    rollback: dict[str, Any] = field(default_factory=dict)
    cloudflare: dict[str, Any] = field(default_factory=dict)
    local: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "deployment_id": self.deployment_id,
            "created_at": self.created_at,
            "source_root": self.source_root,
            "package_root": self.package_root,
            "files": list(self.files),
            "public_file_count": self.public_file_count,
            "provider_target": self.provider_target,
            "rollback": dict(self.rollback),
            "cloudflare": dict(self.cloudflare),
            "local": dict(self.local),
        }


def new_deployment_id() -> str:
    return f"dep_{uuid.uuid4().hex[:12]}"


def build_file_entries(package_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(package_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(package_root).as_posix()
        entries.append(
            {
                "path": rel,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


def write_manifest(manifest: DeploymentManifest, package_root: Path) -> Path:
    package_root.mkdir(parents=True, exist_ok=True)
    out = package_root / MANIFEST_FILENAME
    out.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out
