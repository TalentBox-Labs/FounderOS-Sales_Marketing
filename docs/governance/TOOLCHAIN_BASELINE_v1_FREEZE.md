# Toolchain Baseline v1.0 — Freeze

Sprint T0.6 — Documentation only  
Date: 2026-08-09  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`

Preceding: T0 inventory · T0.5 review · T0.6 overlap + gate cleanup  
Living docs: [TOOLCHAIN_BASELINE.md](TOOLCHAIN_BASELINE.md), [TOOLCHAIN_DECISION_MATRIX.md](TOOLCHAIN_DECISION_MATRIX.md), [TOOLCHAIN_ROADMAP.md](TOOLCHAIN_ROADMAP.md)

**No code, dependency, CI, Docker, runtime, or Git operations in T0.6.**

---

# Executive Summary

| Metric | Value |
|--------|------:|
| Current tools (inventory) | 35 |
| KEEP | 32 |
| ADD NOW approved | 1 (Ruff — not yet installed) |
| ADD LATER | 10 |
| Overlap risks resolved | 2 |
| Introduction gates updated | 3 |
| High security risks | 0 |
| Paid tools approved | 0 |
| Code / runtime / dependency changes | 0 |
| Architecture | UNCHANGED |

This document freezes the Founder OS engineering toolchain policy for the next planning horizon (12–18 months), subject to documented introduction gates and the Tool Governance Rule.

---

# Approved Current Tools

**KEEP (active / configured):**

Git · GitHub Actions · Python · pip / requirements\* · pytest · FastAPI TestClient / httpx · pre-commit · **Gitleaks** · pre-commit-hooks (private-key / large-files) · Docker · Docker Compose · PostgreSQL · Redis · Celery (+ Beat) · Alembic · SQLAlchemy · FastAPI · Uvicorn · Jinja2 · CrewAI · pandas / PyYAML / python-dotenv · Google API client (existing Sheets path) · Node / npm · Vite · React · axios · ChromaDB (existing dependency) · bcrypt / python-jose · Ollama (env) · OpenAI / Gemini keys (optional usage) · n8n bridge (existing) · in-repo observability / Prometheus-text metrics · Render config · Markdown docs · Obsidian vault · SQLite (transitional local)

**Ops hygiene (not a new tool):** resolve CrewAI version pin conflict across requirements (architecture audit GAP-007).

---

# Approved Add-Now Tool

| Tool | Status | Constraint |
|------|--------|------------|
| **Ruff** | APPROVE NOW (T0.5); pending tooling PR | Install PR must confirm OSS license (cost **NOT VERIFIED** until then). No app behavior change. Prefer Ruff over Black+isort+flake8. |

---

# Deferred Tools

| Tool | Reason |
|------|--------|
| Black / isort / flake8 | Superseded by canonical **Ruff**; reconsider only if Ruff install blocked |
| detect-secrets | Superseded by canonical **Gitleaks**; reconsider only if policy requires a second scanner |
| MkDocs | Markdown/`docs/` sufficient until a published docs site is required |
| PlantUML | Prefer Mermaid when diagrams are needed |
| OpenTelemetry full stack | In-process tracer sufficient until distributed tracing is required |
| Loki | Docker/std logs sufficient until central log platform is required |
| deptry / pipdeptree | Optional dependency-graph cleanup later |

---

# Explicitly Rejected Tools

| Tool | Reason | Reconsider only if |
|------|--------|-------------------|
| Kubernetes | Compose topology sufficient | Multi-node production scale proven |
| Airflow | Celery Beat + n8n cover evidenced needs | Complex DAG ownership proven |
| Elasticsearch | No search-stack requirement | Platform full-text search required |
| Zapier / Make.com | n8n already integrated | Founder-approved SaaS |
| Jira / Confluence | GitHub + Markdown/Obsidian | Org mandate |
| LangChain | CrewAI is Founder AI orchestration | AI Platform ADR replaces CrewAI |
| Paid APM / monitoring SaaS | Custom metrics + later OSS Prometheus/Grafana | Founder + cost case |
| Paid API testing suites | TestClient; Bruno later | Founder approval |
| OpenClaw as Founder runtime | CMS reference; Editorial OUT OF SCOPE | Never as Editorial SoT |
| Flask CMS / Sheets as content SoT | Founder Content Studio path | Never as SoT |

---

# Canonical Tool Selections

Resolved T0.5 overlap risks (REDUNDANT class):

| Concern | Canonical selection | Alternate not preferred | Rationale |
|---------|---------------------|-------------------------|-----------|
| Python lint / format / import sort | **Ruff** | Black + isort + flake8 | Single tool, lower ops overhead; alternates remain DEFER only if Ruff cannot ship |
| Secret scanning in git hooks | **Gitleaks** | detect-secrets | Already ACTIVE in `.pre-commit-config.yaml`; second scanner adds noise without new evidence |

No alternate tools were present in the repository to remove; policy only.

---

# Introduction Gates

### ADD NOW

| Tool | Gate |
|------|------|
| Ruff | Tooling PR: config + pre-commit and/or CI; confirm OSS license in governance note; no application behavior change |

### ADD LATER (measurable)

| Tool | Gate |
|------|------|
| Playwright | Authenticated **browser mutation** tests become **release-critical** for Content Studio write UI or CRM SPA |
| Bruno | Sprint requires **≥2 Git-tracked shared HTTP collection files** used by more than one engineer outside pytest |
| pip-audit | Security/pre-prod sprint adds a **CI job that fails on known dependency CVEs** after requirements pin hygiene |
| Bandit | Security hardening sprint adds **Bandit as CI or pre-commit** with a defined rule set |
| Mermaid | A merged ADR or architecture doc includes **≥1 committed ` ```mermaid ` diagram** as figure SoT |
| Prometheus | Production requires **scraped time-series** for service-level monitoring beyond on-demand `/api/v1/metrics/prometheus` |
| Grafana | Introduced **with Prometheus** when persistent dashboards over scraped metrics are required |
| mypy | Quality sprint declares **mypy clean/gated for a named package path** as a release criterion |
| DBeaver Community | Operator task needs GUI on **non-production Compose Postgres** and records that **`psql` is insufficient** |
| pytest-cov in CI | Product policy requires a **coverage report or threshold artifact in GitHub Actions** |

