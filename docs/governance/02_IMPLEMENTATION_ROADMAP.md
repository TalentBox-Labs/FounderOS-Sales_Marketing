# 02 — Implementation Roadmap

Sprint P0 — Documentation only  
Date: 2026-08-09

Baselines frozen: Architecture · Runtime · Migration · Content Studio · Kanban · Editorial Readiness · Toolchain v1.0  
Blocking: Founder Decision Record (FDR-001/002/003) before Editorial Approval Command (E7)

---

## Phase 1 — Platform

| Field | Content |
|-------|---------|
| **Goal** | Keep Shared Platform/Runtime/Auth stable; apply toolchain hygiene without redesign |
| **Deliverables** | Ruff tooling PR (Toolchain ADD NOW); CrewAI pin hygiene; no auth/API contract changes; protect frozen routers |
| **Dependencies** | Toolchain Baseline v1.0 |
| **Blocking decisions** | None for Ruff (OSS confirm at install); Auth redesign forbidden |
| **Complexity** | LOW–MEDIUM |

---

## Phase 2 — Marketing

| Field | Content |
|-------|---------|
| **Goal** | Complete Editorial Engine approval command; preserve Content Studio read baselines; keep Publishing decoupled |
| **Deliverables** | Founder FDR completed → E7 Approval Command (thin promote wrapper); optional readiness UI; no Calendar until E5A date ADR resolved |
| **Dependencies** | Phase 1 stability; FDR-001/002/003; Editorial Readiness baseline; promote_staged + promotion_audit |
| **Blocking decisions** | FDR-001 object · FDR-002 actor · FDR-003 publish boundary |
| **Complexity** | MEDIUM (E7); HIGH if Founder chooses content-item lifecycle or publish coupling |

---

## Phase 3 — Sales

| Field | Content |
|-------|---------|
| **Goal** | Harden Sales OS + CRM paths without Marketing editorial coupling |
| **Deliverables** | Prospecting/outreach reliability; CRM SPA against frozen auth patterns; tests for sales routers |
| **Dependencies** | Shared Platform auth/DB; avoid Editorial files |
| **Blocking decisions** | None from Editorial FDR set |
| **Complexity** | MEDIUM–HIGH |

---

## Phase 4 — Revenue

| Field | Content |
|-------|---------|
| **Goal** | Deepen Revenue OS services (deals, forecasting, CSM) with clear separation from Marketing Editorial Approval |
| **Deliverables** | Service/API improvements; keep Revenue approvals queue distinct from content promote |
| **Dependencies** | Phase 3 CRM data quality; Celery/Redis healthy |
| **Blocking decisions** | None Editorial; do not merge approval domains |
| **Complexity** | HIGH |

---

## Phase 5 — Automation

| Field | Content |
|-------|---------|
| **Goal** | Strengthen Celery/n8n/heartbeat loops with evidence-based workflows |
| **Deliverables** | Reliable task paths; n8n webhook contracts; no OpenClaw as Editorial runtime |
| **Dependencies** | Redis/Celery; Integrations credentials |
| **Blocking decisions** | Founder if adopting paid iPaaS (rejected by default) |
| **Complexity** | MEDIUM–HIGH |

---

## Phase 6 — Intelligence

| Field | Content |
|-------|---------|
| **Goal** | Analytics depth + Knowledge Base/RAG where wiring is proven |
| **Deliverables** | KB/search hardening; analytics reports; Chroma keep/retire decision |
| **Dependencies** | Phases 3–4 data; AI Runtime |
| **Blocking decisions** | Chroma usage audit; typing/observability gates (toolchain ADD LATER) |
| **Complexity** | MEDIUM–HIGH |

---

## Near-term sequence (critical path)

```
Founder FDR-001/002/003
    → E7 Editorial Approval Command
        → (optional) Editorial reject/revoke later
            → Publishing Engine work (only per FDR-003)
Platform parallel: Ruff install PR (Toolchain)
```
