"""Markdown → HTML rendering contract (stdlib only; no external HTTP)."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_INLINE_CODE = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class RenderResult:
    """Rendering contract object produced by Website Engine."""

    html: str
    content_type: str = "text/html; charset=utf-8"
    renderer: str = "website_engine.stdlib_markdown"
    source_format: str = "markdown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "html": self.html,
            "content_type": self.content_type,
            "renderer": self.renderer,
            "source_format": self.source_format,
        }


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = _BOLD.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC.sub(r"<em>\1</em>", escaped)
    escaped = _INLINE_CODE.sub(r"<code>\1</code>", escaped)
    escaped = _LINK.sub(r'<a href="\2">\1</a>', escaped)
    return escaped


def markdown_to_html(markdown: str) -> str:
    """Convert a practical subset of Markdown to HTML (headings, lists, p, inline)."""
    lines = (markdown or "").splitlines()
    out: list[str] = []
    i = 0
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            close_lists()
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            close_lists()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        ul_item = re.match(r"^[-*]\s+(.*)$", stripped)
        if ul_item:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_inline(ul_item.group(1))}</li>")
            i += 1
            continue

        ol_item = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ol_item:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_inline(ol_item.group(1))}</li>")
            i += 1
            continue

        close_lists()
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith("#") or re.match(r"^[-*]\s+", nxt) or re.match(
                r"^\d+\.\s+", nxt
            ):
                break
            para_lines.append(nxt)
            i += 1
        out.append(f"<p>{_inline(' '.join(para_lines))}</p>")

    close_lists()
    return "\n".join(out) + ("\n" if out else "")


def render_markdown(markdown: str) -> RenderResult:
    """Public rendering contract entrypoint."""
    return RenderResult(html=markdown_to_html(markdown))
