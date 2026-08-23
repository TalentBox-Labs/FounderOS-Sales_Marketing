# M2.5 — Website Provider Readiness Analysis

**Status:** ANALYSIS ONLY — **DO NOT IMPLEMENT in M2.5**  
**Sprint:** M2.5 (prepare for future M3)  
**Date:** 2026-08-10  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Architecture:** v2.1 ([Architecture_v2.1.md](../architecture/Architecture_v2.1.md), [Architecture_ADR_002.md](../architecture/Architecture_ADR_002.md))  
**Prerequisite:** Website Engine Core (M2) — [M2_WEBSITE_ENGINE_REPORT.md](M2_WEBSITE_ENGINE_REPORT.md)

**Constraint:** No paid SaaS assumptions. Self-hosted / free / OSS paths only.  
**Scope:** Recommend the **first concrete** website provider for future M3. Not a final forever destination.

---

## 1. Mission

Pick one first provider among:

| Candidate | Label |
|-----------|-------|
| WordPress self-hosted | `WORDPRESS` |
| Ghost self-hosted | `GHOST` |
| Static-site adapter | `STATIC` |

If evidence is insufficient: `NOT VERIFIED`.

---

## 2. Evidence base (repository facts)

| Source | Relevant fact |
|--------|----------------|
| [Architecture_v2.1.md](../architecture/Architecture_v2.1.md) § Website Engine | Website Engine owns **canonical Founder website**: Markdown rendering, HTML, slug, canonical URLs, metadata, OG, Schema.org, RSS, sitemap, static assets, website API integration, cache invalidation, **deployment hooks**. WordPress / Ghost listed as **future** integrations. Publishing Engine owns orchestration only. |
| [Website_Engine_Implementation_Checklist.md](Website_Engine_Implementation_Checklist.md) | Explicit FUTURE rows: WordPress adapter, Ghost adapter, **Static site adapter**. Provider abstraction prepared; no CMS ownership inside Publishing. |
| [M2_WEBSITE_ENGINE_REPORT.md](M2_WEBSITE_ENGINE_REPORT.md) | M2 delivered provider-neutral interface + **in-process stub** writing under `output/website/`. No WordPress/Ghost/external HTTP. Follow-up #2: “Real static-site / WordPress / Ghost providers (still behind `WebsiteProvider`).” |
| `src/tools/website_engine/provider.py` | `WebsiteProvider` protocol: `publish(WebsitePublicationRequest) -> WebsiteProviderResult`. Request already carries `html`, `markdown`, `metadata`, `slug`, `canonical_url`, `render`. Stub writes `index.html`, `metadata.json`, `source.md`, sitemap, RSS. `external_http=False`. |
| `src/tools/website_engine/content_model.py` | Canonical content from filesystem: `input/{week}/05_Final.md` (+ optional `02_SEO_Plan.md`). **No CMS database.** Markdown body + string front matter. |
| Founder content pipeline | Live bundles under `input/W*/05_Final.md` (Markdown editorial artifacts). |

**Implication:** M2 already owns the hard website contracts (render, URLs, metadata, feeds) and emits filesystem artifacts. The first M3 provider should **consume that contract with minimal translation**, not introduce a second rendering owner.

---

## 3. Evaluation criteria

Scoring: **5** = strong fit for this repo now · **3** = workable with material adapter/ops cost · **1** = poor first-provider fit.

| # | Criterion | Meaning for Founder OS |
|---|-----------|------------------------|
| C1 | Ownership / control | Does Website Engine remain canonical owner of render/URLs/metadata/site publish? |
| C2 | API fit | Fit to `WebsiteProvider.publish(request)` without inventing parallel models |
| C3 | Markdown / content compatibility | Fit to `input/{week}/05_Final.md` pipeline |
| C4 | SEO support | Can carry OG, Schema.org, canonical, sitemap, RSS already produced in M2 |
| C5 | Operational complexity | Runtime, DB, upgrades, auth for a first M3 slice |
| C6 | Hosting burden | Self-host cost for a solo/founder-ops path (no paid SaaS) |
| C7 | Reversibility | Ease of abandoning the provider without rewriting Website Engine |
| C8 | Free / OSS suitability | Viable without paid cloud CMS |
| C9 | Adapter complexity | Net-new code beyond promoting/extending the stub |
| C10 | Lock-in risk | Theme/API/content format captivity |

