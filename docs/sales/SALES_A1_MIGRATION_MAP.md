# SALES A1 — Migration Map

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Rule:** No migration executed in A1

Disposition classes: **RESOLVED_BY_CONTRACT** · **REQUIRES_FUTURE_ADAPTER** · **REQUIRES_FUTURE_MIGRATION** · **ACCEPTED_LEGACY** · **DEFERRED**

---

## A0 conflicts → A1 disposition

| # | A0 conflict / gap | Disposition | Notes |
|---|-------------------|-------------|-------|
| 1 | CRM ownership Sales vs Revenue docs | **RESOLVED_BY_CONTRACT** | ADR-004 + SALES_REVENUE_CONTRACT |
| 2 | Lead vs Contact entity | **RESOLVED_BY_CONTRACT** | Lead = alias |
| 3 | Opportunity missing | **RESOLVED_BY_CONTRACT** | Opportunity ≡ Deal |
| 4 | Account vs Company | **RESOLVED_BY_CONTRACT** | Account = CSM alias |
| 5 | Dual API stacks | **REQUIRES_FUTURE_MIGRATION** | Runner + JWT |
| 6 | Dual lead scorers | **REQUIRES_FUTURE_ADAPTER** | Single scorer + gate |
| 7 | LeadScorer auto status | **REQUIRES_FUTURE_MIGRATION** | Authority matrix |
| 8 | No `sales_os` package | **DEFERRED** | After A1.5 freeze |
| 9 | Co-location in `revenue_os/` | **ACCEPTED_LEGACY** | Until slice migration |
| 10 | Pipeline.stages CSV vs enum | **REQUIRES_FUTURE_ADAPTER** | Normalize stages |
| 11 | DealStage recruitment mix | **REQUIRES_FUTURE_MIGRATION** | Split enum |
| 12 | Note dual representation | **REQUIRES_FUTURE_ADAPTER** | Prefer Activity NOTE |
| 13 | owner_id no User FK | **REQUIRES_FUTURE_MIGRATION** | Shared RBAC |
| 14 | Marketing → Sales handoff | **RESOLVED_BY_CONTRACT** | QualifiedDemand — not built |
| 15 | Closed-won → CS/Client | **RESOLVED_BY_CONTRACT** | CommercialOutcome — not built |
| 16 | Runner deal stage update missing | **REQUIRES_FUTURE_MIGRATION** | Post UI decision |
| 17 | CRM UI unmounted | **DEFERRED** | RETAIN_AND_REFACTOR_LATER |
| 18 | Content vs deal “pipeline” name | **RESOLVED_BY_CONTRACT** | Marketing vs Sales |
| 19 | MeetingActivity dead schema | **DEFERRED** | DEPRECATED_CANDIDATE |
| 20 | Nurture SubscriberProfile | **DEFERRED** | Not Sales SoT |
| 21 | LinkedIn UGC in RevenueOS | **RETIRE** (integration I08) | Not Sales |
| 22 | Alembic empty revision | **ACCEPTED_LEGACY** | Toolchain debt |
| 23 | prospecting_ui tests on JWT+DB | **ACCEPTED_LEGACY** | Classified ENVIRONMENT_DEPENDENCY |

---

## LIVE capability preservation map

All **12 LIVE** capabilities → **ACCEPTED_LEGACY** (preserve behavior; no A1 changes):

C01, C02, C03, C07, C08, C09, C11, C12, C13, C14, C15, C17

---

## Recommended migration sequence (post-A1.5 — not executed)

1. A1.5 baseline freeze  
2. Sales facade adapter on runner (stage update + authority gates)  
3. Scorer consolidation + human gate  
4. QualifiedDemand / CommercialOutcome event stubs  
5. Optional `sales_os` package extraction slice  
6. CRM SPA refactor + mount  
7. JWT stack consolidation or deprecation  

---

## Cross-agent integration

**Cross-Agent Conflicts: 0**
