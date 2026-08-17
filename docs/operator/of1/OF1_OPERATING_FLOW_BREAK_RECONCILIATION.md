# OF1 — Operating Flow Break Reconciliation

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13  
**Mode:** Evidence before implementation  
**Source:** CP4 six-break list vs repository trace

---

## Method

Traced Demand → Qualification → Deal → Closed-Won → CommercialOutcome → Revenue against live APIs, services, Jinja shell, and UI2.5 freeze tests. Did not invent breaks to force a count of six.

---

## CP4 claimed breaks vs evidence

| # | CP4 break | Stage | Model | Service | API | UI | Authority | Frozen contract | Missing piece | Class | OF1 fix? | Reason |
|---|-----------|-------|-------|---------|-----|----|-----------|-----------------|---------------|-------|----------|--------|
| 1 | QD **registration** | Demand intake (Marketing emit) | `AgentActionLog` handoff | `register_marketing_handoff` | `POST /api/v1/marketing/qualified-demand/handoff` | None | Human `requested_by` | MC04.5 | Operator UI | **MISSING_UI** | **NO** | OF1 starts from demand already present. Audience→Demand / Marketing emit is next-sprint. |
| 2 | QD **reject** | Demand intake (Sales decision) | `AgentActionLog` reject | `reject_qualified_demand` | `POST /api/v1/sales/intake/demand/reject` | None (cockpit freeze: NOT EXPOSED) | Human | MC04.5 + UI2.5 | Operator UI **outside cockpit** | **MISSING_UI** | **YES** | API + contract exist. Expose on `/operator`, not cockpit. |
| 3 | **Deal create** | Contact → Deal | `Deal` | `get_or_create_sales_pipeline` + ORM create | `POST /api/v1/crm/deals` (ungated) | None (SPA UNMOUNTED) | None on create API | A1.5 entity SoT | Operator UI + trusted-human wrap | **MISSING_UI** | **YES** | Needed for operable Contact→Deal. Proxy uses trusted operator; does **not** change frozen create route. Restrict operator create to non-terminal sales stages. |
| 4 | **Deal stage** | Deal → Closed-Won | `Deal.stage` | `apply_deal_stage_update` | `PATCH /api/v1/crm/deals/{id}/stage` | None | Human | A3.5 | Operator UI | **MISSING_UI** | **YES** | Highest-cost CP4 break. Exposure/composition only. |
| 5 | **CO handoff** | Closed-Won → CommercialOutcome | `AgentActionLog` | `register_commercial_outcome_handoff` | `POST /api/v1/sales/commercial-outcome/handoff` | None | Human | MC06.5 | Operator UI | **MISSING_UI** | **YES** | Eligibility remains MC06 `closed_won` only. |
| 6 | **Revenue accept/reject** | CommercialOutcome → Revenue decision | `AgentActionLog` | `accept_commercial_outcome` / `reject_commercial_outcome` | `POST /api/v1/revenue/intake/commercial-outcome/accept\|reject` | None | Human | MC06.5 | Operator UI | **MISSING_UI** | **YES** | Ends at MC06.5; no billing. |

---

## Not a seventh break

| Item | Class | Notes |
|------|-------|-------|
| QD **accept** | **NOT_ACTUALLY_A_BREAK** | Already on cockpit + API. OF1 may also expose accept for one coherent surface. |
| Contact.status | **NOT_ACTUALLY_A_BREAK** | Cockpit exposes high-score subset. OF1 widens **visibility** to contacts with truthful scores; mutation still A4.5. |
| QD → Contact link | Proven only after accept (`contact_id` on accept audit). Show degraded if no accept. |
| Contact → Deal link | Proven only via `Deal.contact_id`. No mapping table. |

---

## Count

| Metric | Value |
|--------|------:|
| CP4 operating breaks expected | 6 |
| Reconciled against repo | **6** |
| Actual confirmed | **6** (all **MISSING_UI**; none MISSING_API) |
| OF1 should fix | **5** (reject, deal create, stage, CO handoff, revenue decision) |
| OF1 must not fix | **1** (QD Marketing register — demand generation) |

**Discrepancy vs CP4 count:** none. Classification is uniformly MISSING_UI / composition, not missing domain APIs.

---

## Gate

Reconciliation complete. Implementation may proceed as composition on `/operator` without changing frozen contracts.
