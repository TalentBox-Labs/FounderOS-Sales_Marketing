# Founder OS COS-3 Regression Reconciliation

**Interpreter:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing/.venv/bin/python`
**Env:** `SECRET_KEY=ui-d2-1-local-test-secret-key-32b`

## Suites

| Suite | Expected |
|-------|----------|
| COS-3 focused | PASS |
| COS-2 | PASS |
| COS-1 | PASS |
| Tenant remediation v1 | PASS |
| MC04 tenant-v2 | PASS |
| UI-D2 core | PASS |
| D1.x init/demo | PASS |

## Historical / out-of-scope failures (unchanged policy)

| Class | Examples | Treatment |
|-------|----------|-----------|
| OBSOLETE_UNSAFE_CONTRACT | Old MC04/OF1/MDG1 tenantless mutation HTTP tests | Documented in tenant remediation; not modified |
| SUPERSEDED_NEGATIVE_SCOPE | UI-D1 “booking workflow pending” copy | Pre-COS-1/UI-D2; frozen files untouched |
| HARNESS_CONTEXT_MISSING | Old MC04 accept-without-handoff expects 422 | V2 proves 404 with tenant via scoped guard |

COS-3 does not reopen tenantless mutation. Do not weaken old tests to green COS-3.
