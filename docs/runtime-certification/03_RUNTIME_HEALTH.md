# 03 — Runtime Health (Sprint D1)

Date: 2026-08-09  
Stack: existing Compose containers (`…-csm-os-*`), ~46 hours uptime (same topology as Sprint C)

---

## Docker services

| Service | Status | Notes |
|---------|--------|-------|
| api | Up (healthy) | `:8000` |
| db | Up (healthy) | `:5432` — `pg_isready` accepting connections |
| redis | Up (healthy) | `:6379` — `PONG` |
| worker | Up (**unhealthy**) | Process running; Docker health label unhealthy (Known Sprint C) |
| beat | Up (**unhealthy**) | Process running; Docker health label unhealthy (Known Sprint C) |

Compose rebuild was not performed in D1 (certification-only; no feature/ops changes).

---

## D1.6 — Database

| Check | Result |
|-------|--------|
| Connectivity | PASS — `pg_isready` accepting connections |
| Alembic heads (repo) | `e8278e1169e6 (head)` |
| Alembic current (local sqlite cert DB) | `e8278e1169e6 (head)` |
| Schema drift / new migration required for D1 | **None** — D0 did not touch models/migrations |
| Host alembic against Docker Postgres credentials | Not fully authenticated from host with guessed DSN (Environment); DB service itself healthy |

**Database status for baseline:** CONNECTED / no migration required for D0/D1.

---

## D1.7 — Redis / Celery

| Check | Result |
|-------|--------|
| Redis | HEALTHY — `PONG` |
| Worker functional ping | PASS — `celery -A revenue_os.tasks.celery_app inspect ping` → `pong` |
| Worker Docker health | unhealthy (Known) |
| Beat Docker health | unhealthy (Known) |
| Registered tasks | PASS — 5 tasks: `score_lead_background`, `bulk_enrich_leads`, `enrich_lead`, `schedule_outreach_sequence`, `send_email_task` |

Note: incorrect probe module `revenue_os.automation.celery_app` fails; live containers use `revenue_os.tasks.celery_app` (matches container CMD).

---

## D1.8 — Runtime health signals

| Signal | Observation |
|--------|-------------|
| Startup | API healthy; continuous healthchecks 200 |
| Memory (docker stats) | api ~251 MiB; worker ~504 MiB; beat ~66 MiB; db ~30 MiB; redis ~10 MiB — within host limits |
| Logs | API access logs show repeated `GET /health 200`; no flood of unhandled marketing-router import crashes on health path |
| Unhandled exceptions | Marketing **UI** template raises `UndefinedError: integration_status` (Known); marketing **generate** on Docker still ModuleNotFound (pre-D0 image) |

---

## Runtime status summary

**PARTIAL**

- Core: API / DB / Redis healthy  
- Celery: functionally pingable + tasks registered; health labels unhealthy  
- Docker API image lagging D0 fix  
- Marketing HTML UI template gap remains
