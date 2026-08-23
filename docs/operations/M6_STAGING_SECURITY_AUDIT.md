# M6 — Staging Security Audit

**Agent:** Cipher  
**Sprint:** M6  
**Date:** 2026-08-10  
**Scope:** Staging public surface (package + deploy readiness)

---

## Package contents audit (`dep_m6_staging`)

| Risk | Finding |
|------|---------|
| Secrets in tree | **NONE** |
| `.env` files | **NONE** |
| `metadata.json` | **ABSENT** from package |
| `source.md` | **ABSENT** from package |
| Repository paths in HTML | **NONE** in page HTML |
| Credentials / debug output | **NONE** in public HTML/XML |

---

## Manifest exposure (pre-upload)

`deployment-manifest.json` is **included** in the frozen local package and contains:

- Absolute `source_root` and `package_root` paths (operator metadata).

**Recommendation for Cloudflare upload:** Upload **only** `hiring-systems/index.html`, `sitemap.xml`, and `rss.xml` — **exclude** `deployment-manifest.json` from the edge tree so internal paths are not publicly fetchable.

| Check | Result |
|-------|--------|
| Edge-safe upload set defined | **PASS** (operator procedure) |
| Manifest on public edge today | **N/A** (no deploy) |

---

## HTTPS

| Check | Result |
|-------|--------|
| TLS on staging host | **N/A** — URL not created |
| Cloudflare default TLS | Expected **PASS** once deployed on `*.pages.dev` |

---

## Production coupling

| Check | Result |
|-------|--------|
| Production custom domain attached | **NO** |
| Production DNS changed | **NO** |

---

## Verdict

| Gate | Result |
|------|--------|
| Public subset security (operator files) | **PASS** |
| Staging edge verification | **BLOCKED** (no deploy) |
| Pre-upload manifest hygiene | **ACTION REQUIRED** before Wrangler upload |

**Security (staging edge):** **FAIL** (not verifiable without live URL; package audit **PASS**)
