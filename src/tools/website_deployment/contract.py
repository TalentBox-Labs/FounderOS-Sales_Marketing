"""Output directory and public-subset contract for website deployment (M5)."""

from __future__ import annotations

from pathlib import Path

from src.tools.runtime_paths import REPO_ROOT

# Mirrors Static Provider default; read-only contract reference (Core unchanged).
DEFAULT_SOURCE_ROOT = REPO_ROOT / "output" / "website"
DEFAULT_DEPLOY_ROOT = REPO_ROOT / "output" / "website-deploy"

PUBLIC_PAGE_ARTIFACT_NAME = "index.html"
PUBLIC_ROOT_FEED_NAMES = frozenset({"sitemap.xml", "rss.xml"})
OPERATOR_ARTIFACT_NAMES = frozenset({"metadata.json", "source.md"})

MANIFEST_FILENAME = "deployment-manifest.json"
ROLLBACK_HISTORY_JSONL = "rollback-history.jsonl"
CLOUDFLARE_CONFIG_DIRNAME = "cloudflare"


def is_public_page_path(relative: Path) -> bool:
    """True when path is ``{slug}/index.html`` (single slug segment)."""
    parts = relative.parts
    if len(parts) != 2:
        return False
    slug, name = parts
    if not slug or slug.startswith("."):
        return False
    return name == PUBLIC_PAGE_ARTIFACT_NAME


def is_public_root_feed(relative: Path) -> bool:
    return len(relative.parts) == 1 and relative.name in PUBLIC_ROOT_FEED_NAMES


def is_public_artifact(relative: Path) -> bool:
    return is_public_page_path(relative) or is_public_root_feed(relative)
