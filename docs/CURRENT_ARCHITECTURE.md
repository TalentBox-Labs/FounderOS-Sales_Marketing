# Current Architecture (pre-separation baseline)

This document describes the FounderOS / WorkCrew CRM repository **as it exists today**, before any repository separation work. It is the factual baseline for `docs/REPOSITORY_SEPARATION_REPORT.md` — nothing here is a design recommendation.

Stack note: this codebase is **FastAPI (Python) backend + Vite/React frontend**, not Next.js/Prisma. There is no TypeScript backend and no Prisma ORM anywhere in this repo.

## 1. Current repository structure

Single monorepo, `TalentBox-Labs/FounderOS-Sales_Marketing`, repo root as backend root:

```text
.
├── runner_api.py                 # FastAPI app entrypoint (root ASGI app)
├── runner_api_routers/           # 42 FastAPI router modules (API + legacy HTML routes)
├── revenue_os/                   # Core domain package (models, services, agents, auth, scheduler...)
├── src/                          # Separate, older CrewAI content-pipeline subsystem
├── templates/                    # 32 Jinja2 HTML templates (server-rendered legacy UI)
├── frontend/                     # Vite/React SPA — self-contained, own package.json
├── migrations/, alembic.ini      # DB migration tooling (Alembic; lightly used — see §5)
├── scripts/                      # Ops/dev scripts (fixture generation, etc.)
├── tests/                        # 119 Python test files (pytest) — backend-only; no frontend tests exist
├── docs/                         # Extensive architecture/governance documentation (Markdown only)
├── data/, input/, output/, obsidian_vault/, tracker.csv   # Runtime/working data, not source code
├── Dockerfile, docker-compose.yml, docker-compose.demo.yml, render.yaml   # Deployment
├── requirements.txt, requirements-api.txt, requirements-revenue.txt      # Python deps (split by concern, not by service)
├── .env.example                  # Backend env vars (frontend needs none of these — see §6)
└── .github/workflows/test.yml    # CI: pytest matrix (3.11/3.12/3.13) against Postgres
```

There is currently **no separate frontend repository** — `frontend/` is a subdirectory of this repo, already structurally self-contained (its own `package.json`, `vite.config.js`, lockfile) but not independently deployed.

## 2. Frontend components

Everything under `frontend/`:

```text
frontend/
├── index.html
├── package.json, package-lock.json     # react 18, react-router-dom 7, axios, vite 8
├── vite.config.js                      # dev-only /api proxy → localhost:8000; base: './' for relative asset paths
├── src/
│   ├── main.jsx, App.jsx, App.css
│   ├── api.js                          # single axios instance; all API calls go through this
│   ├── components/
│   └── pages/                          # Dashboard, Contacts, ContactDetail, Deals, DealDetail,
│                                        # Analytics, Marketing, Agents, Copilot (route-level pages)
```

- Client-side routing: `HashRouter` (from `react-router-dom`) — chosen specifically so the built SPA works when mounted at a sub-path (`/app`) without server-side route configuration.
- API communication: exactly one axios instance (`frontend/src/api.js`), base URL resolved as `VITE_API_BASE` env override → `/api` in dev (proxied by Vite) → same-origin in production build.
- Auth: a single `RUNNER_API_KEY`-style bearer token stored in `localStorage` (`crm_api_key`), attached via an axios request interceptor; a 401 response force-logs-out.
- No frontend test suite exists (`tests/` in the repo root is 100% Python/pytest).
- No frontend-specific CI job exists yet — `npm run build` is only invoked inside `Dockerfile`'s build stage, not in `.github/workflows/test.yml`.

## 3. Backend components

Everything else at the repo root is backend:

