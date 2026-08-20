# Tenant Resolution Failure Contract v1

## Problem (v1 audit)

`resolve_tenant_context()` caught `SQLAlchemyError` and returned `None`, allowing mutation callers using `optional_tenant_mutation()` to fall through to tenantless legacy behavior.

## v1.1 mutation contract

### `require_tenant_mutation()`

1. Calls `resolve_tenant_context(fail_closed_on_db_error=True)`
2. If no tenant context → **HTTP 403** `Organization context required`
3. If DB error during resolution → **HTTP 503** `Tenant resolution unavailable`
4. Validates mutation role (human, active membership, non-VIEWER)

### Distinction

| Outcome | Meaning | Mutation response |
|---------|---------|-------------------|
| No human session / no org | NO TENANT | 403 |
| DB infrastructure failure | TENANT RESOLUTION FAILURE | 503 |
| Valid tenant resolved | OK | Proceed |

## Read paths (unchanged tolerance)

`resolve_tenant_context()` without `fail_closed_on_db_error` still returns `None` on DB error for read composition paths that degrade gracefully.

Mutation paths **must** use `require_tenant_mutation()` — never `optional_tenant_mutation()` for commercial intake.

## Proof

`tests/test_mc04_qualified_demand_tenant_v2.py::test_mutation_db_resolution_failure_fails_closed`

## Callers using strict mutation resolution (v1.1)

- `runner_api_routers/qualified_demand.py` — marketing handoff, sales intake
- `runner_api_routers/operator_flow.py` — qualified-demand accept/reject only
- `runner_api_routers/cockpit.py` — qualified-demand accept only
- `runner_api_routers/manual_demand.py` — manual-demand register

Other operator/cockpit mutations (contact-status, deal) retain `optional_tenant_mutation()` — out of v1.1 commercial-intake scope.
