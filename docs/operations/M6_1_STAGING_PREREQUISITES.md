# M6.1 — Staging Prerequisites (Ledger)

**Sprint:** M6.1  
**Date:** 2026-08-10  
**Agent:** Ledger  
**For:** Safe M6.2 staging retry (no production DNS)

---

## Verified ready today

| Prerequisite | Status |
|--------------|--------|
| Frozen Deployment Adapter v1.0 | **READY** |
| Public artifact package `dep_m6_staging` | **READY** (or re-export with new ID) |
| Local snapshot / rollback metadata | **READY** |
| Python `.venv` + pytest baseline | **READY** |
| Production custom domain | **NOT REQUIRED** (forbidden for staging retry) |
| Founder production publish approval | **NOT REQUIRED** for staging preview |

---

## Required before Cloudflare upload (verified gaps)

| Prerequisite | Status |
|--------------|--------|
| Cloudflare account access | **NOT VERIFIED** in this environment |
| API authentication | **MISSING** — see env vars below |
| Wrangler authenticated session | **MISSING** (`wrangler login` not completed) |
| Pages project `founder-os-staging-m6` (or chosen name) | **NOT VERIFIED** — may auto-create on first authenticated deploy |
| Edge-safe upload set (exclude manifest) | **OPERATOR PROCEDURE** — recommended |

---

## Environment variables (names only — never commit values)

| Name | Purpose |
|------|---------|
| `CLOUDFLARE_API_TOKEN` | **Required** for non-interactive `wrangler pages deploy` |
| `CLOUDFLARE_ACCOUNT_ID` | Optional/required depending on Wrangler version and account setup |

---

## Tooling

| Item | Requirement |
|------|-------------|
| `npx wrangler` | **4.120.0** observed working |
| Deploy command | Direct Upload from package directory |
| Suggested project name | `founder-os-staging-m6` (M6 attempt) |
| Suggested branch | `preview` (non-production) |

---

## Staging retry command template (after auth)

From `output/website-deploy/packages/<deployment_id>/` (edge-safe tree):

```bash
# Option A: upload subset directory containing only html+xml
# Option B: upload package after removing deployment-manifest.json

npx wrangler pages deploy . \
  --project-name=founder-os-staging-m6 \
  --branch=preview \
  --commit-dirty=true
```

Record resulting `*.pages.dev` URL in M6.2 docs.

---

## Ledger verdict

**CONFIGURATION REQUIRED BEFORE RETRY** — authentication is the blocking prerequisite.
