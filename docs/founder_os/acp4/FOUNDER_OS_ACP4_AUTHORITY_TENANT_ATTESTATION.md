# Founder OS ACP-4 — Authority & Tenant Attestation (Post Remediation)

## Authority revalidation (current — claimed paths)

Pre-effect fence in `acp4_execution_fence.pre_effect_fence` runs after claim, before executor.

| Check | Immediately before effect? |
|-------|----------------------------|
| Organization present | **YES** (fence) |
| Tenant allowlist ∩ ACTIVE | **YES** (fence) |
| Kill switch | **YES** (fence + process env) |
| Pause | **YES** (fence + process env) |
| ACP-1 / catalog mode | **YES** (fence) |
| Approval state (HUMAN_REQUIRED) | **YES** — status + **org-bound** ApprovalRequest |
| Idempotency / already succeeded | **YES** (fence) |

Distributed pause/kill consensus: **CONFIG-DEPENDENT** (identical `os.environ` on replicas).

## Tenant concurrency

| Property | Proven? | Notes |
|----------|---------|-------|
| organization_id in logical work scope | **YES** | claim material + idempotency key |
| No cross-tenant claim | **YES** | org in SHA-256 claim material |
| No cross-tenant reconciliation | **YES** | AgentActionLog org filter |
| Contact ownership ≠ tenant activation | **YES** (ACP-1) | |
| Tenant re-resolve on reclaim | **YES** (fence) | |

## Human approval concurrency

| Scenario | After remediation |
|----------|-------------------|
| Two concurrent `decide(approve=True)` | `with_for_update` + ACP-4 claim `approval_execute:{id}` → ≤1 executor |
| Cross-tenant decide | Blocked via `get_approval_for_tenant` / org mismatch |
| Foreign-org approved row at fence | Rejected — status alone insufficient |
| Already executed | Idempotent `execution_result` short-circuit |

`CURRENT_APPROVAL_REVALIDATION` is claimed for:

1. `decide()` approve path (claim + org scope + status re-check)
2. Claimed `HUMAN_REQUIRED` work through `pre_effect_fence` (approved + org-bound)

Not claimed for bare `orchestrate` / observational paths.
