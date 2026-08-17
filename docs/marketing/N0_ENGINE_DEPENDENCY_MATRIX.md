# N0 — Engine Dependency Matrix (Atlas)

**Sprint:** N0  
**Date:** 2026-08-10  
**Architecture:** v2.2 (UNCHANGED)  
**Code changes:** 0  

Legend: **HARD** = must exist for useful v1 · **SOFT** = improves quality later

---

## SEO Engine

| Dependency | Type | Current evidence |
|------------|------|------------------|
| Website Engine + live site | HARD | **SHIPPED** — Website v1.0 production baseline |
| Metadata / canonical / OG / Schema | HARD | Emitted by `website_engine/metadata.py` |
| Sitemap / RSS | HARD | Static Provider feeds live |
| Content Studio / bundles | HARD | `input/{week}/`, Content Studio UI |
| Editorial approval | SOFT | Exists; SEO can score pre/post approve |
| Publishing Engine | SOFT | Orchestration only; SEO ≠ deploy |
| Analytics / Search Console | SOFT | Manual keyword ranks in `runner_api_routers/seo.py`; **no GSC** |
| Structured data | HARD (emit) / SOFT (score) | JSON-LD already emitted |

---

## Social Engine

| Dependency | Type | Current evidence |
|------------|------|------------------|
| Publishing Engine channel jobs | HARD | Channels exist; adapters `NOT_IMPLEMENTED` |
| Editorial approval | HARD | Required before publish |
| Channel adapters LinkedIn/X/IG | HARD | Stubs only in Publishing; legacy `social_publisher.py` **not** Marketing OS Social Engine |
| OAuth / platform credentials | HARD | Env-based in legacy integration; not Shared Platform Social Engine |
| Brand / voice gate | SOFT | Implicit validators; no Brand Engine |
| Automation scheduling | SOFT | Not Marketing OS Social runtime |

---

## Email Engine

| Dependency | Type | Current evidence |
|------------|------|------------------|
| Editorial + Publishing `newsletter` channel | HARD | Channel stub `NOT_IMPLEMENTED` |
| Subscriber / contact SoT | HARD | RevenueOS nurture subscriber **in-memory** ≠ Marketing Email Engine |
| Consent / unsubscribe | HARD | Documented in playbooks; **no Marketing OS consent model** |
| Delivery provider (SMTP/ESP) | HARD | `EmailNotifier` SMTP skeleton; no production ESP wire |
| Templates | SOFT | Template dataclass exists; not Marketing OS product |
| Campaign Engine | SOFT | Can send without Campaign; Campaign needs Email later |
| Analytics (opens/clicks) | SOFT | Not Marketing OS Email analytics |

---

## Campaign Engine

| Dependency | Type | Current evidence |
|------------|------|------------------|
| Content Studio / Editorial | HARD | Available |
| Publishing orchestration | HARD | Available |
| ≥1 working distribution channel beyond static site | HARD | Website live; Social/Email **not** Marketing OS engines |
| Social / Email engines | HARD for multi-channel | Missing |
| Analytics / attribution | HARD for ROI claims | Revenue analytics ≠ campaign attribution |
| Human launch gate | HARD | Architecture requires; not implemented as Campaign package |

---

## Hard vs soft summary

| Engine | Hard deps ready? | Soft deps ready? |
|--------|------------------|------------------|
| SEO | **YES** (site + content + metadata) | Partial (manual ranks only) |
| Social | **NO** (adapters/OAuth) | Partial legacy publisher |
| Email | **NO** (consent/list/ESP) | Partial SMTP/nurture sketches |
| Campaign | **NO** (distribution engines) | Orchestration patterns only |

---

## Campaign special audit

**Hypothesis confirmed:** Campaign without Social/Email becomes orchestration without useful execution channels (Website-only “campaigns” duplicate Publishing/Website).

**Verdict:** **WAIT FOR DISTRIBUTION ENGINES**
