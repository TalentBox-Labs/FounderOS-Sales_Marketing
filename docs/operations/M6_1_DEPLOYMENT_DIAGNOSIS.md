# M6.1 — Deployment Diagnosis (Nova)

**Sprint:** M6.1 — Cloudflare Staging Blocker Diagnosis  
**Date:** 2026-08-10  
**Agent:** Nova  
**Code changes:** **NONE**

---

## M6 deployment attempt (verified)

| Field | Value |
|-------|-------|
| **Command** | `npx wrangler pages deploy . --project-name=founder-os-staging-m6 --branch=preview --commit-dirty=true` |
| **Working directory** | `output/website-deploy/packages/dep_m6_staging/` |
| **Deploy mode** | **Direct Upload** (static directory upload via Wrangler Pages) |
| **Git-backed Pages build** | **NOT attempted** |
| **Exit code** | **1** |
| **Wrangler version** | **4.120.0** (via `npx wrangler`) |
| **Wrangler availability** | **YES** (`npx` resolves and runs) |

---

## Stdout / stderr (sanitized)

Wrangler log: `~/Library/Preferences/.wrangler/logs/wrangler-2026-08-10_09-50-46_374.log`

**Error (verbatim message, no secrets):**

```text
In a non-interactive environment, it's necessary to set a CLOUDFLARE_API_TOKEN
environment variable for wrangler to work.
```

**Pre-auth checks in log:**

- No `.env` / `.env.local` in package directory (expected; no secrets in repo)
- `configFileType: none` — no `wrangler.toml` in package cwd (config lives under `output/website-deploy/cloudflare/`; deploy used CLI flags only)
- `isInteractive: false` — Cursor/shell non-interactive

**Prior check (M6):** `npx wrangler whoami` → *You are not authenticated. Please run `wrangler login`.*

---

## Package and config (verified)

| Item | Status |
|------|--------|
| Deployment package path | `output/website-deploy/packages/dep_m6_staging/` |
| Public files | `hiring-systems/index.html`, `sitemap.xml`, `rss.xml` |
| Operator files in package | **Excluded** (`metadata.json`, `source.md` absent) |
| `deployment-manifest.json` | Present locally (operator metadata; not edge-safe if uploaded as-is) |
| Adapter export (`dep_m6_staging`) | **PASS** (M6) |
| Template `wrangler.toml` | `output/website-deploy/cloudflare/wrangler.toml` — project name **`founder-website`** (template default; M6 CLI used **`founder-os-staging-m6`**) |

**Note:** Project name mismatch is **not** the M6 failure point — authentication failed before any Pages API/project validation.

---

## Authentication and identifiers (M6.1 re-check)

| Variable / signal | M6 | M6.1 |
|-------------------|-----|------|
| `CLOUDFLARE_API_TOKEN` | unset | **unset** |
| `CLOUDFLARE_ACCOUNT_ID` | unset | **unset** |
| `wrangler whoami` | not authenticated | **not authenticated** |
| OAuth / cached login | not present | **not present** |

Values were **never printed** in logs or docs.

---

## Blocker classification

| Code | Assessment |
|------|------------|
| **A. MISSING AUTHENTICATION** | **PRIMARY — CONFIRMED** |
| B. MISSING CLOUDFLARE PROJECT | **NOT REACHED** (no API call after auth gate) |
| C. INVALID CONFIGURATION | **NOT VERIFIED** as root cause |
| D. INVALID DEPLOYMENT ARTIFACT | **NO** — public subset valid |
| E. CLI/WRANGLER ISSUE | **NO** — CLI ran; failed at auth |
| F. ACCOUNT/PERMISSION ISSUE | **NOT VERIFIED** |
| G. NETWORK ISSUE | **NO** evidence |
| H. APPLICATION DEFECT | **NO** |
| I. NOT VERIFIED | Project existence post-auth |

---

## Nova verdict

Staging URL was **not created** because Wrangler **refused to run Pages deploy without credentials** in a non-interactive environment. The frozen Deployment Adapter produced a valid package; failure is at the **operator/Cloudflare credential boundary**, not inside Website Engine or Publishing.
