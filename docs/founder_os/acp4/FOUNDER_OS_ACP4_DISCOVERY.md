# Founder OS ACP-4 — Discovery (Repository Grounding)

**Branch:** `founder-os-acp4-production-runtime`
**HEAD / `founder-os-acp3-v1.0`:** `89329f421bcdca41fcabc69b17a585c70324e555`
**Working tree at discovery start:** clean
**Pass type:** documentation only — no production / test / model / migration changes

## Mission framing

| Milestone | Question answered |
|-----------|-------------------|
| ACP-1 | May this agent/effect execute? |
| ACP-2 | How is authorized work assigned, delegated, retried, escalated, observed? |
| ACP-3 | How can governed work be reconciled/recovered without a second workflow SoT? |
| **ACP-4** | How can multiple production executors safely process the same autonomous commercial runtime? |

ACP-4 is **not** an authority expansion milestone.

## Primary architecture question (answered)

**Can existing repository facts support safe multi-process execution without a second persistent workflow SoT?**

**Answer: PARTIALLY today; YES for a minimum ACP-4 design if implemented with existing DB primitives + pre-effect fencing — without a new Work/Lease table — provided effects stay idempotent/ambiguous-safe as ACP-3 requires.**

Evidence against “already safe”:

- Heartbeat is **in-process** asyncio with **no distributed lock** (`revenue_os/scheduler.py`).
- Every API process that starts calls `initialize_heartbeat()` (`runner_api.py` startup).
- `AgentActionLog` has **no unique constraint** on idempotency keys (`revenue_os/models/automation_state.py`).
- No `with_for_update` / advisory lock usage under `revenue_os/`.
- `_already_succeeded` is a best-effort scan of the last 50 success logs (`acp2_orchestration.py`).
- Pause/kill gates run at **job entry** / recovery entry, **not** immediately before `executor()` (`acp3_durable_runtime.py`, `acp2_orchestration.run_work`).

Evidence supporting “no new Work SoT required”:

- Deterministic work identity already exists (`acp2:{kind}:{org}:{target}:{logical}`).
- PostgreSQL is the production DB (`render.yaml`).
- Session/transaction advisory locks and/or domain-row conditional updates can serialize claims **without** a lease table.
- ACP-3 reconciliation already classifies ambiguous external completion.
- Celery must remain dormant (compose-only; not on Render; tasks bypass ACP).

## Surfaces inspected

ACP-1 `acp1_autonomous_boundary.py` · ACP-2 work/orchestration/catalog/oversight · ACP-3 runtime/reconcile/scheduler gates · `scheduler.py` · `runner_api.py` · `database.py` · `activity_log.py` · `AgentActionLog` / `HeartbeatRun` · `ApprovalRequest` paths · Gmail sync · booking/calendar · `revenue_os/tasks/*` · `docker-compose.yml` · `render.yaml` · `Dockerfile`

## Persistence / async defaults (discovery)

| Decision | Value |
|----------|-------|
| New persistent Work/Task/Lease SoT | **NOT required** for minimum ACP-4 (prefer DB locks + fence) |
| `ACP4_PERSISTENCE_EXCEPTION_REQUIRED` | **NO** (unless implementation later proves locks insufficient) |
| Celery | **DORMANT** — keep dormant |
| `ACP4_ASYNC_RUNTIME_EXCEPTION_REQUIRED` | **NO** |
| Redis / broker | **NOT required** for ACP-4 control plane |
