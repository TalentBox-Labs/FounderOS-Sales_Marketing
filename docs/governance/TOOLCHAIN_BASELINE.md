# Toolchain Baseline

Sprint T0 — inventory; **T0.5** review; **T0.6** freeze amendments  
Date: 2026-08-09  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
CMS reference: `/Users/krishna/Documents/workcrew-cms-os` (read-only)

**Freeze record:** [TOOLCHAIN_BASELINE_v1_FREEZE.md](TOOLCHAIN_BASELINE_v1_FREEZE.md)  
Related: [TOOLCHAIN_DECISION_MATRIX.md](TOOLCHAIN_DECISION_MATRIX.md), [TOOLCHAIN_ROADMAP.md](TOOLCHAIN_ROADMAP.md), [T0_5_TOOLCHAIN_REVIEW.md](T0_5_TOOLCHAIN_REVIEW.md)

**No tools installed, dependencies changed, CI modified, or code changed in T0–T0.6.**

---

# Executive Summary

Founder OS runs a free/open-leaning toolchain: Git/GitHub Actions, Python/pip, pytest, FastAPI/Uvicorn, Docker Compose (Postgres + Redis + Celery), Alembic, CrewAI, pre-commit + **Gitleaks**, Vite/React, in-repo Prometheus-text metrics.

| Gap | Urgency | Canonical direction |
|-----|---------|---------------------|
| No Python lint/format gate | **NOW** | **Ruff** (APPROVE NOW; install PR pending; confirm OSS license at install) |
| Dependency CVE gate | LATER | pip-audit |
| Browser E2E | LATER | Playwright |
| Shared API collections | LATER | Bruno |
| Typing gate | LATER | mypy |
| Prod scrape/dashboards | LATER | Prometheus + Grafana |

**DEFAULT POLICY:** Prefer free/open-source tools. Paid tools require explicit Founder approval.  
**Paid tools approved: 0**

### Canonical selections (T0.6 overlap resolution)

| Concern | Canonical | Not preferred (not removed from policy lists) |
|---------|-----------|-----------------------------------------------|
| Python lint/format/imports | **Ruff** | Black + isort + flake8 (DEFER — redundant if Ruff ships) |
| Secret scanning in hooks | **Gitleaks** | detect-secrets (DEFER — redundant with Gitleaks) |

---

# Current Toolchain

| Tool | Purpose | Evidence | Version/config | Status |
|------|---------|----------|----------------|--------|
| Git | VCS | `.git/` | — | ACTIVE |
| GitHub | Hosting + PRs | `.github/workflows/test.yml` | Actions v4 | ACTIVE |
| Python | Runtime | Dockerfile `python:3.11-slim`; CI 3.11–3.13 | 3.10+ | ACTIVE |
| pip + requirements* | Packages | three requirements files | unpinned ranges | ACTIVE |
| pytest | Tests | `pytest.ini`, CI, pre-commit | ≥8.0.0 | ACTIVE |
| FastAPI TestClient / httpx | API tests | `tests/`, revenue reqs | httpx≥0.27 | ACTIVE |
| pre-commit | Local hooks | `.pre-commit-config.yaml` | — | ACTIVE |
| pre-commit-hooks | Key / large files | same | v5.0.0 | ACTIVE |
| Gitleaks | Secret scanning | pre-commit | v8.25.1 | ACTIVE (**canonical**) |
| Docker / Compose | Runtime | `Dockerfile`, `docker-compose.yml` | compose 3.9 | ACTIVE |
| PostgreSQL 14 | DB | compose | 14 | ACTIVE |
| SQLite | Local DB | `pytest_local.db` | — | TRANSITIONAL |
| Redis 7 | Broker | compose | 7 | ACTIVE |
| Celery + Beat | Tasks | compose + `revenue_os/tasks` | ≥5.3 | ACTIVE |
| Alembic / SQLAlchemy | Migrations / ORM | `alembic.ini`, reqs | — | ACTIVE |
| FastAPI / Uvicorn / Jinja2 | API + HTML | runner + templates | — | ACTIVE |
| CrewAI | Agents | `src/base_crew.py` | pin conflict GAP-007 | ACTIVE |
| Node / npm / Vite / React / axios | CRM SPA | `frontend/package.json` | Node 20 | ACTIVE |
| ChromaDB | Vector | revenue reqs | ≥1.1.0 | CONFIGURED |
| Ollama / OpenAI / Gemini | LLM | `.env.example` | — | ACTIVE / CONFIGURED |
| n8n bridge | Automation | `n8n_webhooks.py` | external | ACTIVE |
| Custom observability | Metrics | `src/observability.py` | Prometheus text | ACTIVE |
| Render | Deploy | `render.yaml` | — | CONFIGURED |
| Markdown + Obsidian | Docs | `docs/`, vault | — | ACTIVE |
| pytest-cov | Coverage | `COVERAGE.md` only | not in CI | CONFIGURED BUT UNUSED in CI |

