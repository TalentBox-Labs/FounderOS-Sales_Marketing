"""Deployment Adapter — package, manifest, local deploy, Cloudflare prep (M5)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.tools.website_deployment.cloudflare import (
    DEFAULT_PAGES_PROJECT,
    write_cloudflare_config,
)
from src.tools.website_deployment.contract import (
    DEFAULT_DEPLOY_ROOT,
    DEFAULT_SOURCE_ROOT,
    MANIFEST_FILENAME,
)
from src.tools.website_deployment.export import ExportResult, export_public_package
from src.tools.website_deployment.manifest import (
    SCHEMA_VERSION,
    DeploymentManifest,
    build_file_entries,
    new_deployment_id,
    utc_now_iso,
    write_manifest,
)
from src.tools.website_deployment.rollback import append_rollback_record, read_last_deployment_id

PROVIDER_CLOUDFLARE = "cloudflare_pages"
PROVIDER_LOCAL = "local_static"


@dataclass
class DeploymentResult:
    ok: bool
    message: str
    deployment_id: str
    provider_target: str
    export: ExportResult | None = None
    manifest_path: str = ""
    package_root: str = ""
    snapshot_root: str = ""
    cloudflare_config: dict[str, str] = field(default_factory=dict)
    local_target: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "message": self.message,
            "deployment_id": self.deployment_id,
            "provider_target": self.provider_target,
            "export": self.export.to_dict() if self.export else None,
            "manifest_path": self.manifest_path,
            "package_root": self.package_root,
            "snapshot_root": self.snapshot_root,
            "cloudflare_config": dict(self.cloudflare_config),
            "local_target": self.local_target,
            "details": dict(self.details),
        }


class DeploymentAdapter:
    """Host-agnostic deployment surface outside Website Engine Core."""

    def __init__(
        self,
        *,
        source_root: Path = DEFAULT_SOURCE_ROOT,
        deploy_root: Path = DEFAULT_DEPLOY_ROOT,
        pages_project: str = DEFAULT_PAGES_PROJECT,
    ) -> None:
        self.source_root = source_root
        self.deploy_root = deploy_root
        self.pages_project = pages_project

    def export_package(
        self,
        *,
        deployment_id: str | None = None,
        provider_target: str = PROVIDER_CLOUDFLARE,
    ) -> DeploymentResult:
        """Build public-subset artifact export + manifest + rollback metadata."""
        dep_id = deployment_id or new_deployment_id()
        packages_dir = self.deploy_root / "packages"
        package_root = packages_dir / dep_id
        previous_id = read_last_deployment_id(self.deploy_root)

        export = export_public_package(
            source_root=self.source_root,
            package_root=package_root,
            clean=True,
        )
        if not export.ok:
            return DeploymentResult(
                ok=False,
                message=export.message,
                deployment_id=dep_id,
                provider_target=provider_target,
                export=export,
            )

        manifest = DeploymentManifest(
            schema_version=SCHEMA_VERSION,
            deployment_id=dep_id,
            created_at=utc_now_iso(),
            source_root=str(self.source_root),
            package_root=str(package_root),
            files=build_file_entries(package_root),
            public_file_count=len(export.copied_files),
            provider_target=provider_target,
            rollback={
                "previous_deployment_id": previous_id,
                "local_snapshot_hint": (
                    f"{self.deploy_root / 'snapshots' / dep_id}"
                    if previous_id
                    else None
                ),
            },
            cloudflare={
                "pages_project": self.pages_project,
                "direct_upload_ready": True,
                "wrangler_docs": "output/website-deploy/cloudflare/README-CLOUDFLARE-PAGES.md",
            },
        )
        manifest_path = write_manifest(manifest, package_root)

        snapshot_root = self.deploy_root / "snapshots" / dep_id
        if snapshot_root.exists():
            shutil.rmtree(snapshot_root)
        shutil.copytree(package_root, snapshot_root)

        append_rollback_record(
            self.deploy_root,
            {
                "deployment_id": dep_id,
                "provider_target": provider_target,
                "package_root": str(package_root),
                "snapshot_root": str(snapshot_root),
                "manifest_path": str(manifest_path),
                "previous_deployment_id": previous_id,
                "public_file_count": len(export.copied_files),
            },
        )

        cf_paths = write_cloudflare_config(self.deploy_root, project_name=self.pages_project)

        return DeploymentResult(
            ok=True,
            message="Deployment package exported",
            deployment_id=dep_id,
            provider_target=provider_target,
            export=export,
            manifest_path=str(manifest_path),
            package_root=str(package_root),
            snapshot_root=str(snapshot_root),
            cloudflare_config={k: str(v) for k, v in cf_paths.items()},
            details={
                "manifest_filename": MANIFEST_FILENAME,
                "copied_files": list(export.copied_files),
                "skipped_files": list(export.skipped_files),
            },
        )

    def deploy_local(
        self,
        target_dir: Path,
        *,
        deployment_id: str | None = None,
        export_first: bool = True,
    ) -> DeploymentResult:
        """Copy public package to a local docroot (Nginx/Caddy portable fallback)."""
        if export_first:
            result = self.export_package(
                deployment_id=deployment_id,
                provider_target=PROVIDER_LOCAL,
            )
            if not result.ok:
                return result
        else:
            dep_id = deployment_id or read_last_deployment_id(self.deploy_root)
            if not dep_id:
                return DeploymentResult(
                    ok=False,
                    message="No prior deployment package; run export_package first",
                    deployment_id=dep_id or "",
                    provider_target=PROVIDER_LOCAL,
                )
            package_root = self.deploy_root / "packages" / dep_id
            if not package_root.is_dir():
                return DeploymentResult(
                    ok=False,
                    message=f"Package not found: {package_root}",
                    deployment_id=dep_id,
                    provider_target=PROVIDER_LOCAL,
                )
            result = DeploymentResult(
                ok=True,
                message="Using existing package",
                deployment_id=dep_id,
                provider_target=PROVIDER_LOCAL,
                package_root=str(package_root),
            )

        package = Path(result.package_root)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(package, target_dir)

        append_rollback_record(
            self.deploy_root,
            {
                "event": "local_deploy",
                "deployment_id": result.deployment_id,
                "local_target": str(target_dir),
                "provider_target": PROVIDER_LOCAL,
            },
        )

        result.local_target = str(target_dir)
        result.message = f"Local deployment copied to {target_dir}"
        result.details = dict(result.details)
        result.details["local_docroot"] = str(target_dir)
        return result

    def prepare_cloudflare(self) -> dict[str, str]:
        """Refresh Cloudflare Pages configuration under deploy_root/cloudflare/."""
        paths = write_cloudflare_config(self.deploy_root, project_name=self.pages_project)
        return {k: str(v) for k, v in paths.items()}
