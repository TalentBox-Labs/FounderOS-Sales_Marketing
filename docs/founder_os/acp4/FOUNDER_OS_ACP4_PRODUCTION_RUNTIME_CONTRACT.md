# Founder OS ACP-4 — Production Runtime Contract

## Invariant

**PAST ELIGIBILITY ≠ CURRENT EXECUTION AUTHORITY.**

Durability and multi-worker concurrency MUST NOT amplify ACP-1 authority.

## Target distributed guarantee (truthful) — IMPLEMENTED

```
AT_LEAST_ONCE_DISCOVERY
+ SINGLE_CURRENT_CLAIM          (pg_try_advisory_xact_lock on PostgreSQL)
+ CURRENT_AUTHORITY_REVALIDATION (catalog mode wins at fence)
+ CURRENT_TENANT_REVALIDATION
+ CURRENT_APPROVAL_REVALIDATION
    - decide(): row lock + approval_execute claim + org scope
    - claimed HUMAN_REQUIRED fence: approved + org-bound ApprovalRequest
+ PAUSE/KILL PROCESS FENCING
+ PAUSE/KILL DISTRIBUTED SAFETY = CONFIG-DEPENDENT (identical env on replicas)
+ IDEMPOTENT_EFFECT_EXECUTION
+ STALE_EXECUTOR_FENCING
+ ACP-3 RECONCILIATION
```

**Do not claim** distributed exactly-once execution.
**Do not claim** pause/kill distributed consensus.

Entry points: `orchestrate_claimed` / `run_work_claimed` / `retry_work_claimed` /
Hermes score & deal-risk claimed paths / `decide()` approval_execute claim.

**Production gate:** PostgreSQL two-connection / two-process advisory lock proof
must be executed before multi-replica GA (CI currently uses SQLite process-local).

## Forbidden

- Authority expansion (Hermes Deal create, outbound/booking autonomy, etc.)
- Second commercial workflow SoT
- Blind replay of ambiguous external effects
- Cross-tenant claim / retry / reconcile / stale execution
- Activating Celery as ACP control plane by default
- Claiming pause/kill rolls back committed external effects

## Required behaviors (contract)

1. **Durable identity** — reuse ACP-2/3 `idempotency_key` as logical work scope (must include organization).
2. **Claim** — at most one concurrent owner of a logical unit during effect attempt (see claim model doc).
3. **Fence** — immediately before effect: re-read pause/kill, tenant eligibility, ACP-1/catalog mode, approval state; fail closed if narrower.
4. **Idempotency** — after claim, still short-circuit if success provenance or domain proof exists.
5. **Ambiguity** — external timeout / crash after side effect without proof → ACP-3 `AMBIGUOUS_EFFECT`, no blind replay.
6. **Bounds** — discovery, claim reclaim, and resume remain bounded (ACP-3 limits preserved).
7. **Observability** — founder oversight must expose multi-worker safety signals (claims/fence rejects, backlog, gates).

## Negative assertions (must remain NO)

Can multi-worker past eligibility grant authority?
Can claim invent approval?
Can missing tenant execute?
Can claim cross tenants?
Can PROHIBITED become executable via reclaim?
Can HUMAN_REQUIRED execute without real approval + fresh ACP-1?
Can pause/kill be ignored by a stale holder after fence?
Can Celery bypass ACP because it exists in compose?
