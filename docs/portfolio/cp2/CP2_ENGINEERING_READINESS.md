# CP2 — Engineering Readiness (NOVA)

**Sprint:** CP2 — Cross-OS Portfolio Engineering Assessment  
**Date:** 2026-08-13  
**Repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Mode:** Read-only engineering readiness — no runtime or contract changes  
**Evidence:** `docs/sales/SALES_A2_*`, `docs/sales/a4_5/*`, `docs/marketing/social/S0_*`, `docs/marketing/seo/*`, `docs/governance/CP1_*`, `docs/portfolio/cp2/CP2_FOUNDER_OS_CAPABILITY_MAP.md`, codebase spot-check  
**Post-state:** Sales A3.5 + A4.5 **FROZEN**; Marketing Website/SEO baselines **FROZEN**

---

## Executive summary

| Candidate | Recommended implementation type | Engineering readiness |
|-----------|--------------------------------|---------------------|
| **A** Sales next after A4.5 | **CONNECT_EXISTING** | **READY** — sequenced A5 slice |
| **B1** Social S1 live LinkedIn | **BUILD_NEW** + **EXTERNAL_SETUP** | **BLOCKED** (live) until FD-01 + ES-01..03 |
| **B2** Social S1 fake-first | **BUILD_NEW** | **READY** — no external hard blockers |
| **C** QualifiedDemand MC04/C27 | **BUILD_NEW** | **SOFT-BLOCKED** — cross-OS coordination |
| **D1** Domain-independent SEO | **COMPLETE_EXISTING** | **READY** — frozen and operable |
| **D2** Production SEO activation | **BLOCKED** | **BLOCKED** — FDR-N05 + GSC/DNS |
| **E** CommercialOutcome / closed-won | **BUILD_NEW** | **READY** (contract) — unblocked post-A3.5 |

**CP2 Sales-lane recommendation:** **A5 — Thin Companies on runner (C19 connect)** as the highest-*executable* Sales-only slice after A4.5. **Outreach send (C10)** scores higher in A2 (3.33 vs 3.05) but is **EXTERNAL_SETUP**, not a clean engineering sprint.

**CP2 cross-OS recommendation:** **C (QualifiedDemand)** has highest strategic leverage; **E (CommercialOutcome)** is the cleanest Revenue-adjacent BUILD with A3.5 preconditions met.

---

## Readiness table

