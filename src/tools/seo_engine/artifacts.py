"""Website Engine / static artifact adapter (NOVA — S1).

Read-only inspection of existing rendered artifacts under output/website/.
Does not render, publish, or mutate source content.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.tools.runtime_paths import REPO_ROOT
from src.tools.seo_engine.extract import ExtractedPage, extract_page
from src.tools.seo_engine.policy import MAX_PAGES_PER_BATCH

DEFAULT_WEBSITE_ARTIFACT_ROOT = REPO_ROOT / "output" / "website"

_SAFE_SLUG_DIR = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,200}$")


def default_artifact_root() -> Path:
    return DEFAULT_WEBSITE_ARTIFACT_ROOT


def list_page_slugs(artifact_root: Path, *, max_pages: int = MAX_PAGES_PER_BATCH) -> tuple[list[str], bool]:
    """List page directories that contain index.html. Returns (slugs, truncated)."""
    root = Path(artifact_root)
    if not root.is_dir():
        return [], False
    slugs: list[str] = []
    truncated = False
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not _SAFE_SLUG_DIR.match(child.name):
            continue
        if not (child / "index.html").is_file():
            continue
        if len(slugs) >= max_pages:
            truncated = True
            break
        slugs.append(child.name)
    return slugs, truncated


def _feed_contains(feed_path: Path, slug: str) -> bool | None:
    if not feed_path.is_file():
        return None
    try:
        text = feed_path.read_text(encoding="utf-8")
    except OSError:
        return None
    return slug in text


def load_page_artifact(
    artifact_root: Path,
    slug: str,
) -> ExtractedPage | None:
    """Load a single page artifact. Returns None if HTML missing."""
    root = Path(artifact_root)
    html_path = root / slug / "index.html"
    if not html_path.is_file():
        return None
    html = html_path.read_text(encoding="utf-8")
    meta: dict = {}
    meta_path = root / slug / "metadata.json"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {}
    page = extract_page(html, slug=slug, metadata=meta)
    page.in_sitemap = _feed_contains(root / "sitemap.xml", slug)
    page.in_rss = _feed_contains(root / "rss.xml", slug)
    return page


def load_site_inventory(
    artifact_root: Path,
    *,
    max_pages: int = MAX_PAGES_PER_BATCH,
) -> tuple[list[ExtractedPage], set[str], bool]:
    """Load pages + known slug inventory for local link checks.

    Returns (pages, known_slugs, truncated).
    """
    slugs, truncated = list_page_slugs(artifact_root, max_pages=max_pages)
    known = set(slugs)
    pages: list[ExtractedPage] = []
    for slug in slugs:
        page = load_page_artifact(artifact_root, slug)
        if page is not None:
            pages.append(page)
    return pages, known, truncated
