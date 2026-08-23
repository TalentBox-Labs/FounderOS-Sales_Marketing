# N0.5 — Domain Identity Audit (Atlas)

**Sprint:** N0.5  
**Date:** 2026-08-10  
**Architecture:** UNCHANGED  
**Code / DNS changes:** **0**

---

## Host roles (current facts)

| Role | Value | Evidence |
|------|-------|----------|
| Public deployment host (Pages Production) | `founderos-staging.pages.dev` | M7 / M7.5 production baseline |
| Staging preview host | `preview.founderos-staging.pages.dev` | M6.2 / M6.5 |
| Embedded canonical / feed host | `workcrew.ai` (paths under `/blog`) | Website Engine defaults + content FM + live artifacts |
| Founder-ratified production domain | **NOT FOUND** | No FDR / governance Accept for website host |

---

## Inventory

| Location | Value / pattern | Classification |
|----------|-----------------|---------------|
| `src/tools/website_engine/urls.py` `DEFAULT_SITE_BASE` | `https://workcrew.ai/blog` | **HARDCODED** default · **CONFIGURABLE** via `site_base` / FM |
| `src/tools/website_engine/feeds.py` RSS channel default `link` | `https://workcrew.ai/blog` | **HARDCODED** default · overrideable |
| `input/*/05_Final.md` `canonical_url` | `https://workcrew.ai/blog/...` | **CURRENT** content convention · **not** founder ratification of DNS |
| Live `output/website/**/index.html` canonical / OG / Schema | `https://workcrew.ai/blog/hiring-systems` | **CURRENT** artifact |
| Live `sitemap.xml` `<loc>` | `https://workcrew.ai/blog/...` | **CURRENT** |
| Live `rss.xml` channel/item links | `https://workcrew.ai/blog` | **CURRENT** |
| Cloudflare Pages project domains | `founderos-staging.pages.dev` (+ pending `workcrew.ai` / `blog.workcrew.ai`) | **CURRENT** host · pending custom = **NOT CONFIGURED** (DNS) |
| `.env.local` `CLOUDFLARE_PROJECT_NAME` | `founderos-staging` | **CONFIGURABLE** (ops) · not brand domain |
| `CLOUDFLARE_PRODUCTION_DOMAIN` | Absent | **UNKNOWN** / unset |
| Publishing Engine | No production hostname ownership | N/A (orchestration) |
| Deployment Adapter / runbook | Align DNS with `canonical_url` | **DOCUMENTED** guidance |
| M7 attach of `workcrew.ai` | Engineering attach; CNAME pending | **PLACEHOLDER** cutover · **not** FDR |
| Docs (`API.md`, `runner_api.py` contact URLs) | `workcrew.ai` / `api.workcrew.ai` | **STALE/PRODUCT** brand refs · ≠ website FDR |
| Tests (`test_website_engine`, static fixtures) | `workcrew.ai` examples | **HARDCODED** fixtures |
| M7.5 production baseline | Certifies `founderos-staging.pages.dev` | **CURRENT** certified public host |
| robots.txt on Pages | Cloudflare default on `*.pages.dev` | **CURRENT** host behavior · not Founder Static artifact |

---

## Ratification search

| Source class | Founder-approved website production domain? |
|--------------|-----------------------------------------------|
| `docs/governance/F0_*` / `F1_*` | **NO** (editorial decisions only) |
| Architecture ADR-002/003 | Website ownership; **no** hostname ratification |
| M4–M7.5 ops docs | Recommend custom domain; **no** Accept of specific brand host |
| N0 domain audit | **CUSTOM DOMAIN RECOMMENDED** — not chosen |

**Conclusion:** `workcrew.ai` is a **widespread content/default convention**, not a **founder-ratified production domain decision**.

---

## Alignment

| Check | Result |
|-------|--------|
| Public host == canonical host | **FAIL** (`founderos-staging.pages.dev` ≠ `workcrew.ai`) |
| Approved production domain | **NOT RATIFIED** |

**Outcome: B — FOUNDER DOMAIN DECISION REQUIRED** before DNS/host cutover or SEO Engine.