| ID | Candidate | Existing code | Missing code | Contract readiness | DB impact | External deps | **Implementation type** |
|----|-----------|---------------|--------------|-------------------|-----------|---------------|-------------------------|
| **A** | **Sales next after A4.5** — A5 Companies on runner (C19); alt: Outreach send (C10) | `revenue_os/api/v1/companies.py` full JWT CRUD; `Company` model + FK on Contact/Deal; runner reads Company in forecasting/health; A3.5/A4.5 runner CRM **OPERABLE** | Runner `/api/v1/crm/companies` facade (list/get/create/update); API-key auth + tests mirroring A3/A4 pattern; optional thin Jinja hook (excluded per A2). **Alt C10:** approvals LIVE, `runner_api_routers/outreach.py`, n8n bridge code — send path inactive | No new cross-OS contract. C19 disposition **API_ONLY** in A2 register. A1.5 Sales/Revenue boundaries **FROZEN** | **NO migration** — reuse existing `companies` table | **None** for Companies. **Alt C10:** n8n instance + `N8N_WEBHOOK_BASE_URL`, SMTP/ESP (I04/I05) — classified **RETAIN_OPTIONAL**, **0 activated** | **CONNECT_EXISTING** (Companies — **recommended**). Alt: **EXTERNAL_SETUP** (Outreach) |
| **B1** | **Social S1 live LinkedIn** | Editorial + Publishing human gates **LIVE** (`editorial_approval.py`, `publishing_engine.py`); website channel adapter **LIVE**; LinkedIn channel stub returns `NOT_IMPLEMENTED` | `src/tools/social_engine/` (absent); Marketing OS LinkedIn adapter; OAuth/token bind routes (IB-03); wire `ADAPTERS[linkedin]`; `FakeLinkedInPublisher` for tests only | **DEFINED** — `S0_LINKEDIN_PUBLISHING_CONTRACT.md`, architecture boundary **FROZEN**-compatible; Editorial/Publishing **FROZEN** | **NO** — job/audit JSONL only (Publishing pattern) | **ES-01..03** (LinkedIn Developer app, Share on LinkedIn product + OAuth, token vault); **FD-01** (person vs org); **ES-04** if org identity | **BUILD_NEW** + **EXTERNAL_SETUP**; live path **BLOCKED** until Founder/external gates |
| **B2** | **Social S1 fake-first** | Same as B1 — gates + Publishing orchestration **LIVE**; S0 test strategy documented | Same engineering scope as B1 minus live API client: Social Engine package, fake injectable adapter, Publishing adapter registration, contract tests per `S0_LINKEDIN_TEST_STRATEGY.md` | Same as B1 — contracts **READY** for BUILD | **NO** | **None** for CI/unit tests. FD-01 deferrable if CONFIGURABLE default (member-only fake) | **BUILD_NEW** |
| **C** | **Marketing→Sales QualifiedDemand (MC04/C27)** | `ContactSource.WEB_FORM` enum + scoring weight only; manual Contact create on runner **LIVE**; EventBus infrastructure **LIVE**; zero Python `QualifiedDemand` references | Marketing **emitter** (form/web/social → event); Sales **intake** handler (accept/reject/idempotency/merge); `SalesDemandRejected` audit; optional runner route or webhook; **no** direct Marketing CRM writes | **FROZEN** — `SALES_MARKETING_BOUNDARY_CONTRACT_v1.0.md` (ADR-005); payload fields + rules defined | **Likely NO new tables** v1 — EventBus + audit JSONL or append-only intake log; Contact create via existing Revenue SoT | Form hosting / Turnstile **later** (soft); Marketing engine coordination **required** | **BUILD_NEW** — **SOFT-BLOCKED** on Marketing emitter + dual-stream sprint |
| **D1** | **Domain-independent SEO** | **FROZEN + OPERABLE:** `src/tools/seo_engine/` (readiness + technical, 72 rules), `src/tools/site_origin.py`, GET routes in `runner_api_routers/seo.py` + UI templates; tests 34+27+ site_origin | `src/tools/seo_engine/indexing.py` (planned, not built); Website Engine `robots.txt` / robots meta (**WEBSITE-SEO-ROBOTS-001** accepted limitation); marginal rule expansion only | **FROZEN** — SEO Readiness v1.0 (S1.5), Technical SEO v1.0 (S2.5), `S0_SITE_ORIGIN_CONTRACT.md` | **NO** for engines — existing `SEOKeyword`/`SEORankCheck` for manual rank log only | **None** — offline artifact analysis, placeholder origin `example.invalid` | **COMPLETE_EXISTING** — deliverable state; further work is incremental rule/robots debt |
| **D2** | **Production SEO activation** | Indexing safety gates in `site_origin.py` (`is_indexing_activation_allowed()`); engine correctness frozen | GSC / Search Console integration; sitemap submission; DNS/TLS cutover; artifact regeneration for ratified origin; Website robots capability; Search Console property setup | **BLOCKED** — FDR-N05 **OPEN**; `SEO_DOMAIN_DECISION_PENDING.md`; activation explicitly forbidden until Founder Accept | **NO** engine migration; **ops** artifact/canonical refresh on domain change | **FDR-N05** Founder Accept; DNS control (`workcrew.ai` CNAME pending); GSC credentials (free); Cloudflare cutover | **BLOCKED** (+ **EXTERNAL_SETUP** post-unblock) |
| **E** | **Revenue-adjacent — CommercialOutcome / closed-won handoff (MC06/C28)** | `advance_deal_stage` / runner `PATCH .../deals/{id}/stage` **FROZEN** (A3.5); sets `closed_at`, returns `commercial_outcome_emitted: false`; `DealStage.CLOSED_WON`; EventBus `DEAL_STAGE_CHANGED`; CSM health **LIVE** | `CommercialOutcome` event type + emitter on human close; Revenue intake (Contact→CUSTOMER optional, CS handoff stub); idempotency on `outcome_id`; tests for boundary (no auto-invoice, no ownership transfer) | **FROZEN** — `SALES_REVENUE_BOUNDARY_CONTRACT_v1.0.md`, `SALES_REVENUE_CONTRACT.md` (ADR-004); field schema defined | **NO migration** v1 — event + audit; optional Contact.status side-effect via existing model | **None** for stub; finance/CS systems **future** | **BUILD_NEW** |

