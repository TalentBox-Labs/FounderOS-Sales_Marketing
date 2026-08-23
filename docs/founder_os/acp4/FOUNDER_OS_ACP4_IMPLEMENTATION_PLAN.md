# Founder OS ACP-4 — Implementation Plan (Post-Discovery)

## Scheduler coverage (re-audit after ACP-3)

| Job | Class | Dup tick safe today? | Concurrent worker safe? | Stale exec safe? | Idempotency | Authority revalidated pre-effect? |
|-----|-------|----------------------|-------------------------|------------------|-------------|-----------------------------------|
| score_new_leads | A | Partial | **No** | **No** | Soft | **No** |
| scan_follow_up_eligibility | A | Partial | **No** | **No** | Soft | **No** |
| check_deals_at_risk | A | Partial | **No** | **No** | Soft day key | **No** |
| sync_gmail_inbox | A | Partial | **No** | **No** | message_id soft | **No** |
| snapshot_pipeline_metrics | C (+orch) | Soft | Soft | Soft | Soft | **No** |
| hermes_goal_check | Mixed A/B | Partial | **No** | **No** | Partial | Partial |
| acp3_reconcile | A | Partial | **No** | **No** | Soft | evaluate on recover; **no** pre-effect fence |
| Celery | E | — | — | — | — | KEEP_DORMANT |

## Founder oversight contract (no UI build this pass)

Must eventually expose (org-scoped):

- autonomous execution state (kill)
- scheduler health (heartbeat running, last job times)
- worker/process health (replica identity if available)
- active claims (if observable) / stale claim / fence rejection events
- recovery backlog, retryable, exhausted, ambiguous, waiting human, blocked/prohibited
- recent successes
- pause / kill / resume flags
- affected organization
- stale executor / fence rejection counts

## Minimum ACP-4 implementation (recommended)

Every YES requires evidence from this discovery pack.

| Need | YES/NO | Evidence / note |
|------|--------|-----------------|
| New `acp4_*` runtime service | **YES** | claim+fence helpers composed over ACP-2/3 |
| Claim service | **YES** | advisory lock / row lock wrapper |
| DB locking | **YES** | no locks today |
| Unique DB constraint | **NO** (default) | prefer locks; optional later |
| Execution epoch/fence | **YES** | pre-effect revalidation mandatory |
| Scheduler changes | **YES** | route mutating units through claim+fence |
| ACP-3 runtime changes | **YES** | recovery path same fence |
| Oversight changes | **YES** | fence rejects / multi-worker signals |
| External integration changes | **PARTIAL** | only if needed for idempotent request IDs; no dormant activation |
| New tests | **YES** | failure injection plan |
| Migration | **NO** | advisory-lock design |
| New persistent model | **NO** | |
| Celery | **NO** | |
| Redis | **NO** | |
| Broker | **NO** | |

## Explicitly deferred

1. Celery/Redis async control plane
2. New lease/work table SoT
3. Distributed exactly-once
4. Hermes full micro-step WorkItems (class B residual)
5. UI build for oversight (contract only now)
6. Multi-region / multi-DB lock semantics beyond Postgres production
7. Authority policy expansion

## Implementation sequence (future sprint)

1. `acp4_claim` + `acp4_fence` modules (no new models)
2. Wrap `run_work` / recovery executor entry
3. Scheduler/reconcile use wrappers
4. Oversight fields
5. Failure injection tests
6. Regression matrix (ACP-4…COS-1 + prior)
