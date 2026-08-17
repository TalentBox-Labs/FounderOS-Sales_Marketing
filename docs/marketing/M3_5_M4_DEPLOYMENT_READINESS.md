# M3.5 / M4 — Deployment Readiness Analysis

**Status:** ANALYSIS ONLY — **DO NOT DEPLOY / IMPLEMENT in this sprint**  
**Sprint:** M3.5 (prepare for future M4)  
**Role:** Agent D  
**Date:** 2026-08-10  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 ([Architecture_v2.1.md](../architecture/Architecture_v2.1.md), [Architecture_ADR_002.md](../architecture/Architecture_ADR_002.md), [Platform_vs_OS_Boundaries.md](../architecture/Platform_vs_OS_Boundaries.md))  
**Prerequisite:** M3 Static Website Provider ([M3_STATIC_PROVIDER_REPORT.md](M3_STATIC_PROVIDER_REPORT.md), [M3_STATIC_OUTPUT_AUDIT.md](M3_STATIC_OUTPUT_AUDIT.md))

**Constraint:** No deployment actions, no cloud resource creation, no paid-provider selection, no implementation.  
**Scope:** Requirements to make the **static Founder website publicly reachable**, given existing `output/website/` artifacts and Website Engine ownership of deploy hooks.

---

## 1. Mission

Determine what M4 must decide and prepare so that Website Engine static artifacts can become a public site — without moving ownership to Publishing Engine or choosing a CMS prematurely.

Evaluate only:

| ID | Mode |
|----|------|
| A | Local / self-hosted static serving |
| B | Git-backed static hosting |
| C | Managed static hosting |
| D | Containerized static serving |
| E | Future CMS adapter path |

---

## 2. Evidence base (repository facts)

| Source | Relevant fact |
|--------|----------------|
| [Architecture_v2.1.md](../architecture/Architecture_v2.1.md) § Website Engine | Website Engine owns canonical site: render, URLs, metadata, OG, Schema.org, RSS, sitemap, static assets, cache invalidation, **website deployment hooks**. Publishing owns orchestration only. |
| [Platform_vs_OS_Boundaries.md](../architecture/Platform_vs_OS_Boundaries.md) | Site deploy hooks → Website Engine; Automation Platform may execute deploy transport; Shared Platform owns secrets/config; SEO Engine must **not** own site deploy. |
| [M3_STATIC_PROVIDER_REPORT.md](M3_STATIC_PROVIDER_REPORT.md) | `StaticWebsiteProvider` (`name=static`) writes under `output/website/`; `external_http=False`; **no deploy / CDN / network**. |
| [M3_STATIC_OUTPUT_AUDIT.md](M3_STATIC_OUTPUT_AUDIT.md) | Verified layout: `{slug}/index.html`, `{slug}/metadata.json`, `{slug}/source.md`, root `sitemap.xml`, `rss.xml`. Audit: **PASS**. |
| `src/tools/website_engine/static_provider.py` | Filesystem write only; idempotent overwrite per slug; message explicitly “no external HTTP, no deploy.” |
| `src/tools/website_engine/provider.py` | `DEFAULT_SITE_OUTPUT = REPO_ROOT / "output" / "website"`. |
| [Website_Engine_Implementation_Checklist.md](Website_Engine_Implementation_Checklist.md) | “Website deployment hooks” still **PREPARE** (not implemented). |
| [M2_5_WEBSITE_PROVIDER_READINESS.md](M2_5_WEBSITE_PROVIDER_READINESS.md) | First provider = STATIC; host left **agnostic**; optional deploy hook interface owned by Website Engine. |
| Publishing channel docs | Publishing does **not** deploy, invalidate cache, or call Website Engine for site hosting. |

**Implication:** M3 produced a **local publication surface**, not a public site. Public reachability is an M4 decision + Website Engine deploy-hook concern — not a Publishing Engine feature.

---

## 3. Deployment artifact contract (current)

Canonical tree produced by Website Engine static path (default root `output/website/`):

```text
output/website/
├── {slug}/
│   ├── index.html      ← public page (directory URL /{slug}/)
│   ├── metadata.json   ← operator/debug; typically NOT public
│   └── source.md       ← source archive; typically NOT public
├── sitemap.xml         ← public feed
└── rss.xml             ← public feed
```

