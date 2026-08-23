# M7 — Production Release (RC1 Cutover)

**Sprint:** M7 — Production Domain Cutover  
**Date:** 2026-08-10  
**Release Candidate promoted:** **RC1** (`dep_m62_staging`)  
**Code changes (Website / Publishing / Architecture):** **NONE**

---

## Production deployment (Nova)

| Field | Value |
|-------|-------|
| Artifact | RC1 / `dep_m62_staging` (edge-safe tree) |
| Cloudflare project | `founderos-staging` |
| Production branch | `main` |
| Environment | **Production** |
| Cloudflare deployment ID | `80d03643-e871-4a28-bf74-376014301a12` |
| Deployment URL | `https://80d03643.founderos-staging.pages.dev` |
| **Production URL** | `https://founderos-staging.pages.dev` |
| Status | **LIVE** |
| Timestamp | 2026-08-10 (Wrangler production deploy) |
| SHA-256 page match vs RC1 edge | **PASS** (`42c95071ba79d9b0…`) |

### Verification (production URL)

| Check | Result |
|-------|--------|
| HTTPS | **PASS** (HTTP/2) |
| `/hiring-systems/` | **200** |
| `/hiring-systems/index.html` | redirect/dir URL OK (Pages) |
| Canonical tag present | **PASS** (`https://workcrew.ai/blog/hiring-systems`) |
| `sitemap.xml` / `rss.xml` | **200** |
| CSS/JS assets | **N/A** (not in RC1 package) |
| Root `/` | **404** (known Static v1.0 gap) |

### Custom domains (attached; DNS pending)

| Domain | Cloudflare Pages status | DNS |
|--------|-------------------------|-----|
| `blog.workcrew.ai` | Attached · **pending** | CNAME **not set** |
| `workcrew.ai` | Attached · **pending** | CNAME **not set** |

**Operator DNS (required to finish branded cutover):**

```text
# Subdomain (recommended first)
blog.workcrew.ai.  CNAME  founderos-staging.pages.dev.

# Apex workcrew.ai requires Cloudflare zone / ALIAS strategy —
# zone workcrew.ai was NOT present on this Cloudflare account at M7.
```

Until CNAMEs validate, branded hostnames are **not** serving this Pages deployment. Production content **is** live on `https://founderos-staging.pages.dev`.

---

## End-to-end publishing (Hermes)

```text
Editorial / existing approved Static artifacts
→ Publishing Engine (orchestration; unchanged; no production grant change in code)
→ Website Engine / Static Provider (unchanged; RC1 artifacts)
→ Deployment Adapter (Direct Upload)
→ Cloudflare Pages Production (main)
→ https://founderos-staging.pages.dev/hiring-systems/
```

**Publishing path: PASS** (production observe URL). No engine modifications.

---

## Security (Cipher)

| Check | Production result |
|-------|-------------------|
| TLS / HTTPS | **PASS** |
| Headers | `x-content-type-options: nosniff`; `referrer-policy: strict-origin-when-cross-origin` |
| `robots.txt` | **200** (Pages default) |
| `metadata.json` / `source.md` / manifest / `.env` | **404** |
| Secret leakage in bodies | **NONE** |

**Security: PASS**

---

## Smoke vs staging (Sentinel)

| Probe | Staging preview | Production |
|-------|-----------------|------------|
| Page SHA-256 | `42c95071…` | `42c95071…` (**identical**) |
| Content | PASS | PASS |
| Feeds | 200 | 200 |
| Private paths | 404 | 404 |

**Smoke: PASS** · **Regression baseline: UNCHANGED** (no code changes; M6.5 327/339 / 0 new)

---

## Release evidence (Ledger)

| Item | Value |
|------|-------|
| Production deployment ID | `80d03643-e871-4a28-bf74-376014301a12` |
| Release timestamp | 2026-08-10 |
| Domain (live now) | `founderos-staging.pages.dev` |
| Domains attached (pending DNS) | `blog.workcrew.ai`, `workcrew.ai` |
| DNS status | **Pending CNAME** for branded domains; Pages production **active** |
| Rollback reference | Prior production deploy via Cloudflare Deployments history; local snapshot `output/website-deploy/snapshots/dep_m62_staging/`; staging preview `a4d3550c…` remains |
| HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Branch | `develop` |

---

## Architecture

Adapter-only promotion. Website Engine / Publishing Engine untouched. Provider independence preserved.

**Architecture: PASS**

---

## Rollback

**READY**

1. Cloudflare dashboard → `founderos-staging` → Deployments → roll back Production to prior deployment (or redeploy staging preview package).  
2. Local: re-upload `edge-upload/dep_m62_staging` or use snapshot.  
3. To undo branded domains (when active): remove custom domains in Pages settings / revert DNS CNAMEs.

---

## Residual risks

1. Branded domains pending DNS — canonical HTML already points at `workcrew.ai`.  
2. Project name remains `founderos-staging` while serving production branch (operational naming debt).  
3. Root `/` still 404 until landing page exists in Static Provider.

---

## Verdict

**FOUNDER OS WEBSITE v1.0 LIVE** on Cloudflare Pages production (`https://founderos-staging.pages.dev`).  
Complete branded hostname cutover after DNS CNAMEs validate.
