# P1 — Engine Dependency Matrix

**Sprint:** P1 (Post SEO Baseline)  
**Agent:** ATLAS  
**Date:** 2026-08-11  
**Code changes:** 0

Evidence from `src/tools/publishing_engine.py`, Website/SEO packages, RevenueOS adjacent modules, Architecture v2.2.

---

## SOCIAL ENGINE

| Dependency | Status | Notes |
|------------|--------|-------|
| Editorial Engine | IMPLEMENTED | Approval gate for publish jobs |
| Publishing Engine | IMPLEMENTED | Jobs, audit, channel registry |
| Channel registry (linkedin/twitter/instagram) | PARTIAL | Registered; adapters `NOT_IMPLEMENTED` |
| LinkedIn adapter (Marketing OS) | NOT IMPLEMENTED | |
| X / Instagram adapters | NOT IMPLEMENTED | Out of first slice |
| OAuth / token vault (Marketing OS) | NOT IMPLEMENTED | Legacy env tokens in RevenueOS only |
| Scheduling | NOT IMPLEMENTED | Deferrable for S0 manual publish |
| Analytics | NOT IMPLEMENTED | Deferrable |
| Campaign Engine | NOT REQUIRED | Job flag `campaign_engine: False` |
| Automation/Celery for publish | NOT REQUIRED | Publishing is manual-human |

**Bounded start without Campaign/Email?** **YES** — LinkedIn-only behind Editorial + Publishing.

**Classification:** READY FOR BOUNDED SLICE (adapter + OAuth still missing)

---

## EMAIL ENGINE

| Dependency | Status | Notes |
|------------|--------|-------|
| Publishing `newsletter` channel | PARTIAL | Stub `NOT_IMPLEMENTED` |
| Subscriber DB SoT | NOT IMPLEMENTED | |
| Consent / unsubscribe / suppression | NOT IMPLEMENTED | Docs only |
| Delivery provider abstraction | NOT IMPLEMENTED | |
| SMTP sketch (`EmailNotifier`) | PARTIAL | Adjacent RevenueOS; not Marketing SoT |
| CRM `Contact` as list | IMPLEMENTED (CRM) | **Unsafe** as marketing SoT (no consent) |
| Campaign Engine | NOT REQUIRED for list foundation | Required later for blasts |

**CRM safe for Email without leakage?** **NO**

**Classification:** NOT READY (foundation blockers)

---

## CAMPAIGN ENGINE

| Dependency | Status | Notes |
|------------|--------|-------|
| Editorial / Publishing | IMPLEMENTED | |
| Website as Publishing adapter | PARTIAL | `PLACEHOLDER`; Website Engine exists but not wired in adapter |
| Social channels | NOT IMPLEMENTED | |
| Email channel | NOT IMPLEMENTED | |
| Attribution / campaign ROI | NOT IMPLEMENTED | CRM `Contact.source` ≠ campaign |
| Human launch gate | DOCUMENTED ONLY | |

**Would Campaign orchestrate enough real channels today?** **NO** → **PREMATURE**

---

## SEO PHASE 2

| Remaining area | Status | Blocker |
|----------------|--------|---------|
| Readiness + Technical SEO | IMPLEMENTED (frozen) | — |
| Search Console KPIs | NOT IMPLEMENTED | DOMAIN BLOCKED + property |
| Indexing activation / sitemap submit | NOT IMPLEMENTED | DOMAIN BLOCKED + ratification |
| Paid rank datasets | NOT IMPLEMENTED | Policy + paid |
| Website robots *emission* | NOT IMPLEMENTED | Website debt (not SEO Phase 2) |
| Soft local recommendations | DOCUMENTED ONLY | Low marginal value |

**Classification:** DOMAIN BLOCKED for high-value work; wait on FDR-N05

---

## Domain absence impact

| Candidate | Materially blocked by pending domain? |
|-----------|----------------------------------------|
| Social | **NO** (deep links optional; channel is external) |
| Email | PARTIAL (sender auth/domain reputation later) |
| Campaign | NO (premature for other reasons) |
| SEO Phase 2 | **YES** |
