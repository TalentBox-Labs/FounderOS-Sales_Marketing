# Founder OS ACP-4 — Celery Decision

## Status

**DORMANT** (for ACP commercial control plane)

| Signal | Evidence |
|--------|----------|
| Task modules exist | `revenue_os/tasks/{leads,outreach,agents}.py` |
| Broker config | `Celery(..., broker=REDIS_URL)` in `tasks/__init__.py` |
| Compose wiring | `docker-compose.yml` `worker` + `beat` |
| Render production | **No** Celery/Redis service in `render.yaml` |
| Dockerfile CMD | uvicorn only |
| ACP imports in tasks | **None** (no acp1/acp2/acp3/orchestrate) |
| ACP-3 tests | Assert celery not in acp3 runtime/scheduler sources |

Not `PRODUCTION_WIRED`. Compose presence ≠ ACP control plane.
Classify as **DORMANT** (substrate exists; unwired to ACP and unwired on Render).

## Default ACP-4 position

**KEEP_DORMANT**

## Celery activation required?

**NO**

## `ACP4_ASYNC_RUNTIME_EXCEPTION_REQUIRED`

**NO**

ACP-4 should extend the **in-process heartbeat + DB claim/fence** path, not activate Celery.

If a future milestone requires Celery, it must prove: org propagation, ACP-1 evaluate, claim/fence, idempotency, provenance, and no authority bypass — via a separate exception document.
