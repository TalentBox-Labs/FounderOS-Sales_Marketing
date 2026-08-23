# Website Engine Implementation Checklist (Prepare Only)

**Status:** CHECKLIST ONLY — **DO NOT IMPLEMENT in M1.5**  
**Sprint:** M1.5  
**Date:** 2026-08-09  
**Architecture:** v2.1 ([Architecture_ADR_002.md](../architecture/Architecture_ADR_002.md))  
**Prerequisite baseline:** Publishing Engine v1.0 FROZEN

This document prepares M2. **No Website Engine code is authorized by M1.5.**

---

## 1. Ownership (Architecture v2.1)

Website Engine owns the **canonical Founder website**.

Publishing Engine owns **orchestration only** (jobs, queue, channel routing, audit, manual publish).

Website Engine must consume publish jobs for channel=`website`; it must not re-own the Publishing state machine.

---

## 2. Responsibilities checklist (implement in M2+)

| # | Responsibility | Status |
|---|----------------|--------|
| 1 | Canonical website ownership | PREPARE |
| 2 | Markdown rendering | PREPARE |
| 3 | HTML generation / rendering | PREPARE |
| 4 | Slug generation | PREPARE |
| 5 | Metadata | PREPARE |
| 6 | OpenGraph | PREPARE |
| 7 | Schema.org | PREPARE |
| 8 | RSS | PREPARE |
| 9 | Sitemap | PREPARE |
| 10 | Search indexing hooks | PREPARE |
| 11 | Static assets | PREPARE |
| 12 | Website API integration | PREPARE |
| 13 | Website cache invalidation | PREPARE |
| 14 | Website deployment hooks | PREPARE |
| 15 | Provider abstraction | PREPARE |
| 16 | WordPress adapter (future) | FUTURE |
| 17 | Ghost adapter (future) | FUTURE |
| 18 | Static site adapter (future) | FUTURE |

---

## 3. Explicit non-ownership (do not implement here)

| Concern | Owner |
|---------|-------|
| Publish jobs / queue / state machine | Publishing Engine |
| Social publishing APIs | Social Engine |
| Newsletter delivery | Email Engine |
| Campaign scheduling / sequences | Campaign Engine |
| Editorial approval | Editorial Engine |
| Celery / n8n / queues transport | Automation Platform |
| Auth / secrets | Shared Platform |

---

## 4. Integration contract with Publishing Engine (planned)

When M2 starts (not now):

1. Publishing Engine remains source of `website` channel jobs.
2. Website Engine replaces / extends the website adapter **behind** the frozen channel interface (`ok`, `status`, `channel`, `owner_engine`, `message`).
3. `website_engine_invoked` may become `true`; `rendering_performed` may become `true` **inside Website Engine**, not inside Publishing business rules sprawl.
4. Prefer calling Website Engine from the website adapter boundary without expanding Publishing API surface unless a new baseline is opened.

---

## 5. Suggested M2 acceptance gates (future)

- [ ] Consumes `published`/`publishing` website jobs without inventing a parallel queue
- [ ] Renders Markdown → HTML for approved bundles only
- [ ] Emits slug + canonical URL + metadata + OG + Schema.org
- [ ] Produces RSS + sitemap hooks
- [ ] No LinkedIn/X/Instagram/email APIs
- [ ] No campaign scheduling
- [ ] Focused tests + no Publishing baseline regressions
- [ ] Architecture v2.1 compliance attested

---

## 6. M1.5 attestation

| Item | Value |
|------|-------|
| Website Engine code in repo | **NONE** |
| Checklist created | **YES** |
| Implementation authorized | **NO** |
