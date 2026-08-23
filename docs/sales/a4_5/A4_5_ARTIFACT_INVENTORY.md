# A4.5 — Artifact Inventory (ATLAS)

**Sprint:** SALES A4.5  
**Date:** 2026-08-13  
**Mode:** Verification / baseline freeze — **no runtime changes**

---

## SALES A4 artifacts (introduced or modified)

### RUNTIME

| Path | Role |
|------|------|
| `revenue_os/services/lead_scoring_service.py` | LeadScorer score-only path; `suggest_status_from_score`; `apply_contact_status_update`; `score_contact` |
| `runner_api_routers/crm.py` | `POST /contacts/{id}/score`; `PATCH /contacts/{id}/status`; human gate |
| `runner_api_routers/hermes.py` | Batch score response — no status mutation count |
| `revenue_os/services/hermes_planner.py` | `action_qualify_high_scorers` — recommendation only |
| `revenue_os/scheduler.py` | Heartbeat score audit payload |
| `revenue_os/tasks/leads.py` | Removed Celery auto-promotion |

### TEST

| Path | Role |
|------|------|
| `tests/test_a4_runner_contact_status.py` | 15 focused A4 tests |

### DOCUMENTATION (A4 sprint)

| Path | Role |
|------|------|
| `docs/sales/a4/A4_*` | Implementation audits, decision, report (9 files) |

### CONTRACT (frozen by A4.5)

| Path | Role |
|------|------|
| `docs/sales/a4_5/LEADSCORER_CONTACT_STATUS_CONTRACT_v1.0.md` | Behavioral contract v1.0 |
| `docs/sales/a4_5/LEADSCORER_CONTACT_STATUS_BASELINE_v1.0.md` | Baseline document |

### CONFIGURATION

| Item | A4 impact |
|------|-----------|
| None | No env, docker, or schema config changes |

### UNRELATED (not A4)

| Path | Note |
|------|------|
| `revenue_os/services/deal_automation_service.py` | A3 — not A4 |
| Marketing / SEO routers | Out of scope |

---

## Capability map

| Concern | Implementation |
|---------|----------------|
| LeadScorer | `LeadScorer.calculate_score` — `lead_scoring_service.py` |
| Score / recommendation | `suggest_status_from_score`; runner `POST .../score` |
| Runner integration | `runner_api_routers/crm.py` |
| Contact.status mutation | `apply_contact_status_update` via runner `PATCH .../status` only (production agent paths) |
| Authentication | `_verify_api_key` |
| Human-only gate | `is_human_approver(requested_by)` → 403 |
| Agent prohibition | Scoring paths do not write status; planner qualify returns eligible list |
| Status validation | `ContactStatus` enum parse → 422 |
| Audit | `EventType.LEAD_SCORED`; `EventType.CONTACT_STATUS_CHANGED` |
| Canonical model | Revenue `Contact` / `ContactStatus` — `revenue_os/models/contact.py` |
| Marketing boundary | No Marketing imports or state mutation |
| Revenue boundary | Contact field only; no Deal/CommercialOutcome |

---

## A4.5 sprint changes

| Category | Count |
|----------|------:|
| Feature code changes | **0** |
| Runtime changes | **0** |
| Documentation (A4.5) | This inventory + attestation pack |
