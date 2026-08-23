# Founder OS ACP-4 — Implemented Corrections vs Discovery Gaps

Discovery findings are preserved in `FOUNDER_OS_ACP4_DISCOVERY.md`. This document maps **DISCOVERED GAP → IMPLEMENTED CORRECTION**.

| Discovered gap | Implemented correction |
|----------------|------------------------|
| No distributed claim | `try_acquire_claim` via `pg_try_advisory_xact_lock` (Postgres) |
| `_already_succeeded` race | Claim serializes; idempotency still checked in fence |
| Authority too early | `pre_effect_fence` immediately before effect under claim |
| Pause/kill not pre-effect | Fence re-reads env gates |
| Tenant not revalidated pre-effect | Fence checks ACTIVE + allowlist + ownership |
| Multi-replica schedulers | A-paths use `orchestrate_claimed` |
| ACP-3 recovery bypass | `retry_work_claimed` |
| Oversight blind to collisions | `claim_rejected` / `fence_rejected` buckets |

## Unchanged by design

- No lease/work table / migration
- Celery remains DORMANT
- No exactly-once claim
- Observational metrics may still use plain `orchestrate` (class C)
- Hermes micro-steps remain class B residual
