# T0.5 — Toolchain Decision Review

Sprint T0.5 — Governance only  
Date: 2026-08-09  
Code / install / CI changes: **0**

Sources: [TOOLCHAIN_BASELINE.md](TOOLCHAIN_BASELINE.md), [TOOLCHAIN_DECISION_MATRIX.md](TOOLCHAIN_DECISION_MATRIX.md), [TOOLCHAIN_ROADMAP.md](TOOLCHAIN_ROADMAP.md)

This review pressure-tests T0 decisions. It does **not** install tools or re-inventory the full repository.

---

# Executive Summary

| Item | Result |
|------|--------|
| ADD NOW tool | **Ruff** → **APPROVE NOW** (install still future tooling PR) |
| ADD LATER tools reviewed | **10** (Playwright, Bruno, pip-audit, Bandit, Mermaid, Prometheus, Grafana, mypy, DBeaver Community, pytest-cov) |
| Paid tools approved | **0** |
| Material overlap issues | Controlled (ACCEPTABLE or DEFER/REJECT already) |
| High security risks (ADD NOW/LATER) | **0** |
| Vague introduction gates found | **2** (rewritten below) |
| Corrections required | **3** (documented; freeze may proceed with these amendments) |

**Verdict: READY TO FREEZE TOOLCHAIN BASELINE**  
(with Corrections Required applied as freeze amendments in this document)

---

# Add Now Review

## Tool: Ruff

| Field | Assessment |
|-------|------------|
| **Problem solved** | No Python lint / format / import-sort gate in repo or CI |
| **Repository evidence** | No `ruff.toml` / Ruff in requirements; CI (`.github/workflows/test.yml`) runs pytest + fixture verify only; large Python trees `src/`, `revenue_os/`, `runner_api_routers/`; T0 gap analysis |
| **Why current tools insufficient** | pytest does not enforce style; Gitleaks/pre-commit do not lint Python; no Black/isort/flake8 configured |
| **Expected engineering benefit** | Consistent style, catch unused imports/basic errors before CI; single tool vs Black+isort+flake8 (T0 DEFER of those) |
| **Operational cost** | Low — CLI + optional pre-commit/CI step; no long-running service |
| **Learning cost** | Low for standard lint/format usage |
| **Security impact** | Local CLI on checkout; supply-chain = new dependency when added (see Security Review) |
| **Lock-in risk** | Low — config file + CI step removable |
| **Rollback/removal path** | Delete config/hooks/CI step; no runtime coupling |
| **Owner** | Developer Experience |
| **Free/paid status** | **NOT VERIFIED** from repository evidence alone (package not present in repo). T0 labeled FREE / OPEN SOURCE aspirationally. **Install PR must confirm OSS license in governance note before merge.** |
| **Why NOW** | Quality gap exists today; blocks nothing product-wise but grows with every sprint; E7+ will add more Python without a gate |

### Add Now Decision

**APPROVE NOW**

Constraint: first install PR must record confirmed license/cost class (must not be PAID ONLY). If install would require paid tier → stop and seek Founder approval (Cost Policy).

---

# Add Later Matrix

