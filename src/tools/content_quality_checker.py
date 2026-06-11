"""
Phase 2C — Deterministic body-quality scoring for `05_Final.md`.

Rule-based only (no LLMs). Complements metadata/schema gates and structure checks.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from src.tools.metadata_checker import _split_front_matter
from src.tools.runtime_paths import REPO_ROOT, load_runtime_config

# --- Thresholds (tune here; documented in Artifact PRD) ---------------------------------

MIN_BODY_WORDS_HARD_FAIL = 400
MIN_BODY_WORDS_SOFT = 800
PASS_SCORE_MIN = 60
STRONG_SCORE_PROMOTE = 75

DEDUCT_NO_FAQ = 18
DEDUCT_TOO_FEW_H2 = 12  # if H2 count < 3 (top-level ## not ### )
DEDUCT_H2_SPARSE = 6  # if 3 <= H2 < 5
DEDUCT_KEYWORD_WEAK = 14
DEDUCT_KEYWORD_MILD = 7
DEDUCT_NO_HTTPS_BODY = 8
DEDUCT_NO_CTA_SIGNAL = 14
DEDUCT_SHORT_BODY = 12  # words between MIN_BODY_WORDS_SOFT and hard min handled separately
DEDUCT_DUP_PARA_EACH = 4
DEDUCT_DUP_PARA_CAP = 12
DEDUCT_RESEARCH_OVERLAP = 10
DEDUCT_NUMERIC_SPRAWL = 8  # many bare numeric claims

MIN_H2_TOPLEVEL = 3
PREFERRED_H2_TOPLEVEL = 5

RESEARCH_MIN_CHARS_FOR_OVERLAP = 1200
OVERLAP_FAIL_BELOW = 0.012

_STOPWORDS = frozenset(
    "the and for that this with from have were been their they about which while "
    "your into more than when what some these there such other were also been".split()
)


@dataclass
class QualityReport:
    quality_score: int
    risk_flags: list[str]
    promotion_recommendation: str
    metrics: dict[str, float | int | str] = field(default_factory=dict)
    deductions: list[tuple[str, int]] = field(default_factory=list)


def _strip_scalar(raw: str) -> str:
    s = raw.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1].strip()
    return s


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def _h2_toplevel_count(body: str) -> int:
    """Count `## ` headings that are not `###`."""
    return len(re.findall(r"(?m)^## (?![#])", body))


def _has_faq_section(body: str) -> bool:
    if "Frequently Asked Questions" in body:
        return True
    return bool(re.search(r"(?mi)^##\s+faq\s*$", body))


def _https_in_body(body: str) -> int:
    """Count https/http URLs in body (excludes content inside fenced code blocks)."""
    out: list[str] = []
    rest = body
    while "```" in rest:
        a, _, b = rest.partition("```")
        out.append(a)
        if "```" in b:
            _, _, rest = b.partition("```")
        else:
            rest = ""
    out.append(rest)
    scrubbed = "\n".join(out)
    return len(re.findall(r"https?://[^\s)>\]]+", scrubbed, re.IGNORECASE))


def _cta_signal(body_lower: str, variants: list[str]) -> bool:
    for v in variants:
        if v.strip().lower() in body_lower:
            return True
    if "workcrew" in body_lower and any(
        x in body_lower for x in ("demo", "trial", "free", "book", "try ", "workflow")
    ):
        return True
    return False


def _keyword_metrics(body_lower: str, primary_keyword: str) -> tuple[int, bool]:
    """
    Returns (phrase_count, tokens_ok).
    tokens_ok: each whitespace token in PK appears at least twice (light spread heuristic).
    """
    pk = primary_keyword.strip().lower()
    if not pk:
        return 0, False
    phrase_count = body_lower.count(pk)
    tokens = [t for t in re.split(r"\s+", pk) if len(t) > 2]
    if not tokens:
        return phrase_count, phrase_count >= 2
    ok = sum(1 for t in tokens if body_lower.count(t) >= 2) >= len(tokens)
    return phrase_count, ok


def _keyword_in_opening(body_lower: str, primary_keyword: str, opening_words: int = 400) -> bool:
    pk = primary_keyword.strip().lower()
    if not pk:
        return True
    words = body_lower.split()
    opening = " ".join(words[:opening_words])
    first_tok = pk.split()[0] if pk.split() else ""
    return bool(first_tok) and first_tok in opening


def _duplicate_paragraph_count(body: str) -> int:
    paras = [
        re.sub(r"\s+", " ", p).strip()
        for p in body.split("\n\n")
        if len(re.sub(r"\s+", " ", p).strip()) > 80
    ]
    norm = [p.lower() for p in paras]
    seen: set[str] = set()
    dup = 0
    for p in norm:
        if p in seen:
            dup += 1
        seen.add(p)
    return dup


def _significant_words(text: str) -> set[str]:
    return {
        w
        for w in re.findall(r"[a-z]{5,}", text.lower())
        if w not in _STOPWORDS
    }


def _research_overlap_ratio(body: str, research: str) -> float:
    if len(research.strip()) < RESEARCH_MIN_CHARS_FOR_OVERLAP:
        return 1.0
    rb = _significant_words(body)
    rr = _significant_words(research)
    if not rr:
        return 1.0
    inter = len(rb & rr)
    return inter / len(rr)


def _numeric_sprawl(body: str) -> bool:
    """Heuristic: many isolated percentage / currency figures may need citations."""
    pct = len(re.findall(r"\b\d{1,2}(?:\.\d)?%", body))
    return pct >= 18


def compute_quality_report(
    *,
    fm: dict[str, str] | None,
    body: str,
    research_text: str | None,
    cta_variants: list[str],
) -> QualityReport:
    risk_flags: list[str] = []
    deductions: list[tuple[str, int]] = []
    metrics: dict[str, float | int | str] = {}

    body_lc = body.lower()
    words = _word_count(body)
    metrics["word_count"] = words
    h2 = _h2_toplevel_count(body)
    metrics["h2_toplevel_count"] = h2
    faq = _has_faq_section(body)
    metrics["faq_section"] = "yes" if faq else "no"
    https_n = _https_in_body(body)
    metrics["https_url_count_in_body"] = https_n
    pk_raw = (fm or {}).get("primary_keyword", "")
    pk = _strip_scalar(str(pk_raw)) if pk_raw else ""
    phrase_n, token_ok = _keyword_metrics(body_lc, pk)
    metrics["primary_keyword_phrase_hits"] = phrase_n
    metrics["primary_keyword_token_coverage_ok"] = "yes" if token_ok else "no"
    opening_kw = _keyword_in_opening(body_lc, pk)
    metrics["keyword_in_opening"] = "yes" if opening_kw else "no"

    dup_n = _duplicate_paragraph_count(body)
    metrics["duplicate_paragraph_blocks"] = dup_n

    overlap_r = 1.0
    if research_text and len(research_text.strip()) >= RESEARCH_MIN_CHARS_FOR_OVERLAP:
        overlap_r = _research_overlap_ratio(body, research_text)
        metrics["research_lexical_overlap_ratio"] = round(overlap_r, 4)
    else:
        metrics["research_lexical_overlap_ratio"] = "n/a"

    cta_ok = _cta_signal(body_lc, cta_variants)
    metrics["cta_signal"] = "yes" if cta_ok else "no"

    if words < MIN_BODY_WORDS_HARD_FAIL:
        risk_flags.append("body_too_short_hard")
        deductions.append(("body_below_hard_word_floor", 100))
        return QualityReport(
            quality_score=0,
            risk_flags=risk_flags,
            promotion_recommendation="hold",
            metrics=metrics,
            deductions=deductions,
        )

    score = 100

    if words < MIN_BODY_WORDS_SOFT:
        deductions.append(("body_below_soft_word_target", DEDUCT_SHORT_BODY))
        score -= DEDUCT_SHORT_BODY
        risk_flags.append("body_short")

    if not faq:
        deductions.append(("missing_faq_section", DEDUCT_NO_FAQ))
        score -= DEDUCT_NO_FAQ
        risk_flags.append("missing_faq")

    if h2 < MIN_H2_TOPLEVEL:
        deductions.append(("few_h2_sections", DEDUCT_TOO_FEW_H2))
        score -= DEDUCT_TOO_FEW_H2
        risk_flags.append("sparse_headings")
    elif h2 < PREFERRED_H2_TOPLEVEL:
        deductions.append(("moderate_h2_count", DEDUCT_H2_SPARSE))
        score -= DEDUCT_H2_SPARSE

    if pk:
        if phrase_n < 2 and not token_ok:
            deductions.append(("primary_keyword_underrepresented", DEDUCT_KEYWORD_WEAK))
            score -= DEDUCT_KEYWORD_WEAK
            risk_flags.append("keyword_weak")
        elif phrase_n < 2 or not token_ok:
            deductions.append(("primary_keyword_mild", DEDUCT_KEYWORD_MILD))
            score -= DEDUCT_KEYWORD_MILD
            risk_flags.append("keyword_mild")
        if not opening_kw:
            deductions.append(("keyword_not_in_opening_excerpt", 5))
            score -= 5
            risk_flags.append("keyword_late")

    if https_n == 0:
        deductions.append(("no_https_urls_in_body", DEDUCT_NO_HTTPS_BODY))
        score -= DEDUCT_NO_HTTPS_BODY
        risk_flags.append("no_outbound_urls")

    if not cta_ok:
        deductions.append(("no_cta_signal", DEDUCT_NO_CTA_SIGNAL))
        score -= DEDUCT_NO_CTA_SIGNAL
        risk_flags.append("weak_cta_signal")

    if dup_n > 0:
        d = min(DEDUCT_DUP_PARA_CAP, DEDUCT_DUP_PARA_EACH * dup_n)
        deductions.append(("duplicate_paragraphs", d))
        score -= d
        risk_flags.append("duplicate_paragraphs")

    if (
        research_text
        and len(research_text.strip()) >= RESEARCH_MIN_CHARS_FOR_OVERLAP
        and overlap_r < OVERLAP_FAIL_BELOW
    ):
        deductions.append(("low_research_term_overlap", DEDUCT_RESEARCH_OVERLAP))
        score -= DEDUCT_RESEARCH_OVERLAP
        risk_flags.append("research_drift")

    if _numeric_sprawl(body):
        deductions.append(("numeric_claim_density_high", DEDUCT_NUMERIC_SPRAWL))
        score -= DEDUCT_NUMERIC_SPRAWL
        risk_flags.append("numeric_claim_density")

    score = max(0, min(100, score))

    if score >= STRONG_SCORE_PROMOTE:
        rec = "promote"
    elif score >= PASS_SCORE_MIN:
        rec = "revise"
    else:
        rec = "hold"

    return QualityReport(
        quality_score=score,
        risk_flags=risk_flags,
        promotion_recommendation=rec,
        metrics=metrics,
        deductions=deductions,
    )


def run_content_quality_check() -> None:
    runtime = load_runtime_config()
    active = runtime["active_week"]
    final_rel = runtime["final_path"]
    research_rel = runtime.get("research_path", "")
    final_path = REPO_ROOT / final_rel
    out_dir = REPO_ROOT / Path(runtime["qa_output_dir"].strip("/"))
    output_path = out_dir / f"{active}_Content_Quality_Check.md"

    variants = list((runtime.get("research_gate") or {}).get("cta_variants") or [])

    passed: list[str] = []
    failed: list[str] = []

    research_text: str | None = None
    if research_rel:
        rp = REPO_ROOT / research_rel
        if rp.is_file():
            research_text = rp.read_text(encoding="utf-8")

    if not final_path.is_file():
        failed.append(f"- Final file missing: {final_path}")
        report = _render_markdown(
            active,
            QualityReport(
                quality_score=0,
                risk_flags=["missing_final"],
                promotion_recommendation="hold",
                metrics={},
                deductions=[("missing_file", 100)],
            ),
            passed,
            failed,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(report)
        sys.exit(1)

    text = final_path.read_text(encoding="utf-8")
    fm, body = _split_front_matter(text)
    if fm is None:
        failed.append("- No YAML front matter (Phase 2C requires split body)")
        body = text

    qr = compute_quality_report(fm=fm, body=body, research_text=research_text, cta_variants=variants)

    passed.append(f"- quality_score: **{qr.quality_score}** (0–100)")
    passed.append(f"- promotion_recommendation: **{qr.promotion_recommendation}**")
    passed.append(f"- risk_flags: `{qr.risk_flags}`")
    for k, v in qr.metrics.items():
        passed.append(f"- metric `{k}`: {v}")
    for reason, pts in qr.deductions:
        passed.append(f"- deduction: {reason} (−{pts})")

    verdict_fail = qr.quality_score < PASS_SCORE_MIN or "body_too_short_hard" in qr.risk_flags
    if verdict_fail:
        failed.append(
            f"- Phase 2C threshold: score < {PASS_SCORE_MIN} or hard body failure → gate FAIL"
        )
    else:
        passed.append(f"- Score meets minimum **{PASS_SCORE_MIN}** for PASS")

    report = _render_markdown(active, qr, passed, failed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(report)
    sys.exit(1 if verdict_fail else 0)


def _render_markdown(
    active: str,
    qr: QualityReport,
    passed: list[str],
    failed: list[str],
) -> str:
    lines = [
        f"# {active} Content Quality (Phase 2C)",
        "",
        "## Quality summary",
        "",
        f"- **quality_score:** {qr.quality_score}",
        f"- **risk_flags:** {qr.risk_flags}",
        f"- **promotion_recommendation:** {qr.promotion_recommendation}",
        "",
        "## Passed checks",
        "",
    ]
    lines.extend(passed if passed else ["- None"])
    lines.extend(["", "## Failed checks", ""])
    lines.extend(failed if failed else ["- None"])
    lines.extend(["", "## Final Verdict", "", "FAIL" if failed else "PASS", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    run_content_quality_check()
