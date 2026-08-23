# M4 — Nova Deployment Requirements (Website Engine)

**Role:** Agent Nova — Website Engine (M4 analysis only)  
**Status:** ANALYSIS ONLY — **DO NOT DEPLOY / IMPLEMENT**  
**Sprint:** M4 (requirements capture)  
**Date:** 2026-08-10  
**Owned file:** `docs/marketing/M4_NOVA_DEPLOYMENT_REQUIREMENTS.md`  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Constraint:** No code, runtime, CI, infrastructure, or deploy changes in this document.  
**Code / API / DB / git implementation:** **NONE**.

### Evidence SoT (read-only)

| Source | Role |
|--------|------|
| `src/tools/website_engine/static_provider.py` | Frozen Static Provider write path |
| `src/tools/website_engine/provider.py` | `DEFAULT_SITE_OUTPUT`, `WebsitePublicationRequest`, wrap helpers |
| [M3_5_STATIC_PROVIDER_BASELINE.md](M3_5_STATIC_PROVIDER_BASELINE.md) | Static Website Provider **v1.0 FROZEN** |
| [M3_5_M4_DEPLOYMENT_READINESS.md](M3_5_M4_DEPLOYMENT_READINESS.md) | Prior mode analysis (A–E); non-binding candidates |
| [Architecture_v2.2.md](../architecture/Architecture_v2.2.md) + [Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md) §4.4 | Destination: Website Engine SHIPPED (Core + Static); M4 = deploy-mode decision |
| [M2_5_WEBSITE_ENGINE_BASELINE.md](M2_5_WEBSITE_ENGINE_BASELINE.md) | Website Engine Core **v1.0 FROZEN** (render / provider) |

---

## 1. Boundary law (Core vs extensibility)

| Layer | In scope of frozen Core / Static Provider | Out of Core contracts |
|-------|-------------------------------------------|------------------------|
| **Website Engine Core** | Content model, slug/URL, metadata, Markdown→HTML render, sitemap/RSS builders, provider protocol | Deploy hooks, CDN APIs, TLS, DNS, host selection |
| **Static Provider v1.0** | Filesystem write under configured `output_dir`; `external_http=False` | Network publish, CDN, cache invalidation, remote rollback |
| **Deploy / serve** | Consumes artifacts after Core publish | Extensibility only — **outside** Website Engine Core contracts |

**Nova rule (authoritative for this document):**

- **Core remains render + provider** (prepare page → `WebsitePublicationRequest` → static write).
- **Deploy hooks are OUTSIDE Website Engine Core contracts.** Destination architecture may name future “CMS/deploy hooks” as Website Engine *module* extensibility ([Marketing_OS_v2.2.md](../architecture/Marketing_OS_v2.2.md) §4.4), but they are **not** part of Core v1.0 / Static Provider v1.0 frozen APIs and must not be smuggled into Core baselines without a new baseline version.
- Automation Platform may execute deploy *transport*; Shared Platform owns secrets/config; Publishing Engine stays orchestration-only (no docroot ownership); SEO Engine must not own site deploy.

---

## 2. Build artifact

| Item | Requirement |
|------|-------------|
| **Artifact type** | Directory tree of static files (not a CMS DB, not an app binary). Optional later packaging (tarball, git tree, image `COPY`) **derives from** this tree. |
| **Producer** | Website Engine static path: `StaticWebsiteProvider.publish` / engine `publish_content` (already implemented for local write). |
| **Per-page (required for public HTML)** | `{slug}/index.html` — full document via `wrap_html_document` (doctype, meta, canonical, OG, JSON-LD, `<article>`). |
| **Per-page (operator / non-public by default)** | `{slug}/metadata.json`, `{slug}/source.md` — exclude or block from public serve unless explicitly chosen. |
| **Site-level (public feeds)** | `sitemap.xml`, `rss.xml` at site root of the artifact tree. |
| **Encoding** | UTF-8 for all text writes. |
| **Idempotency** | Same slug overwrites page files and regenerates feeds from the **current** request only (no multi-page feed aggregation in Static Provider v1.0). |
| **Not a build artifact today** | Root `index.html` / landing page; cumulative multi-URL sitemap/RSS; container image; git commit; CDN object set. |

**Public subset (minimum for reachability):**

```text
{artifact_root}/
├── {slug}/index.html
├── sitemap.xml
└── rss.xml
```

---

