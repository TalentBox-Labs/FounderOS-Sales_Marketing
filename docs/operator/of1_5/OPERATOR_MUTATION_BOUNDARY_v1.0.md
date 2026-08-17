# OPERATOR MUTATION BOUNDARY v1.0

**STATUS: FROZEN**

## Closed-won / CommercialOutcome

| Rule | Frozen |
|------|--------|
| A3.5 stage → `closed_won` | Does **not** emit CommercialOutcome (`commercial_outcome_emitted: false`) |
| CO handoff eligibility | `Deal.stage == closed_won` only (MC06.5) |
| CO processing mutates Deal | **PROHIBITED** |
| Shared Sales/Revenue SoT | **PROHIBITED** |
| Billing / recognition | **NOT_INCLUDED** |

## Operator create vs CRM create

`POST /api/v1/crm/deals` remains the ungated runner create API (A1.5/CRM).  
OF1 create is a **separate trusted-human proxy** restricted to non-terminal sales stages. It does not replace or rewrite the CRM route.

## Prohibited OF1.5 expansions

Marketing handoff register · cockpit mutation-set change · CRM SPA · new SoT · billing.
