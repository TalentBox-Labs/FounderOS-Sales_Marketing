# Sales ↔ Revenue Boundary Contract v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**ADR:** [Architecture_ADR_005.md](../architecture/Architecture_ADR_005.md)  
**Source:** [SALES_REVENUE_CONTRACT.md](SALES_REVENUE_CONTRACT.md) (A1)

---

## Freeze statement

**Sales ↔ Revenue Boundary: FROZEN**

Revenue OS must not become a duplicate CRM. Sales OS must not become an accounting/revenue-recognition system.

---

## 1. Sales ownership (frozen)

- Prospecting, outreach ops, SDR workflows  
- Sales qualification policy & engagement orchestration  
- Pipeline stage movement as sales process (mutates Revenue `Deal.stage` via adapter)  
- Sales operator UI  
- Sales agent assists (draft)  
- Emit **`CommercialOutcome`**

## 2. Revenue ownership (frozen)

- Entity SoT: Contact, Company, Deal, Pipeline, Activity  
- Deal value, probability, expected_close_date, closed_at  
- Forecast models & financial performance analytics  
- Billing / invoices / payments (future finance)  
- Revenue-impacting approvals queue  
- CSM account health over Company  

## 3. Transition / handoff

```
Sales Opportunity (Deal in process)
  → CommercialOutcome { closed_won | closed_lost }
  → Revenue Intake
```

Implementation: NOT_IMPLEMENTED (contract only).

## 4. Shared data rules

- One entity SoT under Revenue OS  
- Sales reads/writes through facades/adapters — not a second schema  
- Co-location under `revenue_os/` = ACCEPTED_LEGACY, not ownership redefinition  

## 5. Mutation authority

| Mutation | Authority |
|----------|-----------|
| Deal.stage (ops) | Sales ops + human accountability |
| Contact.status promotion | Human/policy (LeadScorer auto-write = known gap → future migration) |
| Forecast models | Revenue / HUMAN_ONLY |
| Approvals for outbound/deal propose | Revenue queue; Sales files |

## 6. Prohibited duplicate ownership

- No second Contact/Deal store labeled “Sales CRM SoT”  
- No Revenue ownership of Marketing publish  
- No Sales ownership of recognized revenue  

Known violations remain documented in A1 — **not fixed** by A1.5.
