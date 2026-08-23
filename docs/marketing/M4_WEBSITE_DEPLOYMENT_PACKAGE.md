# M4 — Website Deployment Package (Artifact Inventory)

**Role:** Agent Nova — Website Engine (M4)  
**Status:** ANALYSIS ONLY — **DO NOT DEPLOY / IMPLEMENT**  
**Sprint:** M4 (deployment package definition)  
**Date:** 2026-08-10  
**Owned file:** `docs/marketing/M4_WEBSITE_DEPLOYMENT_PACKAGE.md`  
**Canonical repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

**Constraint:** No code, runtime, CI, infrastructure, or deploy changes in this document.  
**Code / API / DB / git implementation:** **NONE**.

### Evidence SoT (read-only)

| Source | Role |
|--------|------|
| `src/tools/website_engine/static_provider.py` | Frozen Static Provider write path (`StaticWebsiteProvider._write_artifacts`) |
| `src/tools/website_engine/feeds.py` | `build_sitemap` / `build_rss` / `write_feed_artifacts` |
| `src/tools/website_engine/provider.py` | `DEFAULT_SITE_OUTPUT`, `wrap_html_document` |
| `src/tools/website_engine/metadata.py` | `WebsiteMetadata.to_dict()` persistence shape |
| [M3_5_STATIC_PROVIDER_BASELINE.md](M3_5_STATIC_PROVIDER_BASELINE.md) | Static Website Provider **v1.0 FROZEN** |
| [M4_NOVA_DEPLOYMENT_REQUIREMENTS.md](M4_NOVA_DEPLOYMENT_REQUIREMENTS.md) | Prior Nova requirements (artifact path / public subset) |
| [M4_DEPLOYMENT_ARCHITECTURE.md](M4_DEPLOYMENT_ARCHITECTURE.md) | Chosen static self-host architecture (M5 deploy deferred) |

---

## Verdict

| Item | Value |
|------|-------|
| **Package root (canonical)** | `output/website/` (`REPO_ROOT / "output" / "website"`) |
| **Build artifact type** | Static site **directory tree** (filesystem), not a CMS DB, container image, or tarball |
| **Producer** | Website Engine → `StaticWebsiteProvider.publish` (default provider `static`) |
| **Deploy in this sprint** | **NONE** — package definition only |

---

## 1. Package root path

| Item | Value |
|------|-------|
| **Canonical package root** | `output/website/` |
| **Absolute default** | `{REPO_ROOT}/output/website` via `DEFAULT_SITE_OUTPUT` (`provider.py`) and `DEFAULT_OUTPUT_DIR` (`feeds.py`) |
| **Constructor override** | `StaticWebsiteProvider(output_dir=…)` / engine `output_dir=` — tests or alternate roots; Founder SoT for packaging remains **`output/website/`** |
| **Creation** | `page_dir.mkdir(parents=True, exist_ok=True)`; feeds `output_dir.mkdir(parents=True, exist_ok=True)` |
| **Nature** | Local filesystem write only; `external_http=False`; **no deploy step** in Static Provider v1.0 |

---

## 2. Build artifact definition

The **deployment package** for M4/M5 planning is the Static Provider output tree itself:

```text
output/website/                          ← PACKAGE ROOT
├── {slug}/
│   ├── index.html                       ← VERIFIED (generated)
│   ├── metadata.json                    ← VERIFIED (generated; operator)
│   └── source.md                        ← VERIFIED (generated; operator)
├── sitemap.xml                          ← VERIFIED (generated; site-level)
└── rss.xml                              ← VERIFIED (generated; site-level)
```

| Concept | Definition |
|---------|------------|
| **Build artifact** | The directory tree under the package root after one or more successful `StaticWebsiteProvider.publish` calls |
| **Deployment package** | Same tree (or a **public subset** copy) intended as docroot input for a future deploy hook — **not** produced as a separate archive by Core/Static today |
| **Public subset (recommended for serve)** | `{slug}/index.html` + `sitemap.xml` + `rss.xml` |
| **Operator / non-public by default** | `{slug}/metadata.json`, `{slug}/source.md` |

**Not a build artifact today (NOT VERIFIED / not generated):**

- Root site `index.html` / landing page
- Packaged tarball, zip, OCI image, or git commit object from Static Provider
- Cumulative multi-page sitemap/RSS index (feeds rebuilt from **current** request only — M3.5 § Explicit non-ownership)
- CDN object set, TLS certs, or host config

