# S0 — SEO Measurement Plan

**Sprint:** S0  
**Agent:** BEACON  
**Status:** Plan only — no external tooling installed

---

## 1. Purpose

Define future SEO KPIs and data sources without activating Search Console, analytics SaaS, or paid tools.

---

## 2. KPI catalog

| KPI | Definition | Internal (S0/S1) | External (future) |
|-----|------------|------------------|-------------------|
| **Indexed pages** | URLs known to search index | Sitemap URL count; readiness pass count | Google Search Console |
| **Impressions** | SERP views | — | Search Console |
| **Clicks** | SERP → site clicks | — | Search Console |
| **CTR** | clicks / impressions | — | Search Console |
| **Average position** | Mean rank for queries | — | Search Console |
| **Organic sessions** | Non-paid web visits | — | Analytics (GA4 / Plausible / CF Web Analytics) |
| **Landing-page conversions** | Goal completions from organic | — | Analytics + CRM attribution |

---

## 3. Internally available metrics (now)

| Metric | Source | Sprint |
|--------|--------|--------|
| Pages with ERROR-free readiness | `evaluate_artifact_readiness()` | S0 |
| Canonical / origin alignment warnings | Readiness report | S0 |
| Sitemap URL count | `output/website/sitemap.xml` | S0 |
| RSS item count | `output/website/rss.xml` | S0 |
| Publish artifact completeness | Website Engine publish result | M2+ |
| Deployment package integrity | Website Deployment manifest | M5+ |

---

## 4. Metrics requiring future external services

| Service | KPIs enabled | Activation gate |
|---------|--------------|-----------------|
| Google Search Console | indexed, impressions, clicks, CTR, position | Domain ratified + `is_indexing_activation_allowed()` |
| Web analytics | organic sessions, landing conversions | Founder tool selection (not in S0 scope) |
| CRM / Revenue OS | attributed pipeline from organic | Revenue OS integration slice |

**Paid SEO SaaS:** NOT REQUIRED for baseline (N0 score: 0 paid tools).

---

## 5. Reporting cadence (future)

| Cadence | Audience | Content |
|---------|----------|---------|
| Per publish | Engineering | Readiness report snapshot |
| Weekly | Founder | Readiness trend, sitemap delta, blocked indexing status |
| Monthly | Marketing | Organic KPIs (post-activation) |

---

## 6. S0 constraints

- No Search Console property creation
- No analytics script injection
- No sitemap ping automation
- Measurement plan is documentation-only

---

## 7. S1 measurement deliverables

1. Readiness aggregate CLI (`seo readiness --root output/website`)
2. JSON export for CI gates
3. Baseline snapshot file for regression comparison
