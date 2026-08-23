# M6.5 — Release Candidate RC1 Baseline Freeze

**Status:** **FROZEN**  
**Release Candidate:** **RC1**  
**Sprint:** M6.5  
**Date:** 2026-08-10  
**Coordinator:** Lead Engineering Coordinator  

**Scope:** Staging baseline freeze only. **NO** production deployment. **NO** production DNS. **NO** feature or architecture changes.

---

## RC1 identity

| Field | Frozen value |
|-------|----------------|
| Release Candidate | **RC1** |
| Artifact / package ID | `dep_m62_staging` |
| Cloudflare project | `founderos-staging` |
| Cloudflare branch | `preview` |
| Cloudflare deployment URL | `https://a4d3550c.founderos-staging.pages.dev` |
| Staging alias URL | `https://preview.founderos-staging.pages.dev` |
| Deployment timestamp (manifest) | `2026-08-10T12:24:38+00:00` |
| Git branch | `develop` |
| HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |

### Artifact checksums (SHA-256)

| Path | SHA-256 |
|------|---------|
| `hiring-systems/index.html` | `42c95071ba79d9b0a7b4771d2aebaebd69ca7ce015dd1ee6c6c5818e6e9b1d47` |
| `rss.xml` | `2927adcd64c76166dd15c60039394eafb24e721aa193467d9229f24cace99ee0` |
| `sitemap.xml` | `156e5e4c1c09f033b02e981c1a4322bfb1c7b1c3f47025056d6fbd0599aa3805` |

### Package locations (local)

| Role | Path |
|------|------|
| Full package + manifest | `output/website-deploy/packages/dep_m62_staging/` |
| Edge-safe upload tree | `output/website-deploy/edge-upload/dep_m62_staging/` |
| Snapshot | `output/website-deploy/snapshots/dep_m62_staging/` |
| Manifest file | `…/dep_m62_staging/deployment-manifest.json` |

**Public edge contents (frozen):** `{slug}/index.html`, `sitemap.xml`, `rss.xml` only.  
**Excluded from edge:** `metadata.json`, `source.md`, `deployment-manifest.json`, secrets.

---

## Agent freeze attestations

| Agent | Result | Evidence |
|-------|--------|----------|
| Nova | RC1 artifact freeze | this document § RC1 identity |
| Sentinel | Regression **PASS** | Focused **65/65**; Full **327/339**; 8 failed; 4 errors; **0** new |
| Cipher | Security **PASS** | HTTPS; private paths 404; feeds 200; no leaks |
| Atlas | Architecture **PASS** | Adapter-only deploy; Core/Publishing unchanged |
| Ledger | Release docs frozen | [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md), [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md), [M6_5_RC1_ROLLBACK.md](M6_5_RC1_ROLLBACK.md) |

---

## Regression (Sentinel — M6.5 re-run)

**Env:** `SECRET_KEY=test-secret-m6-5` · `HEARTBEAT_ENABLED=0`

| Suite | Result |
|-------|--------|
| Focused certification | **65/65** |
| Full | **327/339**; **8** failed; **4** errors |
| New regressions | **0** |

Historical failures unchanged (crews_unit ×3, utilities_unit ×5; orchestration_api ×2 errors; prospecting_ui ×2 errors).

---

## Security (Cipher — M6.5 re-check)

Against `https://preview.founderos-staging.pages.dev` and deployment URL:

| Check | Result |
|-------|--------|
| HTTPS / HTTP2 | **PASS** |
| `/hiring-systems/` | **200** |
| `sitemap.xml` / `rss.xml` | **200** |
| `metadata.json` / `source.md` / manifest / `.env` | **404** |
| Secret/path leakage in bodies | **NONE** |
| Headers observed | `x-content-type-options: nosniff`; `referrer-policy: strict-origin-when-cross-origin`; `x-robots-tag: noindex` (preview) |
| `robots.txt` | **200** (Cloudflare Pages default surface; not Founder Static Provider artifact) |

---

## Architecture (Atlas)

| Check | Result |
|-------|--------|
| Drift from v2.2 | **NONE** |
| Deploy remains adapter-only | **PASS** |
| Website Engine Cloudflare coupling | **NONE** |
| Publishing orchestration-only | **PASS** |
| Production DNS | **UNCHANGED** |

---

## Rollback

**READY** — see [M6_5_RC1_ROLLBACK.md](M6_5_RC1_ROLLBACK.md)

---

## Production isolation

| Gate | Status |
|------|--------|
| Production deployment | **NOT PERFORMED** |
| Production DNS | **UNCHANGED** |
| Production domain attached | **NO** |

---

## Known frozen gaps (not regressions)

1. Staging root `/` returns **404** (no landing `index.html` in Static v1.0).  
2. HTML `canonical_url` still embeds production host (content contract; not a DNS change).  
3. Working tree may remain dirty relative to git HEAD — RC1 freezes **artifact + staging URL**, not a git tag requirement.

---

## Verdict

**READY FOR M7 PRODUCTION CUTOVER**
