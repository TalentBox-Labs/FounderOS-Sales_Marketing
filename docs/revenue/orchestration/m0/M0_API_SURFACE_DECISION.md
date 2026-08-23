# M0 API Surface Decision

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17

---

## Finding

Two FastAPI applications exist:

| App | Entry | Production? |
|-----|-------|-------------|
| `runner_api:app` | `runner_api.py` | **YES** — Dockerfile CMD, local dev docs |
| `revenue_os.main:app` | `revenue_os/main.py` | **NO** — legacy standalone |

---

## Canonical for New Orchestration (M1)

**`runner_api:app`**

Evidence:
- Dockerfile: `CMD ["sh", "-c", "uvicorn runner_api:app ..."]`
- Tenant-aware CRM, cockpit, operator flow, integrations
- S1–S4.5 frozen tests use `from runner_api import app`
- `seed_platform_agents()` on startup

---

## Surface Classification

| Surface | Classification | Notes |
|---------|----------------|-------|
| `runner_api:app` | **CANONICAL_FOR_NEW_ORCHESTRATION** | All M1 work here |
| `runner_api_routers/agents.py` | Canonical agent/workflow routes | `/api/v1/agents/*` |
| `runner_api_routers/approvals.py` | Canonical approval queue | `/api/v1/approvals/*` |
| `runner_api_routers/crm.py` | Canonical CRM | Org-scoped |
| `revenue_os/main.py` | **LEGACY_COMPATIBILITY** | Do not extend |
| `revenue_os/api/v1/*` | **DEPRECATE_LATER** | CrewAI quarantined M0 |
| `revenue_os/api/v1/orchestration.py` | **INTERNAL_ONLY** (GTM marketing) | Duplicate of runner orchestration router |

---

## Auth Model Comparison

| | runner_api | revenue_os/main |
|---|------------|-----------------|
| Human session | Yes (cockpit, CRM) | JWT `get_current_user` |
| TenantContext | Yes (CRM, integrations) | **No** on most routes |
| API key | `_verify_api_key` on agents | N/A |
| Frozen test target | **Yes** | No |

---

## Agent Endpoints

| Route | App | Status |
|-------|-----|--------|
| `POST /api/v1/agents/sales/{id}/cold-email` | runner_api | Canonical |
| `POST /api/v1/agents/workflows/{id}/execute` | runner_api | Canonical (stub) |
| `POST /api/v1/agents/score-lead` | main.py only | **410 QUARANTINED** |

---

## M1 Rule

**All new M1 orchestration routes MUST be added to `runner_api_routers/` and mounted in `runner_api.py`.**

No new routes on `revenue_os/main.py`.

---

*End of M0 API Surface Decision*
