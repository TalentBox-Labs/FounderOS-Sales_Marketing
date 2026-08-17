# A3 — Existing Capability Map (NOVA)

**Sprint:** SALES A3  
**Date:** 2026-08-13

| Capability | Location | Reuse for A3 |
|------------|----------|--------------|
| Deal model | `revenue_os/models/deal.py` | YES — canonical |
| DealStage enum | same (sales + recruitment values) | YES — restrict to sales stages at runner gate |
| `advance_deal_stage` | `revenue_os/services/deal_automation_service.py` | YES — sets stage, probability, `closed_at` on CLOSED_WON |
| JWT PUT deals | `revenue_os/api/v1/deals.py` | Reference only — **not** primary runner path |
| Runner CRM | `runner_api_routers/crm.py` | YES — add stage endpoint; create/list already exist |
| Auth | `_verify_api_key` Bearer | YES |
| Human gate pattern | `editorial_approval.is_human_approver` / publishing alias | YES |
| Audit | `EventType.DEAL_STAGE_CHANGED` + `emit_deal_stage_changed` | YES — publish with `requested_by` |
| Persistence | SQLAlchemy `deals` via SessionLocal | YES — no migration |
| Tests | No dedicated runner stage tests | ADD |

**Duplication risk:** Runner must not reimplement probability/`closed_at` logic — call `advance_deal_stage`.

**Gap today:** Runner has POST/GET deals; **no** stage PATCH/PUT.
