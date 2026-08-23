# Sales OS — Canonical Architecture

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Status:** CANONICAL TARGET (governance)  
**ADR:** [Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md)  
**Parent:** Founder OS Architecture v2.2 (FROZEN)

**Nature:** Destination architecture for Sales OS.  
**Does not change:** current implementation, APIs, database, runtime, or business logic.

---

## 1. Three-layer model

| Layer | Meaning |
|-------|---------|
| **CURRENT IMPLEMENTATION** | What exists today in `revenue_os/`, `runner_api_routers/*`, `templates/sales.html`, `frontend/` |
| **CANONICAL TARGET** | This document + contracts |
| **MIGRATION REQUIRED** | Items in `SALES_A1_MIGRATION_MAP.md` |

A1 preserves all **12 LIVE** capabilities (see §8). No greenfield redesign.

---

## 2. Sales OS owns (destination)

| Domain | Ownership |
|--------|-----------|
| Prospecting plans & SDR workflows | Sales OS |
| Outreach sequence **operations** (enroll, propose, execute after approval) | Sales OS |
| Sales qualification **workflow** & engagement state transitions (policy) | Sales OS |
| Pipeline **operations** (stage movement as sales process) | Sales OS |
| Sales operator surfaces (`/sales`, future CRM shell) | Sales OS |
| Sales agent **assist** (draft research, email, sequences — no send) | Sales OS |
| Handoff **requests** to Revenue (closed-won event emission) | Sales OS |
| Marketing demand **intake** processing (after contract accept) | Sales OS |

---

## 3. Sales OS does NOT own

| Domain | Owner |
|--------|-------|
| CRM entity SoT (`Contact`, `Company`, `Deal`, `Pipeline`, `Activity`) | **Revenue OS** |
| Recognized revenue, billing, invoices, payments | **Revenue OS** / finance systems |
| Revenue forecasting models & financial performance analytics | **Revenue OS** |
| Editorial / publish / website / SEO / social publish | **Marketing OS** |
| LLM providers, agent runtime substrate | **AI Platform** |
| Celery, n8n transport, queues, schedulers | **Automation Platform** |
| AuthN/RBAC engine, audit infra, secrets store | **Shared Platform** |
| Third-party CRM sync (HubSpot, Salesforce) | **Not implemented** — future adapter only |

---

## 4. Entity responsibility map

| Concept | Canonical owner | Sales role |
|---------|-----------------|------------|
| Lead | Revenue (`Contact` + status/events) | Operates qualification workflow |
| Contact | Revenue (entity) | Creates/updates via approved workflows |
| Company | Revenue (entity) | Associates during prospecting/enrich |
| Account (CSM) | Revenue (`Company` view) | Reads health; does not own CS model |
| Opportunity | Revenue (`Deal` alias) | Opens/advances in sales process |
| Deal | Revenue (entity) | Pipeline ops on Revenue records |
| Pipeline / Stage | Revenue (entity + enum) | Operates stage transitions |
| Activity / Task / Note | Revenue (entity) | Creates via sales engagement |
| Source | Revenue (`ContactSource`) | Sets on intake |
| Owner | Revenue (field; RBAC future) | Assigns per policy |
| Status | Revenue (`ContactStatus`) | Proposes; human/policy gate |
| Value / Probability / CloseDate | Revenue (`Deal` fields) | Sales updates during pipeline ops |
| Forecasting inputs | Revenue aggregates Deal data | Sales supplies movement events |
| Handoff state | Contract event (`CommercialOutcome`) | Sales emits; Revenue consumes |

---

## 5. Cross-OS flow (canonical)

```
Marketing OS
    │  QualifiedDemand (contract event)
    ▼
Sales OS — intake, qualify, engage, pipeline ops
    │  CommercialOutcome (ClosedWon / ClosedLost)
    ▼
Revenue OS — CRM SoT, forecast, revenue automations, CS handoff
```

See: `SALES_MARKETING_CONTRACT.md`, `SALES_REVENUE_CONTRACT.md`.

---

## 6. Platform boundaries

| Capability | Platform | Sales usage |
|------------|----------|-------------|
| LLM inference for drafts | AI Platform | Consume via agents |
| Job execution / retries | Automation Platform | Consume; no business rules in Celery |
| API key / JWT / audit / vault | Shared Platform | Consume |
| Qualification scoring **policy** | Sales OS | May recommend; human gate for mutations |
| Outreach **approval queue** execution routing | Revenue OS service today | Sales files; Revenue owns approval domain |

Sales OS must not duplicate platform infrastructure inside domain code.

---

## 7. Current implementation vs target (honest map)

| Target | Current location | Migration |
|--------|------------------|-----------|
| Sales prospecting UI | `templates/sales.html`, `prospecting` router | ACCEPTED_LEGACY |
| Sales CRM APIs | `runner_api_routers/crm.py` | REQUIRES_FUTURE_ADAPTER (Sales facade) |
| CRM models | `revenue_os/models/*` | ACCEPTED_LEGACY co-location |
| Dual JWT API | `revenue_os/main.py` | REQUIRES_FUTURE_MIGRATION |
| React CRM | `frontend/` unmounted | RETAIN_AND_REFACTOR_LATER |

---

## 8. LIVE capabilities preserved (A0 C01–C17 subset)

These **must not** be removed or behaviorally changed by architecture work:

| ID | Capability |
|----|------------|
| C01 | Jinja `/sales` prospecting shell |
| C02 | Prospecting plan/import APIs |
| C03 | Runner CRM contacts |
| C07 | Activities create/list/complete |
| C08 | Follow-ups inbox |
| C09 | Outreach sequences CRUD |
| C11 | Sales AI assists |
| C12 | Hermes score/qualify/pipeline health |
| C13 | Approvals queue |
| C14 | Copilot operator assist |
| C15 | Goals / Hermes goals |
| C17 | CSM account health APIs |

**Existing Live Capabilities Preserved: 12/12**

---

## 9. Agent registry note

No new permanent Founder OS runtime agent is created in A1. Sprint agents (Atlas, Scout, …) are **Cursor governance identities**, not CrewAI production agents. Future Sales runtime agent registration requires Platform Agent Registry amendment.

Recommended future registry entry (A1 recommendation only): **SDR** or **Pipeline** agent under Sales OS with forbidden CRM delete and required human approval for outbound send — deferred to post-A1.5 implementation planning.

---

## 10. Architecture integrity

Sales OS is a **bounded domain** under Founder OS. It must not merge with Revenue OS during migration. Shared tables today are **legacy co-location**, not ownership proof.

**Canonical Sales Architecture: PASS** (destination defined; implementation migration deferred)
