# Founder OS ACP-4 — Transaction Boundary Audit

## Canonical desired order

```
DISCOVERY → CLAIM → AUTHORITY/FENCE → DOMAIN READ → EFFECT → PROVENANCE → DB COMMIT
```

## Current typical order (orchestrated paths)

```
DISCOVERY → AUTHORITY (evaluate) → [RUNNING log commits via separate session]
  → EFFECT → [SUCCEEDED log commits via separate session]
  → job db.commit() (sometimes)
```

**No CLAIM.** Provenance uses `log_agent_action` → **independent Session + commit** (`activity_log.py`), decoupled from the job session.

## Crash window matrix

| ID | Scenario | Current outcome | ACP-4 requirement |
|----|----------|-----------------|-------------------|
| A | Effect succeeds externally → crash → success provenance absent | Side effect may exist; reconcile may RETRYABLE or AMBIGUOUS | Classify AMBIGUOUS for external; no blind replay; domain proof if safe |
| B | Success provenance written → job DB rollback | Success log durable (separate commit); domain may lag | Treat success provenance as soft proof; domain proof preferred for replay-safe kinds |
| C | Authority evaluated → delayed execution → authority changed | **May still execute** (gap) | Fence immediately before effect |
| D | Work discovered → duplicate executor discovers | **Both may execute** | Claim serializes |
| E | DB mutation committed → worker reports failure | Domain changed; failure/retry provenance possible | Idempotent re-entry; do not double-apply |

## Path notes

### lead_score (`job_score_new_leads`)

- Orchestrate + score on job `db`; job `db.commit()` at end.
- RUNNING/SUCCEEDED logs commit independently mid-flight.
- Window: score committed in memory, crash before job commit → peer may re-score (often harmless if overwrite).

### gmail_inbound

- `sync_inbox` opens own session and **commits** Activities internally.
- Orchestrate success log separate → classic A window.

### deal_at_risk / metrics

- Emit + logs; deal_at_risk job has **no** job-level `db.commit()`; relies on log commits / side emitters.

### approval execute (human)

- `decide()` mutates ApprovalRequest then runs executor then `db.commit()`.
- Concurrent decides race without row lock → dual external effect risk.

### ACP-3 recovery

- Gate → evaluate → retry_work → executor; same C/D windows as orchestrate; ends with `db.commit()` in `job_reconcile_autonomous_work`.
