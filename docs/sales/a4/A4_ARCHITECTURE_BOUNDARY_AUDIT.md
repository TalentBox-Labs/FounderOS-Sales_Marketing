# A4 — Architecture Boundary Audit (ATLAS)

**Sprint:** SALES A4  
**Date:** 2026-08-13  
**Role:** Contract Guard  
**Baseline:** Sales OS Architecture Baseline v1.0 FROZEN (ADR-005)  
**Prior slice:** SALES A3 / A3.5 FROZEN — runner deal stage update (ADR-006)  
**Scope:** LeadScorer / `Contact.status` human gate (A2 sequence item **A4**; capability **C12** debt)

**Authoritative contracts inspected:**

| Contract | Status |
|----------|--------|
| `docs/sales/SALES_A1_5_BASELINE_MANIFEST.md` | FROZEN |
| `docs/sales/SALES_OS_ARCHITECTURE_BASELINE_v1.0.md` | FROZEN |
| `docs/sales/SALES_DOMAIN_MODEL_CONTRACT_v1.0.md` | FROZEN |
| `docs/sales/SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md` | FROZEN |
| `docs/sales/SALES_REVENUE_BOUNDARY_CONTRACT_v1.0.md` | FROZEN |
| `docs/sales/SALES_MARKETING_BOUNDARY_CONTRACT_v1.0.md` | FROZEN |
| `docs/sales/SALES_INTEGRATION_DISPOSITION_v1.0.md` | FROZEN |
| `docs/sales/CRM_UI_DISPOSITION_v1.0.md` | FROZEN |
| `docs/sales/SALES_RUNNER_DEAL_STAGE_CONTRACT_v1.0.md` | FROZEN (A3.5 — do not regress) |
| A1 binding sources (by reference): `SALES_DOMAIN_MODEL.md`, `SALES_AGENT_AUTHORITY_MATRIX.md`, `SALES_REVENUE_CONTRACT.md`, `SALES_A1_MIGRATION_MAP.md` | FROZEN BY REFERENCE |

---

## Sprint intent (contract-aligned)

A4 closes the **known authority gap** documented in A1.5:

> `LeadScorer.update_contact_status` mutates `Contact.status` without human approval — classified **HUMAN_APPROVAL_REQUIRED**; remediation deferred to a future migration sprint.

A2 selected A4 as **COMPLETE_EXISTING**: gate around existing scorer behavior. A4 **implements against** frozen contracts; it does **not** amend them.

| Field | Contract value |
|-------|----------------|
| Sprint type | COMPLETE_EXISTING |
| DB migration | **NO** |
| External integration | **NO** |
| Cross-OS dependency | **NO** (Revenue Contact SoT only) |
| Target authority class | **HUMAN_APPROVAL_REQUIRED** for status promotion from scoring |

---

## Contact.status authority rules (from contracts)

### Domain model (frozen)

| Rule | Source |
|------|--------|
| `Contact.status` is a **Revenue OS field** (`ContactStatus` enum on Revenue SoT) | `SALES_DOMAIN_MODEL_CONTRACT_v1.0` §1, §3 |
| **Sales proposes** qualification / status transitions; **human or policy gate** required for **promotion** | `SALES_DOMAIN_MODEL_CONTRACT_v1.0` §3; `SALES_DOMAIN_MODEL.md` §2 |
| **Lead** is a **canonical alias** — same persistence as `Contact` + status/events; **no parallel Lead table** | `SALES_DOMAIN_MODEL_CONTRACT_v1.0` §1 |
| Dual scorers (`scoring_service` vs `lead_scoring_service`) = **DUPLICATE → REQUIRES_FUTURE_ADAPTER** (separate from gate sprint) | `SALES_DOMAIN_MODEL_CONTRACT_v1.0` §5; `SALES_A1_MIGRATION_MAP` #6 |

### Agent authority (frozen)

