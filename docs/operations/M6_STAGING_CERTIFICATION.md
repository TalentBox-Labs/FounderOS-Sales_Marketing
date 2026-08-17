# M6 — Staging Certification

**Sprint:** M6 — Cloudflare Pages Staging Deployment  
**Date:** 2026-08-10  
**Coordinator:** Lead Engineering Coordinator  

---

## Deployment outcome

| Item | Result |
|------|--------|
| Package export | **PASS** (`dep_m6_staging`) |
| Cloudflare Pages upload | **FAIL** (no API token / not authenticated) |
| Staging URL | **NOT CREATED** |
| Production DNS | **NO CHANGE** |
| Engine code changes | **NONE** |

---

## Post-sprint test ladder

**Environment:** `SECRET_KEY=test-secret-m6` · `HEARTBEAT_ENABLED=0`

| Step | Command | Exit | Passed | Failed | Errors |
|------|---------|------|--------|--------|--------|
| Focused | `pytest tests/test_website_deployment.py tests/test_website_engine.py tests/test_static_provider.py tests/test_publishing_engine.py tests/test_routers_integration.py -q` | 0 | **65** | 0 | 0 |
| Full | `pytest tests/ -q` | 1 | **327** | **8** | **4** |

**Baseline comparison:** 327/339 · 8 failed · 4 errors · **0 new regressions** — **MATCH**

---

## Agent gates

| Agent | Gate | Result |
|-------|------|--------|
| Nova | Package + deploy prep | **PARTIAL** — upload blocked |
| Sentinel | Live smoke | **FAIL** (no URL) |
| Cipher | Package security | **PASS**; edge **N/A** |
| Hermes | E2E boundaries | **PASS** logical / **FAIL** live edge |
| Atlas | Architecture | **PASS** |
| Ledger | Release evidence | **UPDATED** |

---

## Stop conditions triggered

| Condition | Triggered? |
|-----------|------------|
| Production DNS required | **NO** |
| Secrets exposed | **NO** |
| Website/Publishing modification required | **NO** |
| Private operator files in package | **NO** |
| New regressions | **NO** |
| Rollback path lost | **NO** (snapshot preserved) |
| **Cloudflare auth missing** | **YES** — remote staging not created |

---

## Cross-agent conflicts

**0**

---

## Verdict

**FOLLOW-UP REQUIRED**

Complete Cloudflare staging by setting `CLOUDFLARE_API_TOKEN` (and account ID if needed), uploading edge-safe files (exclude manifest from public tree), and re-running Sentinel smoke against the issued `*.pages.dev` URL.

**Not ready for M6.5 freeze** until live staging URL passes smoke + HTTPS checks.