| Tool | Problem solved | Evidence | Introduction trigger (amended if needed) | Existing alternative | Overlap risk | Operational burden | Lock-in risk | Cost class | Decision |
|------|----------------|----------|------------------------------------------|----------------------|--------------|-------------------|--------------|------------|----------|
| Playwright | Browser E2E | ROADMAP mentions hand Playwright; not in `package.json`/requirements | **When a sprint introduces browser-level mutation workflows** for Content Studio write UI or CRM SPA (not read-only pages) | Manual browser / curl; pytest HTML smoke via TestClient | ACCEPTABLE OVERLAP with pytest (different layer) | Medium (browsers, flake risk) | Low–Med | NOT VERIFIED in-repo (likely OSS at install) | **KEEP AS LATER** |
| Bruno | Shared API collections | Growing FastAPI surface; TestClient in tests | **When ≥2 engineers need shared, Git-versioned HTTP collections outside pytest** | pytest TestClient; ad-hoc curl | ACCEPTABLE OVERLAP with TestClient | Low | Low | NOT VERIFIED in-repo | **KEEP AS LATER** |
| pip-audit | Dependency CVEs | No audit in CI; heavy transitive graph via CrewAI reqs | **When a security/pre-production sprint adds a CI dependency CVE gate** (after requirements pin hygiene) | None automated | NO OVERLAP with Gitleaks | Low–Med (CI time, advisory fetch) | Low | NOT VERIFIED in-repo | **KEEP AS LATER** |
| Bandit | Python SAST | No SAST tool in pre-commit/CI | **When a security hardening sprint adds static security lint to CI/pre-commit** | Manual review | ACCEPTABLE OVERLAP with Ruff (different rules) | Low | Low | NOT VERIFIED in-repo | **KEEP AS LATER** |
| Mermaid | In-repo diagrams | Heavy `docs/architecture*`, `docs/migration*` | **When an ADR or architecture doc requires a diagram committed as Markdown/Mermaid** (no external board) | Prose / external images | ACCEPTABLE OVERLAP with Markdown | None (text in docs) | None | NOT VERIFIED (syntax in MD; renderer optional) | **KEEP AS LATER** |
| Prometheus | Metrics scrape/store | `/api/v1/metrics/prometheus` exists (`metrics.py`) | **When production runs multiple instances or an SLO/uptime target requires scraped metrics storage** | In-process `/metrics` JSON/text | ACCEPTABLE OVERLAP with custom observability | Medium (ops service) | Low | NOT VERIFIED in-repo (image OSS typical) | **KEEP AS LATER** |
| Grafana | Dashboards | Pairs with Prometheus; no dashboards in repo | **Same gate as Prometheus — introduce with Prometheus when scrape-based prod monitoring is required** | Manual `/metrics` inspection | ACCEPTABLE OVERLAP | Medium | Low | NOT VERIFIED in-repo | **KEEP AS LATER** |
| mypy | Static typing gate | No mypy config/CI | **When a quality sprint declares type-check as a release gate for selected packages** | Runtime tests only | ACCEPTABLE OVERLAP with Ruff (limited typing lint) | Medium (debt burn-down) | Low | NOT VERIFIED in-repo | **KEEP AS LATER** |
| DBeaver Community | DB GUI | Compose Postgres; no GUI in repo | **When operators need a local GUI against non-production Compose Postgres and CLI `psql` is insufficient for the task** | `psql` / SQLAlchemy | ACCEPTABLE OVERLAP with CLI | Low (local only) | Low | NOT VERIFIED in-repo | **KEEP AS LATER** |
| pytest-cov (in CI) | Coverage gate/report | `COVERAGE.md` documents manual `--cov`; not in CI/`requirements.txt` | **When product policy requires coverage report or threshold in GitHub Actions** | Manual coverage runs | ACCEPTABLE OVERLAP with pytest | Low | Low | NOT VERIFIED in-repo (`coverage` not pinned) | **KEEP AS LATER** |

**No tool moved to NOW** — none have evidence of blocking current frozen baselines or E7 design (which T0 says uses existing pytest + promote).

---

# Overlap Review

| Pairing | Classification | Notes |
|---------|----------------|-------|
| Ruff vs pytest | NO OVERLAP | Different concerns |
| Ruff vs Gitleaks | NO OVERLAP | Lint vs secrets |
| Ruff vs Black/isort/flake8 (deferred) | REDUNDANT if both added | Keep Black suite **DEFER**; Ruff preferred |
| Bruno vs TestClient | ACCEPTABLE OVERLAP | Manual/shared vs automated |
| Playwright vs TestClient | ACCEPTABLE OVERLAP | Browser vs HTTP |
| pip-audit vs Gitleaks | NO OVERLAP | Dep CVEs vs secret strings |
| Bandit vs Gitleaks | NO OVERLAP | SAST vs secrets |
| Bandit vs Ruff | ACCEPTABLE OVERLAP | Security rules vs general lint |
| Prometheus/Grafana vs `observability.py` | ACCEPTABLE OVERLAP | Scrape/UI vs in-process export |
| Mermaid vs Markdown/Obsidian | ACCEPTABLE OVERLAP | Diagram DSL in docs |
| detect-secrets (deferred) vs Gitleaks | REDUNDANT | Keep detect-secrets **DEFER** |
| mypy vs Ruff | ACCEPTABLE OVERLAP | Deeper types vs lint |
| DBeaver vs psql | ACCEPTABLE OVERLAP | GUI vs CLI |
| pytest-cov vs pytest | ACCEPTABLE OVERLAP | Coverage plugin |

