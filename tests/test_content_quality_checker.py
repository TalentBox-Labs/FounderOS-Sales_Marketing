"""Phase 2C deterministic content quality scoring."""

from __future__ import annotations

from src.tools.content_quality_checker import (
    PASS_SCORE_MIN,
    QualityReport,
    compute_quality_report,
)


def test_compute_quality_high_when_strong_article():
    filler = (
        "Supporting recruiter sourcing narrative text for length. " * 120
    )
    body = """# Title Here

Intro linkedin recruiter alternatives opening.

## Section One

Some text with linkedin recruiter alternatives repeated for coverage.

## Section Two

More linkedin recruiter alternatives discussion.

## Three

""" + filler + """

## Four

""" + filler + """

## Frequently Asked Questions

### One?

Answer try workcrew free.

### Two?

Answer https://example.com/source

"""
    qr = compute_quality_report(
        fm={"primary_keyword": "linkedin recruiter alternatives"},
        body=body,
        research_text=None,
        cta_variants=["try workcrew free"],
    )
    assert qr.quality_score >= PASS_SCORE_MIN
    assert qr.promotion_recommendation in ("promote", "revise")


def test_hard_fail_short_body():
    body = "word " * 50
    qr = compute_quality_report(
        fm={"primary_keyword": "test"},
        body=body,
        research_text=None,
        cta_variants=[],
    )
    assert qr.quality_score == 0
    assert "body_too_short_hard" in qr.risk_flags


def test_missing_faq_and_cta_score_low():
    body = ("paragraph text " * 200) + "\n\n## Only One Section\n\n" + ("more " * 100)
    qr = compute_quality_report(
        fm={"primary_keyword": "foobar keyword phrase"},
        body=body,
        research_text=None,
        cta_variants=["try workcrew"],
    )
    assert "missing_faq" in qr.risk_flags
    assert "weak_cta_signal" in qr.risk_flags


def test_https_and_duplicate_flags():
    pad = "Additional narrative filler words for minimum article length. " * 80
    dup = (
        "Same paragraph repeated below with keyword keyword keyword coverage area. "
        + pad
    )
    body = f"""# X

## A

{dup}

## B

{pad}

## Frequently Asked Questions

### Q?

A short answer.

{dup}

"""
    qr = compute_quality_report(
        fm={"primary_keyword": "keyword coverage"},
        body=body,
        research_text=None,
        cta_variants=["try workcrew free"],
    )
    assert "no_outbound_urls" in qr.risk_flags
    assert "duplicate_paragraphs" in qr.risk_flags


def test_quality_report_dataclass_fields():
    r = QualityReport(
        quality_score=70,
        risk_flags=["x"],
        promotion_recommendation="revise",
        metrics={"a": 1},
        deductions=[("t", 5)],
    )
    assert r.quality_score == 70
