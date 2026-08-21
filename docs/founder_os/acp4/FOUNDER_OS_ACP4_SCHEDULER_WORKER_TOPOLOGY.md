# Founder OS ACP-4 — Scheduler / Worker Topology

## Evidence summary

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 1 | What process owns scheduler execution? | The **API process** (`runner_api:app`) that runs uvicorn and starts heartbeat on startup | `runner_api.py` `@app.on_event("startup")` → `initialize_heartbeat()` |
| 2 | Can more than one scheduler run? | **YES** — one in-memory `HeartbeatScheduler` **per process**; N replicas ⇒ N schedulers | module singleton `scheduler = HeartbeatScheduler()`; no leader election |
| 3 | Can scheduler intervals overlap? | **Same process:** soft — `last_run_at` set at job **start**; jobs in a tick run **sequentially** via `to_thread`. **Cross process:** **YES**, full overlap | `scheduler.py` `_loop` / `run_job_now` |
| 4 | Does scheduler execute work inline? | **YES** — job function runs in thread pool of the API event loop; no external queue | `await asyncio.to_thread(self.run_job_now, …)` |
| 5 | Is work ever queued externally? | **Not for ACP path.** Celery exists in compose but is **not** ACP-wired; Render has no worker | `render.yaml` web+Postgres only; `docker-compose.yml` has worker/beat |
| 6 | Can multiple Python processes execute the same logical work? | **YES** today | dual heartbeats + shared Postgres + no claim |
| 7 | Leader election? | **NO** | no code |
| 8 | Scheduler lock? | **NO** distributed; `HeartbeatRun` is audit only | `HeartbeatRun` insert does not gate peers |
| 9 | Distributed mutex? | **NO** | no advisory/`FOR UPDATE` in `revenue_os/` |
| 10 | Claim/lease primitive? | **NO** | WorkItem in-memory only |
| 11 | Can reconciliation overlap itself? | **YES** across processes (`acp3_reconcile` every 1800s default, no lock) | `HEARTBEAT_ACP3_RECONCILE_SEC` |
| 12 | Scheduler + reconciliation same work? | **YES** — e.g. `score_new_leads` and `acp3_reconcile` both can target lead_score units | scheduler registration |

## Topology diagram

```
[Render / Docker web]
   uvicorn runner_api:app   (default: single worker in Dockerfile)
        │
        ├── HTTP handlers
        └── HeartbeatScheduler (asyncio loop, 30s poll)
                 ├── score_new_leads
                 ├── scan_follow_up_eligibility
                 ├── check_deals_at_risk
                 ├── sync_gmail_inbox
                 ├── snapshot_pipeline_metrics
                 ├── hermes_goal_check
                 └── acp3_reconcile
                        │
                        ▼
                 shared PostgreSQL
                 (AgentActionLog, Approvals, CRM)

[Compose optional]
   celery worker / beat  → DORMANT for ACP (bypass risk if manually enabled)
```

## Worker topology (ACP sense)

There is **no** first-class worker fleet for ACP. “Workers” today = **API processes hosting heartbeat** (and optionally humans deciding approvals on the same API). Scaling web replicas scales autonomous executors unintentionally.

## Operational implication

Single-replica deployment reduces collision probability but is **not** a runtime guarantee. ACP-4 must assume multi-process.
