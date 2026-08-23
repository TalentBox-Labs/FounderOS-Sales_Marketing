# CP2 — Commercial Value Chain Audit (HERMES)

**Sprint:** CP2 — Portfolio Value Chain Mapping  
**Date:** 2026-08-13  
**Mode:** Audit only — no runtime changes  
**Repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**Evidence base:** CP1 governance pack, Sales A1/A2/A3/A4 baselines, Marketing M-series/S0 freezes, cross-OS contracts

---

## 1. Value chain map

```
Content → Publishing → Audience → Demand → Qualification → Sales Contact
    → Deal → Closed-Won → Commercial Outcome → Revenue
```

### Transition classification

| # | Transition | Class | Evidence summary |
|---|------------|-------|------------------|
| 1 | **Content → Publishing** | **OPERABLE** | Editorial Approval Engine (E7) LIVE with human gates FROZEN; Publishing Engine (M1) FROZEN; approve → promote_staged → manual publish job path works (`docs/editorial/E7_IMPLEMENTATION_REPORT.md`, `docs/governance/CP1_FOUNDER_OS_PORTFOLIO_STATE.md`). |
| 2 | **Publishing → Audience** | **PARTIAL** | Website Engine Core v1.0 + Static Provider v1.0 + M4 deploy decision FROZEN — static web audience reachable via `output/website/` adapter path. Social channel adapter returns `NOT_IMPLEMENTED`; LinkedIn runtime MISSING; FD-01 identity OPEN; live LinkedIn blocked by ES-01..03 (`docs/marketing/social/S0_LINKEDIN_READINESS_DECISION.md`, `src/tools/publishing_engine.py`). |
| 3 | **Audience → Demand** | **MISSING** | No web-form submission handler; `ContactSource.WEB_FORM` enum exists with **no Marketing writer**; `lead_nurturing.SubscriberProfile` in-memory and unwired; social not live; measurement PARTIAL; analytics funnel narrative-only (`docs/sales/SALES_MARKETING_CONTRACT.md` §5, `docs/sales/SALES_A0_WORKFLOW_MAP.md`). |
| 4 | **Demand → Qualification** | **CONTRACT_ONLY** | Marketing qualification (MQL semantics) defined in frozen Sales↔Marketing boundary v1.0; `marketing_qualification` payload field specified; **no runtime qualification engine or demand object store** (`docs/sales/SALES_MARKETING_BOUNDARY_CONTRACT_v1.0.md`). |
| 5 | **Qualification → Sales Contact** | **MISSING** | `QualifiedDemand` contract FROZEN (A1/A1.5) but **NOT_IMPLEMENTED** — no emitter, no intake route (`/api/v1/sales/intake/demand` absent), no event bus wiring; MC04 capability register: "enum only" (`docs/sales/SALES_A2_CAPABILITY_REGISTER.md` MC04). Manual runner CRM contact create compensates on Sales side only. |
| 6 | **Sales Contact → Deal** | **PARTIAL** | Contact CRUD + Deal create LIVE on runner (`/api/v1/crm`); prospecting `/sales` LIVE. CRM React SPA UNMOUNTED (`frontend/dist` absent → `/app` 503). No auto-deal-from-qualify without approvals path (`docs/sales/SALES_A2_CAPABILITY_REGISTER.md` C03/C05). |
| 7 | **Deal → Closed-Won** | **OPERABLE** | Runner deal stage update FROZEN (A3.5/ADR-007); human-gated `PATCH .../deals/{id}/stage`; JWT + runner paths share `advance_deal_stage`. Explicit `commercial_outcome_emitted: false` at close (`docs/sales/SALES_A3_5_BASELINE_MANIFEST.md`, `revenue_os/services/deal_automation_service.py`). |
| 8 | **Closed-Won → Commercial Outcome** | **CONTRACT_ONLY** | `CommercialOutcome` contract DEFINED in `SALES_REVENUE_CONTRACT.md`; MC06 MISSING; stage mutation does **not** emit outcome event; no `Contact.status → CUSTOMER`; no CS/Client handoff (`docs/sales/a3/A3_REVENUE_BOUNDARY_AUDIT.md`). |
| 9 | **Commercial Outcome → Revenue** | **MISSING** | No Revenue intake on outcome; recognized revenue / billing / invoices explicitly future; Deal field updates only on `closed_won`; forecast APIs API_ONLY without outcome-driven CS workflow (`docs/sales/SALES_REVENUE_CONTRACT.md` §3–4, `docs/governance/CP1_FOUNDER_OS_PORTFOLIO_STATE.md`). |

### Terminal state: Revenue

