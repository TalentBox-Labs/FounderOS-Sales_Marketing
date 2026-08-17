# M7.5 — Production Smoke Test (Sentinel)

**Agent:** Sentinel  
**Sprint:** M7.5  
**Date:** 2026-08-10  
**Production URL:** `https://founderos-staging.pages.dev`  
**Staging baseline:** `https://preview.founderos-staging.pages.dev` (M6.5 RC1)

---

## Production results

| Check | Path / note | Result |
|-------|-------------|--------|
| Root | `/` → **404** | **EXPECTED** (no root `index.html` in Static v1.0 / RC1) |
| Public page | `/hiring-systems/` → **200** | **PASS** |
| Redirect | `/hiring-systems/index.html` → **308** | **PASS** |
| Static assets (CSS/JS) | not in RC1 package | **N/A** |
| HTTPS | HTTP/2 | **PASS** |
| Sitemap | `/sitemap.xml` → **200** | **PASS** |
| RSS | `/rss.xml` → **200** | **PASS** |
| Canonical | `rel="canonical"` present | **PASS** |
| Invalid route | `/no-such-route-m75` → **404** | **PASS** |
| Stability | 200 / 200 | **PASS** |
| Content | “Hiring Systems…” | **PASS** |
| Page SHA-256 | `42c95071ba79d9b0…` | **PASS** |

---

## Staging comparison (M6.5)

| Metric | Staging preview | Production |
|--------|-----------------|------------|
| Page SHA-256 | `42c95071…` | `42c95071…` |
| Feeds | 200 | 200 |
| Private paths | 404 | 404 |
| Root | 404 | 404 |

**Match: PASS**

---

## Local regression (M7.5)

| Suite | Result |
|-------|--------|
| Focused | **65/65** |
| Full | **327/339**; **8** failed; **4** errors |
| New regressions | **0** |

Historical failures unchanged (crews_unit ×3, utilities_unit ×5; orchestration_api ×2 errors; prospecting_ui ×2 errors).

**Regression: PASS**
