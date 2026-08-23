# A4 — Implementation Report

**Sprint:** SALES A4 — LeadScorer / Contact.status Human Gate  
**Date:** 2026-08-13  
**Type:** COMPLETE_EXISTING  
**Verdict:** READY FOR SALES A4.5

---

## Capability reused

| Component | Location |
|-----------|----------|
| LeadScorer scoring | `revenue_os/services/lead_scoring_service.py` — `LeadScorer.calculate_score` |
| Status recommendation | `LeadScorer.suggest_status_from_score` |
| Human gate | `is_human_approver` (A3 pattern) |
| Canonical model | Revenue `Contact` / `ContactStatus` |

## Files changed

| File | Change |
|------|--------|
| `revenue_os/services/lead_scoring_service.py` | Score-only path; `apply_contact_status_update`; removed auto-promotion |
| `runner_api_routers/crm.py` | `POST /contacts/{id}/score`, `PATCH /contacts/{id}/status` |
| `runner_api_routers/hermes.py` | Batch score response — no qualification count from mutation |
| `revenue_os/services/hermes_planner.py` | `action_qualify_high_scorers` recommendation-only |
| `revenue_os/scheduler.py` | Score audit payload |
| `revenue_os/tasks/leads.py` | Removed Celery auto-promotion |
| `tests/test_a4_runner_contact_status.py` | 15 focused tests |

## Behavior

1. **Score:** `POST /api/v1/crm/contacts/{id}/score` — updates `lead_score`, emits `LEAD_SCORED`, returns `suggested_status`, **does not** change `Contact.status`.
2. **Qualify:** `PATCH /api/v1/crm/contacts/{id}/status` — requires human `requested_by`; emits `CONTACT_STATUS_CHANGED` on change.
3. **Hermes batch / heartbeat / planner scoring** — score only; planner qualify returns eligible list without mutation.

## Authority enforcement

- `is_human_approver` blocks agent/AI/bot/system identities → 403
- Runner API key via `_verify_api_key`

## Audit

- `EventType.LEAD_SCORED` on score
- `EventType.CONTACT_STATUS_CHANGED` on human status change (includes `requested_by`, `notes`)

## Cross-OS boundary

- Marketing: **PASS** — no Marketing state touched
- Revenue: **PASS** — Contact.status via canonical Revenue model only; no Deal/CommercialOutcome changes

## Test results

| Suite | Result |
|-------|--------|
| A4 focused | **15/15** |
| A3.5 frozen | **15/15** |
| A1.5 (`test_prospecting_ui`) | **0/2** errors (known Postgres/JWT — unchanged) |
| Full regression | **427 passed**, **8 failed**, **4 errors** |
| Historical failures | **UNCHANGED** |
| New regressions | **0** |

## Deferred scope

- JWT contacts API ungated status field
- n8n `meeting.booked` auto-qualify
- Dual scorer consolidation (`scoring_service` vs `lead_scoring_service`)
- CRM SPA mount
- MC04 QualifiedDemand

## Architecture attestation

| Check | Status |
|-------|--------|
| A1.5 baseline | UNCHANGED |
| A3.5 baseline | UNCHANGED |
| Frozen contracts | 0 changes |
| DB migrations | 0 |
| External integrations | 0 |
| Credentials committed | 0 |

**Recommended next sprint:** SALES A4.5 — LEADSCORER / CONTACT.STATUS BASELINE FREEZE