---

## 4. Candidate analysis

### 4.1 WordPress (self-hosted)

**Model:** PHP app + MySQL/MariaDB; publish via REST API (Application Passwords / JWT) or WP-CLI; classic/block editor content model.

| Criterion | Score | Evidence-based note |
|-----------|------:|---------------------|
| C1 Ownership / control | 2 | WP themes/plugins typically own HTML/SEO presentation. Publishing pre-rendered HTML fights Gutenberg; publishing Markdown cedes render ownership Website Engine already claimed in v2.1. |
| C2 API fit | 2 | REST expects WP posts/media/meta shapes. `WebsitePublicationRequest` would need translation (status, categories, featured media, `meta`/`yoast` fields). Auth + HTTP path (`external_http=True`) not present in M2 stub. |
| C3 Markdown compatibility | 2 | WP is HTML/block-native. Repo source of truth is Markdown under `input/{week}/`. Conversion + round-trip loss risk. |
| C4 SEO support | 3 | Achievable via plugins (classic SEO / Schema) or custom meta, but **duplicates** M2 metadata/sitemap/RSS contracts and adds plugin surface. |
| C5 Operational complexity | 1 | PHP, DB, updates, plugin security, permalinks, cron — high for first M3. |
| C6 Hosting burden | 1 | Always-on LAMP/LEMP (or container equivalent); heavier than static. |
| C7 Reversibility | 2 | Content lands in WP DB; export/migration non-trivial. |
| C8 Free / OSS suitability | 4 | WordPress.org is free/OSS; self-host OK under mission constraint. |
| C9 Adapter complexity | 1 | Auth, media, HTML vs blocks, idempotent update-by-slug, error mapping — large vs stub. |
| C10 Lock-in risk | 2 | Plugin/theme/DB lock-in; URL and shortcode habits stick. |
| **Total** | **20 / 50** | |

**Verdict:** Valid long-term option (architecture names it), **poor first M3 provider**.

---

### 4.2 Ghost (self-hosted)

**Model:** Node.js + DB (MySQL/SQLite); Admin API; Markdown-friendlier editorial UX than WordPress.

| Criterion | Score | Evidence-based note |
|-----------|------:|---------------------|
| C1 Ownership / control | 3 | Ghost still owns public theme/render. Better API for remote publish of HTML/Markdown than WP, but Website Engine’s “canonical website” ownership is still split. |
| C2 API fit | 3 | Admin API maps closer to article publish (title, slug, HTML/Markdown, meta). Still requires HTTP auth tokens and Ghost-specific fields; M2 stub is filesystem-only. |
| C3 Markdown compatibility | 4 | Stronger Markdown story than WP; aligns better with `05_Final.md`. Front-matter mapping still custom. |
| C4 SEO support | 3 | Native meta/OG/canonical; sitemap/RSS exist in Ghost. Risk of **double sitemap/RSS** vs M2 `feeds.py` unless adapter deliberately defers. |
| C5 Operational complexity | 2 | Node + DB + Ghost upgrades + mail config for members features (even if unused). |
| C6 Hosting burden | 2 | Always-on process + DB; lighter than full WP stack, heavier than static files. |
| C7 Reversibility | 3 | Content in Ghost DB; export exists but not as natural as repo Markdown + static HTML. |
| C8 Free / OSS suitability | 4 | Ghost is OSS; self-host path exists without paid Ghost(Pro). |
| C9 Adapter complexity | 2 | Smaller than WP, still JWT/Admin API client, idempotent upsert, media, failure taxonomy. |
| C10 Lock-in risk | 3 | Lower than WP plugin ecosystem; still Ghost theme/API coupling. |
| **Total** | **29 / 50** | |

**Verdict:** Better API/Markdown fit than WordPress; still introduces a second runtime and splits site ownership. **Second choice**, not first M3.

---

### 4.3 Static-site adapter

**Model:** Treat M2 stub artifacts (`output/website/{slug}/index.html`, `metadata.json`, `source.md`, `sitemap.xml`, `rss.xml`) as the publication surface; M3 adds a real static provider (artifact package + optional deploy hook) behind `WebsiteProvider`. Hosting can be any free/OSS static file server, object storage + CDN, or local nginx — **no CMS**.

