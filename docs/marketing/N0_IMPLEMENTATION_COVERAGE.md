# N0 — Implementation Coverage (Hermes)

**Sprint:** N0  
**Date:** 2026-08-10  
**Rule:** Documentation alone ≠ runtime implementation  

---

## Classification

| Engine | Status | Repository evidence |
|--------|--------|---------------------|
| **SEO Engine** | **PARTIAL** | Crew `02_SEO_Plan.md`; `content_quality_checker` keyword metrics; Website metadata emit; `/api/v1/seo` keyword + **manual** rank log (`revenue_os/models/seo.py`). **No** formal `SEO Engine` package / scoring service under Marketing OS ownership. |
| **Social Engine** | **NOT IMPLEMENTED** (Marketing OS) | Publishing adapters return `NOT_IMPLEMENTED`. Legacy `revenue_os/integrations/social_publisher.py` + `revenue_os/api/v1/social.py` exist as **RevenueOS/integration** code — not frozen Marketing Social Engine. |
| **Email Engine** | **NOT IMPLEMENTED** (Marketing OS) / **PARTIAL** adjacent | Publishing `newsletter` stub. `EmailNotifier` SMTP + `lead_nurturing` subscriber sketches in RevenueOS. No Marketing Email Engine package, consent, or production delivery. |
| **Campaign Engine** | **NOT IMPLEMENTED** | Named in Architecture v2.2 / Marketing OS docs only. Job flag `campaign_engine: false`. No campaign module under Marketing OS. |

---

## Reusable components (without claiming engines)

| Asset | Useful for |
|-------|------------|
| `input/*/02_SEO_Plan.md` + generation crew SEO agent | SEO Engine inputs |
| Website metadata / sitemap / RSS / production site | SEO scoring surface |
| `/api/v1/seo` manual rank history | SEO measurement bootstrap |
| Publishing channel registry + audit | Social/Email orchestration hooks later |
| Editorial approval | All engines’ human gates |
| Deployment Adapter / Website v1.0 | SEO owned-asset compounding |
| Legacy social_publisher / EmailNotifier | Reference only — do not silently promote to Marketing OS engines |

---

## Hermes note

Architecture docs mark SEO/Email as PARTIAL — **runtime evidence agrees for SEO partial; Email is effectively NOT IMPLEMENTED as Marketing OS engine** despite adjacent RevenueOS helpers.
