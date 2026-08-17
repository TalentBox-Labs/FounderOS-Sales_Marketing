"""Canonical website content representation from editorial filesystem bundles.

Reads ``input/{week}/`` artifacts only. No CMS database.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.tools.runtime_paths import REPO_ROOT

FINAL_FILENAME = "05_Final.md"
SEO_PLAN_FILENAME = "02_SEO_Plan.md"
CONTENT_ID_RE = re.compile(r"^W\d{2}[A-Z]?$", re.IGNORECASE)


@dataclass(frozen=True)
class WebsiteContent:
    """Provider-neutral website article derived from an approved bundle."""

    content_id: str
    bundle_path: str
    title: str
    markdown_body: str
    front_matter: dict[str, str] = field(default_factory=dict)
    primary_keyword: str = ""
    description_hint: str = ""
    source_final_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_id": self.content_id,
            "bundle_path": self.bundle_path,
            "title": self.title,
            "markdown_body": self.markdown_body,
            "front_matter": dict(self.front_matter),
            "primary_keyword": self.primary_keyword,
            "description_hint": self.description_hint,
            "source_final_path": self.source_final_path,
        }


def normalize_content_id(content_id: str) -> str:
    cid = (content_id or "").strip().upper()
    if not CONTENT_ID_RE.match(cid):
        raise ValueError(f"Invalid content_id: {content_id!r}")
    return cid


def split_front_matter(text: str) -> tuple[dict[str, str] | None, str]:
    """Split YAML-like front matter; values are plain strings (no nested YAML)."""
    if not text.lstrip().startswith("---"):
        return None, text
    lines = text.splitlines()
    if len(lines) < 2 or lines[0].strip() != "---":
        return None, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    body = "\n".join(lines[end + 1 :])
    data: dict[str, str] = {}
    for raw in lines[1:end]:
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and (
            (value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")
        ):
            value = value[1:-1].strip()
        data[key] = value
    return data, body


def _first_paragraph(markdown_body: str) -> str:
    chunks: list[str] = []
    for line in markdown_body.splitlines():
        stripped = line.strip()
        if not stripped:
            if chunks:
                break
            continue
        if stripped.startswith("#"):
            continue
        chunks.append(stripped)
    text = " ".join(chunks).strip()
    return text


def _seo_description_hint(seo_text: str) -> str:
    """Best-effort hint from SEO plan CTA / notes — not SEO Engine scoring."""
    for line in seo_text.splitlines():
        lower = line.lower().strip()
        if lower.startswith("## cta") or lower.startswith("## notes"):
            continue
        if lower.startswith("try ") or lower.startswith("get "):
            return line.strip()
    return ""


def resolve_bundle_dir(
    content_id: str,
    *,
    bundle: str | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Resolve ``input/{week}/`` directory from content_id or job bundle path."""
    root = repo_root or REPO_ROOT
    cid = normalize_content_id(content_id)
    if bundle:
        rel = bundle.strip().rstrip("/")
        if rel.startswith("input/"):
            path = root / rel
        else:
            path = Path(rel)
            if not path.is_absolute():
                path = root / rel
        if path.is_dir():
            return path
    return root / "input" / cid


def load_website_content(
    content_id: str,
    *,
    bundle: str | None = None,
    repo_root: Path | None = None,
) -> WebsiteContent:
    """Load canonical website content from filesystem bundle artifacts."""
    root = repo_root or REPO_ROOT
    cid = normalize_content_id(content_id)
    bundle_dir = resolve_bundle_dir(cid, bundle=bundle, repo_root=root)
    final_path = bundle_dir / FINAL_FILENAME
    if not final_path.is_file():
        raise FileNotFoundError(
            f"Website content requires {FINAL_FILENAME} under {bundle_dir}"
        )

    text = final_path.read_text(encoding="utf-8")
    fm, body = split_front_matter(text)
    front_matter = fm or {}
    title = (
        front_matter.get("article_title")
        or front_matter.get("title")
        or _heading_title(body)
        or cid
    ).strip()
    primary_keyword = (front_matter.get("primary_keyword") or "").strip()
    description_hint = _first_paragraph(body)

    seo_path = bundle_dir / SEO_PLAN_FILENAME
    if seo_path.is_file():
        seo_hint = _seo_description_hint(seo_path.read_text(encoding="utf-8"))
        if seo_hint and not description_hint:
            description_hint = seo_hint

    try:
        bundle_path = str(bundle_dir.relative_to(root))
    except ValueError:
        bundle_path = str(bundle_dir)

    try:
        source_rel = str(final_path.relative_to(root))
    except ValueError:
        source_rel = str(final_path)

    return WebsiteContent(
        content_id=cid,
        bundle_path=bundle_path,
        title=title,
        markdown_body=body.strip() + ("\n" if body.strip() else ""),
        front_matter=front_matter,
        primary_keyword=primary_keyword,
        description_hint=description_hint,
        source_final_path=source_rel,
    )


def _heading_title(markdown_body: str) -> str:
    for line in markdown_body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""