| Dimension | Current state |
|-----------|---------------|
| **Deployment artifact** | Filesystem directory tree under `output/website/` (not a tarball, image, or git commit by itself) |
| **Build step** | In-process Website Engine publish (`publish_content` / `StaticWebsiteProvider.publish`) from approved Markdown under `input/{week}/` — **already implemented** for local write |
| **Public subset** | At minimum: `{slug}/index.html` + `sitemap.xml` + `rss.xml`. `metadata.json` / `source.md` should be excluded or blocked from public serve unless intentionally published |
| **Site root** | **No** root `index.html` / landing page emitted today |
| **Multi-page feeds** | Sitemap/RSS are **single-item overwrite per publish** (M3 audit non-blocking note) — insufficient as a full-site index until M4+ aggregation is decided |
| **Deploy hook** | **Not implemented** (`external_http=False`; checklist PREPARE) |
| **Owner of deploy** | **Website Engine** (v2.1), not Publishing |

---

## 4. Cross-cutting requirements (all public modes)

These apply regardless of A–D (E deferred to CMS):

| Concern | Requirement for public reachability |
|---------|-------------------------------------|
| **Deployment artifact** | Stable package of public files derived from `output/website/` (sync tree, git subtree, object upload, or image `COPY`) |
| **Build step** | Run Website Engine static publish for intended slugs **before** expose/sync; do not re-render on the host |
| **Runtime** | Static file server only for A–D (no app server required for HTML); CMS runtime only for E |
| **HTTPS** | Terminate TLS at reverse proxy / host edge; Founder artifacts do not include certs |
| **Custom domain** | DNS + host binding to match `canonical_url` already embedded in HTML/metadata/feeds |
| **Cache / CDN** | Optional for A; usually native for B/C; reverse-proxy or edge for D. Cache invalidation is **Website Engine** ownership (v2.1) — still unimplemented |
| **Rollback** | Retain prior artifact snapshot (git commit, object version, image tag, or directory backup) and re-point serve root |
| **Secrets** | Deploy credentials live in **Shared Platform** secrets/config — not in Website Engine business logic, not in Publishing |
| **CI/CD** | Optional automation: generate artifacts → package public subset → deploy via Website Engine hook / Automation Platform. Not present today |
| **Operational burden** | Must stay compatible with solo/founder ops; avoid second CMS unless E is chosen later |
| **Architecture law** | Website Engine owns site deploy hooks + cache invalidation; Automation executes transport; Publishing stays orchestration-only |

---

## 5. Mode analysis

Scoring guidance (readiness, not vendor pick): **Ready** = artifact fit + low missing work · **Partial** = viable with M4 decisions/hooks · **Deferred** = valid later path, not first public-static path.

### A. Local / self-hosted static serving

**Model:** Serve `output/website/` (or a public subset) with nginx, Caddy, Apache, or `python -m http.server` behind a host you control. Optional rsync/scp from build machine to web root.

| Dimension | Assessment |
|-----------|------------|
| Deployment artifact | Directory tree; sync `{slug}/index.html`, `sitemap.xml`, `rss.xml` to docroot; exclude or deny `metadata.json` / `source.md` |
| Build step | Existing Website Engine static publish on operator machine or CI runner |
| Runtime | Lightweight static web server + OS process supervision |
| HTTPS | Operator-managed (Caddy/Let’s Encrypt, nginx + certbot, etc.) |
| Custom domain | Operator DNS → host; must align with Website Engine `canonical_url` |
| Cache / CDN | Optional reverse-proxy cache; invalidation hook still missing |
| Rollback | Keep prior docroot snapshot / rsync `--backup`; restore previous tree |
| Secrets | SSH keys / host access via Shared Platform; no CMS tokens |
| CI/CD | Manual rsync acceptable; later Automation Platform job calling Website Engine deploy hook |
| Operational burden | **Medium** — you own uptime, TLS renewals, firewall, backups |

**Fit:** Strongest conceptual match to M3 filesystem artifacts and “no paid SaaS” posture from M2.5. Closest path to exercise a **Website Engine deploy hook** (e.g. rsync) without vendor lock-in.

**Gaps for public use:** always-on host; TLS; public-subset filter; optional root index; multi-URL sitemap aggregation; deploy hook interface.

**Readiness:** **Partial** — artifacts exist; serving + TLS + hook not chosen/implemented.

---

### B. Git-backed static hosting

**Model:** Commit (or CI-publish) the public static tree to a git branch/repo that a host builds/serves as static files (e.g. Pages-style free/OSS flows). Website Engine remains render owner; git is distribution, not CMS.

| Dimension | Assessment |
|-----------|------------|
| Deployment artifact | Git tree of public HTML/XML (not full `output/website/` with operator JSON/MD unless filtered) |
| Build step | Website Engine publish → filter public files → commit/push (hook) |
| Runtime | Host’s static edge; no Founder app process required for the public site |
| HTTPS | Typically provided by host |
| Custom domain | Host DNS instructions; must match canonical URLs |
| Cache / CDN | Usually included; invalidation may be “new deploy” only |
| Rollback | `git revert` / redeploy previous commit |
| Secrets | Deploy token / deploy key in Shared Platform; never bake into repo |
| CI/CD | Natural fit: generate → commit/push or `actions` upload |
| Operational burden | **Low–medium** — less server ops; more git hygiene and branch policy |

