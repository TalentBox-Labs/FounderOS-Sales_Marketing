# M6.2 — Staging Smoke Test (Sentinel)

**Agent:** Sentinel  
**Sprint:** M6.2  
**Date:** 2026-08-10  

**Primary staging URL:** `https://preview.founderos-staging.pages.dev`  
**Deployment URL:** `https://a4d3550c.founderos-staging.pages.dev`

---

## Results (preview alias)

| Check | URL | HTTP | Result |
|-------|-----|------|--------|
| Root | `/` | **404** | **EXPECTED** — Static v1.0 has no root `index.html` |
| Content page | `/hiring-systems/` | **200** | **PASS** — “Hiring Systems…” present |
| Static HTML path | `/hiring-systems/index.html` | **308** | **PASS** — redirect to canonical dir URL |
| Sitemap | `/sitemap.xml` | **200** | **PASS** |
| RSS | `/rss.xml` | **200** | **PASS** |
| CSS/JS assets | — | — | **N/A** — not in frozen Static package |
| Canonical link | in page HTML | present | **PASS** |
| Invalid route | `/no-such-route-m62` | **404** | **PASS** |
| Directory listing | — | not observed | **PASS** |
| Stability | `/hiring-systems/` ×2 | **200 / 200** | **PASS** |
| HTTPS | all probes | TLS | **PASS** |

Identical outcomes on `https://a4d3550c.founderos-staging.pages.dev`.

**Note:** `https://founderos-staging.pages.dev` (production branch `main`) has **no** M6.2 assets — M6.2 deployed to **`preview` only** by design.

---

## Verdict

**Smoke: PASS** (against preview staging URLs)
