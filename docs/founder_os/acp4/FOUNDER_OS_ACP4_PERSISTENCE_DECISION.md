# Founder OS ACP-4 — Persistence Decision

## Default

**NEW PERSISTENT WORK SoT = PROHIBITED.**

## Can safe production multi-executor behavior use existing facts?

**YES — for minimum ACP-4**, using:

- Deterministic `idempotency_key`
- `AgentActionLog` append-only provenance (not as claim SoT)
- `ApprovalRequest` for human gates
- Domain state for completion proof
- **PostgreSQL transaction advisory locks** and/or domain `SELECT FOR UPDATE`
- ACP-3 reconciliation for ambiguity
- Env-based pause/kill + **pre-effect fence**

## Decision

| Flag | Value |
|------|-------|
| `ACP4_PERSISTENCE_EXCEPTION_REQUIRED` | **NO** |
| New models | **0** (planned) |
| Migrations | **0** (planned) for advisory-lock design |
| New Redis | **NO** |

## If implementation later proves locks insufficient

Stop and file `ACP4_PERSISTENCE_EXCEPTION_REQUEST` covering:

- missing safety guarantee
- why AgentActionLog/domain cannot provide durable visible claims alone
- minimum schema (org-scoped unique claim key, owner, expires_at, generation)
- tenant boundary, uniqueness, lifecycle, cleanup, concurrency, reconcile interaction
- migration/rollback impact
- why it is not a second commercial SoT (execution ownership only; authority remains ACP-1; commercial state remains CRM/Approvals)

Do **not** invent that exception now.