---

## 3. Artifact inventory (by category)

Status legend:

| Status | Meaning |
|--------|---------|
| **VERIFIED** | Emitted today by frozen Static Provider v1.0 / Core helpers it consumes |
| **NOT VERIFIED / not generated today** | Not written by Static Provider; do not assume present in the package |

### 3.1 Output directory

| Item | Status | Detail |
|------|--------|--------|
| Package root `output/website/` | **VERIFIED** | Default `DEFAULT_SITE_OUTPUT`; page dirs + feeds created on successful publish |
| Per-page dir `{output_dir}/{slug}/` | **VERIFIED** | Single path-segment slug; unsafe/path-like slugs rejected before write |

### 3.2 HTML

| Item | Status | Detail |
|------|--------|--------|
| `{slug}/index.html` | **VERIFIED** | Full document from `wrap_html_document(request)`: doctype, `lang="en"`, charset, title, meta description, canonical link, OG metas, Schema.org JSON-LD `<script type="application/ld+json">`, `<article>` body from pre-rendered `request.html` |
| Root `/index.html` | **NOT VERIFIED / not generated today** | No site landing page from Static Provider v1.0 |
| Separate HTML templates / theme files | **NOT VERIFIED / not generated today** | Inline wrap only; no template assets directory |

### 3.3 CSS / JS / static assets

| Item | Status | Detail |
|------|--------|--------|
| CSS files (`.css`) | **NOT VERIFIED / not generated today** | No stylesheet link or CSS write in `static_provider.py` / `wrap_html_document` |
| JS bundle / app scripts (`.js`) | **NOT VERIFIED / not generated today** | No external script assets; only inline JSON-LD in HTML head |
| `assets/`, `static/`, `css/`, `js/` directories | **NOT VERIFIED / not generated today** | Not part of Static Provider output contract |
| Inline `<style>` in HTML | **NOT VERIFIED / not generated today** | `wrap_html_document` does not emit styles |

### 3.4 Images

| Item | Status | Detail |
|------|--------|--------|
| Image files (`.png` / `.jpg` / `.webp` / etc.) | **NOT VERIFIED / not generated today** | Static Provider does not copy or write media |
| `og:image` / image metadata files | **NOT VERIFIED / not generated today** | Core `build_metadata` OG keys are type/title/description/url/site_name only — no image URL emission in frozen metadata builder |
| Image directories under package root | **NOT VERIFIED / not generated today** | Absent from artifact set |

> **Note:** If Markdown/HTML body already contains remote `<img src="https://…">` URLs, those remain content-embedded references only. The provider does **not** materialize image binaries into the package. Presence of such tags in a given content body is content-dependent and **NOT VERIFIED** as a package deliverable.

### 3.5 Metadata

| Item | Status | Detail |
|------|--------|--------|
| `{slug}/metadata.json` | **VERIFIED** | `json.dumps(request.metadata.to_dict(), indent=2) + "\n"` — keys: `title`, `description`, `canonical_url`, `slug`, `primary_keyword`, `og`, `schema_org` |
| HTML-head metadata (title, description, OG, JSON-LD) | **VERIFIED** | Same `WebsiteMetadata` object via `wrap_html_document` |
| SEO scoring / keyword optimization artifacts | **NOT VERIFIED / not generated today** | Explicit non-ownership (SEO Engine); Static Provider emit/persist only |

### 3.6 Markdown (operator source)

| Item | Status | Detail |
|------|--------|--------|
| `{slug}/source.md` | **VERIFIED** | Raw `request.markdown` UTF-8; no front-matter injection |

### 3.7 Sitemap

| Item | Status | Detail |
|------|--------|--------|
| `sitemap.xml` at package root | **VERIFIED** | `build_sitemap([FeedItem…])` → `write_feed_artifacts`; xmlns `http://www.sitemaps.org/schemas/sitemap/0.9` |
| Sitemap `loc` values | **VERIFIED** | Absolute `request.canonical_url` (current publish item) |
| Multi-page cumulative sitemap | **NOT VERIFIED / not generated today** | Each successful publish overwrites feeds from the **current** request only (M3.5 frozen non-goal) |

### 3.8 RSS

