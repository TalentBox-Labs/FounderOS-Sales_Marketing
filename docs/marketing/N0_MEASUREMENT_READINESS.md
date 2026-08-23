# N0 — Measurement Readiness (Sentinel)

**Sprint:** N0  
**Date:** 2026-08-10  
**Rule:** Do not invent analytics capabilities  

---

## Required KPIs vs what exists

### SEO

| KPI | Exists today? |
|-----|---------------|
| Indexed pages / sitemap presence | **Yes** — live sitemap; can count Static pages |
| On-page readiness (title/canonical/keyword) | **Partial** — metadata + quality checker |
| Manual rank / AI visibility log | **Yes** — `/api/v1/seo` + `seo_keywords` / `seo_rank_checks` |
| Organic clicks / impressions (GSC) | **No** |
| Automated rankings | **No** |

**Measurement readiness: 3/5**

### Social

| KPI | Exists today? |
|-----|---------------|
| Reach / engagement / followers | **No** Marketing OS analytics |
| Referral traffic | **No** dedicated social attribution |
| Publish success audit | Publishing audit **framework** only (adapters unimplemented) |

**Measurement readiness: 2/5**

### Email

| KPI | Exists today? |
|-----|---------------|
| Subscribers (Marketing OS) | **No** durable Marketing list |
| Delivery / opens / clicks | **No** ESP events |
| Nurture counters | In-memory RevenueOS sketches only |

**Measurement readiness: 2/5**

### Campaign

| KPI | Exists today? |
|-----|---------------|
| Pipeline / CAC / multi-touch attribution | Revenue analytics **adjacent**, not Campaign Engine |
| Channel conversion rollup | **No** Campaign package |

**Measurement readiness: 1/5**

---

## Sentinel verdict

SEO is the only candidate with **existing KPI hooks** (manual ranks + on-page artifacts + live site). Others require new measurement plumbing before “success” is falsifiable.