**Overlap Risks (REDUNDANT class): 2** — both already controlled by DEFER (Black suite, detect-secrets).

---

# Deferred / Rejected Review

Material items for 12–18 months only:

| Tool | Why deferred/rejected | Current alternative | Reconsideration trigger | Risk of premature adoption | Confirm |
|------|----------------------|---------------------|-------------------------|----------------------------|---------|
| Kubernetes | Compose 5-service topology sufficient | Docker Compose | Multi-node / multi-host production scale evidenced | High ops cost | **REJECT** |
| Airflow | Celery Beat + n8n cover evidenced automation | Celery / n8n | Complex cross-system DAG ownership proven | Duplicate schedulers | **REJECT** |
| LangChain | CrewAI is Founder AI stack | CrewAI | AI Platform ADR explicitly replaces CrewAI | Dual agent frameworks | **REJECT** |
| OpenClaw runtime | CMS reference; Editorial OUT OF SCOPE | Founder crews/validators | Never as Editorial SoT | Architecture regression | **REJECT** |
| Paid APM SaaS | Custom metrics + later OSS path | `/metrics` + Prometheus/Grafana later | Founder approval + cost case | Cost + data egress | **REJECT** |
| Zapier / Make.com | n8n already integrated | n8n | Founder-approved SaaS only | Second iPaaS | **REJECT** |
| Black / isort / flake8 | Prefer single Ruff | Ruff (APPROVE NOW) | Only if Ruff install blocked | Tool sprawl | **DEFER** |
| OpenTelemetry | In-process tracer exists | `src/observability.py` | Multi-service distributed tracing required | Complexity | **DEFER** |
| MkDocs | `docs/` Markdown sufficient | Markdown / Obsidian | Public/versioned docs site required | Extra publish pipeline | **DEFER** |
| detect-secrets | Gitleaks already hooked | Gitleaks | Policy demands second scanner | Duplicate noise | **DEFER** |

---

# Cost Review

| Tool | Class | Flag |
|------|-------|------|
| Ruff (ADD NOW) | **NOT VERIFIED** in-repo | Confirm OSS at install PR; else **PAID APPROVAL REQUIRED** |
| All 10 ADD LATER | **NOT VERIFIED** in-repo until added | Same rule |
| pytest, Gitleaks, Docker, Compose, Postgres, Redis, Celery, FastAPI, etc. (KEEP) | FREE / OPEN SOURCE or FREE TIER as T0 (repo-present) | No change |
| OpenAI / Gemini API usage (KEEP env) | PAID ONLY (usage) | **Not newly approved** — existing optional keys; no expansion |
| Render | UNKNOWN | Hosting; not a new ADD |
| CrewAI | UNKNOWN | Existing dependency; pin hygiene only |
| n8n self-host | FREE / OPEN SOURCE (self-host path) | Cloud n8n paid tier **not** approved |
| Paid APM / Zapier / Jira / paid API suites | PAID ONLY | Remain **REJECT** |

**Paid Tools Approved: 0**

---

# Security Review

Scope: ADD NOW + ADD LATER. Telemetry/cloud behavior **NOT VERIFIED** from repo (packages absent). Assessments are local-use assumptions + supply-chain caution.