| Operation | Required class | A4 relevance |
|-----------|----------------|--------------|
| Lead scoring (compute score) | **AUTONOMOUS_ALLOWED** | Score calculation must remain allowed; **must not write status** without gate |
| Lead scoring → auto `Contact.status` change | **HUMAN_APPROVAL_REQUIRED** | **Primary A4 remediation target** |
| Qualification decision (SQL) | **HUMAN_ONLY** | Business decision — not replaced by scorer auto-promotion |
| CRM Contact modify (fields) | **HUMAN_APPROVAL_REQUIRED** | Status promotion is a Contact field mutation |
| Silently promote `Contact.status` or `Deal.stage` | **PROHIBITED** (agents) | A4 must eliminate silent scorer promotion |

Full matrix: `SALES_AGENT_AUTHORITY_MATRIX.md` (frozen by reference). Known gap row explicitly names `LeadScorer.update_contact_status`.

### Sales ↔ Revenue boundary (frozen)

| Mutation | Authority | A4 behavior |
|----------|-----------|-------------|
| `Contact.status` promotion | Human/policy; LeadScorer auto-write = **known gap → future migration** | A4 **is** that migration sprint for the scorer path |
| `Deal.stage` (ops) | Sales ops + **HUMAN_ONLY** (A3 delivered) | **Out of A4 scope** — preserve A3.5 contract |
| `Contact.status → CUSTOMER` on close | Future CommercialOutcome path | **NO** — not in A4 |
| Entity SoT | Revenue owns Contact/Deal/Company | A4 writes via existing Revenue models only |

### Sales ↔ Marketing boundary (frozen)

| Rule | A4 impact |
|------|-----------|
| Marketing must not write Revenue Contact/Deal tables from publish engines | **NONE** — A4 is Sales qualification governance |
| No autonomous Marketing→Sales CRM create | **NONE** |
| `QualifiedDemand` handoff | **NOT_IMPLEMENTED** — A4 must not invent emitter/intake |

### Architecture baseline (frozen)

| Rule | A4 impact |
|------|-----------|
| Qualification scoring **policy** = Sales OS; may **recommend**; **human gate for mutations** | Direct A4 mandate |
| C12 Hermes score/qualify = **LIVE** — must not be deleted | Preserve scoring; gate status side-effect |
| C13 Approvals queue = **LIVE** — reuse for HUMAN_APPROVAL_REQUIRED | Preferred integration surface |
| 12/12 LIVE capabilities preserved | Scoring remains; auto-promotion removed or gated |

---

## Lead / Contact ownership

```
┌─────────────────────────────────────────────────────────────┐
│ Revenue OS — entity SoT                                     │
│   Contact (UUID), ContactStatus enum, lead_score field      │
└──────────────────────────▲──────────────────────────────────┘
                           │ read/write via facades/adapters
┌──────────────────────────┴──────────────────────────────────┐
│ Sales OS — qualification policy & ops                       │
│   • LeadScorer policy (fit/engagement thresholds)           │
│   • Propose status promotion (score recommendation)         │
│   • Human/approval gate before Contact.status mutation      │
└─────────────────────────────────────────────────────────────┘

Lead (concept) ≡ Contact + ContactStatus + LEAD_* events — alias only, Revenue persistence.
```

| Concept | Owner | Sales role in A4 |
|---------|-------|------------------|
| **Contact** entity | Revenue OS | Operate via existing `revenue_os.models.contact.Contact` |
| **Lead** alias | Revenue (`Contact` + status) | Document-only; no new table |
| **Contact.status** field | Revenue field | Sales **proposes**; human/approval **executes** promotion |
| **lead_score** field | Revenue field | May update autonomously on score recompute |
| **Qualification policy** (thresholds) | Sales OS | May adjust scorer logic within service — not a contract change |

Sales does **not** acquire CRM entity ownership. Co-location under `revenue_os/` remains **ACCEPTED_LEGACY**.

---

## What A4 MAY change (implementation)

### Primary mutation surface (known gap)

