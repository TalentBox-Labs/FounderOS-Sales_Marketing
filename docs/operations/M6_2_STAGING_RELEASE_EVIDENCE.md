# M6.2 — Staging Release Evidence (Ledger)

**Agent:** Ledger  
**Sprint:** M6.2  
**Date:** 2026-08-10  

---

## Repository

| Item | Value |
|------|-------|
| Branch | `develop` |
| HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Working tree | **Dirty** (uncommitted docs/modules) |
| Secrets in git | **NO** (`.env.*` gitignored) |

---

## Deployment

| Item | Value |
|------|-------|
| Artifact ID | `dep_m62_staging` |
| Checksum reference | package `deployment-manifest.json` + `edge-upload/dep_m62_staging.sha256.json` |
| Cloudflare project | `founderos-staging` |
| Branch | `preview` |
| Deployment URL | `https://a4d3550c.founderos-staging.pages.dev` |
| Staging alias | `https://preview.founderos-staging.pages.dev` |
| Timestamp | 2026-08-10 |
| Smoke | **PASS** |
| Security | **PASS** |
| Architecture | **PASS** |
| Rollback reference | Local `output/website-deploy/snapshots/dep_m62_staging/`; Cloudflare Pages Deployments history for project |
| Production DNS changed | **NO** |
| Founder production approval | **NOT GRANTED** (staging only) |

---

## Env var names used (values not recorded)

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_PROJECT_NAME`
