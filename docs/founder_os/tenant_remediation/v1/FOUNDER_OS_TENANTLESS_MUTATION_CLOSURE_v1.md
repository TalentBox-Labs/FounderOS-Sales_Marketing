# Tenantless Mutation Closure v1.1

**Sprint:** FOUNDER OS TENANT-BOUNDARY REMEDIATION v1.1
**Date:** 2026-08-20

## Closed paths (v1.1)

| HTTP mutation route | v1 | v1.1 |
|---------------------|----|------|
| `POST /api/v1/marketing/qualified-demand/handoff` | `require_tenant_mutation()` | unchanged |
| `POST /api/v1/sales/intake/demand/accept\|reject` | `require_tenant_mutation()` | unchanged |
| `POST /api/v1/operator/actions/qualified-demand/accept\|reject` | `optional_tenant_mutation()` | **`require_tenant_mutation()`** |
| `POST /api/v1/cockpit/actions/qualified-demand/accept` | `optional_tenant_mutation()` | **`require_tenant_mutation()`** |
| `POST /api/v1/mdg/manual-demand/register` | `optional_tenant_mutation()` + post-stamp | **`require_tenant_mutation()`** + atomic org on insert |

## Read-path closure

| Surface | Change |
|---------|--------|
| `cockpit_read_model._load_pending_qualified_demands` | Returns `[]` when `organization_id` absent (mirrors operator/founder) |

## Tenant resolution

`require_tenant_mutation()` calls `resolve_tenant_context(fail_closed_on_db_error=True)`.

DB errors during mutation tenant resolution return **HTTP 503** — no legacy `None` fallback on mutation paths.

Read paths continue using `resolve_tenant_context()` without strict DB fail-closed.

## Superseded behavior

Env-operator / API-key-only commercial intake mutation **without human session + org context** is superseded. Historical OF1/MDG1 tests encoding this behavior are **unsafe-contract debt**, not active production contract.

## Legacy service API

Direct `register_marketing_handoff` / `accept_qualified_demand` / `reject_qualified_demand` with `organization_id=None` remains for **internal unit tests only**. No production HTTP route reaches these without trusted tenant context after v1.1.

## Historical test debt (not active contract)

### Old MC04 (`tests/test_mc04_qualified_demand.py`)

| Test | Classification |
|------|----------------|
| `test_runner_handoff_and_accept_flow` | OBSOLETE_UNSAFE_CONTRACT |
| `test_reject_creates_audit` | OBSOLETE_UNSAFE_CONTRACT |
| `test_handoff_idempotent` | OBSOLETE_UNSAFE_CONTRACT |
| `test_accept_without_handoff_rejected` | HARNESS_CONTEXT_MISSING (expects 422; production with tenant → 404 via scoped guard) |

### OF1 (`tests/test_of1_operator_flow.py`)

| Test | Classification |
|------|----------------|
| `test_spoofed_human_identity_ignored` | OBSOLETE_UNSAFE_CONTRACT (tenantless accept) |
| `test_path_a_qualified_demand_accept` | OBSOLETE_UNSAFE_CONTRACT |
| `test_path_a_qualified_demand_reject` | OBSOLETE_UNSAFE_CONTRACT |
| `test_audit_trail_on_accept` | OBSOLETE_UNSAFE_CONTRACT |

### MDG1 (`tests/test_mdg1_manual_demand_registration.py`)

HTTP register tests expecting 200 without session/org → OBSOLETE_UNSAFE_CONTRACT.
`test_jinja_shell_not_react` → UNRELATED.

Active proof: `tests/test_mc04_qualified_demand_tenant_v2.py` + `tests/test_founder_os_tenant_remediation_v1.py`.
