# Sales ↔ Revenue Contract

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Status:** DEFINED (governance) — **not implemented**  
**ADR:** [Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md)

Resolves A0: **Sales ↔ Revenue Boundary: CONFLICTED** → **DEFINED**.

---

## 1. Ownership (ratified)

### Revenue OS owns (system of record)

| Domain |
|--------|
| `Contact`, `Company`, `Deal`, `Pipeline`, `Activity` persistence |
| CRM APIs as entity authority (target: unified under Revenue SoT) |
| Deal **value**, **probability**, **expected_close_date**, **closed_at** fields |
| Revenue forecasting, scenarios, financial performance analytics |
| Recognized revenue, billing state, invoices, payments (future finance integration) |
| Revenue-impacting **approvals** queue (`/api/v1/approvals`) |
| Revenue automations enablement decisions |
| CSM account health over Company |

### Sales OS owns (operations & workflow)

| Domain |
|--------|
| Prospecting plans, SDR workflows, outreach **operations** |
| Sales qualification **policy** and engagement orchestration |
| Pipeline **stage movement** as sales process (mutating Revenue `Deal.stage` via adapter) |
| Sales operator UI (`/sales`, future CRM shell) |
| Sales agent assists (draft only) |
| Emitting **CommercialOutcome** events at close |

### Sales does NOT own

- Accounting / revenue recognition
- Duplicate CRM schema
- Financial forecast **models** (may supply inputs)

### Revenue does NOT become

- A second prospecting tool
- Outreach sequence author for SDR copy (Sales owns ops; Revenue owns approval execution routing today)

---

## 2. Transition boundary

```
Sales Opportunity (Deal in DISCOVERY…NEGOTIATION)
    → CommercialOutcome event
        → closed_won | closed_lost
    → Revenue Intake
        → forecast update, CS handoff, Client/Project (future), customer status
```

**Closed/Won Commercial Event** is the canonical handoff trigger — not merely a UI stage click.

---

## 3. Contract: `CommercialOutcome` (future event)

| Field | Required | Semantics |
|-------|----------|-----------|
| `outcome_id` | Yes | Idempotency UUID |
| `deal_id` | Yes | Revenue Deal reference |
| `outcome` | Yes | `closed_won` \| `closed_lost` |
| `occurred_at` | Yes | ISO timestamp |
| `actor` | Yes | Human identity |
| `value` | If won | Final commercial value |
| `currency` | If won | ISO currency |
| `loss_reason` | If lost | Optional |
| `handoff_hints` | No | CS/delivery notes |

### Revenue intake actions (future)

| Outcome | Revenue responsibilities |
|---------|-------------------------|
| `closed_won` | Set `Deal.closed_at`; optional `Contact.status → CUSTOMER`; emit CS handoff; **no auto-invoice** without finance sprint |
| `closed_lost` | Archive pipeline state; retain Deal for analytics |

---

## 4. Existing violations (documented, not fixed in A1)

| Violation | Class | Migration |
|-----------|-------|-----------|
| CRM models under `revenue_os/` used by Sales UI | ACCEPTED_LEGACY | REQUIRES_FUTURE_ADAPTER |
| Dual API stacks (runner CRM vs JWT) | CONFLICTED impl | REQUIRES_FUTURE_MIGRATION |
| Hermes planner creates deals via approvals | Overlap OK if approval gate holds | RESOLVED_BY_CONTRACT |
| Forecast router on runner while Deal SoT in Revenue | API surface split | REQUIRES_FUTURE_ADAPTER |
| LeadScorer auto-mutates Contact.status | Governance gap | REQUIRES_FUTURE_MIGRATION (human gate) |
| CSM health on runner (Sales-adjacent) | Revenue domain | ACCEPTED_LEGACY |

Revenue OS **must not** become a duplicate CRM — meaning no second Contact/Deal store. Sales **must not** become accounting.

---

## 5. Opportunity / Deal / Pipeline / Forecast

| Question | Answer |
|----------|--------|
| Sales owns Opportunity? | **Conceptually** — persisted as Revenue `Deal` |
| Sales owns Deal entity? | **No** — Revenue SoT; Sales operates |
| Sales owns Pipeline? | **No** — Revenue entity; Sales ops |
| Sales owns forecast probability? | **Input via stage**; Revenue owns forecast aggregation |
| Sales owns expected value? | Updates via pipeline ops; Revenue stores |
| Sales owns close state? | **Initiates** via CommercialOutcome; Revenue **records** |

---

## Verdict

**Sales ↔ Revenue Boundary: DEFINED**