**Fit:** Good once artifact packaging (public subset + multi-page feeds) is stable. Aligns with repo-centric Founder content (`input/{week}/`) if public HTML is treated as a **derived** publish product, not editorial SoT.

**Gaps:** policy for “do we commit generated HTML?”; filter rules; Website Engine deploy hook that pushes without Publishing owning git; avoid committing secrets or full operator metadata.

**Readiness:** **Partial** — needs packaging + hook decision; no vendor selection in this analysis.

---

### C. Managed static hosting

**Model:** Upload or CI-deploy the public static tree to a managed static host / object-storage+CDN style service. Still filesystem artifacts; host is dumb object/static edge.

| Dimension | Assessment |
|-----------|------------|
| Deployment artifact | Same public file set; often zip/dir upload or CLI sync |
| Build step | Website Engine publish → sync/upload via deploy hook |
| Runtime | Fully managed static/CDN edge |
| HTTPS | Host-managed |
| Custom domain | Host + DNS; canonical URL alignment required |
| Cache / CDN | Native; Website Engine cache-invalidation responsibility becomes host API or redeploy |
| Rollback | Prior deploy version / previous upload set |
| Secrets | Host API token / access key in Shared Platform |
| CI/CD | Strong fit once hook exists |
| Operational burden | **Low** for runtime; **decision risk** if paid tiers creep in |

**Fit:** Excellent for public reachability once a **free/OSS-compatible or already-owned** target is chosen later. M2.5 explicitly deferred vendor choice; this analysis also **does not** pick a paid provider.

**Gaps:** provider-agnostic deploy hook contract; secrets plumbing; invalidation semantics; cost/tier policy outside this document.

**Readiness:** **Partial** — artifact-ready; host + credentials + hook undecided. **No provider chosen here.**

---

### D. Containerized static serving

**Model:** Package public files into a container image with nginx/Caddy (or similar) and run on any container host. Build = Website Engine artifacts + `COPY` into image; runtime = container.

| Dimension | Assessment |
|-----------|------------|
| Deployment artifact | Container image whose docroot is the public subset of `output/website/` |
| Build step | Website Engine publish → image build → registry push → roll out |
| Runtime | Container runtime + ingress/load balancer |
| HTTPS | Ingress / reverse proxy / mesh — not inside Website Engine |
| Custom domain | Ingress host rules + DNS |
| Cache / CDN | Optional fronting CDN; image redeploy as coarse invalidation |
| Rollback | Previous image tag / digest |
| Secrets | Registry credentials, cluster/host creds via Shared Platform |
| CI/CD | Standard image pipeline; Automation Platform can own ship |
| Operational burden | **Medium–high** vs plain static sync (registry, orchestration, image churn) |

**Fit:** Useful if Founder already standardizes on containers for other surfaces. Heavier than A/B/C for a pure static brochure/blog set. Does **not** require CMS.

**Gaps:** Dockerfile/serve config not in Website Engine today; root index; public-subset filter; deploy hook = “build & roll image” rather than file sync.

**Readiness:** **Partial** — same artifact base; more platform machinery than needed for first public static cut unless containers are already mandatory.

---

### E. Future CMS adapter path

**Model:** WordPress / Ghost (self-hosted or otherwise) as `WebsiteProvider` destinations. Public site is CMS-rendered or CMS-hosted; static `output/website/` becomes optional staging, not the public docroot.

| Dimension | Assessment |
|-----------|------------|
| Deployment artifact | CMS posts/pages/media in CMS DB — **not** the M3 static tree as primary public artifact |
| Build step | Adapter maps `WebsitePublicationRequest` → CMS API; may still keep local artifacts for audit |
| Runtime | CMS app + DB (+ theme) |
| HTTPS / domain / CDN | CMS host stack |
| Cache / CDN | CMS/plugin/host; risk of duplicating Website Engine sitemap/RSS/metadata |
| Rollback | CMS revisions / DB backup — weaker than static file revert |
| Secrets | CMS Admin/API tokens in Shared Platform; `external_http=True` |
| CI/CD | Optional; publish is often API-driven at approval time |
| Operational burden | **High** relative to static (updates, DB, theme, auth) |

**Fit:** Explicitly **future** in v2.1 / M2.5 / M3 (WP/Ghost not implemented; registry rejects unknown CMS names). Valid after static public path is proven. Splits or challenges “Website Engine owns canonical render” unless adapter publishes pre-rendered HTML carefully.

