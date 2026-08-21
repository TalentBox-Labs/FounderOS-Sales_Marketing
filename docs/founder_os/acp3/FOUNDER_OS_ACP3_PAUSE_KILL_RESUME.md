# Founder OS ACP-3 — Pause / Kill / Resume Semantics

## PAUSE (`HEARTBEAT_ENABLED=0`)

Prevents initiation of **new** autonomous mutating scheduler work and **recovery
execution**. Does not erase logs, approvals, or domain state. Read-only
reconciliation remains available. HUMAN_REQUIRED approvals remain human-decidable.

Already-running in-process work may complete the current function call; durability
does not claim abort of mid-flight OS threads.

## KILL (`ACP2_AUTONOMOUS_EXECUTION_ENABLED=0`)

Fail closed for future autonomous execution (ACP-2 evaluate + ACP-3 gates).
Does **not** claim rollback of committed external effects.
Reconciliation remains observationally available.
Visible in founder oversight `runtime_gates` / `pause` block.

## RESUME

1. Observational reconcile (always, when org resolves).
2. If gates allow and `ACP3_RESUME_ENABLED=1`, recover up to `DEFAULT_RECOVERY_EXEC_LIMIT`
   RETRYABLE units only.
3. Each unit: reconstruct → assign → **fresh ACP-1 evaluate** → retry.
4. Never resumes SUCCEEDED, WAITING_HUMAN→autonomous send, PROHIBITED, EXHAUSTED,
   or AMBIGUOUS_EFFECT into blind execution.

No thundering herd of unbounded historical replay.
