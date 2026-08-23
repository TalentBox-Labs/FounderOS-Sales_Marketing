# S2.1 — Technical SEO Closeout

**Sprint:** S2.1  
**Date:** 2026-08-11  
**Scope:** Disposition only — no Technical SEO feature expansion  
**S1.5 readiness contract:** UNCHANGED  
**Website Engine HTML contract:** UNCHANGED (no silent repair)

---

## 1. Robots Analysis: PARTIAL — root cause

### Evidence

| Check | Result |
|-------|--------|
| `src/tools/website_engine/**` contains `robots` / `noindex` | **None** (grep) |
| `wrap_html_document()` emits `<meta name="robots">` | **No** |
| Static provider writes `robots.txt` | **No** |
| Live `output/website/robots.txt` | **Absent** |
| Live page robots meta (`hiring-systems/index.html`) | **Absent** |
| Technical SEO `analyze_robots` / site `tech_robots_txt_absent` | **Implemented** — emits INFO/WARNING findings when controls missing |

### Classification

**Primary: B — WEBSITE ENGINE CAPABILITY MISSING**

Supporting disposition: **D — INTENTIONAL PHASE-1 LIMITATION**

Not:

- A (Technical SEO implementation defect) — analyzer covers page meta, conflicts, noindex, accidental index risk, site robots.txt presence  
- C (domain-dependent) — absence of robots emission is independent of future domain ratification  
- E (test/coverage gap) — robots cases covered in S2 tests  
- F alone — PARTIAL reflected end-to-end coverage, not a false failure of the analyzer

### Why S2 labeled PARTIAL

S2 final status meant: *Technical SEO can analyze robots signals that exist, but Website Engine does not yet emit site `robots.txt` or page robots meta, so full robots/indexability control surface is incomplete end-to-end.*

That is a **Website Engine capability gap**, not a broken Technical SEO robots family.

### Disposition

| Item | Decision |
|------|----------|
| Technical SEO robots analyzer | Complete for available artifacts — **no S2.1 code change** |
| Website Engine `robots.txt` / default `noindex` | **Deferred** to a future Website Engine / deploy-safety sprint |
| Freeze impact | **Non-blocking Phase-1 limitation** (explicit) |
| Robots Analysis (closeout) | Remains **PARTIAL** with documented limitation below |

**Robots remaining limitation:** Website Engine does not emit `robots.txt` or page-level robots meta; Technical SEO detects absence and accidental index risk but does not generate those controls (SEO Engine must not become a second Website Engine).

---

## 2. Website Engine Defect: 1 — identification

### Defect record

| Field | Value |
|-------|-------|
| **Defect ID** | `tech_robots_accidental_index_risk` |
| **Affected artifact** | `output/website/hiring-systems/index.html` (and any page whose canonical host is deprecated or infrastructure and lacks robots meta) |
| **Observed** | No `<meta name="robots" content="noindex…">`; canonical host in live sample is deprecated `workcrew.ai` |
| **Expected (safety)** | Non-production / deprecated / infrastructure hosts should carry `noindex` (or equivalent edge header) until production SEO activation |
| **SEO impact** | Search engines *could* index staging/wrong-host URLs if crawled |
| **Production impact** | Mitigated today: production SEO activation **BLOCKED**; domain unratified; deprecated host already DOMAIN_BLOCKED elsewhere |
| **Ownership** | **WEBSITE_ENGINE** (emission) — detected by SEO Engine |
| **Domain dependency** | Partially related (risk heightened when canonical is deprecated/infra) but root gap is missing robots emission regardless of final brand domain |
| **Severity** | **MEDIUM** |
| **Reproducible** | Yes — `analyze_technical_site()` against current `output/website` |

### Related INFO findings (not counted as the “1 defect”)

| ID | Severity | Note |
|----|----------|------|
| `tech_robots_meta_absent` | INFO | Documents Website Engine default |
| `tech_robots_txt_absent` | INFO | Documents missing `robots.txt` |

S2 “Website Engine Defects: 1” referred specifically to the **WARNING** `tech_robots_accidental_index_risk`.

### Classification vs freeze

