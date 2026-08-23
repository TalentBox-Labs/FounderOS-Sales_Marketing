"""Focused tests for Website Deployment Adapter (Sprint M5)."""

from __future__ import annotations

import json
from pathlib import Path

from src.tools.website_engine import StaticWebsiteProvider, publish_content
from src.tools.website_deployment import (
    DeploymentAdapter,
    export_public_package,
)
from src.tools.website_deployment.contract import (
    MANIFEST_FILENAME,
    is_public_artifact,
)
from src.tools.website_deployment.manifest import build_file_entries
from tests.test_static_provider import _request, _write_bundle


class TestPublicSubsetContract:
    def test_public_artifact_rules(self) -> None:
        assert is_public_artifact(Path("hiring-systems/index.html"))
        assert is_public_artifact(Path("sitemap.xml"))
        assert is_public_artifact(Path("rss.xml"))
        assert not is_public_artifact(Path("hiring-systems/metadata.json"))
        assert not is_public_artifact(Path("hiring-systems/source.md"))
        assert not is_public_artifact(Path("nested/extra/index.html"))


class TestExportPublicPackage:
    def test_export_excludes_operator_files(self, tmp_path: Path) -> None:
        source = tmp_path / "output" / "website"
        out_pkg = tmp_path / "pkg"
        provider = StaticWebsiteProvider(output_dir=source)
        provider.publish(_request())

        result = export_public_package(source_root=source, package_root=out_pkg)
        assert result.ok
        assert (out_pkg / "hiring-systems" / "index.html").is_file()
        assert (out_pkg / "sitemap.xml").is_file()
        assert (out_pkg / "rss.xml").is_file()
        assert not (out_pkg / "hiring-systems" / "metadata.json").exists()
        assert not (out_pkg / "hiring-systems" / "source.md").exists()
        assert "hiring-systems/metadata.json" in result.skipped_files

    def test_export_fails_when_source_missing(self, tmp_path: Path) -> None:
        result = export_public_package(
            source_root=tmp_path / "missing",
            package_root=tmp_path / "pkg",
        )
        assert not result.ok


class TestDeploymentAdapter:
    def test_export_writes_manifest_and_rollback(self, tmp_path: Path) -> None:
        source = tmp_path / "output" / "website"
        deploy_root = tmp_path / "output" / "website-deploy"
        StaticWebsiteProvider(output_dir=source).publish(_request())

        adapter = DeploymentAdapter(source_root=source, deploy_root=deploy_root)
        result = adapter.export_package()
        assert result.ok
        package = Path(result.package_root)
        manifest_path = package / MANIFEST_FILENAME
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["deployment_id"] == result.deployment_id
        assert manifest["public_file_count"] >= 3
        assert manifest["cloudflare"]["direct_upload_ready"] is True

        history = deploy_root / "rollback-history.jsonl"
        assert history.is_file()
        assert Path(result.snapshot_root).is_dir()
        assert (deploy_root / "cloudflare" / "wrangler.toml").is_file()

    def test_local_deploy_copies_package(self, tmp_path: Path) -> None:
        source = tmp_path / "output" / "website"
        deploy_root = tmp_path / "output" / "website-deploy"
        docroot = tmp_path / "srv" / "www"
        StaticWebsiteProvider(output_dir=source).publish(_request())

        adapter = DeploymentAdapter(source_root=source, deploy_root=deploy_root)
        result = adapter.deploy_local(docroot)
        assert result.ok
        assert (docroot / "hiring-systems" / "index.html").is_file()
        assert not (docroot / "hiring-systems" / "metadata.json").exists()

    def test_rollback_chain_records_previous_id(self, tmp_path: Path) -> None:
        source = tmp_path / "output" / "website"
        deploy_root = tmp_path / "output" / "website-deploy"
        StaticWebsiteProvider(output_dir=source).publish(_request())
        adapter = DeploymentAdapter(source_root=source, deploy_root=deploy_root)

        first = adapter.export_package()
        second = adapter.export_package()
        assert second.ok
        manifest = json.loads(
            (Path(second.package_root) / MANIFEST_FILENAME).read_text(encoding="utf-8")
        )
        assert manifest["rollback"]["previous_deployment_id"] == first.deployment_id


class TestIntegrationWithPublishContent:
    def test_publish_then_deploy_adapter(self, tmp_path: Path) -> None:
        _write_bundle(tmp_path)
        source = tmp_path / "output" / "website"
        publish_content(
            "W99",
            repo_root=tmp_path,
            provider_name="static",
            output_dir=source,
        )
        deploy_root = tmp_path / "output" / "website-deploy"
        adapter = DeploymentAdapter(source_root=source, deploy_root=deploy_root)
        result = adapter.export_package()
        assert result.ok
        entries = build_file_entries(Path(result.package_root))
        paths = {e["path"] for e in entries if e["path"] != MANIFEST_FILENAME}
        assert "hiring-systems/index.html" in paths