---

## Candidate detail

### A — Sales next capability after A4.5

**A2 post-freeze state**

| Prior A2 rank | Candidate | Status after A4.5 |
|---------------|-----------|-------------------|
| #1 Deal stage (4.85) | Runner deal stage | **DONE / FROZEN** (A3.5) |
| D LeadScorer gate (3.28) | Contact.status human gate | **DONE / FROZEN** (A4.5) |
| #2 QualifiedDemand (3.38) | MC04 | **MISSING** — see **C** |
| #3 Outreach send (3.33) | C10 | **PARTIAL** — external |
| MC06 CommercialOutcome (3.23) | Close handoff | **MISSING** — see **E** |
| F Companies runner (3.05) | C19 connect | **API_ONLY** — **A5 sequenced** |

**Remaining Sales workflow gaps** (from `SALES_A2_WORKFLOW_GAP_MAP.md`, updated):

1. ~~Pipeline stage ops~~ — closed A3.5  
2. ~~LeadScorer auto-promotion~~ — closed A4.5  
3. Marketing automated intake — **MISSING** (manual workaround operable)  
4. CommercialOutcome — **MISSING** (A3.5 sets Deal fields only)  
5. Outreach send — **PARTIAL** (approvals LIVE; n8n inactive)  
6. Companies on runner — **MISSING** facade (JWT API exists)  
7. CRM SPA — **UNMOUNTED** (A6, not immediate)

**A2 sequence (`SALES_A2_IMPLEMENTATION_SEQUENCE.md`):** **A5 = Thin Companies on runner (C19 connect) OR CommercialOutcome stub.** CommercialOutcome is evaluated separately as **E**.

**Engineering verdict:** **CONNECT_EXISTING** — expose existing JWT Companies service on runner with API-key auth; complexity **S**; no frozen-contract edits; no external deps. Outreach is higher-scored but **EXTERNAL_SETUP** (I04 n8n), matching ADR-006 rationale for deferral.

---

### B1 — Social S1 live LinkedIn

**Existing:** Publishing state machine, editorial approval, human `manual_publish`, LinkedIn channel registered with owner `Social Engine`.

**Missing:** Entire Social Engine runtime; adapter replacing `_adapter_not_implemented("linkedin")`; OAuth or operator token bind.

**Blockers:** IB-01..03 (engineering — S1 scope) + ES-01..03 (external — live) + FD-01 (Founder). `revenue_os/integrations/social_publisher.py` **STALE** — do not adopt as Marketing SoT (I08 **RETIRE**).

**Engineering verdict:** **BUILD_NEW** for adapter/engine; live publish **BLOCKED** until **EXTERNAL_SETUP** complete. S0 verdict: **CONDITIONAL GO**.

---

### B2 — Social S1 fake-first

Same engineering surface as B1 with injectable fake provider (`S0_LINKEDIN_TEST_STRATEGY.md`). CP1 explicitly authorizes fake-first without FD-01 ratification or live credentials.

**Engineering verdict:** **BUILD_NEW** — **READY** to start; tests use fakes only; no live API in CI.

---

### C — Marketing→Sales QualifiedDemand (MC04/C27)

**Existing:** Frozen contract only. `ContactSource.WEB_FORM` is scoring metadata, not an intake pipeline.

**Missing:** Both halves of the handoff — Marketing emitter and Sales intake. No `QualifiedDemand` / `SalesDemandRejected` in `EventType` enum.

