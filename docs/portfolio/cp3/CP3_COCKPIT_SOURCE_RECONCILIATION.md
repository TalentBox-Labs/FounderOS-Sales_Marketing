# CP3 — Cockpit Source Reconciliation

**Sprint:** CP3 — Founder OS Cross-OS Priority Checkpoint  
**Date:** 2026-08-13  
**Mode:** Decision only

---

## Discrepancy statement

| Metric | UI1 plan | UI2.5 verified |
|--------|----------|----------------|
| Authoritative data sources | **11** (widget map) | **8** (runtime integrations) |
| Unverified | — | **3** |

UI2 reported 11 based on UI1 cockpit widget inventory. UI2.5 verified **8 distinct authoritative source integrations** in `revenue_os/services/cockpit_read_model.py`. The count is **not silently rewritten** — both numbers are documented with reconciliation below.

---

## UI1 eleven-widget inventory (reference)

From `docs/ui/UI1_COCKPIT_DATA_SOURCE_MAP.md`:

1. SEO readiness summary  
2. Technical SEO summary  
3. Contact count by status  
4. Deal pipeline by stage  
5. Lead score bands  
6. Pending editorial  
7. Publishing queue  
8. QualifiedDemand queue  
9. Heartbeat health  
10. Agent activity  
11. Commercial flow diagram  

(+ optional frozen baseline status — static, not a runtime SoT)

---

## Eight verified runtime integrations (UI2.5)

| # | Integration | Code path |
|---|-------------|-----------|
| 1 | QualifiedDemand audit | `_load_pending_qualified_demands()` → `AgentActionLog` |
| 2 | CRM Contacts | `_load_sales_snapshot()` → `Contact` |
| 3 | CRM Deals | `_load_sales_snapshot()` → `Deal` |
| 4 | Editorial pending | `build_editorial_pending()` |
| 5 | Publishing queue | `publishing_engine.list_queue()` |
| 6 | SEO readiness | `seo_engine.analyze_site()` |
| 7 | Technical SEO | `seo_engine.analyze_technical_site()` |
| 8 | Heartbeat scheduler | `scheduler.status()`, `heartbeat_enabled()` |

Items 3–4 in UI1 (contacts, deals) are **two entity reads** from one Sales DB session — counted as **two SoT entities, one integration session**. UI1 counted them as separate widgets (=2 toward 11).

---

## Three unverified sources (11 − 8)

| # | UI1 widget | Classification | Rationale |
|---|------------|----------------|-----------|
| **U1** | Agent activity (`AgentActionLog` / `GET /api/v1/heartbeat/activity`) | **DEFERRED** | API exists (`get_recent_actions` in `runner_api_routers/heartbeat.py`); cockpit governance panel uses scheduler status only. Absence does not fabricate metrics. |
| **U2** | Lead score bands (Hermes / server aggregate) | **STALE_EXPECTATION** | UI1 proposed optional server aggregate. UI2 implements high-score attention items **derived from Contact.lead_score** in the same Contact query — not a separate integration. |
| **U3** | Commercial flow diagram (independent SoT) | **STALE_EXPECTATION** | UI1 map explicitly said "Compose from above — read-only derive." Implemented as derived composition + honest static Revenue stage. Never an independent SoT. |

### Additional UI1 widgets mapped to verified integrations

| UI1 widget | Maps to verified # |
|------------|-------------------|
| SEO readiness | 6 |
| Technical SEO | 7 |
| Contact by status | 2 |
| Deal by stage | 3 |
| Editorial pending | 4 |
| Publishing queue | 5 |
| QualifiedDemand queue | 1 |
| Heartbeat health | 8 |
| Frozen baseline (governance) | Static in governance panel — not counted as runtime source |

---

## Misleading-metric assessment

| Unverified source | Could mislead? | Evidence |
|-------------------|----------------|----------|
| U1 Agent activity | **NO** | Governance shows heartbeat job count; no fake agent log |
| U2 Lead score bands | **NO** | High-score items labeled as recommendation; sourced from real Contact scores when DB available |
| U3 Commercial flow SoT | **NO** | Revenue stage explicitly `emerging` / **NOT YET ACTIVE** |

---

## Decision rule outcome

**COCKPIT REMEDIATION REQUIRED:** **NO**

All three unverified items are **DEFERRED** or **STALE_EXPECTATION**. Current panels use truthful degraded states (`unavailable`, `empty`, `error`, `blocked`, `emerging`). No displayed executive metric substitutes zero for unknown data.

**UI2.5 baseline:** **VALID** (conditional note: expect 11 in planning docs, 8 in runtime manifest — documented discrepancy)

**Cockpit Source Reconciliation:** **PASS**

---

## Optional future enhancements (not CP3 scope)

- Wire `GET /api/v1/heartbeat/activity` into governance panel (U1)  
- Hermes score-distribution read-only widget (U2 enhancement)  
- No change needed for U3 — composition is correct  
