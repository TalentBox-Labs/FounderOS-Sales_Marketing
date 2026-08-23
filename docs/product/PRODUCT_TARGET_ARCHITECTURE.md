# Product Target Architecture

**Sprint:** MDG0  
**Date:** 2026-08-13  
**Mode:** DECISION / AUDIT ONLY

## Recommended product model

**HOSTED_SINGLE_USER** (hosted single-founder web application)

One private Founder OS instance per founder. Public marketing site remains a separate static deployment.

## Option scores (0–5)

| Option | Fit | Eng effort | Security | Scale | Commercial | Founder UX | Team UX | Deploy | Maint | Arch compat | **Total /50** |
|--------|----:|-----------:|---------:|------:|-----------:|-----------:|--------:|-------:|-----:|-----------:|-------------:|
| 1 Standalone/local | 4 | 5 | 4 | 1 | 1 | 4 | 1 | 5 | 4 | 5 | **34** |
| 2 Hosted single-founder | 5 | 4 | 3 | 2 | 3 | 5 | 2 | 4 | 4 | 5 | **37** |
| 3 Single-tenant SaaS | 2 | 2 | 2 | 3 | 4 | 3 | 3 | 2 | 2 | 2 | **25** |
| 4 Multi-tenant SaaS | 0 | 1 | 1 | 5 | 5 | 2 | 4 | 1 | 1 | 0 | **20** |
| 5 Hybrid local+cloud | 4 | 3 | 3 | 2 | 2 | 4 | 2 | 3 | 3 | 4 | **30** |

**Winner: Option 2 — Hosted single-founder web**  
Hybrid (5) describes today’s topology accurately but is not the product *intent* target.

## Target diagram

```
PUBLIC LAYER
  Founder OS public website (static)
  content / SEO / audience / [future demand capture]
  Host: Cloudflare Pages (SEPARATE)
            │
            │ form POST / webhook (future MDG)
            ▼
APPLICATION LAYER  (HOSTED_SINGLE_USER)
  Founder OS authenticated product UI (Jinja shell → incremental)
  Host: uvicorn / Docker / Render
            │
CONTROL LAYER
  Executive Cockpit (UI2.5 FROZEN)
  Operator Flow (OF1.5 FROZEN)
            │
DOMAIN LAYER
  Marketing OS │ Sales OS │ Revenue OS │ Content/Editorial/Publishing
            │
PLATFORM LAYER
  AI / Automation / Agent Governance / Shared Platform
            │
DATA / SoT LAYER
  Domain-owned canonical state (Contact, Deal, AgentActionLog, FS content)
  NO shared cross-OS SoT · NO Lovable DB
```

## Multi-tenant SaaS ready today?

**NO**

Major gaps: no tenant columns, no scoped queries, no per-tenant secrets, no RBAC productization, Jinja unauthenticated reads, dual-app auth confusion, empty/sparse migration discipline for SaaS onboarding.
