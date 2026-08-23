# Technical SEO Engine v1.0 — Baseline Freeze

**Sprint:** S2.5  
**Status:** **FROZEN**  
**Baseline version:** TECHNICAL SEO ENGINE **v1.0**  
**Freeze date:** 2026-08-11  
**Architecture:** v2.2 (frozen)  
**Related independent freeze:** SEO READINESS ENGINE v1.0 (S1.5) — **UNCHANGED**

---

## 1. Freeze declaration

Technical SEO Engine Phase 1 (S2), as closed out in S2.1, is hereby frozen as:

**TECHNICAL SEO ENGINE v1.0**

Future changes to this contract require an explicit subsequent sprint, compatibility assessment, tests, and documented rationale.

S2.5 performed **VERIFY → DOCUMENT → FREEZE** only. Feature code changes: **0**.

---

## 2. Module layout (authoritative)

| Path | Role |
|------|------|
| `src/tools/seo_engine/technical/policy.py` | Technical scoring thresholds (independent of S1) |
| `src/tools/seo_engine/technical/models.py` | Findings, severities, reports |
| `src/tools/seo_engine/technical/parsers.py` | Sitemap/RSS/HTML artifact adapters |
| `src/tools/seo_engine/technical/rules.py` | Deterministic technical rules |
| `src/tools/seo_engine/technical/engine.py` | Orchestration + aggregation |
| `src/tools/seo_engine/technical/audit.py` | Non-authoritative `output/seo/technical/` writes |
| `src/tools/site_origin.py` | Origin / indexing gates (shared) |

---

## 3. Check families verified (10)

| # | Family (`TechCategory`) | Analysis status |
|---|-------------------------|-----------------|
| 1 | CANONICAL | PASS |
| 2 | ROBOTS | **PARTIAL — ACCEPTED DOCUMENTED LIMITATION** |
| 3 | SITEMAP | PASS |
| 4 | STRUCTURED_DATA | PASS |
| 5 | OPEN_GRAPH | PASS |
| 6 | INTERNAL_LINKS | PASS |
| 7 | CRAWLABILITY | PASS (local evidence only) |
| 8 | HTTP_ROUTING | PASS |
| 9 | FEED | PASS |
| 10 | CONSISTENCY | PASS |

**Technical Check Families Verified:** **10**

---

## 4. Rule registry count (authoritative)

Verified from `rules.py` + `engine.py` (`tech_*` IDs):

**Technical Rules Verified:** **72**

Matches S2 report (72). No silent normalization.

Severity / blocking / scoring semantics are frozen per `S2_TECHNICAL_SEO_RULE_REGISTRY.md` and implementation:

```
tech_score = max(0, 100 - 35*CRITICAL - 20*ERROR - 6*WARNING)
```

`DOMAIN_BLOCKED` does not reduce score; it gates overall status (highest precedence).

---

## 5. Accepted v1.0 limitation — Robots

| Item | Value |
|------|-------|
| Root cause (S2.1) | **B — WEBSITE ENGINE CAPABILITY MISSING** |
| Limitation | Website Engine does not emit `robots.txt` or page-level robots meta |
| Technical SEO behavior | Detects absence + accidental index risk; does **not** generate robots assets |
| Robots Analysis | **PARTIAL — ACCEPTED DOCUMENTED LIMITATION** |
| Blocks v1.0 freeze | **NO** |

Debt record: `docs/governance/WEBSITE_ENGINE_TECHNICAL_DEBT.md` → **WEBSITE-SEO-ROBOTS-001**

---

## 6. Read-only architectural contract (frozen)

Technical SEO Engine v1.0 **MUST NOT**:

- fix / rewrite / auto-edit artifacts  
- publish  
- submit sitemaps or URLs for indexing  
- crawl the Internet  
- call external SEO / rank APIs  
- AI auto-remediate  

Reports carry: `read_only: true`, `mutates_content: false`, `submits_to_search_engines: false`, `s1_readiness_contract: UNCHANGED`.

---

## 7. Origin / indexing safety (frozen expectations)

| Check | Result |
|-------|--------|
| No invented production domain | PASS |
| No `workcrew.ai` runtime fallback | PASS |
| `pages.dev` not production canonical | PASS |
| `example.invalid` not production | PASS |
| Unratified origin blocks activation | PASS |
| Production SEO activation | **BLOCKED PENDING DOMAIN** |

Verified domain blockers on live sample remain **DOMAIN_BLOCKED** (8/8), not misclassified technical failures.

---

## 8. Separation from S1.5

| Layer | Version | Status |
|-------|---------|--------|
| SEO Readiness Engine | v1.0 | FROZEN (S1.5) — independent |
| Technical SEO Engine | v1.0 | FROZEN (S2.5) — this baseline |

Do not merge contracts. S2 consumes Website artifacts; S1 readiness scoring/rules remain separate.

---

## 9. Post-freeze

Do **not** auto-start S3. Next step: **Marketing OS priority review**.
