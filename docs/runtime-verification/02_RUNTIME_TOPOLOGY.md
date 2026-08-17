# 02 — Runtime Topology (Verified)

---

## Compose services (declared)

From `docker compose config --services`:

| Service | Declared role |
|---------|----------------|
| `db` | postgres:14 |
| `redis` | redis:7-alpine |
| `api` | uvicorn `runner_api:app` |
| `worker` | celery worker |
| `beat` | celery beat |

---

## Observed running containers (verification target)

| Logical service | Container name (observed) | State | Health |
|-----------------|---------------------------|-------|--------|
| API | `…-s-m-csm-os-api-1` | Up ~46h | healthy |
| Postgres | `…-s-m-csm-os-db-1` | Up ~46h | healthy |
| Redis | `…-s-m-csm-os-redis-1` | Up ~46h | healthy |
| Worker | `…-s-m-csm-os-worker-1` | Up ~46h | unhealthy* |
| Beat | `…-s-m-csm-os-beat-1` | Up ~46h | unhealthy* |

\*Docker health label unhealthy; process still responsive for worker ping (see below). Beat log shows start with no schedule activity observed.

Ports observed:

| Port | Binding |
|------|---------|
| 8000 | API |
| 5432 | Postgres |
| 6379 | Redis |

API entry command (Dockerfile / compose): `uvicorn runner_api:app --host 0.0.0.0 --port ${PORT:-8000}` — **VERIFIED** in running container command.

---

## Database

| Check | Result | Evidence |
|-------|--------|----------|
| Connectivity | CONNECTED | `pg_isready` accepting; `SELECT 1` ok |
| Engine | PostgreSQL | postgres:14 container |
| Alembic current | `e8278e1169e6 (head)` | `alembic current` inside API container |
| Migration DDL content | Empty upgrade body (known baseline) | Source migration file; not re-applied |

---

## Redis / Celery

| Check | Result | Evidence |
|-------|--------|----------|
| Redis ping | CONNECTED | `redis-cli ping` → `PONG` |
| Celery worker ping | CONNECTED | `celery … inspect ping` → `pong`, 1 node online |
| Registered tasks | PRESENT | `score_lead_background`, `bulk_enrich_leads`, `enrich_lead`, `schedule_outreach_sequence`, `send_email_task` |
| Celery Beat schedule map | NOT VERIFIED in code / empty activity | No `beat_schedule` in repo; beat process running |

---

## API health

| Method | Path | Status | Response evidence |
|--------|------|--------|-------------------|
| GET | `/health` | 200 | `{"status":"ok","service":"WorkCrew CMS OS"}` |
| GET | `/api/v1/health` | 200 | `{"overall":"healthy",…,"components":{},"healthy":0,"total":0}` |
| GET | `/health/debug` | 404 | `{"detail":"Not Found"}` |

Note: `/api/v1/health` shape matches metrics/system health style, not the frozen-baseline narrative of UI liveness `{status, service: "WorkCrew CMS OS API"}`. Classified in architecture delta.

---

## OpenAPI surface (runtime)

| Metric | Value |
|--------|-------|
| Paths | 161 |
| Operations | 171 |

Marketing paths registered: `/marketing`, `/marketing/generate`, `/marketing/dry-run`, `/marketing/publish`  
Webhook paths registered: `/api/v1/integrations/webhooks/subscribe|subscriptions|subscriptions/{id}`
