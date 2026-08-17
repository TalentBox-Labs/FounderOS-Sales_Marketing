# UI1 — Executive Cockpit Information Architecture

**Sprint:** UI1  
**Date:** 2026-08-13  
**Mode:** Design only — not built

---

## Recommended navigation (repository-aligned)

Smallest coherent model — **extend existing Jinja shell**, do not fork React:

```
WorkCrew Founder OS (base.html)
├── Home / Executive Cockpit   ← NEW (UI2)
├── Content & Editorial        ← existing cluster
├── Publishing                 ← existing
├── Marketing                  ← existing + SEO sub-nav
├── Sales                      ← existing /sales + link to CRM when mounted
├── Operations                 ← heartbeat, approvals (API-backed)
└── (Settings deferred)
```

Do **not** force Revenue top-level nav until CommercialOutcome exists.

---

## A. Attention / Decision Queue (implementable)

| Queue item | Data source | Implemented? |
|------------|-------------|--------------|
| Pending editorial approvals | `/api/v1/editorial/pending` | **YES** |
| Publishing jobs awaiting human action | `/api/v1/publishing/*` | **YES** |
| QualifiedDemand awaiting Sales accept | Query `AgentActionLog` handoff minus accept | **PARTIAL** — needs read aggregation |
| Deal stage actions | No queue — founder-initiated | N/A |
| Integration blockers | Docs + env checks | **DOC/static** |
| Social FD-01 / ES blockers | S0 register | **DOC/static** |

---

## B. Commercial Flow (lifecycle)

| Stage | State |
|-------|-------|
| Audience | PARTIAL (web live; social blocked) |
| Demand | **MISSING** (no form capture UI) |
| QualifiedDemand | **IMPLEMENTED** (API; no UI) |
| Lead/Contact | OPERABLE (CRM API; UI partial) |
| Deal | OPERABLE (A3.5; no stage UI) |
| Commercial Outcome | **MISSING** |
| Revenue | **MISSING** |

Cockpit shows **honest** implemented vs conceptual stages.

---

## C. Sales Snapshot (authoritative)

| Metric | Source | Available |
|--------|--------|-----------|
| Contacts by status | GET `/api/v1/crm/contacts` | **YES** |
| Lead score distribution | GET `/api/v1/hermes/lead-scores` or CRM | **YES** |
| Deals by stage | GET `/api/v1/crm/deals` | **YES** |
| Stalled deals | Derive from deals + `updated_at` | **PARTIAL** (field exists) |

---

## D. Marketing Snapshot

| Metric | Source | Available |
|--------|--------|-----------|
| SEO readiness score | `/api/v1/seo/readiness` | **YES** |
| Technical SEO status | `/api/v1/seo/technical` | **YES** |
| QualifiedDemand activity | AgentActionLog aggregation | **NEW read-only endpoint** (UI2 optional) |
| Publishing status | publishing API | **YES** |
| Social readiness | Static from S0 docs / env | **DOC** |

---

## E. System / Governance

| Item | Source |
|------|--------|
| Heartbeat status | `/api/v1/heartbeat/status` |
| Recent audit | `/api/v1/heartbeat/activity` or AgentActionLog |
| Frozen baseline list | Static manifest docs (read-only) |
| Regression health | CI / manual (not runtime) |

Cockpit = **visibility + decision queue**, not new SoT.