| Criterion | Score | Evidence-based note |
|-----------|------:|---------------------|
| C1 Ownership / control | 5 | Matches v2.1: Website Engine keeps Markdown→HTML, URLs, metadata, feeds, static assets, deployment hooks. No CMS re-render. |
| C2 API fit | 5 | Identical shape to `StubWebsiteProvider`: request fields already sufficient; promote stub → production static provider without new domain model. |
| C3 Markdown compatibility | 5 | Source remains `input/{week}/05_Final.md`; stub already persists `source.md` beside HTML. |
| C4 SEO support | 5 | M2 already emits description, canonical, OG, Schema.org JSON-LD, sitemap, RSS in-process — no plugin tax. |
| C5 Operational complexity | 5 | No PHP/Node CMS or DB for the site itself. Ops = generate artifacts + sync/deploy files. |
| C6 Hosting burden | 5 | Static files; free/OSS hosting paths plentiful; fits “no paid SaaS” constraint. |
| C7 Reversibility | 5 | Artifacts are repo-adjacent files; switching later to Ghost/WP is additive behind the same protocol. |
| C8 Free / OSS suitability | 5 | No CMS license/hosting product required. |
| C9 Adapter complexity | 5 | Lowest delta from current stub; checklist already lists “Static site adapter (future).” M2 report lists static-site first among real providers. |
| C10 Lock-in risk | 5 | Lowest: HTML/Markdown/XML under Founder control. |
| **Total** | **50 / 50** | |

**Caveat (honest):** Static does **not** give a hosted CMS editor UI. That is acceptable for M3 because Editorial / Content Studio already own the Founder content workflow; Website Engine is the site destination, not a second CMS.

---

## 5. Scoreboard (rank)

| Rank | Provider | Total (/50) | First-M3 fitness |
|-----:|----------|------------:|------------------|
| 1 | **STATIC** (static-site adapter) | **50** | **Recommended** |
| 2 | GHOST (self-hosted) | 29 | Later / optional |
| 3 | WORDPRESS (self-hosted) | 20 | Later / optional |

---

## 6. Decision

### Recommended First Provider: **STATIC**

**Not** WordPress or Ghost for the first concrete M3 provider.

### Rationale (one paragraph)

The repository already implements a provider-neutral `WebsiteProvider` whose stub writes exactly the artifact set a static site needs (HTML page, metadata, source Markdown, sitemap, RSS) from the Founder Markdown pipeline under `input/{week}/`, while Architecture v2.1 assigns Website Engine — not a CMS — ownership of render, URLs, metadata, feeds, static assets, and deploy hooks. Promoting that stub into a real static-site adapter is the lowest-complexity, free/OSS, reversible path into M3: it preserves canonical ownership, reuses the existing request/result contracts without HTTP/CMS translation, carries M2 SEO contracts without plugins, and avoids WordPress/Ghost operational and lock-in cost until a later sprint explicitly needs a CMS destination.

### Explicit non-decisions

- Does **not** retire WordPress/Ghost as future adapters (still named in v2.1 / checklist).
- Does **not** authorize M3 implementation in this sprint.
- Does **not** choose a specific static host/vendor (keep host-agnostic; rsync/nginx/object-storage are sufficient mental models).
- Does **not** require paid SaaS (Ghost Pro, WP.com, Netlify paid tiers, etc.).

---

## 7. Suggested M3 acceptance sketch (non-binding, prepare only)

When M3 opens (not now):

1. Implement `StaticWebsiteProvider` (or equivalent name) behind `WebsiteProvider`.
2. Keep stub available for tests; production path writes/packages under `output/website/` (or configurable out dir).
3. Optional deploy hook interface owned by Website Engine (v2.1), still no social/email/campaign logic.
4. Preserve `external_http=False` unless a later CMS adapter is chosen.
5. Leave WordPress/Ghost as subsequent providers once static path is frozen.

---

## 8. Attestation

| Item | Value |
|------|-------|
| Analysis file | `docs/marketing/M2_5_WEBSITE_PROVIDER_READINESS.md` |
| Code / adapters implemented | **NONE** (analysis only) |
| Paid SaaS assumed | **NO** |
| Recommended first provider | **STATIC** |
| Confidence | **HIGH** — grounded in M2 stub + v2.1 ownership + Markdown filesystem source of truth |
