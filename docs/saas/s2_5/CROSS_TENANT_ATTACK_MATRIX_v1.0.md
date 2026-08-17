# Cross-Tenant Attack Matrix v1.0

**Status:** FROZEN — all required negative tests PASS

## Fixture

| Org | Actor | Assets |
|-----|-------|--------|
| A | Owner A, Viewer A | Contact A, Deal A, QD A, CO A |
| B | Owner B | Contact B, Deal B, QD B, CO B |

## Attack results

| # | Attack | Actor | Expected | Verified |
|---|--------|-------|----------|----------|
| 1 | Read Contact B | Owner A | blocked (filtered) | PASS |
| 2 | Mutate Contact B | Owner A | 404 | PASS |
| 3 | Read Deal B | Owner A | blocked (filtered) | PASS |
| 4 | Mutate Deal B | Owner A | 404 | PASS |
| 5 | QD action on B | Owner A | 404 | PASS |
| 6 | CO action on B | Owner A | 404 | PASS |
| 7 | See B audit/QD pending | Owner A | filtered out | PASS |
| 8 | Override TenantContext via select | Owner A → Org B | 403 | PASS |
| 9 | Forge org cookie B | Owner A | 403 on `/tenant/me` | PASS |
| 10 | Spoof org in JSON body | Owner A | ignored; 404 for B object | PASS |
| 11 | VIEWER mutate same-tenant Contact A | Viewer A | 403 | PASS |
| 12 | Cockpit snapshot cross-tenant | Owner A | counts=1 | PASS |
| 13 | Operator snapshot cross-tenant | Owner B | only B contact | PASS |

## Failure semantics

Cross-tenant mutation returns **404** (not 403) to avoid confirming foreign object existence — acceptable non-leak behavior per S2 design.

## Out of matrix (S3)

CRM API `/api/v1/crm/*` — not tenant-gated; see residual risk register.
