"""Build artifact export — public subset of ``output/website/`` (M5)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from src.tools.website_deployment.contract import (
    DEFAULT_SOURCE_ROOT,
    is_public_artifact,
)


@dataclass(frozen=True)
class ExportResult:
    ok: bool
    message: str
    source_root: Path
    package_root: Path
    copied_files: tuple[str, ...]
    skipped_files: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "message": self.message,
            "source_root": str(self.source_root),
            "package_root": str(self.package_root),
            "copied_files": list(self.copied_files),
            "skipped_files": list(self.skipped_files),
        }


def list_source_artifacts(source_root: Path) -> tuple[list[Path], list[Path]]:
    """Return (public_relative_paths, skipped_relative_paths) under source_root."""
    if not source_root.is_dir():
        return [], []

    public: list[Path] = []
    skipped: list[Path] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source_root)
        if is_public_artifact(rel):
            public.append(rel)
        else:
            skipped.append(rel)
    return public, skipped


def export_public_package(
    *,
    package_root: Path,
    source_root: Path = DEFAULT_SOURCE_ROOT,
    clean: bool = True,
) -> ExportResult:
    """Copy only public artifacts into package_root."""
    public, skipped = list_source_artifacts(source_root)
    if not source_root.is_dir():
        return ExportResult(
            ok=False,
            message=f"Source root does not exist: {source_root}",
            source_root=source_root,
            package_root=package_root,
            copied_files=(),
            skipped_files=tuple(p.as_posix() for p in skipped),
        )

    if clean and package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for rel in public:
        src = source_root / rel
        dest = package_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(rel.as_posix())

    if not copied:
        return ExportResult(
            ok=False,
            message="No public artifacts found to export (expected slug/index.html and/or feeds)",
            source_root=source_root,
            package_root=package_root,
            copied_files=(),
            skipped_files=tuple(p.as_posix() for p in skipped),
        )

    return ExportResult(
        ok=True,
        message=f"Exported {len(copied)} public file(s)",
        source_root=source_root,
        package_root=package_root,
        copied_files=tuple(copied),
        skipped_files=tuple(p.as_posix() for p in skipped),
    )