| Tool | Code leaves env? | Telemetry? | Cloud account? | Accesses secrets? | Prod credentials? | Supply-chain | Risk |
|------|------------------|------------|----------------|-------------------|-------------------|--------------|------|
| Ruff | No (local) | NOT VERIFIED | No | No | No | New PyPI dep at install | **LOW** |
| Playwright | Browser binaries may download | NOT VERIFIED | No | May touch UI tokens in tests | If pointed at prod — avoid | npm/browser deps | **MEDIUM** |
| Bruno | Local collections | NOT VERIFIED | No | Collections must not store secrets | Avoid prod keys in Git | App install | **LOW** |
| pip-audit | May fetch advisory data | NOT VERIFIED | No | Reads lock/requirements | No | Advisory client | **MEDIUM** |
| Bandit | No | NOT VERIFIED | No | No | No | PyPI dep | **LOW** |
| Mermaid | No (text in docs) | N/A in-repo | No | No | No | None if text-only | **LOW** |
| Prometheus | Ops network scrape | N/A | Optional remote | May scrape authenticated `/metrics` | Protect metrics auth | Container image | **MEDIUM** |
| Grafana | Dashboards/datasource | NOT VERIFIED | Optional cloud | Datasource creds | If misconfigured → prod DB | Container image | **MEDIUM** |
| mypy | No | NOT VERIFIED | No | No | No | PyPI dep | **LOW** |
| DBeaver | Local GUI | NOT VERIFIED | No | **Yes — DB passwords** | Must not use prod without policy | App install | **MEDIUM** |
| pytest-cov | No | No | No | No | No | PyPI dep | **LOW** |

**High Security Risks: 0**

---

# Introduction Gate Review

| Tool | T0 trigger quality | Mark | Amended trigger (roadmap-aligned) |
|------|-------------------|------|-----------------------------------|
| Playwright | Specific enough | VALID | Keep: browser-level **mutation** UI workflows |
| Bruno | “Team needs…” soft | **TOO VAGUE** → rewritten | When **≥2 engineers** need shared Git-versioned HTTP collections outside pytest |
| pip-audit | Security sprint + hygiene | VALID | Keep |
| Bandit | Security hardening sprint | VALID | Keep |
| Mermaid | “Diagram-heavy ADR” soft | **TOO VAGUE** → rewritten | When an ADR/architecture doc **requires a committed Mermaid diagram** |
| Prometheus | Multi-instance / SLO | VALID | Keep |
| Grafana | With Prometheus | VALID | Keep (tied to Prometheus gate) |
| mypy | Typing as release gate | VALID | Keep |
| DBeaver | “Optional local” | **TOO VAGUE** → rewritten | When operators need GUI on **non-prod Compose Postgres** and `psql` is insufficient |
| pytest-cov | Coverage policy | VALID | Keep |

**Vague Introduction Gates (found): 3** (Bruno, Mermaid, DBeaver) — all rewritten above; freeze uses amended triggers.

---

# Corrections Required

| # | Correction | Action |
|---|------------|--------|
| 1 | Candidate tools’ FREE/OSS label is **NOT VERIFIED** until present in repo | Install PRs must confirm license; paid → Founder approval |
| 2 | Baseline listed “Prometheus + Grafana” as one line; matrix correctly treats **two** tools | Freeze inventory uses **10** ADD LATER = split Prometheus and Grafana |
| 3 | Vague ADD LATER triggers (Bruno, Mermaid, DBeaver) | Use amended triggers in this review as canonical |

No correction reverses ADD NOW for Ruff or reopens REJECT list.

**Corrections Required: 3**

---

# Toolchain Freeze Recommendation

Freeze criteria check:

| Criterion | Status |
|-----------|--------|
| ADD NOW justified | PASS — Ruff APPROVE NOW |
| ADD LATER triggers explicit | PASS — after amendments |
| No paid tool implicitly approved | PASS — 0 paid; usage APIs unchanged |
| Overlap controlled | PASS — REDUNDANT pairs deferred |
| Security risks understood | PASS — no HIGH; MEDIUM noted |
| Deferred/rejected reconsideration gates | PASS |

## Recommendation

**READY TO FREEZE TOOLCHAIN BASELINE**

Freeze incorporates T0 documents **as amended by this T0.5 review** (cost verification at install, 10 ADD LATER with rewritten gates, Ruff APPROVE NOW pending install PR).