---

# Approved Current Tools

**KEEP:** Git, GitHub Actions, Python, pip, pytest, TestClient/httpx, pre-commit, **Gitleaks**, Docker, Compose, PostgreSQL, Redis, Celery, Alembic, SQLAlchemy, FastAPI, Uvicorn, Jinja2, CrewAI, Vite/React/npm, ChromaDB (existing dep), Ollama/OpenAI/Gemini env, n8n bridge, in-repo metrics, Render config, Markdown/Obsidian, Google API client (existing Sheets path).

Ops hygiene (not a new tool): resolve CrewAI pin conflict (GAP-007).

---

# Add Now

| Tool | Reason | Cost at freeze |
|------|--------|----------------|
| **Ruff** | Lint/format/import gate; canonical over Black+isort+flake8 | **NOT VERIFIED** in-repo until install PR confirms OSS license |

*Not installed. Future tooling PR under Tool Governance Rule + license confirmation.*

---

# Add Later

| Tool | Introduction gate (T0.6 — measurable) |
|------|--------------------------------------|
| **Playwright** | Introduce when authenticated **browser mutation** tests become release-critical for Content Studio write UI or CRM SPA (not read-only pages). |
| **Bruno** | Introduce when a sprint requires **≥2 shared Git-tracked HTTP collection files** under the repo used by more than one engineer outside pytest. |
| **pip-audit** | Introduce when a security/pre-production sprint adds a **CI job that fails on known dependency CVEs** after requirements pin hygiene. |
| **Bandit** | Introduce when a security hardening sprint adds **Bandit as a CI or pre-commit check** with a defined rule set. |
| **Mermaid** | Introduce when a merged ADR or architecture doc includes at least **one committed ` ```mermaid ` diagram** as the source of truth for that figure. |
| **Prometheus** | Introduce when production requires **scraped time-series metrics** for service-level monitoring beyond on-demand `/api/v1/metrics/prometheus`. |
| **Grafana** | Introduce **together with Prometheus** when operators need persistent dashboards over scraped metrics. |
| **mypy** | Introduce when a quality sprint declares **mypy clean (or gated) for a named package path** as a release criterion. |
| **DBeaver Community** | Introduce when an operator task requires a **GUI against non-production Compose Postgres** and documents that `psql` is insufficient for that task. |
| **pytest-cov in CI** | Introduce when product policy requires a **coverage report or threshold artifact in GitHub Actions**. |

---

# Deferred / Rejected Tools

| Tool | Decision | Why | Canonical / alternative |
|------|----------|-----|-------------------------|
| Black / isort / flake8 | DEFER | Redundant with Ruff | **Ruff** canonical |
| detect-secrets | DEFER | Redundant with Gitleaks | **Gitleaks** canonical |
| MkDocs, PlantUML, OpenTelemetry, Loki, deptry/pipdeptree | DEFER | See freeze doc | Markdown / Mermaid / observability.py / Docker logs |
| Kubernetes, Airflow, Elasticsearch | REJECT | Compose / Celery / SQL+Chroma suffice | — |
| Zapier, Make.com, Jira, Confluence, paid APM, paid API suites | REJECT | Cost / duplicate | n8n, GitHub, docs, `/metrics` |
| LangChain | REJECT | CrewAI is AI stack | CrewAI |
| OpenClaw runtime; Flask CMS / Sheets SoT | REJECT | CMS reference only | Founder FastAPI + tracker |

---

# Security / Testing / Observability / Docs / Automation

Unchanged in role from T0; canonical secret scanner = **Gitleaks**; canonical lint path = **Ruff** (pending install).

---

# Tool Introduction Gates

See **Add Later** table above (T0.6 measurable gates).  
**Ruff:** tooling PR with config + CI/pre-commit; confirm OSS; no app behavior change.

---

# Tool Governance Rule

No new engineering tool may be added unless documented with:

Problem · Evidence · Alternatives · Free/paid status (confirmed) · Security · Operational impact · Rollback · Owner · Approval  

Maintainer may approve free/OSS KEEP/ADD. **Founder** must approve any PAID ONLY tool.

---

# Cost Policy

**DEFAULT POLICY:** Prefer free/open-source tools.  
**Paid tools require explicit Founder approval and documented justification.**

Candidate tools not yet in-repo: cost class **NOT VERIFIED** until install PR confirms license.  
**Paid tools approved: 0**