| File / area | Allowed change |
|-------------|------------------|
| `revenue_os/services/lead_scoring_service.py` | Split score compute from status promotion; stop silent `update_contact_status` on autonomous paths; add gated promotion helper |
| `LeadScorer.update_contact_status` | Refactor to require explicit human/approval context, or move behind approval executor |
| `score_contact` / `score_contacts_batch` | Score-only default; status promotion only via approved path |
| `runner_api_routers/hermes.py` | `POST /api/v1/hermes/score-contacts` — add human gate (`requested_by` and/or approval filing) before status mutation |
| `revenue_os/services/approvals.py` | Add executor for e.g. `promote_contact_status` (reuse C13 queue pattern) |
| `src/tools/editorial_approval.py` | Reuse `is_human_approver` (FDR-002 pattern — same as A3 stage gate) |
| `revenue_os/automation/events.py` | Emit / enrich `CONTACT_STATUS_CHANGED` or `LEAD_QUALIFIED` audit with `requested_by` / approval id |
| `revenue_os/scheduler.py` | Scheduled scoring path — score-only or approval-queue, not silent promotion |
| `revenue_os/services/hermes_planner.py` | Planner-initiated scoring — no silent status write |
| `tests/test_a4_*` (new) | Focused tests: score without promotion; promotion blocked without approval; promotion succeeds after approval |
| `docs/sales/a4/*` | Sprint audit / attestation docs |

### Secondary call paths (review; gate if they invoke status promotion)

| File | Notes |
|------|-------|
| `revenue_os/tasks/leads.py` | Celery lead task — uses `lead_scoring_service.score_contact` |
| `revenue_os/api/v1/contacts.py` | JWT path — uses `scoring_service.score_contact` (**does not** auto-mutate status today) |

### Behavioral outcomes A4 may deliver

| Outcome | Allowed |
|---------|---------|
| Autonomous lead **score** recompute (`lead_score` field) | **YES** |
| Scorer **recommends** target status (response payload / audit) | **YES** |
| Status **promotion** without human/approval | **NO — must eliminate** |
| Status promotion via **HUMAN_APPROVAL_REQUIRED** (C13 queue or equivalent) | **YES — target state** |
| Direct operator promotion with `requested_by` + `is_human_approver` on explicit status endpoint | **YES** (if classified as human-initiated modify — align with matrix) |
| EventBus audit trail for gated promotions | **YES** |

### Explicit non-goals A4 may defer (still frozen out of scope)

| Item | Disposition |
|------|-------------|
| Dual scorer consolidation (`scoring_service` ↔ `lead_scoring_service`) | REQUIRES_FUTURE_ADAPTER — not primary A4 deliverable |
| JWT stack rewrite / deprecation | REQUIRES_FUTURE_MIGRATION |
| New `sales_os` package extraction | DEFERRED |
| `QualifiedDemand` / `CommercialOutcome` | NOT_IMPLEMENTED |
| CRM SPA mount/refactor | RETAIN_AND_REFACTOR_LATER |
| DB schema migration / new tables | **NO** |
| External integrations (n8n, Proxycurl, etc.) | **NO activation** |

---

## What A4 MUST NOT change (frozen contracts)

| Area | Forbidden |
|------|-----------|
| A1.5 frozen contract markdown (**content meaning**) | **NO edits** — including manifest, domain model, authority, Marketing/Revenue boundaries, integration disposition, CRM UI disposition |
| ADR-005 / ADR-004 freeze statements | **NO reinterpretation** |
| A3.5 runner deal stage contract & behavior | **NO regression** — `PATCH .../deals/{id}/stage` HUMAN_ONLY path |
| Marketing OS frozen engines (Publishing, Website, SEO, Social) | **NO** |
| Revenue entity **ownership** (Contact/Deal/Company SoT) | **NO transfer to Sales** |
| Lead / Opportunity / Account **alias semantics** | **NO new parallel tables** |
| Agent-autonomous `Contact.status` promotion | **NO** — prohibited before and after A4 |
| Agent-autonomous `Deal.stage` mutation | **NO** |
| `CommercialOutcome` emission or `Contact.status → CUSTOMER` on close | **NO** |
| CRM SPA (`frontend/`) mount, dist build, nav link | **NO** |
| `migrations/` / Alembic new revisions | **NO** |
| Integration activation or credential commits | **NO** |
| Delete or disable C01–C17 LIVE capabilities | **NO** — C12 scoring must remain functional (gated, not removed) |
| Platform Agent Registry amendment | **NO** (temporary Cursor sprint ≠ runtime agent registration) |
| Rewrite A1.5 known-test-exception identities | **NO** |

