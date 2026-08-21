# Founder OS ACP-3 — Durable Autonomous Operations Runtime Contract

**Baseline:** `founder-os-acp2-v1.0` → commit `1444dae9c4914df556e5c570a527d8203c28a542`
**Branch:** `founder-os-acp3-durable-runtime`
**Persistence:** 0 new SoTs / 0 models / 0 migrations

## Mission

ACP-3 establishes durability, recovery, supervision, execution coverage, and
operational safety for founder-supervised autonomous commercial operations.
It does **not** expand authority.

## Foundational rule

Durability MUST NOT amplify authority.

- Recovered work retains only authority re-evaluated at recovery/execution time.
- If current authority is narrower than recorded authority, **current wins**.
- Missing tenant → fail closed.
- Unsafe reconstruction → human review (ambiguous), never guessed success.

## Semantics (precise)

**at-least-once discovery + idempotent effect execution**

Not claimed: distributed exactly-once delivery.

## Contracts (summary)

| # | Contract | Mechanism |
|---|----------|-----------|
| 1 | Durable work identity | `acp2:{work_kind}:{org}:{target}:{logical_key}` |
| 2 | Reconciliation | Classify latest `AgentActionLog` orch events per idempotency key |
| 3 | Restart recovery | Matrix by crash boundary (retry / prove / wait / ambiguous) |
| 4 | Effect-safe recovery | External send/book → AMBIGUOUS without proof; no blind replay |
| 5 | Orchestration coverage | All mutating scheduler commercial paths gated + unit-orchestrated or documented |
| 6 | Retry safety | Bounded attempts; mode re-eval; exhaustion observable |
| 7 | Duplicate invocation | Same idempotency → dedupe via success provenance |
| 8 | Pause | `HEARTBEAT_ENABLED=0` — no new mutating work / no recovery exec |
| 9 | Kill | `ACP2_AUTONOMOUS_EXECUTION_ENABLED=0` — fail closed for autonomous exec |
| 10 | Resume | Bounded resume pass; still passes tenant/ACP-1/idempotency/retry |
| 11 | Human escalation | Distinct recovery classes (not one exception bucket) |
| 12 | Provenance | `acp3_*` + existing `acp2_*` append-only logs |
| 13 | Tenant isolation | Org-scoped reconcile; no cross-tenant recovery |
| 14 | ACP-1 preservation | Fresh `evaluate_authority` on recovery |
| 15 | Approval preservation | Never invent/infer approval |
| 16 | Observability | Oversight: gates + retryable/exhausted/waiting/ambiguous |
| 17 | Bounded execution | Scan ≤200, recover ≤25 per org pass |
| 18–20 | Tests / regression / no scope expansion | Focused suite + matrix; no authority widening |

## Pause / Kill / Resume (env)

| Control | Env | New mutating work | Recovery execution | Approvals | Observational reconcile |
|---------|-----|-------------------|--------------------|-----------|-------------------------|
| Pause | `HEARTBEAT_ENABLED=0` | blocked | blocked | human still decides | allowed |
| Kill | `ACP2_AUTONOMOUS_EXECUTION_ENABLED=0` | blocked | blocked | human still decides | allowed |
| Resume exec | `ACP3_RESUME_ENABLED=0` | (other gates apply) | blocked | — | allowed |

Neither pause nor kill rolls back committed external effects. Neither erases work.

## Negative assertions (all NO)

Restart grant authority? · Reconcile infer approval? · Missing tenant execute? ·
Cross-tenant recovery? · PROHIBITED → executable via retry? · HUMAN_REQUIRED without
approval? · Duplicate scheduler duplicates idempotent effect? · Pause erase work? ·
Kill claim external rollback? · Resume unbounded historical replay? · Fabricate
success? · Blind replay ambiguous effect? · Activate dormant Celery? · New SoT without
exception? · Hermes autonomous Deal? · Delegation amplify ACP-1?

## Persistence decision

**Preferred architecture used:** persistent facts + deterministic reconciliation.
**Persistence exception required:** NO.