| Question | Answer |
|----------|--------|
| CRITICAL / HIGH / MEDIUM / LOW / INFORMATIONAL | **MEDIUM** |
| Blocks Technical SEO Engine correctness? | **No** — detection works |
| Blocks S2.5 Technical SEO baseline freeze? | **No** — non-blocking deferred Website Engine debt |
| Requires frozen Website Engine HTML contract change to fix? | **Yes** — would alter `wrap_html_document` / static output |

### Disposition

**DEFERRED**

Do **not** silently patch Website Engine in S2.1.

Required future correction (separate sprint / governance):

1. Emit page `noindex,nofollow` while `is_indexing_activation_allowed()` is false **or** when canonical host is infrastructure/deprecated  
2. Optionally emit `robots.txt` for static packages / edge headers on Cloudflare  

If that work proceeds: treat as **Website Engine safety enhancement** under explicit sprint ownership — not an SEO Engine rewrite.

**Website Engine blocking defects remaining:** **0**

---

## 3. Domain blockers verification (8/8)

Live `analyze_technical_site()` against `output/website` (origin `https://example.invalid`, unratified):

| # | Finding ID | Artifact | Domain-dependent? | Conceals non-domain defect? |
|---|------------|----------|-------------------|------------------------------|
| 1 | `tech_sitemap_deprecated_host` | sitemap.xml | Yes — `workcrew.ai` | No |
| 2 | `tech_feed_channel_deprecated` | rss.xml | Yes | No |
| 3 | `tech_feed_item_deprecated` | rss.xml | Yes | No |
| 4 | `tech_canonical_deprecated_host` | hiring-systems/index.html | Yes | No |
| 5 | `tech_canonical_unratified` | hiring-systems/index.html | Yes — ratification gate | No |
| 6 | `tech_jsonld_deprecated_host` | hiring-systems/index.html (`url`) | Yes | No |
| 7 | `tech_jsonld_deprecated_host` | hiring-systems/index.html (`@id`) | Yes (second JSON-LD URL field) | No |
| 8 | `tech_og_deprecated_host` | hiring-systems/index.html | Yes | No |

**Verified: 8/8** are genuine domain / deprecated-host / unratified-origin blockers.

Notes:

- Historical `workcrew.ai` appears in **artifacts from content FM / prior publish**, not as SEO Engine or `site_origin` runtime fallback (runtime default remains `https://example.invalid`).  
- `pages.dev` is **not** asserted as branded canonical by Technical SEO; infrastructure hosts are DOMAIN_BLOCKED when present.  
- Website Engine robots WARNING is **separately** owned (`WEBSITE_ENGINE`), not folded into the 8.

**Production SEO Activation:** remains **BLOCKED PENDING DOMAIN**.

---

## 4. Files changed (S2.1)

| File | Change |
|------|--------|
| `docs/marketing/seo/S2_1_TECHNICAL_SEO_CLOSEOUT.md` | This closeout record |

**Feature / engine code changes:** **0**  
**Frozen contract changes:** **0**

---

## 5. Regression (verification only)

| Suite | Result |
|-------|--------|
| S2 focused (`tests/test_technical_seo_engine.py`) | **27/27** |
| S1 frozen (readiness + site_origin) | **34/34** |
| Website + SEO focused gate | **92/92** |
| Full suite | **388 passed; 8 failed; 4 errors** |
| Historical failure identities | **UNCHANGED** |
| New regressions | **0** |

---

## 6. Architecture impact

| Engine | Impact |
|--------|--------|
| SEO Engine | None (no code change) |
| Website Engine | None (defect deferred, not patched) |
| Publishing / Editorial / Content Studio | None |

Architecture: **PASS**

---

## 7. Remaining technical debt (explicit)

1. Website Engine: emit robots meta / `robots.txt` / edge noindex for non-activated environments  
2. Content migration: replace historical `workcrew.ai` canonicals after Founder domain ratification  
3. Optional: dedupe double `tech_jsonld_deprecated_host` emissions into one finding per page (cosmetic; not a freeze blocker)

---

## 8. Freeze recommendation

Technical SEO Engine Phase 1 remains **PASS**.

Robots Analysis remains **PARTIAL** solely due to documented **non-blocking** Website Engine emission gap.

Website Engine **blocking** defects for S2.5: **0**.

**Recommended next sprint:** S2.5 — TECHNICAL SEO BASELINE FREEZE