---

# Governance Rules

1. **Tool Governance Rule** — No new tool without: Problem, Evidence, Alternatives, Free/paid status (confirmed), Security, Operational impact, Rollback, Owner, Approval.  
2. **Maintainer** may approve free/OSS KEEP/ADD NOW/LATER when gates are met.  
3. **Founder** must approve any PAID ONLY capability.  
4. **Canonical selections** above may not be dual-tracked without a written exception (avoid Ruff+Black or Gitleaks+detect-secrets).  
5. CMS OpenClaw / Flask / Sheets tooling remains **reference only**, not Founder SoT.

---

# Cost Policy

**DEFAULT POLICY:** Prefer free/open-source tools.  
**Paid tools require explicit Founder approval and documented justification.**

| Class | Rule |
|-------|------|
| FREE / OPEN SOURCE | Allowed per gates + governance note |
| FREE TIER | Document limits; no silent paid upgrade |
| PAID ONLY | Founder approval before adoption |
| NOT VERIFIED | Confirm license at install PR; treat as unapproved until classified |

**Paid tools approved under Toolchain Baseline v1.0: 0**  
(Existing optional OpenAI/Gemini usage keys are not a new approval.)

---

# Freeze Statement

Validation:

| Check | Result |
|-------|--------|
| Code changes | 0 |
| Runtime changes | 0 |
| Dependency changes | 0 |
| Architecture | UNCHANGED |
| Paid tools approved | 0 |

## Certification

**TOOLCHAIN BASELINE v1.0 FROZEN**

Amendments require a governance note and, for paid tools, Founder approval.  
Next executable tooling action permitted under this freeze: **Ruff install PR** meeting the ADD NOW gate (OSS confirmation required).
