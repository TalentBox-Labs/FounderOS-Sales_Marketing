# SALES A2 — Deferred / Do-Not-Build Register

**Sprint:** SALES A2  
**Date:** 2026-08-13  
**Purpose:** “Not selected” ≠ “forgotten”

---

## Deferred / reject now

| Item | Disposition | Reason |
|------|-------------|--------|
| MC01 `sales_os` package extract | DEFER | Architecture hygiene; low founder workflow value vs stage ops |
| MC02 Lead entity table | REJECT | Alias resolved A1.5 |
| MC03 Opportunity entity table | REJECT | ≡ Deal |
| MC04 QualifiedDemand | DEFER | High value later; Marketing dependency; score 3.38 |
| MC06 CommercialOutcome / Client | DEFER | Premature without stage ops |
| MC07 Owner FK / RBAC | DEFER | Shared Platform; not Sales-first |
| MC08 Companies UI | DEFER | After/with C19 connect |
| MC09 Relational PipelineStage | DEFER | Enum sufficient; migration risk |
| C04 Proxycurl enrich enable | DEFER | Paid / external |
| C10 n8n send activation | DEFER | External setup; approvals already LIVE |
| C16 Automation expansion | DEFER | In-memory debt; risk |
| C18 Mount CRM SPA | REJECT for A3 | Frozen RETAIN_AND_REFACTOR_LATER |
| C21 Forecast UI | DEFER | Revenue proximity without Sales gap #1 |
| C22 JWT stack consolidation | DEFER | ACCEPTED_LEGACY migration |
| I08 LinkedIn UGC Sales use | RETIRE | Marketing Social owns |
| I14 HubSpot/SF/Pipedrive | DEFER | Not implemented; lock-in |
| Autonomous outbound agent | REJECT | Authority PROHIBITED |
| Speculative AI selling features | REJECT | No evidence / A2 bans |

---

## Live capabilities

Do not “rebuild” C01–C03, C07–C09, C11–C15, C17 — reuse only.
