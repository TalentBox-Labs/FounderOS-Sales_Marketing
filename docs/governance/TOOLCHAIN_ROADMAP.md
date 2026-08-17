# Toolchain Roadmap

Sprint T0 · T0.5 · **T0.6 freeze**  
Date: 2026-08-09  
Freeze: [TOOLCHAIN_BASELINE_v1_FREEZE.md](TOOLCHAIN_BASELINE_v1_FREEZE.md)

Aligned to: Content Studio + Editorial read complete; E7 Approval Command pending Founder decisions; production hardening when multi-instance deploy matters ([ROADMAP.md](../../ROADMAP.md)).

**No installs in T0–T0.6.**

---

## NOW

| Item | Justification |
|------|---------------|
| KEEP frozen current stack | Active evidence |
| **Ruff** tooling PR (ADD NOW) | T0.5 APPROVE NOW; confirm OSS license in PR |
| Canonical: **Ruff** over Black/isort/flake8; **Gitleaks** over detect-secrets | T0.6 overlap resolution |
| Tool Governance Rule + Cost Policy | Baseline v1.0 |
| CrewAI pin hygiene (GAP-007) | Ops, not new tool |

---

## NEXT 3–6 MONTHS

| Item | Measurable gate |
|------|-----------------|
| Ruff in pre-commit + CI | After successful tooling PR |
| pip-audit | CI job fails on known dependency CVEs post pin hygiene |
| Bandit | CI or pre-commit Bandit check with defined rules |
| Bruno | ≥2 Git-tracked shared HTTP collection files used by >1 engineer outside pytest |
| pytest-cov in CI | Policy requires coverage report/threshold in Actions |
| Mermaid | ≥1 committed `mermaid` fence in a merged ADR/architecture doc |
| E7 Approval Command | Existing pytest + promote only — no new paid tools |

---

## 6–12 MONTHS

| Item | Measurable gate |
|------|-----------------|
| Playwright | Authenticated browser **mutation** tests are release-critical for CS write UI or CRM SPA |
| mypy | Named package path declared mypy-gated for release |
| Prometheus | Scraped time-series required for prod SLO/multi-instance (beyond on-demand `/metrics/prometheus`) |
| Grafana | Introduced with Prometheus for persistent dashboards |
| DBeaver Community | Operator GUI on **non-prod** Compose Postgres; task notes `psql` insufficient |
| ChromaDB review | KEEP or RETIRE after Knowledge/RAG wiring audit |

---

## 12+ MONTHS

| Item | Gate |
|------|------|
| MkDocs | Public/versioned docs site required |
| OpenTelemetry / Loki | Distributed tracing / central logs at real scale |
| Kubernetes | Compose topology proven insufficient for multi-node |
| Any PAID monitoring/API SaaS | Founder approval + cost justification |

---

## Explicitly out (unless Founder overturns)

Zapier, Make.com, Jira/Confluence as engineering SoT, LangChain replacing CrewAI, OpenClaw as Founder Editorial runtime, Flask/Sheets as content SoT, paid APM by default, Black+isort+flake8 alongside Ruff, detect-secrets alongside Gitleaks without policy need.

---

## Cost posture

Paid tools approved: **0**  
Candidates: cost **NOT VERIFIED** until install PR confirms license.