**Readiness:** **Deferred** — not a candidate for first public-static M4 cut. Remains open as later provider work behind the same protocol.

---

## 6. Scoreboard (public-static fitness now)

| Rank | Mode | Public-static fitness | Notes |
|-----:|------|----------------------:|-------|
| 1 | **A** Local / self-hosted static | High | Direct consume of `output/website/`; teaches deploy hook with rsync/nginx |
| 2 | **B** Git-backed static hosting | High | Needs public-subset packaging + git policy |
| 3 | **C** Managed static hosting | High | Needs host-agnostic hook; **no vendor chosen** |
| 4 | **D** Containerized static serving | Medium | Extra platform weight for static files |
| 5 | **E** Future CMS adapter | Low (for M4 static) | Correct later path; wrong first public-static vehicle |

A–C are the primary **candidate deployment modes** for making the Founder static site publicly reachable. D is optional if container ops are already standard. E is out of scope for first public static reachability.

---

## 7. Ownership map for M4 (do not blur)

| Concern | Owner |
|---------|-------|
| Markdown → HTML, slug, canonical URL, metadata, OG, Schema.org, RSS, sitemap | **Website Engine** |
| Local static artifact write (`output/website/`) | **Website Engine** (`StaticWebsiteProvider`) |
| Website deployment hooks / cache invalidation | **Website Engine** (v2.1; **unimplemented**) |
| Publish jobs, queue, channel routing, audit | **Publishing Engine** (orchestration only) |
| Deploy transport (rsync, CI job, container roll) | **Automation Platform** (no business logic) |
| Deploy tokens, TLS keys, host credentials | **Shared Platform** |
| SEO scoring / keyword tooling | **SEO Engine** (not site deploy) |
| Editorial approval / Content Studio | **Editorial / Content Studio** (pre-site) |

**Non-goals for M4 deployment readiness:** social publish, email, campaigns, WordPress/Ghost implementation, paid provider lock-in, Publishing Engine owning docroots.

---

## 8. Gaps that block “publicly reachable” today

1. **No deploy hook** — M3 stops at filesystem write (`external_http=False`).
2. **No serving topology chosen** — A/B/C/D undecided (this document surfaces candidates only).
3. **No public-subset packaging** — operator files (`metadata.json`, `source.md`) coexist with public HTML/XML.
4. **No site-wide feed aggregation** — sitemap/RSS overwrite to single item per publish.
5. **No root landing page** — only slug directories.
6. **Canonical URL ↔ DNS** — HTML already embeds canonicals; public host/domain not bound.
7. **HTTPS / CDN / rollback runbooks** — none for the website surface.
8. **CI/CD path** — none from `publish_content` → public edge.
9. **Human gate** — v2.1 still requires human approval for production publishing; deploy must not bypass Editorial/Publishing gates.

---

## 9. Suggested M4 decision questions (non-binding)

When M4 opens (not now), founders should answer:

1. Which **first** public mode among **A / B / C** (and optionally **D**)?
2. What is the **public artifact package** (include/exclude rules for `output/website/`)?
3. What is the minimal **Website Engine deploy hook** interface (sync? git push? upload? image build) without selecting a paid vendor in the architecture doc?
4. Who runs **TLS + DNS** (operator vs host), and how do they stay aligned with `canonical_url`?
5. Is **multi-URL sitemap/RSS aggregation** in-scope for first public cut or a fast-follow?
6. Confirm **E (CMS)** remains future-only until static public path is frozen.

---

## 10. Explicit non-decisions (this sprint)

- Does **not** deploy anything or create cloud resources.
- Does **not** choose Netlify / Vercel / Cloudflare / AWS / etc. as a required vendor.
- Does **not** authorize WordPress/Ghost adapters.
- Does **not** implement deploy hooks, CI, Dockerfiles, or nginx configs.
- Does **not** move site hosting ownership into Publishing Engine.

---

## 11. Attestation

| Item | Value |
|------|-------|
| Analysis file | `docs/marketing/M3_5_M4_DEPLOYMENT_READINESS.md` |
| Code / infra implemented | **NONE** (analysis only) |
| Paid provider selected | **NO** |
| Artifact basis | M3 `output/website/` static contract (audit PASS) |
| Deploy hook owner | **Website Engine** (v2.1) |
| Confidence | **HIGH** — grounded in M3 artifact layout + v2.1 ownership + explicit M3 non-deploy scope |

---

## FINAL

```text
M4 Deployment Decision Required: YES
Candidate Deployment Modes: A (local/self-hosted static), B (Git-backed static hosting), C (managed static hosting); optional D (containerized static); E deferred (future CMS adapter)
```
