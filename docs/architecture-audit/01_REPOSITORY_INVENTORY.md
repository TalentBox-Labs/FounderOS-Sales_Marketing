# 01 — Repository Inventory

Evidence source: local filesystem inspection of repository root  
`/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
Date of inspection: repository state as present on disk at audit time.

---

## Repository root structure (depth ≤ 3)

```
.
├── .github/
│   └── workflows/
│       └── test.yml
├── data/
│   ├── runtime_config.json
│   └── week_runtime/
│       └── W*.json
├── docs/
│   ├── API.md
│   ├── *.md (product/domain docs)
│   └── architecture-audit/   (this package)
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── api.js
│       ├── pages/
│       └── components/
├── input/
│   └── W*/
│       ├── 02_SEO_Plan.md
│       ├── 03_Research.md
│       ├── 04_Draft.md
│       ├── 05_Final.md
│       └── 09_Publish_Checklist.md
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   ├── README
│   └── versions/
│       └── e8278e1169e6_full_schema.py
├── obsidian_vault/
│   ├── 00 - Dashboard/
│   ├── 02 - Weeks/
│   ├── 03 - AI Logs/
│   ├── 04 - QA Reports/
│   ├── 05 - SEO & Research/
│   ├── 06 - Audience & Personas/
│   ├── 07 - Brand Voice/
│   ├── 08 - System Notes/
│   └── templates/
├── output/
│   ├── marketing/
│   ├── qa_reports/
│   ├── sales/
│   └── pipeline_orchestrator_run.json
├── revenue_os/
│   ├── api/v1/
│   ├── agents/
│   ├── analytics/
│   ├── automation/
│   ├── customer_success/
│   ├── executive/
│   ├── forecasting/
│   ├── integrations/
│   ├── marketing/
│   ├── models/
│   ├── pipeline/
│   ├── reporting/
│   ├── services/
│   ├── static/
│   ├── tasks/
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── scheduler.py
├── runner_api_routers/
│   └── *.py (API routers)
├── scripts/
│   ├── bootstrap_remaining_weeks.py
│   ├── clear_demo_data.py
│   ├── generate_week_fixtures.py
│   ├── init_demo_db.py
│   ├── sheets_copy_mirror_values.gs
│   └── sync_obsidian_vault.py
├── src/
│   ├── tools/
│   ├── *.py (crews, contracts)
│   └── *.yaml (agents/tasks)
├── templates/
│   └── *.html (Jinja2 UI)
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── alembic.ini
├── docker-compose.yml
├── docker-compose.demo.yml
├── Dockerfile
├── pytest.ini
├── render.yaml
├── requirements.txt
├── requirements-api.txt
├── requirements-revenue.txt
├── runner_api.py
├── tracker.csv
├── .env.example
├── .pre-commit-config.yaml
├── README.md
├── DEPLOYMENT.md
├── DEMO_SETUP.md
├── ROADMAP.md
└── COVERAGE.md
```

---

## Top-level folders

| Path | Present |
|------|---------|
| `.github/` | Yes |
| `data/` | Yes |
| `docs/` | Yes |
| `frontend/` | Yes |
| `input/` | Yes |
| `migrations/` | Yes |
| `obsidian_vault/` | Yes |
| `output/` | Yes |
| `revenue_os/` | Yes |
| `runner_api_routers/` | Yes |
| `scripts/` | Yes |
| `src/` | Yes |
| `templates/` | Yes |
| `tests/` | Yes |

---

## Technology stack (from requirements and config files)

### Languages
- Python (primary; `*.py` count under repo excluding `.venv`: **227**)
- JavaScript / JSX (`frontend/`)
- YAML (`src/*.yaml`, CI, compose)
- HTML (Jinja2 `templates/`, `frontend/index.html`)
- Markdown (content under `input/`, `docs/`, `obsidian_vault/`)
- Google Apps Script (`.gs` under `scripts/`)

### Frameworks / libraries (declared)
From `requirements.txt`:
- `crewai`, `crewai-tools`
- `pandas`, `PyYAML`, `pytest`
- `google-api-python-client`, `google-auth`, `google-auth-httplib2`
- `python-dotenv`

From `requirements-api.txt`:
- `fastapi`, `uvicorn[standard]`, `jinja2`

From `requirements-revenue.txt`:
- `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg2-binary`, `asyncpg`, `alembic`, `pydantic[email]`, `python-dotenv`, `httpx`, `bcrypt`, `python-jose[cryptography]`, `celery[redis]`, `redis`, `chromadb`, `crewai`

From `frontend/package.json`:
- `react`, `react-dom`, `react-router-dom`, `axios`
- Build: `vite`, `@vitejs/plugin-react`

### Docker
- `Dockerfile` — multi-stage: Node 20 frontend build + Python 3.11-slim API; CMD `uvicorn runner_api:app`
- `docker-compose.yml` — services: `db` (postgres:14), `redis` (redis:7-alpine), `api`, `worker` (Celery), `beat` (Celery beat)
- `docker-compose.demo.yml` — demo variants of the same services

### CI/CD
- `.github/workflows/test.yml` — pytest on Python 3.11/3.12/3.13; fixture verify via `scripts/generate_week_fixtures.py --verify`
- `render.yaml` — Render.com blueprint: Docker web service + managed Postgres
- `.pre-commit-config.yaml` — detect-private-key, large files, gitleaks, fixture-verify, pytest

### Package managers
- pip (`requirements*.txt`)
- npm (`frontend/package.json`, `package-lock.json`)
- README mentions Poetry as alternative; **no `pyproject.toml` / `poetry.lock` found in repository root**

### Build tools
- Vite (`frontend/`)
- Docker build
- Alembic (`alembic.ini`, `migrations/`)

### Configuration files
| File | Role (as named / used) |
|------|------------------------|
| `alembic.ini` | Alembic config; `script_location = migrations` |
| `pytest.ini` | `testpaths = tests`, `pythonpath = .` |
| `data/runtime_config.json` | Runtime week/config (referenced by tools) |
| `data/week_runtime/*.json` | Per-week runtime profiles |
| `tracker.csv` | Content week tracker |
| `render.yaml` | Render deploy blueprint |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `src/agents*.yaml`, `src/tasks*.yaml` | CrewAI agent/task configs |

### Environment files
- `.env.example` present
- Documented keys include: `WORKCREW_CREWAI_*`, Google Sheets, Hashnode, LinkedIn, Instagram, YouTube, Hermes/OpenClaw, prospecting, `OPENAI_API_KEY`, `GEMINI_API_KEY`, Slack, Stripe, n8n
- Additional env vars referenced in code/compose: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `RUNNER_API_KEY`, `HEARTBEAT_ENABLED`, `CORS_ALLOWED_ORIGINS`, `PORT`

### Testing frameworks
- `pytest` (`pytest.ini`, `tests/`, CI, pre-commit)
- FastAPI `TestClient` usage in tests (e.g. `tests/conftest.py`)
- Coverage report document: `COVERAGE.md` (snapshot dated 2026-06-11)

---

## Major executable entry points (repository evidence)

| Entry | Evidence |
|-------|----------|
| `uvicorn runner_api:app` | `Dockerfile` CMD; primary combined API |
| `revenue_os.main:app` | FastAPI app in `revenue_os/main.py` |
| `python -m src.main` | CLI validation pipeline |
| `python -m src.tools.pipeline_orchestrator` | Full pipeline + JSON summary |
| `python -m src.tools.pipeline_runner` | Validators |
| `python -m src.generation_crew` | Generation crew CLI |
| `python -m src.editor_crew` | Editor crew CLI |
| `celery -A revenue_os.tasks.celery_app worker` | `docker-compose.yml` worker |
| `celery -A revenue_os.tasks.celery_app beat` | `docker-compose.yml` beat |
| `npm run dev` / `npm run build` | `frontend/package.json` |
| Scripts under `scripts/` | Demo DB init, fixtures, Obsidian sync |

---

## File counts (approximate, excluding `.venv` / `.git`)

| Metric | Count |
|--------|-------|
| Selected source-like files (`*.py`, `*.jsx`, `*.js`, `*.yaml`, `*.yml`, `*.md`, `*.html`) | 498 |
| Python files | 227 |
| Test modules `tests/test_*.py` | 41 |
| Test function definitions (`test_*`) | 223 |

---

## Disk size

`du -sh` on repository root reported **1.1G** (includes local artifacts such as `.venv`, databases, and `output/` as present on disk).
