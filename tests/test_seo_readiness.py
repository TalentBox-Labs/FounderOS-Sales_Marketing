"""Tests for SEO readiness read model (S0)."""

from __future__ import annotations

from src.tools.seo_engine import FindingLevel, evaluate_html_readiness


def _sample_html(*, canonical: str = "https://example.invalid/blog/page") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <title>Sample Page Title Here</title>
  <meta name="description" content="A useful description for search snippets." />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:url" content="{canonical}" />
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"Article"}}</script>
</head>
<body>
  <article>
    <h1>Sample Page Title Here</h1>
    <h2>Section</h2>
    <p><a href="/blog/other">Other</a></p>
  </article>
</body>
</html>"""


def test_readiness_passes_minimal_valid_page() -> None:
    report = evaluate_html_readiness(
        _sample_html(), slug="page", configured_origin="https://example.invalid"
    )
    assert report.ok
    assert not any(f.level == FindingLevel.ERROR for f in report.findings)


def test_readiness_flags_missing_title() -> None:
    html = _sample_html().replace("<title>Sample Page Title Here</title>", "")
    report = evaluate_html_readiness(html, configured_origin="https://example.invalid")
    codes = {f.code for f in report.findings}
    assert "title_missing" in codes
    assert not report.ok


def test_readiness_warns_deprecated_host() -> None:
    report = evaluate_html_readiness(
        _sample_html(canonical="https://workcrew.ai/blog/page"),
        configured_origin="https://example.invalid",
    )
    codes = {f.code for f in report.findings}
    assert "deprecated_host" in codes
