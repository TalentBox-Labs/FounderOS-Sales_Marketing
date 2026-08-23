# N0 — Production Domain Identity Audit

**Sprint:** N0  
**Date:** 2026-08-10  
**Production URL (frozen):** `https://founderos-staging.pages.dev`  
**DNS changes this sprint:** **NONE**

---

## Classification

| Option | Assessment |
|--------|------------|
| **A. Temporary acceptable** | **YES** — valid for v1.0 technical production of RC1 on Pages Production branch |
| **B. Eventually custom Founder OS / WorkCrew domain** | **YES — RECOMMENDED** |
| **C. Naming creates ambiguity** | **YES** |

---

## Ambiguity / risk (C)

| Area | Issue |
|------|-------|
| Branding | Hostname still says **staging** while environment is Production |
| SEO | Canonical tags point at `workcrew.ai`; serving host is `*.pages.dev` — host/canonical mismatch |
| Analytics | Property/host fragmentation until branded DNS validates |
| Operations | Project name `founderos-staging` used for production deploys |
| Custom domains | `workcrew.ai` / `blog.workcrew.ai` **attached but CNAME pending** (M7/M7.5) |

---

## Decision for Founder (analysis only)

**Production Domain Decision: CUSTOM DOMAIN RECOMMENDED**  
(temporary `founderos-staging.pages.dev` remains **acceptable** until CNAMEs land; **not** a freeze blocker for Website v1.0, but **should** be resolved before SEO Engine treats branded URLs as authoritative crawl/host truth.)

**NO DNS CHANGE IN N0.**