## 3. Output directory (recommended)

| Item | Value |
|------|-------|
| **Recommended artifact path** | `output/website/` |
| **Canonical default** | `REPO_ROOT / "output" / "website"` (`DEFAULT_SITE_OUTPUT` in `provider.py`) |
| **Layout** | `{output_dir}/{slug}/index.html\|metadata.json\|source.md` + `{output_dir}/sitemap.xml` + `{output_dir}/rss.xml` |
| **Override** | Constructor / registry / engine `output_dir=` for tests or alternate roots — production packaging should still treat **`output/website/`** as the Founder SoT publish root |
| **Creation** | Provider creates page dirs and feed root with `mkdir(parents=True, exist_ok=True)` |
| **Safety** | Slug is a single path segment; path traversal rejected before write |

**Nova recommendation:** Keep **`output/website/`** as the single recommended artifact path for M4 packaging and any future deploy-hook input. Do not invent a second parallel publish root.

---

## 4. Static serving

| Requirement | Detail |
|-------------|--------|
| **Runtime model** | Static file server only for first public path (nginx/Caddy/Apache/host edge). No Founder app process required to serve HTML. |
| **URL mapping** | Directory URLs: `/{slug}/` → `{slug}/index.html`. |
| **Docroot** | Public subset of `output/website/` (or a sync copy). Prefer not exposing `metadata.json` / `source.md`. |
| **Host re-render** | **Forbidden** — host must not re-run Markdown→HTML; serve Core-produced HTML as-is. |
| **Feeds** | Serve `/sitemap.xml` and `/rss.xml` from site root of the public package. |
| **Gap (known)** | No root landing page from Static Provider v1.0; operators must accept slug-only entry or add a non-Core landing later. |

Candidate serve modes (from M3.5 readiness; **not chosen here**): A local/self-hosted, B git-backed static, C managed static, D containerized static. CMS (E) deferred.

---

## 5. HTTPS

| Requirement | Detail |
|-------------|--------|
| **TLS** | Required for any public production URL that matches embedded `canonical_url` (HTTPS). |
| **Termination** | At reverse proxy / managed host edge — **not** inside Website Engine Core or Static Provider. |
| **Artifacts** | Founder tree does not include certificates or ACME state. |
| **Owner** | Operator or host platform; credentials/config via Shared Platform when automated. |

---

## 6. Custom domains

| Requirement | Detail |
|-------------|--------|
| **Alignment** | Public host + DNS must match `canonical_url` already written into HTML head, `metadata.json`, sitemap `loc`, and RSS `link`. |
| **Ownership** | DNS/host binding is infrastructure (Shared Platform / operator), not Core render. |
| **Mismatch risk** | Serving under a different origin than canonical creates SEO/canonical conflicts; treat alignment as an M4 gate before public cut. |
| **Core change** | Changing base/canonical policy is a Core/URL concern — not a deploy-hook concern — and requires baseline revision if contracts move. |

---

## 7. Cache

| Requirement | Detail |
|-------------|--------|
| **Static Provider** | No cache layer; filesystem overwrite is the freshness model. |
| **Edge / proxy cache** | Optional for self-host; often native on managed/git hosts. |
| **Invalidation** | Destination docs may assign cache-invalidation *intent* to Website Engine module extensibility; **not** implemented and **not** in Core v1.0 / Static Provider v1.0 contracts. |
| **Coarse fallback** | Redeploy / re-sync public tree (new artifact revision) until an invalidation hook exists outside Core. |

---

## 8. CDN

| Requirement | Detail |
|-------------|--------|
| **Need** | Optional for first public cut (A); usual for B/C; optional front for D. |
| **Contract** | CDN config, purge APIs, and vendor choice are **outside Core**. No provider selected in this analysis. |
| **Input** | Same public subset of `output/website/`. |
| **Boundary** | CDN must not become a second render owner; it distributes Core HTML/XML only. |

---

## 9. Rollback

| Layer | Guarantee / requirement |
|-------|-------------------------|
| **Static Provider v1.0** | No transactional multi-file rollback; validation failure → no write; mid-write failure may leave partial files; retry overwrites. |
| **Deploy / public edge** | Must retain a prior **artifact snapshot** (directory backup, git commit, object version, or image tag) and re-point serve root — this is deploy-ops extensibility, not Core. |
| **Remote undo** | Out of Static Provider scope (no remote publish today). |
| **Human gate** | Production deploy must not bypass Editorial / Publishing approval gates (Architecture v2.2 human-gate law). |

