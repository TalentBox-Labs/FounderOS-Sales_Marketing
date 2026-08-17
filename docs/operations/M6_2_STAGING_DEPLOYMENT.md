# M6.2 — Staging Deployment (Cloudflare Pages)

**Agent:** Nova  
**Sprint:** M6.2  
**Date:** 2026-08-10  
**Mode:** STAGING / PREVIEW ONLY  

---

## Phase 0 (preflight)

| Check | Result |
|-------|--------|
| Repository | `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing` |
| Branch | `develop` |
| HEAD | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Working tree | Dirty (uncommitted marketing/deployment work) |
| Package export | `dep_m62_staging` via frozen Deployment Adapter |
| Manifest SHA-256 | **PASS** |
| Public subset | HTML + `sitemap.xml` + `rss.xml` only |
| Operator files excluded | `metadata.json`, `source.md` — **PASS** |
| Edge upload excludes | `deployment-manifest.json` — **PASS** |
| Wrangler | **4.120.0** |
| Auth | **AUTHENTICATED** (`CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` present by **name**; values not recorded) |
| Staging project | `founderos-staging` |
| Production DNS / custom domain | **NOT** attached |

---

## Deployment

| Field | Value |
|-------|-------|
| Mechanism | Direct Upload (`wrangler pages deploy`) |
| Project | `founderos-staging` |
| Branch | `preview` |
| Artifact ID | `dep_m62_staging` |
| Edge directory | `output/website-deploy/edge-upload/dep_m62_staging/` |
| Files uploaded | **3** |
| Status | **SUCCESS** |
| Deployment URL | `https://a4d3550c.founderos-staging.pages.dev` |
| Alias URL | `https://preview.founderos-staging.pages.dev` |
| Timestamp | 2026-08-10 (Wrangler upload complete) |

### Artifact checksums (public)

| Path | SHA-256 (prefix) |
|------|------------------|
| `hiring-systems/index.html` | `42c95071ba79d9b0…` |
| `rss.xml` | `2927adcd64c76166…` |
| `sitemap.xml` | `156e5e4c1c09f033…` |

Full hashes: package manifest under `output/website-deploy/packages/dep_m62_staging/deployment-manifest.json` (local only; **not** on edge).

---

## Repeatable command (placeholders only)

```bash
set -a && source .env.local && set +a   # loads CLOUDFLARE_* names; never commit values
wrangler pages deploy output/website-deploy/edge-upload/<deployment_id> \
  --project-name="${CLOUDFLARE_PROJECT_NAME}" \
  --branch=preview \
  --commit-dirty=true
```

---

## Verdict (Nova)

**PASS** — Staging preview environment created.
