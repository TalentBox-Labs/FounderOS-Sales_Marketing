# Founder OS ACP-4 — Implementation Manifest (Post Pre-Freeze Remediation)

| Item | Value |
|------|-------|
| Baseline | `founder-os-acp3-v1.0` @ `89329f421bcdca41fcabc69b17a585c70324e555` |
| Branch | `founder-os-acp4-production-runtime` |
| New SoTs / models / migrations | 0 / 0 / 0 |
| Celery / Redis | NOT activated |
| Postgres multi-process proof | **NOT EXECUTED** (deployment gate) |

## Truthful distributed guarantee ACP-4 may claim

```
AT_LEAST_ONCE_DISCOVERY
+ SINGLE_CURRENT_CLAIM          (pg_try_advisory_xact_lock on PostgreSQL)
+ CURRENT_AUTHORITY_REVALIDATION (claimed autonomous paths)
+ CURRENT_TENANT_REVALIDATION
+ CURRENT_APPROVAL_REVALIDATION (decide() serialization + org-bound fence for claimed HUMAN_REQUIRED)
+ PAUSE/KILL PROCESS FENCING
+ PAUSE/KILL DISTRIBUTED = CONFIG-DEPENDENT (shared env)
+ IDEMPOTENT_EFFECT_EXECUTION
+ STALE_EXECUTOR_FENCING (claimed paths)
+ ACP-3 RECONCILIATION
```

Not claimed: distributed exactly-once; distributed pause/kill consensus.

## Pre-freeze remediation closed

1. Hermes `score_unscored_leads` / `check_deals_at_risk` → `orchestrate_claimed`
2. `decide()` → `with_for_update` + ACP-4 claim `approval_execute:{id}` + org binding
3. Approval fence requires org-bound ApprovalRequest (not status alone)
4. Process-local claim lifetime aligned to session commit/rollback
5. Docs: Pause/Kill Distributed = CONFIG-DEPENDENT