Amendments to any frozen contract require **explicit ADR + approved unfreeze sprint** per `SALES_A1_5_BASELINE_MANIFEST.md` change control.

---

## Current violation (pre-A4 evidence)

| Violation | Location | Contract class |
|-----------|----------|----------------|
| Silent `Contact.status` promotion on score | `revenue_os/services/lead_scoring_service.py` → `LeadScorer.update_contact_status` called from `score_contact` | HUMAN_APPROVAL_REQUIRED gap |
| Runner Hermes batch score auto-updates status | `runner_api_routers/hermes.py` → `score_contacts_batch` | Same gap |
| Scheduled / planner scoring paths | `revenue_os/scheduler.py`, `revenue_os/services/hermes_planner.py` | Same gap if promotion executes |

**Not a violation:** `revenue_os/services/scoring_service.py` — updates `lead_score` only; does not mutate `Contact.status`.

---

## Frozen contract impact

| Assessment | Value |
|------------|-------|
| **Frozen Contract Impact** | **NONE expected** |
| Rationale | A4 remediates a **pre-documented gap** explicitly listed in A1.5 authority contract §4; implements `HUMAN_APPROVAL_REQUIRED` without altering ownership, entity model, or boundary prose |
| Parent freezes (Architecture v2.2, Marketing OS, Toolchain, Platform Agent Registry) | **NONE** |
| A3.5 deal-stage freeze | **Preserved** — orthogonal mutation surface |
| A1.5 focused test exceptions (2 ENVIRONMENT_DEPENDENCY) | **UNCHANGED identities** expected |

If implementation requires editing frozen contract **meaning**, stop — requires ADR unfreeze.

---

## Implementation boundary verdict

| Gate | Result |
|------|--------|
| Within A1.5 architecture baseline | **PASS** |
| Respects Sales ↔ Revenue ownership | **PASS** |
| Respects Sales ↔ Marketing boundary | **PASS** |
| Closes documented authority gap only | **PASS** |
| Frozen contract impact | **NONE** (conditional on scope discipline) |
| DB migration required | **NO** |
| External integration required | **NO** |

**Verdict: A4 MAY PROCEED** as **COMPLETE_EXISTING** implementation.

A4 success criteria (contract-level):

1. Lead score computation remains **AUTONOMOUS_ALLOWED** (C12 LIVE preserved).  
2. `Contact.status` promotion from scoring paths requires **HUMAN_APPROVAL_REQUIRED** (or explicit human-initiated modify with approver gate).  
3. No silent agent/scorer promotion.  
4. Revenue Contact SoT unchanged; no second CRM store.  
5. A3.5 deal-stage behavior untouched.  
6. Frozen A1.5 documents unchanged in meaning.

---

## Reference: A2 → A4 sequence context

From `SALES_A2_IMPLEMENTATION_SEQUENCE.md`:

| Sprint | Scope | Status at audit |
|--------|-------|-----------------|
| A3 | Runner deal stage (human-gated) | **DONE / FROZEN** |
| A3.5 | Freeze A3 baseline | **DONE** |
| **A4** | LeadScorer / Contact.status human gate | **THIS SPRINT** |
| A4.5 | Freeze A4 behavior baseline | Future |
| A5 | Companies runner or CommercialOutcome stub | After A4 |

---

**ATLAS Contract Guard — A4 boundary audit complete.**