| Item | Status | Detail |
|------|--------|--------|
| `rss.xml` at package root | **VERIFIED** | `build_rss([FeedItem…])` → `write_feed_artifacts`; RSS 2.0 |
| RSS item fields | **VERIFIED** | `title` ← request title; `link` ← canonical URL; `description` ← metadata description; `guid` ← slug (`isPermaLink=false`); `pubDate` ← UTC-now when omitted |
| Channel defaults | **VERIFIED** | Title/link/description defaults from `feeds.build_rss` (`WorkCrew Blog` / `https://workcrew.ai/blog` / `WorkCrew website feed`) unless callers pass overrides (Static Provider uses defaults) |
| Multi-item historical feed | **NOT VERIFIED / not generated today** | Single-item rebuild per publish |

### 3.9 Canonical URLs

| Surface | Status | Detail |
|---------|--------|--------|
| Required on `WebsitePublicationRequest` | **VERIFIED** | Missing/empty `canonical_url` → validation failure, no writes |
| HTML `<link rel="canonical">` | **VERIFIED** | From `metadata.canonical_url` |
| `metadata.json` → `canonical_url` | **VERIFIED** | Persisted field |
| OG `og:url` | **VERIFIED** | Set by Core `build_metadata` to canonical |
| Sitemap `loc` | **VERIFIED** | `FeedItem.link = request.canonical_url` |
| RSS item `link` | **VERIFIED** | Same FeedItem link |
| Deploy/host rewriting of canonical | **NOT VERIFIED / not generated today** | Out of Core/Static; operator must align public host with embedded canonical |

---

## 4. `artifact_paths` contract (provider success)

On successful publish, `WebsiteProviderResult.artifact_paths` includes:

| Key | Path pattern |
|-----|----------------|
| `html_path` | `{output_dir}/{slug}/index.html` |
| `metadata_path` | `{output_dir}/{slug}/metadata.json` |
| `markdown_path` | `{output_dir}/{slug}/source.md` |
| `sitemap_path` | `{output_dir}/sitemap.xml` |
| `rss_path` | `{output_dir}/rss.xml` |

Encoding: **UTF-8** for all text writes.

Provider success `details`: `sitemap_urls`, `rss_item_count`, `output_dir`.

---

## 5. Idempotency / package evolution rules (frozen)

| Behavior | Rule |
|----------|------|
| Re-publish same slug | Overwrites `index.html`, `metadata.json`, `source.md` in place |
| Feeds | Overwritten with single-item feeds for **this** request only |
| Other slug dirs | **Retained** (not deleted) under package root |
| Partial write failure | No transactional rollback (M3.5 § Rollback boundary) |
| Validation failure | **No** artifacts written for that call |

---

## 6. What is in vs out of the deployment package

### In scope (package contents today)

1. Per-page HTML document  
2. Per-page metadata JSON + Markdown source (operator)  
3. Site-level `sitemap.xml` + `rss.xml`  
4. Canonical URL consistency across HTML / metadata / feeds  

### Out of scope / not in package today

1. CSS, JS bundles, image binaries, asset directories  
2. Root landing HTML  
3. Deploy transport, CDN, TLS, DNS, host config  
4. Separate archive/image packaging step  
5. Multi-page feed aggregation  

---

## FINAL — Package root + artifact inventory summary

| Field | Value |
|-------|--------|
| **Package root path** | `output/website/` |
| **Absolute default** | `{REPO_ROOT}/output/website` |

### Artifact inventory summary

| Artifact | Path | Status |
|----------|------|--------|
| HTML page | `{slug}/index.html` | **VERIFIED** — generated |
| Metadata | `{slug}/metadata.json` | **VERIFIED** — generated |
| Markdown source | `{slug}/source.md` | **VERIFIED** — generated |
| Sitemap | `sitemap.xml` | **VERIFIED** — generated (current item only) |
| RSS | `rss.xml` | **VERIFIED** — generated (current item only) |
| Canonical URLs | Embedded in HTML / metadata / sitemap `loc` / RSS `link` | **VERIFIED** — required + propagated |
| CSS | — | **NOT VERIFIED / not generated today** |
| JS assets | — | **NOT VERIFIED / not generated today** (inline JSON-LD only) |
| Images | — | **NOT VERIFIED / not generated today** |
| Root landing `index.html` | — | **NOT VERIFIED / not generated today** |
| Deploy archive / container | — | **NOT VERIFIED / not generated today** |

**Build artifact:** static directory tree at `output/website/`.  
**Deployment package:** that tree (prefer public subset: HTML + sitemap + RSS) for a future M5 deploy hook — **not implemented in M4**.
