# S1.5 — SEO Readiness Engine Baseline (v1.0)

**Sprint:** S1.5  
**Agent:** ATLAS  
**Status:** BASELINE FROZEN  
**Baseline name:** SEO READINESS ENGINE v1.0  
**Freeze date:** 2026-08-11  
**Architecture:** v2.2 (frozen)

---

## 1. Freeze scope

Frozen:

1. SEO readiness state model  
2. Phase-1 deterministic check categories (12)  
3. Scoring semantics  
4. Severity semantics  
5. Read-only guarantee  
6. SEO readiness API contract  
7. SEO readiness UI read-only boundary  
8. SITE_ORIGIN interaction  
9. Origin / indexing safety  
10. Audit / output model  
11. Website Engine integration boundary  
12. Regression baseline  

**Not frozen as S2 scope:** technical SEO expansion, robots emission, Search Console, keyword strategy.

---

## 2. Verified module layout (actual)

| Path | Role |
|------|------|
| `src/tools/seo_engine/policy.py` | Thresholds / scoring constants |
| `src/tools/seo_engine/models.py` | CheckStatus, OverallStatus, results |
| `src/tools/seo_engine/extract.py` | HTML extraction |
| `src/tools/seo_engine/rules.py` | 12 check functions + outcome IDs |
| `src/tools/seo_engine/engine.py` | Orchestration + scoring + aggregate |
| `src/tools/seo_engine/artifacts.py` | Website artifact adapter (read-only) |
| `src/tools/seo_engine/audit.py` | Non-authoritative `output/seo/` writes |
| `src/tools/seo_engine/readiness.py` | S0 FindingLevel API (compat) |
| `src/tools/site_origin.py` | SITE_ORIGIN / indexing gates |

---

## 3. State model (frozen)

### CheckStatus

`PASS` · `WARNING` · `ERROR` · `DOMAIN_BLOCKED` · `NOT_APPLICABLE` · `INFO`

### OverallStatus (page / site aggregate)

Precedence (highest first):

1. `DOMAIN_BLOCKED`  
2. `ERROR`  
3. `WARNING`  
4. `PASS`

Numeric score **never** overrides `DOMAIN_BLOCKED`.

### Operator mapping (BEACON)

| Operator term | Implementation |
|---------------|----------------|
| BLOCKER | `DOMAIN_BLOCKED` / `domain_blockers[]` |
| ERROR | `ERROR` / `errors[]` |
| WARNING | `WARNING` / `warnings[]` |
| INFORMATION | `INFO` / `info[]` |

---

## 4. Scoring (frozen)

```
score = max(0, 100 - 25 * error_count - 8 * warning_count)
```

| Constant | Value |
|----------|-------|
| `SCORE_BASE` | 100 |
| `SCORE_ERROR_PENALTY` | 25 |
| `SCORE_WARNING_PENALTY` | 8 |
| `SCORE_DOMAIN_BLOCK_PENALTY` | 0 |
| `SCORE_INFO_PENALTY` | 0 |

`seo_ready` is True only when `status == PASS`.  
`ok` is True for `PASS` or `WARNING` (no ERROR / DOMAIN_BLOCKED).

---

## 5. Phase-1 checks (verified count)

**Check categories:** **12** (matches S1 report)

1. Title — `check_title`  
2. Meta description — `check_description`  
3. Slug — `check_slug`  
4. Canonical — `check_canonical`  
5. Indexability — `check_indexability`  
6. Open Graph — `check_open_graph`  
7. Structured data — `check_structured_data`  
8. Headings — `check_headings`  
9. Internal links — `check_internal_links`  
10. Sitemap eligibility — `check_sitemap_eligibility`  
11. Feed eligibility — `check_feed_eligibility`  
12. Duplicate risk — `check_duplicate_risk`  

**Outcome rule IDs in `rules.py`:** **60** (see rule registry).  
**Additional engine gate:** `html_missing` (artifact absent) — not one of the 12 categories.

Canonical registry: `SEO_READINESS_RULE_REGISTRY_v1.md`

---

## 6. SITE_ORIGIN interaction (frozen)

| Env | Role |
|-----|------|
| `FOUNDER_SITE_ORIGIN` | Scheme+host; default `https://example.invalid` |
| `FOUNDER_SITE_BASE_PATH` | Default `/blog` |
| `FOUNDER_SITE_ORIGIN_RATIFIED` | Required for indexing activation |

`workcrew.ai` is **not** a runtime fallback.  
`*.pages.dev` / deprecated hosts cannot authorize production SEO.

---

## 7. Read-only / authority boundaries

SEO Engine **may**: analyze, classify, score, recommend, write non-authoritative audits under `output/seo/`.

SEO Engine **must not**: mutate `input/`, render as Website Engine, publish, submit sitemaps, configure Search Console, approve editorial content.

---

## 8. Discrepancies vs S1 narrative (recorded, not rewritten)

| Item | S1 narrative | Actual | Freeze treatment |
|------|--------------|--------|------------------|
| “12 checks” | Categories | Confirmed 12 functions; 60 outcome IDs | Freeze both numbers explicitly |
| Policy unused constants | Not mentioned | `TITLE_WARN_SHORT`, `DESC_HARD_EMPTY` unused | Frozen as unused; no silent enablement |
| `/api/v1/seo` mutations | Readiness read-only | Legacy keyword POST/DELETE coexist on same prefix | Readiness routes frozen read-only; keyword routes out of this baseline |

---

## 9. Regression baseline (verified S1.5)

| Suite | Result |
|-------|--------|
| Focused SEO (`test_seo_readiness_engine` + `test_seo_readiness` + `test_site_origin`) | **34/34** |
| Full | **361 passed; 8 failed; 4 errors** |
| New regressions | **0** |
| Historical failure identities | UNCHANGED vs S1 |

---

## 10. Post-freeze change control

Changes to this contract require an explicit subsequent sprint, compatibility assessment, tests, and documented rationale.  
**S2 must not silently rewrite this baseline.**

**Production SEO Activation:** BLOCKED PENDING DOMAIN
