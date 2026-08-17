# Toolchain Decision Matrix

Sprint T0 inventory · T0.5 review · **T0.6 freeze**  
Date: 2026-08-09  
Baseline: [TOOLCHAIN_BASELINE.md](TOOLCHAIN_BASELINE.md) · Freeze: [TOOLCHAIN_BASELINE_v1_FREEZE.md](TOOLCHAIN_BASELINE_v1_FREEZE.md)

Cost class: repository evidence only. Candidates not in repo → **NOT VERIFIED** until install PR.

## Canonical overlap resolutions (T0.6)

| Concern | Canonical | Alternate not preferred | Why |
|---------|-----------|-------------------------|-----|
| Python lint/format/imports | **Ruff** (ADD NOW) | Black + isort + flake8 | One tool vs three; same concern; alternate remains DEFER only if Ruff blocked |
| Secret scanning in git hooks | **Gitleaks** (KEEP/ACTIVE) | detect-secrets | Already wired in `.pre-commit-config.yaml`; second scanner = noise |

No tools removed from the repository (none of the alternates were installed).

---

| Tool | Category | Status | Evidence | Decision | Timing | Cost Class | Owner | Reconsideration Trigger |
|------|----------|--------|----------|----------|--------|------------|-------|-------------------------|
| Git | VCS | ACTIVE | `.git/` | KEEP | — | FREE / OPEN SOURCE | Infrastructure | — |
| GitHub + Actions | CI/Hosting | ACTIVE | `test.yml` | KEEP | — | FREE TIER | Infrastructure / Testing | Leave GitHub |
| Python | Runtime | ACTIVE | Dockerfile, CI | KEEP | — | FREE / OPEN SOURCE | Shared Platform | — |
| pip / requirements* | Packages | ACTIVE | requirements files | KEEP | — | FREE / OPEN SOURCE | DX | Poetry/uv ADR |
| pytest | Testing | ACTIVE | pytest.ini, CI | KEEP | — | FREE / OPEN SOURCE | Testing | — |
| TestClient / httpx | API testing | ACTIVE | tests/ | KEEP | — | FREE / OPEN SOURCE | Testing | — |
| pre-commit | DX hooks | ACTIVE | config | KEEP | — | FREE / OPEN SOURCE | DX | — |
| **Gitleaks** | Security | ACTIVE | pre-commit v8.25.1 | KEEP | — | FREE / OPEN SOURCE | Security | **Canonical secret scanner** |
| pre-commit-hooks | Security | ACTIVE | config | KEEP | — | FREE / OPEN SOURCE | Security | — |
| Docker / Compose | Infra | ACTIVE | Dockerfile, compose | KEEP | — | FREE / OPEN SOURCE | Infrastructure | K8s only if multi-node |
| PostgreSQL / Redis / Celery | Data/tasks | ACTIVE | compose | KEEP | — | FREE / OPEN SOURCE | Shared / Automation | — |
| Alembic / SQLAlchemy | DB | ACTIVE | migrations | KEEP | — | FREE / OPEN SOURCE | Shared Platform | — |
| FastAPI / Uvicorn / Jinja2 | API/UI | ACTIVE | runner, templates | KEEP | — | FREE / OPEN SOURCE | Shared / DX | — |
| CrewAI | AI | ACTIVE | base_crew, reqs | KEEP | — | UNKNOWN | AI Platform | Pin fix; replace only via ADR |
| Vite / React / npm | Frontend | ACTIVE | frontend/ | KEEP | — | FREE / OPEN SOURCE | DX | — |
| ChromaDB | Vector | CONFIGURED | revenue reqs | KEEP | — | FREE / OPEN SOURCE | AI / Knowledge | Retire if unused post-audit |
| Ollama | Local LLM | ACTIVE env | .env.example | KEEP | — | FREE / OPEN SOURCE | AI Platform | — |
| OpenAI / Gemini | Cloud LLM | CONFIGURED | .env.example | KEEP | — | PAID ONLY (usage) | AI Platform | No new SaaS without Founder |
| n8n | Automation | ACTIVE bridge | webhooks | KEEP | — | FREE / OPEN SOURCE (self-host) | Automation | Founder-approved replace only |
| Custom observability | Metrics | ACTIVE | observability.py | KEEP | — | FREE / OPEN SOURCE | Observability | — |
| Render | Deploy | CONFIGURED | render.yaml | KEEP | — | UNKNOWN | Infrastructure | — |
| Markdown / Obsidian | Docs | ACTIVE | docs/, vault | KEEP | — | FREE / OPEN SOURCE | Documentation | — |
| **Ruff** | Lint/format | Approved | T0.5 APPROVE NOW | ADD NOW | Tooling PR | NOT VERIFIED until install | DX | Confirm OSS at install |
| Playwright | E2E | Candidate | ROADMAP mention | ADD LATER | Mutation E2E release-critical | NOT VERIFIED | Testing | See baseline gate |
| Bruno | API collections | Candidate | API surface growth | ADD LATER | ≥2 Git-tracked shared collections | NOT VERIFIED | Testing / DX | See baseline gate |
| pip-audit | Dep CVEs | Candidate | No CI audit | ADD LATER | CI CVE fail job | NOT VERIFIED | Security | See baseline gate |
| Bandit | SAST | Candidate | No SAST | ADD LATER | CI/pre-commit Bandit check | NOT VERIFIED | Security | See baseline gate |
| Mermaid | Diagrams | Candidate | docs volume | ADD LATER | ≥1 committed mermaid in ADR/arch doc | NOT VERIFIED | Documentation | See baseline gate |
| Prometheus | Metrics scrape | Candidate | /metrics/prometheus | ADD LATER | Scraped SLO/multi-instance prod | NOT VERIFIED | Observability | See baseline gate |
| Grafana | Dashboards | Candidate | pairs Prometheus | ADD LATER | With Prometheus | NOT VERIFIED | Observability | See baseline gate |
| mypy | Typing | Candidate | No typing gate | ADD LATER | Named package mypy release gate | NOT VERIFIED | DX | See baseline gate |
| DBeaver Community | DB GUI | Candidate | Compose Postgres | ADD LATER | Non-prod GUI; psql insufficient | NOT VERIFIED | Infrastructure | See baseline gate |
| pytest-cov in CI | Coverage | CONFIGURED unused | COVERAGE.md | ADD LATER | CI coverage artifact/threshold policy | NOT VERIFIED | Testing | See baseline gate |
| Black / isort / flake8 | Lint suite | Not installed | — | DEFER | — | FREE / OPEN SOURCE | DX | **Only if Ruff install blocked** |
| detect-secrets | Secrets | Not installed | — | DEFER | — | FREE / OPEN SOURCE | Security | Policy demands 2nd scanner |
| MkDocs / PlantUML / OTel / Loki / deptry | Various | — | — | DEFER | 12+ / cleanup | varies | Docs / Obs / DX | Per baseline |
| Kubernetes / Airflow / Elasticsearch | Infra | — | — | REJECT | — | varies | Infrastructure | Scale / DAG / search proof |
| Zapier / Make / Jira / Confluence / paid APM / paid API suites | SaaS | — | — | REJECT | — | PAID ONLY | — | Founder approval only |
| LangChain | AI | — | CrewAI present | REJECT | — | UNKNOWN | AI Platform | AI Platform ADR |
| OpenClaw / Flask+Sheets SoT | CMS | Reference | CMS / migration | REJECT | — | UNKNOWN | — | Never Editorial/CS SoT |

## Counts (frozen)

| Decision | N |
|----------|--:|
| KEEP | 32 |
| ADD NOW | 1 |
| ADD LATER | 10 |
| DEFER | 8 |
| REJECT | 10 |
