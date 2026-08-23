# SALES A0 — Current-State Audit

**Sprint:** SALES A0 — Sales OS Current-State, Architecture & Capability Audit  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — Feature Code Changes: **0** · Architecture Changes: **0**  
**Coordinator:** Lead Engineering Coordinator  
**Agents:** ATLAS · SCOUT · NOVA · HERMES · BEACON · CIPHER · SENTINEL · LEDGER  
**Cross-Agent Conflicts:** **0**

---

## Executive verdict

Sales capability in Founder OS today is a **PARTIAL** co-located stack under `revenue_os/` + `runner_api_routers/*`, with a live Jinja prospecting surface (`/sales`) and a React CRM SPA (`frontend/`) that is **UNMOUNTED** locally (`frontend/dist` absent → `GET /app` **503**). There is **no** `sales_os` package. Architecture v2.2 **names** Sales OS as first-class but under-specifies it; CRM/deal ownership is attributed to **Revenue OS** in Platform law while migration docs often label CRM as Sales — **CONFLICTED**.

**Sales OS Current State: PARTIAL**

Parallel workstream A (Marketing OS / Social) is independent and unchanged by this audit.

---

## Operating topology (evidence)

| Surface | Role | Status |
|---------|------|--------|
| `runner_api:app` | Primary Founder OS gateway | LIVE |
| `GET /sales` | Jinja prospecting / SDR ops UI | LIVE (200) |
| `GET /app` | React CRM SPA | UNMOUNTED locally (503 `not_built`) |
| `/api/v1/crm/*` | API-key CRM for SPA | LIVE code; needs DB at runtime |
| `revenue_os.main` JWT `/api/v1/{contacts,companies,deals,…}` | Parallel fuller CRM | PARTIAL — not mounted on runner |
| Content `/pipeline` | Marketing content weeks | LIVE — **not** Sales deal pipeline |

---

## Architecture (ATLAS summary)

| Boundary | Finding |
|----------|---------|
| Sales OS intended | Prospecting, outreach sequences, SDR workflows, sales pipeline **ops** |
| Revenue OS intended | CRM entities, deals, forecast, revenue automations |
| Sales ↔ Revenue | **CONFLICTED** in docs; as-is code co-located under `revenue_os/` |
| Sales ↔ Marketing | **PARTIAL** — independent engines; no implemented MQL handoff |
| Platforms | Sales/Revenue consume AI / Automation / Shared; must not own RBAC/providers |
| Registry | No dedicated Sales agent; Forge sprint-declares engine |

See also: capability matrix, domain, workflow, UI, integration, security, test baseline, recommendation.

---

## Artifact index

| Doc |
|-----|
| `SALES_A0_CAPABILITY_MATRIX.md` |
| `SALES_A0_DOMAIN_MODEL_AUDIT.md` |
| `SALES_A0_WORKFLOW_MAP.md` |
| `SALES_A0_UI_AUDIT.md` |
| `SALES_A0_INTEGRATION_AUDIT.md` |
| `SALES_A0_SECURITY_GOVERNANCE_AUDIT.md` |
| `SALES_A0_TEST_BASELINE.md` |
| `SALES_A0_RECOMMENDATION.md` |
| `SALES_A0_CURRENT_STATE_AUDIT.md` (this file) |

---

## Counts (roll-up)

| Metric | Value |
|--------|------:|
| Existing Sales capabilities classified | 28 |
| LIVE | 12 |
| PARTIAL | 6 |
| API_ONLY | 4 |
| UI_ONLY | 0 |
| PLACEHOLDER | 1 |
| DEAD_CODE | 2 |
| NOT_IMPLEMENTED (missing core) | 9 |
| External integrations inventoried | 14 |
| External setup required | 8 |
| Focused Sales tests | 15/17 (2 historical errors) |
| Full regression | 397/409; 8 failed; 4 errors |
| New regressions | 0 |

---

## Recommendation preview

Proceed to **SALES A1 — Sales OS Architecture & Domain Boundary** (docs/ADR only). Do not implement CRM features until A1 resolves Sales↔Revenue CRM ownership and the CRM UI retain/rebuild/retire decision.
