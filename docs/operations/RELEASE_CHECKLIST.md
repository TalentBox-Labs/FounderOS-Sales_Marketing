# Release Checklist — Founder Website Deployment

**Sprint:** M5.5 baseline  
**Use:** Local verification now; production/staging when CI and human gates allow  

---

## Repository identity

| Item | Record at release time |
|------|------------------------|
| Branch | `develop` (M5.5 local snapshot) |
| HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Git status | Working tree has untracked/modified marketing/docs/deployment modules — **commit before external release** |
| Git network | **No push required for M5.5 local freeze** |

---

## Test baseline

| Suite | Expected |
|-------|----------|
| Focused | **65/65** pass |
| Full | **327/339** pass; **8** failed; **4** errors (historical) |
| New regressions | **0** |

**Env:** `SECRET_KEY` (required for API tests), `HEARTBEAT_ENABLED=0`

---

## Deployment manifest

- [ ] `DeploymentAdapter.export_package()` returned `ok=True`  
- [ ] `deployment-manifest.json` present under `output/website-deploy/packages/{deployment_id}/`  
- [ ] `schema_version` = `1.0`  
- [ ] `public_file_count` matches copied HTML/feeds  

---

## Artifact checksum verification

- [ ] For each entry in manifest `files[]`, SHA-256 of on-disk file matches `sha256` field  
- [ ] `metadata.json` and `source.md` **absent** from package tree  
- [ ] Operator files may still exist under `output/website/` source root  

---

## Snapshot verification

- [ ] `output/website-deploy/snapshots/{deployment_id}/` exists after export  
- [ ] Snapshot tree matches package (including manifest)  

---

## Rollback verification (local)

- [ ] Deploy package A to local docroot  
- [ ] Deploy package B to same docroot  
- [ ] Roll back via `deploy_local(..., deployment_id=A, export_first=False)`  
- [ ] Docroot content matches package A  
- [ ] Evidence: [M5_5_ROLLBACK_EVIDENCE.md](M5_5_ROLLBACK_EVIDENCE.md)  

---

## Environment readiness

- [ ] Python `.venv` available  
- [ ] Static artifacts exist in `output/website/` (from Static Provider)  
- [ ] Cloudflare secrets **not** in repo (names only in CI replay doc)  

---

## Preview URL verification (staging/production only)

- [ ] Cloudflare preview deployment URL loads (when CI/host available)  
- [ ] Production custom domain **not** changed in M5.5  

---

## HTTPS verification (staging/production only)

- [ ] TLS valid on target host (Cloudflare automatic or local Caddy)  
- [ ] `canonical_url` in HTML matches public host  

---

## Smoke test

- [ ] Sample `{slug}/index.html` serves  
- [ ] `sitemap.xml` / `rss.xml` reachable when present  
- [ ] Local ladder step 7 passed  

---

## Founder approval

- [ ] Human gate for production publish/deploy (Architecture v2.2)  
- [ ] M5.5 local freeze does **not** substitute for production go-live sign-off  

---

## Release timestamp

| Field | M5.5 local freeze |
|-------|-------------------|
| Date | 2026-08-10 |
| Mode | Local verification only |
| External deploy | **NONE** |

---

## M6 — Staging only (Cloudflare Pages)

| Item | M6 record |
|------|-----------|
| Branch | `develop` |
| HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Git status | Uncommitted/untracked deployment + marketing modules (local) |
| Deployment artifact ID | `dep_m6_staging` |
| Checksum reference | [M6_STAGING_DEPLOYMENT.md](M6_STAGING_DEPLOYMENT.md) |
| Staging URL | **NOT CREATED** |
| Test evidence | [M6_STAGING_CERTIFICATION.md](M6_STAGING_CERTIFICATION.md) — 65/65 focused; 327/339 full |
| Smoke evidence | [M6_STAGING_SMOKE_TEST.md](M6_STAGING_SMOKE_TEST.md) — live **pending URL** |
| Security evidence | [M6_STAGING_SECURITY_AUDIT.md](M6_STAGING_SECURITY_AUDIT.md) |
| Rollback reference | `output/website-deploy/snapshots/dep_m6_staging/` |
| Founder approval (production) | **NOT GRANTED** |
| Production DNS | **NO CHANGE** |
| Cloudflare auth | `CLOUDFLARE_API_TOKEN` required — **unset** at M6 run |

---

## M6.2 — Staging retry (completed)

| Item | Record |
|------|--------|
| Branch | `develop` |
| HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Working tree | Dirty |
| Artifact ID | `dep_m62_staging` |
| Cloudflare project | `founderos-staging` |
| Branch deployed | `preview` |
| Staging URL | `https://preview.founderos-staging.pages.dev` |
| Deployment URL | `https://a4d3550c.founderos-staging.pages.dev` |
| Smoke | **PASS** |
| Security | **PASS** |
| Architecture | **PASS** |
| Rollback | **READY** |
| Production DNS | **NO** |
| Evidence | [M6_2_STAGING_RELEASE_EVIDENCE.md](M6_2_STAGING_RELEASE_EVIDENCE.md), [M6_2_STAGING_CERTIFICATION.md](M6_2_STAGING_CERTIFICATION.md) |

---

## M6.5 — RC1 staging baseline freeze

| Item | Frozen value |
|------|--------------|
| Release Candidate | **RC1** |
| Status | **FROZEN** |
| Artifact ID | `dep_m62_staging` |
| Staging URL | `https://preview.founderos-staging.pages.dev` |
| Deployment URL | `https://a4d3550c.founderos-staging.pages.dev` |
| HEAD SHA | `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Focused tests | **65/65** |
| Full regression | **327/339**; 8 failed; 4 errors; 0 new |
| Security | **PASS** |
| Architecture | **PASS** |
| Rollback | **READY** — [M6_5_RC1_ROLLBACK.md](M6_5_RC1_ROLLBACK.md) |
| Production DNS | **UNCHANGED** |
| Baseline SoT | [M6_5_RC1_BASELINE.md](M6_5_RC1_BASELINE.md) |
| Production cutover | **NOT AUTHORIZED** by this freeze — M7 only |

---

## M7 — Production cutover (RC1)

| Item | Value |
|------|-------|
| Release | **FOUNDER OS WEBSITE v1.0** |
| Artifact | RC1 `dep_m62_staging` |
| Production deployment ID | `80d03643-e871-4a28-bf74-376014301a12` |
| Production URL | `https://founderos-staging.pages.dev` |
| Custom domains | `blog.workcrew.ai`, `workcrew.ai` — **attached, DNS pending CNAME** |
| HTTPS | **PASS** |
| Security | **PASS** |
| Rollback | **READY** |
| Evidence | [M7_PRODUCTION_RELEASE.md](M7_PRODUCTION_RELEASE.md) |

---

## M7.5 — Production baseline freeze

| Item | Value |
|------|-------|
| Product | Founder OS Website **v1.0** |
| Status | **FROZEN** |
| Production URL | `https://founderos-staging.pages.dev` |
| Baseline SoT | [FOUNDER_OS_WEBSITE_V1_PRODUCTION_BASELINE.md](FOUNDER_OS_WEBSITE_V1_PRODUCTION_BASELINE.md) |
| M-Series | [M_SERIES_COMPLETION.md](../marketing/M_SERIES_COMPLETION.md) |
| Next engine (analysis) | SEO Engine — [POST_M_SERIES_NEXT_ENGINE_DECISION.md](../marketing/POST_M_SERIES_NEXT_ENGINE_DECISION.md) |
