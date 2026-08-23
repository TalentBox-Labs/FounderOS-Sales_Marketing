# Post M-Series — Next Marketing OS Engine Decision

**Status:** ANALYSIS ONLY — no implementation  
**Date:** 2026-08-10  
**Architecture:** v2.2 / Marketing OS v2.2  
**Prerequisite:** Founder OS Website v1.0 production baseline frozen  

---

## Candidates evaluated

| Engine | Business leverage | Dependencies | Current coverage | External API | Automation | Human gate | Cost / free-tier | Risk |
|--------|-------------------|--------------|------------------|--------------|------------|------------|------------------|------|
| **Social Engine** | High reach | Publishing channels; Brand | NOT_IMPLEMENTED adapters | LinkedIn/X/etc. | High | Mandatory before post | API costs / OAuth | High (external + brand) |
| **Email Engine** | High nurture | Subscribers; Brand; deliverability | Not shipped as engine | ESP (Sendgrid/etc.) | High | Campaign approve | Paid ESP likely | High |
| **Campaign Engine** | Coordinates multi-channel | Social/Email/Website ready | Partial orchestration concepts only | Depends on channels | Medium | Launch approve | Indirect | High until channels exist |
| **SEO Engine** | Improves live site discoverability | Website metadata/feeds **already live** | Explicit non-ownership today; metadata emit only | Optional Search Console later | Medium | SEO policy / promote | Can start **local/free** | **Low–Medium** |
| **GEO Engine** | LLM citation fitness | SEO/Website content | Named future | Research/LLM tools | Medium | Review | Model cost | Medium (immature) |
| **AEO Engine** | FAQ/snippet answers | Website content model | Named future | Optional | Medium | Review | Low initially | Medium |
| **Brand Engine** | Compliance gate across engines | Policies; Editorial | Scattered / future package | None required | Medium | Brand policy changes | Free/local | Medium (scope definition) |

---

## Recommendation

**Recommended next engine: SEO Engine**

### Why

1. Website v1.0 is **live** with canonical URLs, OG, JSON-LD, sitemap, RSS — SEO has immediate surface to score/improve without new hosting.  
2. Architecture already separates SEO scoring from Website deploy (Website emits; SEO scores).  
3. First slice can be **local/free** (read `output/website/` + bundles; checklists; scoring reports) without OAuth or paid APIs.  
4. Lower blast radius than Social/Email (no external posting).  
5. Unlocks later GEO/AEO as specialized layers on the same content readiness substrate.

### First implementation unit (future sprint — not authorized here)

- SEO readiness/scoring over approved bundles + Static artifacts  
- Human-readable report; no auto-mutate of production site  
- No Search Console write required for v0  

### Explicit deferrals

- Social / Email until Brand + channel auth strategy ready  
- Campaign until at least one non-website channel is real  
- GEO / AEO after SEO baseline exists  

---

## Decision

| Field | Value |
|-------|-------|
| **Recommended Next Marketing Engine** | **SEO Engine** |
| Implementation in this doc | **NONE** |