---

## 10. Build pipeline

| Stage | Owner | Status |
|-------|-------|--------|
| 1. Editorial approval / publish authorization | Editorial / Publishing | Existing gates; required before production expose |
| 2. Website Engine prepare + static publish | Website Engine Core + Static Provider | **Implemented** → writes `output/website/` |
| 3. Public-subset package | Future packaging (outside Core) | **Missing** — filter operator files |
| 4. Deploy transport (rsync / git push / upload / image roll) | Automation Platform executes; hook interface = **extensibility outside Core** | **Not implemented** |
| 5. TLS / DNS / CDN attach | Shared Platform + operator/host | **Not implemented** for website surface |
| 6. Verify canonical URL live | Ops checklist | **Not implemented** |

**Pipeline invariant:** Build = Website Engine static publish **before** expose/sync. Do not move render into CI templates, host build plugins, or Publishing Engine.

---

## 11. Deploy hooks — explicit non-Core

| Statement | Status |
|-----------|--------|
| Deploy hooks are **outside** Website Engine **Core** contracts | **REQUIRED reading for M4** |
| Static Provider messages and baselines: “no external HTTP, no deploy” | **FROZEN** |
| Future module-level deploy/CMS hooks (Marketing OS v2.2) | Extensibility / future baseline — not silent Core expansion |
| Publishing Engine | Must not own deploy hooks or docroots |
| SEO Engine | Must not own site deploy |

Any M4 implementation of hooks must be a **new, versioned surface** (e.g. optional adapter or Automation job contract), leaving Core render/provider APIs unchanged unless a deliberate Core baseline bump is approved.

---

## 12. Gaps blocking public reachability (requirements backlog)

1. No deploy-hook interface (correctly outside Core; still missing as extensibility).  
2. No serving topology decision (A/B/C; optional D).  
3. No public-subset packaging rules for `output/website/`.  
4. Single-item sitemap/RSS overwrite (site-wide aggregation undecided).  
5. No root landing page from Static Provider.  
6. No bound public domain ↔ `canonical_url`.  
7. No HTTPS / CDN / rollback runbooks for the website surface.  
8. No CI path: `publish_content` → public edge.

---

## 13. Explicit non-decisions

- No vendor selection (Netlify / Vercel / Cloudflare / AWS / etc.).  
- No WordPress / Ghost adapter authorization.  
- No Dockerfile, nginx config, or CI workflow authored here.  
- No expansion of Static Provider or Core APIs.  
- No move of hosting ownership into Publishing Engine.

---

## FINAL — Nova requirements summary

| Concern | Nova requirement |
|---------|------------------|
| **Build artifact** | Static directory tree from Static Provider: `{slug}/index.html` (+ operator `metadata.json` / `source.md`), root `sitemap.xml` / `rss.xml`. |
| **Output directory** | **`output/website/`** (canonical `DEFAULT_SITE_OUTPUT`). |
| **Static serving** | Serve public subset as files; map `/{slug}/` → `index.html`; no host-side re-render. |
| **HTTPS** | Edge/proxy TLS; not in Core artifacts. |
| **Custom domains** | DNS/host must match embedded `canonical_url`. |
| **Cache** | Optional edge cache; invalidation not in Core — redeploy as coarse default. |
| **CDN** | Optional distributor of the same tree; outside Core; no vendor chosen. |
| **Rollback** | Snapshot + re-point at deploy layer; Provider has no remote/transactional rollback. |
| **Build pipeline** | Approve → Core/Static publish to `output/website/` → package public subset → deploy transport (extensibility) → verify. |
| **Core boundary** | **Core = render + provider only.** |
| **Deploy hooks** | **OUTSIDE Website Engine Core contracts** (future extensibility only). |

### Recommended artifact path

```text
output/website/
```

**M4 Deployment Decision Required:** YES (serving mode A/B/C; packaging; hook surface versioning — without mutating Core v1.0 / Static Provider v1.0).

| Item | Value |
|------|-------|
| Analysis file | `docs/marketing/M4_NOVA_DEPLOYMENT_REQUIREMENTS.md` |
| Implementation in this sprint | **NONE** |
| Recommended artifact path | **`output/website/`** |
| Core remains | Render + provider |
| Deploy hooks | Outside Core contracts |
