# M4 — Website Deployment Decision

**Status:** DECIDED (engineering path) — Founder ratification of production go-live remains a human gate  
**Sprint:** M4 (multi-agent, architecture + planning only)  
**Date:** 2026-08-10  
**Architecture:** v2.2 / ADR-003  
**Registry:** Platform Agent Registry v1.0  
**Baselines:** Publishing v1.0 · Website Engine Core v1.0 · Static Provider v1.0  

**Code / deploy / purchase / runtime / DB / git-network / Cloudflare resource changes:** **NONE**

---

## Evidence pack

| Agent / Addendum | Doc |
|------------------|-----|
| Atlas | [M4_ARCHITECTURE_DECISION.md](M4_ARCHITECTURE_DECISION.md) |
| Nova | [M4_WEBSITE_DEPLOYMENT_PACKAGE.md](M4_WEBSITE_DEPLOYMENT_PACKAGE.md) |
| Hermes | [M4_PUBLISHING_DEPLOYMENT_COMPATIBILITY.md](M4_PUBLISHING_DEPLOYMENT_COMPATIBILITY.md) |
| Scout | [M4_DEPLOYMENT_OPTIONS.md](M4_DEPLOYMENT_OPTIONS.md) |
| Scout (provider) | [M4_CLOUDFLARE_PAGES_EVALUATION.md](M4_CLOUDFLARE_PAGES_EVALUATION.md) |
| Sentinel | [M4_REGRESSION_AUDIT.md](M4_REGRESSION_AUDIT.md) |
| Ledger | [../governance/M4_DEPLOYMENT_GOVERNANCE.md](../governance/M4_DEPLOYMENT_GOVERNANCE.md) |

---

## Canonical decision

| Field | Value |
|-------|-------|
| **Deployment Architecture (provider-independent)** | Core → **Deployment Adapter** → Hosting Platform |
| **Hosting mode class** | Managed / git-backed static hosting of the public subset of `output/website/` |
| **First production hosting provider** | **CLOUDFLARE PAGES** |
| **Portable fallback host** | Self-hosted static server (Nginx/Caddy) via the **same** adapter interface |
| **Provider Independent** | **YES** |
| **Package root** | `output/website/` |
| **Paid infrastructure required** | **NO** (Cloudflare Pages Free plan sufficient for first production) |

Deferred: Containerized static; CMS adapters (WordPress/Ghost).

---

## Why Cloudflare Pages (provider selection)

Evidence in [M4_CLOUDFLARE_PAGES_EVALUATION.md](M4_CLOUDFLARE_PAGES_EVALUATION.md):

| Requirement | Result |
|-------------|--------|
| Static output compatibility | **PASS** (public subset) |
| Free-plan suitability | **PASS** |
| Custom domain | **PASS** |
| HTTPS | **PASS** (automatic) |
| Git-backed deployment | **PASS** (+ Direct Upload alternative) |
| Preview deployments | **PASS** |
| Rollback / history | **PASS** (prior production deploys) |
| Provider lock-in | **ACCEPTABLE** (HTML portable; adapter keeps exit open) |
| Outside Website Engine Core | **PASS** |

Scout’s earlier primary **mode** (self-hosted Nginx/Caddy) remains the **fallback** and lock-in escape hatch. Cloudflare Pages is selected as the **first concrete production provider** because free-tier TLS/CDN/previews/rollback reduce founder ops without forcing Core coupling or paid infra.

---

## Conflict resolution

| Topic | Resolution |
|-------|------------|
| Scout “Self-hosted primary mode” vs CF Pages provider | **Reconciled** — mode-class = managed/git-backed static; **provider** = Cloudflare Pages; self-host = fallback adapter target |
| Atlas boundary vs CF Pages | **Aligned** — Pages is Hosting Platform only; never Core |
| Hermes vs deploy ownership | **Aligned** — Publishing never owns Pages |
| Ledger Founder Accept OPEN | **Accepted** — engineering DECIDED; production expose remains human gate |

**Cross-agent conflicts:** **0** (provider addendum supersedes mode ranking for *first production host* only)

---

## Binding constraints for M5

1. Website Engine Core must **not** depend on Cloudflare SDK, Wrangler, or Pages APIs.  
2. Deployment Adapter (outside Core) packages public subset and performs host transport (git artifact repo and/or Direct Upload).  
3. Public subset: `{slug}/index.html`, `sitemap.xml`, `rss.xml`; exclude `metadata.json` / `source.md`.  
4. Publishing Engine remains orchestration-only.  
5. Prefer Cloudflare Pages **Free**; no paid upgrade unless limits are hit.  
6. HTTPS + custom domain must align with embedded `canonical_url`.  
7. Do not adopt Pages Functions / CF-only features as Core requirements.  
8. Human approval required for production publish/deploy.  
9. M4/M5 planning still: **no** WordPress/Ghost/social/SEO Engine work unless separately authorized.

---

## Gates

| Gate | Result |
|------|--------|
| Architecture (Atlas) | **PASS** |
| Cloudflare Pages evaluation | **PASS** — recommended first provider |
| Publishing compatibility (Hermes) | **PASS** |
| Regression (Sentinel) | **PASS** · New Regressions **0** · Focused **40/40** · Full **320/332** (8 failed / 4 errors historical) |
| Governance (Ledger) | **PASS** |
| Provider Independent | **YES** |
| Code / Cloudflare resources | **0** |

---

## Verdict

**READY FOR M5 WEBSITE DEPLOYMENT IMPLEMENTATION**  
(First production host target: **CLOUDFLARE PAGES**, via Deployment Adapter only.)