| Aspect | Class | Notes |
|--------|-------|-------|
| CRM entity SoT (`Contact`, `Company`, `Deal`, `Pipeline`, `Activity`) | **OPERABLE** | Revenue OS models + runner CRM APIs LIVE |
| Forecast / analytics | **PARTIAL** | APIs exist; no outcome-driven lifecycle |
| Recognized revenue / billing | **MISSING** | Explicitly deferred to future finance integration |

---

## 2. First material break

**Transition:** **Audience → Demand** (#3)

**Why this is first:** Upstream transitions through Content and Publishing are OPERABLE with human gates. Website static path can reach an audience (PARTIAL — social absent but web operable). The chain first fails materially when audience engagement must become **captured, attributable demand** — there is no form handler, no Marketing demand emitter, no wired nurture→CRM path, and no live social inbound channel.

**Compensating workaround:** Manual Sales contact create via runner CRM / Jinja prospecting (`docs/sales/SALES_A2_WORKFLOW_GAP_MAP.md`). This bypasses Marketing entirely and does not heal the chain.

**CP1 alignment note:** CP1 LEDGER identified the **primary cross-OS break** at **Qualification → Sales Contact** (`QualifiedDemand NOT_IMPLEMENTED`) — the highest-leverage handoff once demand exists. CP2 distinguishes:

| Break type | Transition | Impact |
|------------|------------|--------|
| **First material break (chain origin)** | Audience → Demand | Marketing cannot produce demand objects from audience |
| **Primary cross-OS break (ingress)** | Qualification → Sales Contact | Even if demand existed, no automated Marketing→Sales handoff |

Both must be healed for end-to-end commercial automation; Audience→Demand is upstream and blocks all downstream Marketing qualification work.

---

## 3. Later bottlenecks (downstream, ranked)

| Rank | Transition | Class | Blocker | Dependency |
|------|------------|-------|---------|------------|
| 1 | Qualification → Sales Contact | MISSING | MC04 `QualifiedDemand` BUILD_NEW; needs Marketing emitter + Sales intake | Heals CP1 primary ingress break |
| 2 | Closed-Won → Commercial Outcome | CONTRACT_ONLY | MC06 deferred until stage ops proven — **now unblocked** by A3.5 | Sales emit + Revenue consume |
| 3 | Commercial Outcome → Revenue | MISSING | No intake, no CUSTOMER promotion, no CS/Client auto-create | MC06 implementation |
| 4 | Publishing → Audience (social leg) | PARTIAL / BLOCKED | FD-01 Founder decision; ES-01..03 external LinkedIn setup; IB-01..03 engineering | Extends audience before demand capture |
| 5 | Sales Contact → Deal (UX) | PARTIAL | CRM SPA unmounted; Companies JWT-only | Frozen RETAIN_AND_REFACTOR_LATER |
| 6 | Engage → Send | PARTIAL | Outreach send requires n8n activation (C10) | External CONFIG REQUIRED |

**Recently healed (not bottlenecks):**

- Deal → Closed-Won: A3.5 FROZEN (was rank-1 Sales gap per A2 gap map)
- Sales qualification gate: A4.5 LeadScorer / Contact.status human gate FROZEN (CP1 Candidate B delivered)

---

## 4. QualifiedDemand status

| Dimension | Status |
|-----------|--------|
| Contract | **FROZEN** — `SALES_MARKETING_BOUNDARY_CONTRACT_v1.0.md` (A1.5) |
| Payload schema | Defined: `demand_id`, `occurred_at`, `source`, `person`, optional `channel`, `company_hint`, `marketing_qualification`, `consent`, `content_attribution` |
| Transport | Specified (not built): async `marketing.qualified_demand.v1` or POST `/api/v1/sales/intake/demand` |
| Marketing emitter | **MISSING** — no form handler, no campaign writer, `WEB_FORM` unused |
| Sales intake | **MISSING** — no accept/reject API, no idempotency store |
| Code references | **Zero runtime types** — grep finds docs/governance only; no `QualifiedDemand` class in `.py`/`.ts` |
| Capability ID | MC04 — A2 score **3.38** (#2 ranked); CP1 Candidate C weighted **3.70** (highest raw) |
| CP1 disposition | Strategically hottest; deferred for executable Sales-only slice (LeadScorer A4/A4.5) |
| A4 boundary audit | **PASS** — A4 must not invent emitter/intake |
| Rejection audit | Specified: `SalesDemandRejected` event on Sales reject |

**Verdict:** **CONTRACT READY / IMPLEMENTATION NOT READY** (unchanged from CP1 LEDGER).

---

## 5. Sales saturation hints

Sales OS internal workflow is approaching **operational saturation** relative to A2 gap inventory; remaining leverage is predominantly **cross-OS boundary** work.

### Saturated / FROZEN (low incremental Founder value per effort)

| Capability | State | Sprint evidence |
|------------|-------|-----------------|
| Prospecting `/sales` | LIVE | C01–C03 |
| Runner CRM contacts/deals/activities | LIVE | C03, C05, C07 |
| Deal stage progression | FROZEN | A3.5 — closed A2 rank-1 gap |
| LeadScorer / Contact.status authority | FROZEN | A4.5 — closed CP1 Candidate B |
| Sales architecture + boundaries | FROZEN | A1.5 |
| Agent authority matrix | FROZEN | HUMAN_ONLY stage/status mutations enforced |

### Not saturated (remaining Sales-adjacent gaps)

| Gap | Class | Saturation signal |
|-----|-------|-------------------|
| QualifiedDemand intake | MISSING | Cross-OS — Sales cannot unblock alone |
| CommercialOutcome emission | MISSING | Next boundary after MC04 in A2 sequence |
| CRM SPA mount | PARTIAL | UX gap; API-sufficient for ops |
| Companies operator UI | API_ONLY | JWT path only; runner gap |
| Outreach send (n8n) | PARTIAL | Approvals LIVE; delivery external |
| Owner FK / RBAC | MISSING | Platform debt MC07 |

### Interpretation for CP2

1. **A2 "largest workflow break" (deal stage) is healed** — Sales pipeline ops no longer the primary internal blocker.
2. **CP1 scoring inversion:** MC04 (3.70) > LeadScorer (3.60) on raw value, but LeadScorer had **blocker NONE** — Sales executable surface now largely consumed.
3. **Manual intake masks chain break** — Sales appears OPERABLE because founders can hand-enter contacts; automated commercial chain remains broken upstream.
4. **Next Sales-only slices yield diminishing returns** — A2 sequence points to MC04 (cross-OS) or MC06 (post-stage handoff), not further runner CRM CRUD.
5. **Portfolio state:** Sales **PARTIAL→OPERABLE** per CP1 ATLAS; saturation of *internal* ops, not *commercial chain* completion.

---

## 6. Contract cross-reference index

| Contract | Path | Transitions governed |
|----------|------|---------------------|
| Sales ↔ Marketing | `docs/sales/SALES_MARKETING_BOUNDARY_CONTRACT_v1.0.md` | Demand → Qualification → Sales Contact |
| Sales ↔ Revenue | `docs/sales/SALES_REVENUE_CONTRACT.md` | Closed-Won → Commercial Outcome → Revenue |
| Runner Deal Stage | `docs/sales/SALES_RUNNER_DEAL_STAGE_CONTRACT_v1.0.md` | Deal → Closed-Won |
| LeadScorer / Contact.status | `docs/sales/a4_5/LEADSCORER_CONTACT_STATUS_CONTRACT_v1.0.md` | Sales Contact qualification (Sales-side) |
| Publishing Channel | `docs/marketing/Publishing_Channel_Interface.md` | Content → Publishing → Audience |
| Editorial Approval | `docs/architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md` | Content → Publishing |

### CP1 source documents

| Doc | Role |
|-----|------|
| `docs/governance/CP1_VALUE_CHAIN_ANALYSIS.md` | Prior break analysis (LEDGER) |
| `docs/governance/CP1_FOUNDER_OS_PORTFOLIO_STATE.md` | OS state snapshot (ATLAS) |
| `docs/governance/CP1_FOUNDER_OS_PRIORITY_DECISION.md` | Candidate scoring + B selected |
| `docs/governance/CP1_SALES_NEXT_CAPABILITY.md` | Post-A3.5 Sales slice ranking |
| `docs/governance/CP1_MARKETING_READINESS.md` | Social S1 CONDITIONAL status |
| `docs/governance/CP1_MEASUREMENT_VALUE.md` | Instrumentation by candidate |

---

## 7. CP2 executive summary

| Question | Answer |
|----------|--------|
| **First material break** | **Audience → Demand** — no demand capture from Marketing channels |
| **Primary cross-OS break** | **Qualification → Sales Contact** — `QualifiedDemand` MISSING |
| **QualifiedDemand status** | Contract FROZEN; emitter + intake NOT_IMPLEMENTED; zero runtime code |
| **Sales saturation** | Internal ops ~saturated (stage + scorer FROZEN); cross-OS handoffs (MC04, MC06) remain; manual intake masks upstream break |
| **Later bottlenecks** | MC04 QualifiedDemand → MC06 CommercialOutcome → Revenue intake → Social live audience → CRM SPA UX |

**Architecture protection:** Marketing M-series / SEO / Editorial / Publishing / Sales A1.5 / A3.5 / A4.5 / frozen cross-OS contracts — **UNCHANGED** by this audit.
