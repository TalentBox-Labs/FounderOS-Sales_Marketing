# A4 — Implementation Decision

**Sprint:** SALES A4  
**Date:** 2026-08-13  
**Gate:** PASS

## Decision

| Field | Value |
|-------|-------|
| Existing LeadScorer reused | `revenue_os/services/lead_scoring_service.py` — `LeadScorer.calculate_score` |
| Canonical model | Revenue `Contact` + `ContactStatus` |
| Status mutation path | `apply_contact_status_update` → runner `PATCH /contacts/{id}/status` |
| Score path | `score_contact` → runner `POST /contacts/{id}/score` |
| Authentication | `_verify_api_key` (runner API key) |
| Human-only enforcement | `is_human_approver(requested_by)` → 403 |
| Audit | `EventType.CONTACT_STATUS_CHANGED` / `LEAD_SCORED` via EventBus |

## Files changed

| File | Change |
|------|--------|
| `revenue_os/services/lead_scoring_service.py` | Split score vs gated status |
| `runner_api_routers/crm.py` | Score + status PATCH endpoints |
| `revenue_os/services/hermes_planner.py` | Remove agent status promotion |
| `revenue_os/scheduler.py` | Score payload logging |
| `revenue_os/tasks/leads.py` | Remove Celery auto-promotion |
| `runner_api_routers/hermes.py` | Score-only batch response |
| `tests/test_a4_runner_contact_status.py` | A4 focused tests |

## Prohibited (unchanged)

- A1.5 / A3.5 frozen contracts
- Marketing / Revenue boundary contracts
- CRM SPA
- DB migrations
- External integrations

## Gate checklist

| Condition | Result |
|-----------|--------|
| Frozen Contract Impact | **NONE** |
| Database Migration | **NO** |
| External Integration Required | **NO** |
| CRM UI Required | **NO** |
| New LeadScorer Required | **NO** |

**Proceed to Phase 2.**