**Engineering verdict:** **BUILD_NEW** — contract **READY**; implementation **SOFT-BLOCKED** until Marketing stream commits emitter scope. Intake-only stub is low value per A2 premortem.

---

### D1 — Domain-independent SEO

**Existing:** Full read-only SEO stack frozen at S1.5 + S2.5; `site_origin.py` placeholder pattern; operator UI routes; 92/92 combined gate at S2.5 freeze.

**Missing:** Non-blocking — robots.txt generation (Website Engine debt); `indexing.py` module (future activation helper).

**Engineering verdict:** **COMPLETE_EXISTING** — operable today without production domain. Not a greenfield BUILD candidate unless expanding rule families under new ADR.

---

### D2 — Production SEO activation

**Existing:** Safety gates prevent accidental indexing (`example.invalid`, infrastructure hosts, unrated origin all blocked).

**Missing:** Founder domain decision (FDR-N05), DNS/TLS, GSC property, submission workflows, canonical artifact regeneration, robots emission.

**Engineering verdict:** **BLOCKED** — code changes forbidden until FDR-N05 Accept. Post-unblock: **BUILD_NEW** (GSC/indexing) + **EXTERNAL_SETUP** (DNS, Search Console).

---

### E — Revenue-adjacent (CommercialOutcome, closed-won handoff)

**Existing:** Human-gated `closed_won` on runner; Deal field mutation; explicit `commercial_outcome_emitted: false` in API + tests; Revenue Contact/Deal SoT.

**Missing:** Event object, emitter hook post-close, Revenue intake actions per contract (`Contact.status → CUSTOMER` optional, CS handoff, no auto-invoice).

**Preconditions met:** A2 deferred MC06 until stage ops solid — **A3.5 satisfies**. A4.5 does not expand close boundary.

**Engineering verdict:** **BUILD_NEW** — contract **FROZEN** and **READY**; must not alter A3.5 frozen `closed_won` semantics without ADR.

---

## Recommended implementation types (CP2)

| Priority tier | Candidate | Type | Rationale |
|---------------|-----------|------|-----------|
| **1 — Sales lane (executable now)** | **A** Companies on runner | **CONNECT_EXISTING** | A2-sequenced A5; max reuse; zero external deps; closes C19/MC08 precursor |
| **2 — Marketing lane (fakes)** | **B2** Social S1 fake-first | **BUILD_NEW** | Largest missing Marketing runtime; no FD-01/ES hard block for engineering start |
| **3 — Value chain (cross-OS)** | **C** QualifiedDemand | **BUILD_NEW** | Highest strategic leverage; requires Marketing coordination |
| **3 — Value chain (cross-OS)** | **E** CommercialOutcome | **BUILD_NEW** | Post-close break; A3.5 preconditions met; no external deps for stub |
| **4 — Marketing lane (live)** | **B1** Social S1 live LinkedIn | **BUILD_NEW** + **EXTERNAL_SETUP** | Same code as B2; live **BLOCKED** on FD-01 + ES |
| **— — Complete** | **D1** Domain-independent SEO | **COMPLETE_EXISTING** | Frozen and operable; not a CP2 build candidate |
| **— — Blocked** | **D2** Production SEO activation | **BLOCKED** | FDR-N05 + DNS/GSC |

**Do not auto-select** Social S1 or MC04 solely because Sales A-number increments (per `CP1_EXECUTION_ROADMAP.md`). Re-open CP2 Founder priority if Marketing-first after FD-01.

---

## Implementation type legend

| Type | Meaning |
|------|---------|
| **CONNECT_EXISTING** | Wire runner/API facade to existing Revenue service — minimal new logic |
| **COMPLETE_EXISTING** | Finish partial implementation or close documented debt |
| **BUILD_NEW** | New module, event, or adapter with no runtime counterpart |
| **EXTERNAL_SETUP** | Founder/ops configuration outside repo (credentials, DNS, SaaS) |
| **BLOCKED** | Hard gate — Founder decision, frozen contract, or domain forbids start |

---

**Document:** `docs/portfolio/cp2/CP2_ENGINEERING_READINESS.md`  
**Agent:** NOVA  
**Status:** COMPLETE