- **`runner_api.py`** — the FastAPI app object, root-level ASGI entrypoint (`uvicorn runner_api:app`). Registers ~35 routers, CORS/middleware, identity binding, and (in production) mounts the built frontend (`frontend/dist`) as static files at `/app` if present.
- **`runner_api_routers/`** (42 files) — one module per feature area: `crm.py`, `agents.py` (Sales Agent crew), `marketing_agents.py` (Marketing Agent crew), `identity.py`, `tenant.py`, `cockpit.py`, `operator_flow.py`, `manual_demand.py`, `qualified_demand.py`, `commercial_outcome.py`, `copilot.py`, `seo.py`, `knowledge_base.py`, `analytics_depth.py`, `content_studio.py`, `editorial.py`, `publishing.py`, `pipeline.py`, `integrations.py`, `whatsapp.py`, `ui.py` (server-rendered HTML pages, see below), `middleware.py`, `utils.py`, and more.
- **`revenue_os/`** — the core domain package: `models/` (SQLAlchemy ORM), `services/` (business logic — sales agents, marketing agents, approvals, tenant resolution, ACP1–4 governance layer, scheduler jobs), `agents/` (agent registry/orchestration), `auth.py`, `config.py`, `database.py`, `scheduler.py` (heartbeat background jobs), `automation/`, `analytics/`, `customer_success/`, `executive/`, `forecasting/`, `integrations/` (Gmail, WhatsApp, LinkedIn/Proxycurl, n8n, public sources), `marketing/` (email automation, lead nurturing), `reporting/`, `tasks/` (Celery task definitions), `static/`.
- **`src/`** — a separate, older CrewAI-based content-generation pipeline (blog/social content crews: `sdr_crew.py`, `marketing_crew.py`, `editor_crew.py`, `qa_crew.py`, `csm_crew.py`, `generation_crew.py`, `distribution_crew.py`, `artifact_crew.py`, `base_crew.py`, plus `*.yaml` agent/task configs and `tools/`). This predates `revenue_os/` and is still live — e.g. `runner_api_routers/marketing.py`'s `/marketing/generate` endpoint shells out to `src.marketing_crew`.
- **`templates/`** — 32 Jinja2 HTML files, rendered server-side by `runner_api_routers/ui.py` (login, cockpit, operator, dashboard, marketing, analytics, MCP, founder command/approvals/activity pages, etc.). This is a **second, independent frontend** that ships inside the backend process — not part of the React SPA, and not optional (it's the primary UI for several founder/operator flows; the React SPA is scoped mainly to the CRM contacts/deals/marketing/agents surface).
- **`migrations/` + `alembic.ini`** — Alembic is configured but lightly used; most schema evolution in this codebase actually happens via `Base.metadata.create_all()` (new tables) plus a hand-rolled `_migrate_missing_columns()` raw-SQL helper in `runner_api.py` (new columns on existing tables), not through generated Alembic migration scripts.
- **`scripts/`** — dev/ops scripts, e.g. `generate_week_fixtures.py` (used by both the pre-commit hook and CI's "Verify fixture sync" step).
- **`tests/`** (119 files) — pytest, backend-only. Config in `pytest.ini` (`testpaths = tests`, `pythonpath = .`).
- Background jobs: two systems coexist —
  1. `revenue_os/scheduler.py`'s in-process `HeartbeatScheduler` (started on app boot unless `HEARTBEAT_ENABLED=0`), governed by the ACP2/ACP3/ACP4 layer (per-org gated `WorkItem`s).
  2. Celery (`revenue_os.tasks.celery_app`, `revenue_os/tasks/{agents,leads,outreach}.py`), run as separate `worker`/`beat` processes per `docker-compose.yml`, backed by Redis.

## 4. Shared components

There is **no shared source code** between frontend and backend — no shared types, no shared validation schemas, no shared constants package. This is expected for a Python-backend + JS-frontend split (unlike a TS-everywhere monorepo, there's no language-level sharing to begin with). The only "shared contract" is the implicit HTTP/JSON API surface itself, which is not currently formalized as a versioned schema (no OpenAPI client generation step, no shared `.d.ts`/pydantic-to-TS pipeline).

Nothing in this repo needs classification as "needs extraction into a shared package" — there is nothing eligible.

## 5. Database dependencies

- **Primary DB**: PostgreSQL 14 in production/CI (`docker-compose.yml`, `.github/workflows/test.yml`); SQLite is used as a local/test-only fallback (`revenue_os/database.py` picks the dialect from `DATABASE_URL`; tests default to a SQLite file when `DATABASE_URL` isn't set).
- **ORM**: SQLAlchemy (not Prisma). Models are plain declarative classes under `revenue_os/models/`.
- **Schema evolution**: `Base.metadata.create_all()` (new tables, run at app startup) + `_migrate_missing_columns()` (a hand-written `ALTER TABLE ADD COLUMN` helper in `runner_api.py`) is the operative mechanism today. Alembic (`alembic.ini`, `migrations/`) exists in the repo but is not the primary path — worth flagging in `docs/POST_SEPARATION_TECH_DEBT.md` (two competing migration mechanisms) rather than "fixing" here.
- **Vector store**: Chroma (`data/chroma_db/`, mounted as a Docker volume) for the CrewAI/RAG pieces.
- The frontend has **zero direct database access** — it only ever talks to the backend over HTTP.

## 6. Environment variables

Backend (`.env.example`, ~50 vars): `SECRET_KEY` (required, no insecure default — app raises `FATAL` at import time if unset), `DATABASE_URL`, `RUNNER_API_KEY`, `OPENAI_API_KEY`/`GEMINI_API_KEY`, `SLACK_*`, `STRIPE_API_KEY`, `N8N_*`, `HEARTBEAT_ENABLED`, `FOUNDER_OS_*` (login/bootstrap/cookie config), `ACCESS_TOKEN_EXPIRE_MINUTES`, `HASHNODE_*`, `LINKEDIN_*`, `INSTAGRAM_*`, `YOUTUBE_*`, `HERMES_*`/`OPENCLAW_*` (external agent backends), `PROSPECT_*` thresholds, `CLOUDFLARE_*`, `WORKCREW_CREWAI_*` (Ollama/local LLM config for `src/`'s crews).

Frontend: **exactly one** optional variable, `VITE_API_BASE` (referenced in `frontend/src/api.js`; not currently declared in any `.env.example` because the default same-origin behavior covers the only production deployment today). No secrets of any kind live in the frontend.

## 7. External services

OpenAI/Gemini (LLM), Ollama (local LLM for `src/`'s crews), Gmail (OAuth, inbox sync), WhatsApp Cloud API (Meta), LinkedIn (Proxycurl enrichment + OAuth posting), Instagram/YouTube/Hashnode (publishing), n8n (workflow webhooks), Slack, Stripe, Reddit + Hacker News (public search APIs, unauthenticated), Cloudflare Pages (a separate, docs-referenced static-site deployment path unrelated to this app's own frontend), Redis (Celery broker), Postgres, Chroma.

## 8. API communication

Frontend → backend: HTTP/JSON only, via the single axios instance in `frontend/src/api.js`. No GraphQL, no websockets, no server actions (this isn't Next.js — there's no RSC/server-action mechanism to worry about). All 42 `runner_api_routers/*.py` modules are mounted onto the one `runner_api.py` FastAPI app; there is no separate "backend service" the frontend calls indirectly — the frontend calls the same process that also serves the legacy Jinja templates.

## 9. Authentication flow

Two parallel auth surfaces exist:
1. **Legacy/CRM bearer-token auth** (`RUNNER_API_KEY`): the React frontend and some older endpoints check a single shared bearer token via `_verify_api_key` (`runner_api_routers/utils.py`). This is what `frontend/src/api.js` implements (`crm_api_key` in `localStorage`).
2. **SaaS S1+ session/tenant auth**: cookie-based login (`/login`, session tokens, `revenue_os/auth.py` — `create_access_token`/`hash_password`/`verify_password`), resolved per-request into a `TenantContext` (`revenue_os/services/tenant_resolution.py`) that most newer endpoints (sales agents, marketing agents, approvals) require via `require_tenant_context()`. This is what the Jinja-templated founder/operator/cockpit pages use, gated by `founder_login_redirect()`.

These two systems currently coexist on the same endpoints in places (e.g. `_verify_api_key` as a `Depends()` alongside a separate `require_tenant_context()` call inside the handler body) — this dual-auth-system reality is itself worth a `docs/POST_SEPARATION_TECH_DEBT.md` entry, not a fix here.

## 10. Build commands

- Backend: no build step — `pip install -r requirements.txt -r requirements-api.txt -r requirements-revenue.txt`, then run directly (`uvicorn runner_api:app`).
- Frontend: `cd frontend && npm ci && npm run build` (outputs `frontend/dist/`, consumed either by `Dockerfile`'s multi-stage copy into the backend image, or served via `npm run dev`/`vite preview` standalone).

## 11. Test commands

- Backend: `python -m pytest tests/ -q` (pytest.ini scopes to `tests/`, `pythonpath = .` so imports resolve from repo root). CI additionally runs `python scripts/generate_week_fixtures.py --verify`.
- Frontend: none exist today (no test runner configured in `frontend/package.json`).
- Pre-commit (`.pre-commit-config.yaml`): `detect-private-key`, `gitleaks`, the fixture-verify script, and the full pytest suite — all backend-scoped, all run from repo root assuming `./.venv/bin/python` exists there.

## 12. Deployment process

**Single-image, single-service deployment** — this is the most consequential fact for any separation plan:

- `Dockerfile` is a two-stage build: stage 1 (`node:20-slim`) runs `npm ci && npm run build` inside `frontend/`; stage 2 (`python:3.11-slim`) installs backend deps, copies the whole repo in, then copies stage 1's `frontend/dist` into `./frontend/dist`.
- `runner_api.py` mounts `frontend/dist` as static files at `/app` if the directory exists at runtime — meaning the running Python process serves both the API and the built SPA from one port.
- `render.yaml` deploys this Dockerfile as **one** Render web service (`founderos-backend`) plus one managed Postgres database. There is no separate frontend static-site service in the current Render blueprint.
- `docker-compose.yml` (local/self-hosted) runs `db` (Postgres), `redis`, `api` (this same Dockerfile), `worker` and `beat` (Celery, same Dockerfile, different `command:`) — four containers, but only one built image.
- CI (`.github/workflows/test.yml`) only builds/tests the backend (pytest matrix against a Postgres service container); it does not build or test the frontend at all today.

## 13. Dependencies between frontend and backend

- **Runtime**: the frontend's production build is physically embedded inside the backend's Docker image and served by the same process (§12) — this is the one true "coupling" a separation must decide how to handle (two independently deployed services vs. keep the same build-then-embed step but from two repos).
- **Source-level**: none. The frontend never imports backend Python code, and the backend never imports frontend JS. `frontend/` could be `git mv`'d out to a new repo today with zero import-graph changes on either side.
- **Config-level**: `vite.config.js`'s `base: './'` and the `/app` static-mount path in `runner_api.py` are the only two places that encode "the frontend is served from within the backend" as an assumption; both would need to stay in sync (or be revisited) if deployment topology changes.
