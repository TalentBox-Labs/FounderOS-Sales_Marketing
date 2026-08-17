# 13 — Architecture Gaps (Evidence-Backed Observations)

This is the only file in the package that records observations.  
Each item includes evidence, affected files, and why it may matter.  
No redesign proposals.

---

## GAP-001 — Alembic migration contains no DDL

**Severity:** HIGH

**Evidence:**  
`migrations/versions/e8278e1169e6_full_schema.py` defines `upgrade()` / `downgrade()` with only `pass`. Revision message is `full_schema`.

**Affected files:**  
`migrations/versions/e8278e1169e6_full_schema.py`, `alembic.ini`

**Why it may matter:**  
Schema creation appears to rely on `Base.metadata.create_all` and ad-hoc startup `ALTER TABLE` patches rather than versioned migration operations.

---

## GAP-002 — Dual FastAPI applications with overlapping routes

**Severity:** MEDIUM

**Evidence:**  
- `runner_api.py` defines `app = FastAPI(title="WorkCrew CMS OS API")` and includes routers.  
- `revenue_os/main.py` defines a separate `app = FastAPI(title="Revenue OS")`.  
- Docker/Render start `runner_api:app`.  
- `runner_api.py` also still declares `@app.get`/`@app.post` handlers that overlap router paths (prospecting, orchestration, marketing, HTML pages).

**Affected files:**  
`runner_api.py`, `revenue_os/main.py`, `Dockerfile`, `runner_api_routers/*`

**Why it may matter:**  
Operators may be unclear which app is canonical; duplicate route definitions can shadow or confuse OpenAPI and tests depending on registration order.

---

## GAP-003 — Marketing generate subprocess module path not found as a file

**Severity:** HIGH

**Evidence:**  
`runner_api_routers/marketing.py` runs:
`python -m revenue_os.agents.marketing_crew ...`  
Inventory found `src/marketing_crew.py` but **no** `revenue_os/agents/marketing_crew.py` file.

**Affected files:**  
`runner_api_routers/marketing.py`, `src/marketing_crew.py`, `revenue_os/agents/`

**Why it may matter:**  
`POST /marketing/generate` may fail at runtime with module-not-found unless the module exists outside the searched tree or is generated dynamically (neither evidenced).

---

## GAP-004 — Celery beat service without evidenced beat schedule map

**Severity:** MEDIUM

**Evidence:**  
`docker-compose.yml` defines service `beat` with  
`celery -A revenue_os.tasks.celery_app beat`.  
`revenue_os/tasks/__init__.py` configures serializers/timezone/acks but no `beat_schedule` was found in that file.

**Affected files:**  
`docker-compose.yml`, `docker-compose.demo.yml`, `revenue_os/tasks/__init__.py`

**Why it may matter:**  
Beat process may start with an empty schedule while recurring work instead runs in the in-process heartbeat scheduler.

---

## GAP-005 — Auth disabled when `RUNNER_API_KEY` unset

**Severity:** MEDIUM

**Evidence:**  
`runner_api_routers/utils.py::_verify_api_key` returns `None` when env key is empty, skipping 401.

**Affected files:**  
`runner_api_routers/utils.py`, all routes using `Depends(_verify_api_key)`

**Why it may matter:**  
Local/demo deployments without the env var expose API routes without Bearer auth.

---

## GAP-006 — Two distinct auth systems

**Severity:** INFO

**Evidence:**  
Runner uses API key (`RUNNER_API_KEY`).  
`revenue_os.api.v1` uses JWT (`revenue_os/auth.py`) via `Depends(get_current_user)`.

**Affected files:**  
`runner_api_routers/utils.py`, `revenue_os/auth.py`, `revenue_os/api/v1/__init__.py`

**Why it may matter:**  
Clients of the combined `runner_api` app and the standalone `revenue_os.main` app authenticate differently.

---

## GAP-007 — Requirements version overlap for CrewAI

**Severity:** LOW

**Evidence:**  
`requirements.txt` pins `crewai>=0.80.0`.  
`requirements-revenue.txt` pins `crewai>=1.9.0`.  
Docker installs all three requirements files together.

**Affected files:**  
`requirements.txt`, `requirements-revenue.txt`, `Dockerfile`

**Why it may matter:**  
Resolved CrewAI version depends on pip merger behavior; tests/CI currently install only `requirements.txt` per workflow file.

---

## GAP-008 — CI installs subset of dependencies

**Severity:** MEDIUM

**Evidence:**  
`.github/workflows/test.yml` runs `pip install -r requirements.txt` only (not `requirements-api.txt` / `requirements-revenue.txt`).  
Many API/DB tests import FastAPI/SQLAlchemy packages that are declared in the other requirement files.

**Affected files:**  
`.github/workflows/test.yml`, `requirements*.txt`, `tests/*`

**Why it may matter:**  
CI environment may differ from Docker runtime dependency set; outcomes depend on transitive installs or preinstalled runners.

---

## GAP-009 — Coverage document is a historical snapshot

**Severity:** INFO

**Evidence:**  
`COVERAGE.md` dated 2026-06-11 reports 140 passed and 44% coverage.

**Affected files:**  
`COVERAGE.md`

**Why it may matter:**  
Current suite size (41 modules / 223 test defs) no longer matches that snapshot’s “140 passed” figure; coverage numbers may be stale.

---

## GAP-010 — Empty / pass-through webhook shim risk

**Severity:** LOW

**Evidence:**  
`revenue_os/main.py` includes `webhooks_router` from `revenue_os.integrations.webhooks`.  
File presence: `revenue_os/integrations/webhooks.py` (imported). Content depth not fully enumerated here beyond import usage.

**Affected files:**  
`revenue_os/integrations/webhooks.py`, `revenue_os/main.py`

**Why it may matter:**  
If the router is an empty shim, standalone Revenue OS webhook surface may be narrower than docs imply.  
**Repository evidence not found** in this audit pass for a complete route list inside that shim beyond the import.

---

## GAP-011 — SQLite and Postgres dual dialect support in startup migrations

**Severity:** INFO

**Evidence:**  
`runner_api.py` `_migrate_missing_columns` branches on `postgresql` vs `sqlite`.  
`pytest_local.db` exists at repo root.

**Affected files:**  
`runner_api.py`, `pytest_local.db`

**Why it may matter:**  
Local tests and production Postgres may exercise different DDL capabilities for the same models.

---

## GAP-012 — Legacy `.old` crew files retained

**Severity:** LOW

**Evidence:**  
Files present: `src/artifact_crew.py.old`, `distribution_crew.py.old`, `editor_crew.py.old`, `generation_crew.py.old`, `marketing_crew.py.old`.

**Affected files:**  
`src/*.py.old`

**Why it may matter:**  
Duplicate historical implementations may confuse navigation; they are not imported by current module names ending in `.old`.

---

## GAP-013 — Anthropic/Claude provider wiring

**Severity:** INFO

**Evidence:**  
OpenAI and Gemini keys appear in settings/MCP hub. CrewAI/Ollama env vars appear in `.env.example` and `base_crew.py`.  
Dedicated Anthropic client module / `ANTHROPIC_API_KEY` usage: **Repository evidence not found**.

**Affected files:**  
N/A (absence)

**Why it may matter:**  
Documentation or product language mentioning Claude/Anthropic is not backed by a first-class integration module in this tree.
