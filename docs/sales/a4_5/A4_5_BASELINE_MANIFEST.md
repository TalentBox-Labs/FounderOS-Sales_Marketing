# SALES A4.5 — Baseline Manifest

**Baseline:** LEADSCORER / CONTACT.STATUS BASELINE v1.0  
**Status:** FROZEN  
**Date:** 2026-08-13

**Parent:** Sales OS Architecture Baseline v1.0 — **UNCHANGED**  
**Sibling:** SALES RUNNER DEAL STAGE UPDATE v1.0 (A3.5) — **UNCHANGED**

---

## Frozen version

**v1.0** — LeadScorer / Contact.status Human Gate

---

## Frozen artifacts

| Path | Role |
|------|------|
| `docs/sales/a4_5/LEADSCORER_CONTACT_STATUS_BASELINE_v1.0.md` | Behavioral baseline |
| `docs/sales/a4_5/LEADSCORER_CONTACT_STATUS_CONTRACT_v1.0.md` | Interface / authority contract |
| `docs/sales/a4_5/A4_5_BASELINE_MANIFEST.md` | This manifest |
| `docs/sales/a4_5/A4_5_*` | Attestation pack |

---

## Runtime files covered (frozen behavior SoT)

| Path |
|------|
| `revenue_os/services/lead_scoring_service.py` |
| `runner_api_routers/crm.py` — `POST/PATCH .../contacts/{id}/score|status` |
| `revenue_os/models/contact.py` — canonical Contact / ContactStatus |
| `revenue_os/services/hermes_planner.py` — qualify recommendation-only |
| `revenue_os/scheduler.py` — heartbeat score-only |
| `revenue_os/tasks/leads.py` — no Celery auto-promotion |
| `runner_api_routers/hermes.py` — batch score-only response |

---

## Test files covered

| Path | Result at freeze |
|------|------------------|
| `tests/test_a4_runner_contact_status.py` | 15/15 |
| `tests/test_a3_runner_deal_stage.py` (A3.5 sibling) | 15/15 |

---

## Contract files

| Path |
|------|
| `docs/sales/a4_5/LEADSCORER_CONTACT_STATUS_CONTRACT_v1.0.md` |
| `docs/sales/SALES_AGENT_AUTHORITY_CONTRACT_v1.0.md` (parent — unchanged) |
| `docs/sales/SALES_DOMAIN_MODEL_CONTRACT_v1.0.md` (parent — unchanged) |

---

## Authority boundaries

| Boundary | Rule |
|----------|------|
| LeadScorer | Existing implementation; advisory output |
| Contact.status mutation | Human-only via runner PATCH |
| Authentication | Runner API key |
| Agent prohibition | No agent path mutates status via LeadScorer flow |
| Audit | LEAD_SCORED + CONTACT_STATUS_CHANGED |
| Marketing | No dependency / no mutation |
| Revenue | Contact SoT only; no CommercialOutcome |

---

## Known historical exceptions

Inherited from A1.5 — see `docs/sales/SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md`:

| # | Test | Class |
|---|------|-------|
| 1 | `test_prospecting_ui.py::test_prospecting_plan_endpoint_returns_stage_allocation_and_leads` | ENVIRONMENT_DEPENDENCY |
| 2 | `test_prospecting_ui.py::test_prospecting_plan_validation_error_for_invalid_score` | ENVIRONMENT_DEPENDENCY |

Reconciliation: `docs/sales/a4_5/A1_5_EXCEPTION_RECONCILIATION.md` — **2/2 MATCH**

---

## Regression baseline at freeze

| Metric | Value |
|--------|------:|
| Full regression passed | 427 |
| Full regression total | 439 |
| Failed | 8 |
| Errors | 4 |
| New regressions | 0 |

---

## A4.5 sprint delta

| Category | Count |
|----------|------:|
| Feature code changes | 0 |
| Runtime changes | 0 |
| DB migrations | 0 |
| Documentation only | A4.5 attestation pack |

---

## Prohibited future modifications

Without explicit architecture review + ADR:

- Restore LeadScorer auto-promotion on score
- Allow agent/AI status mutation
- Alter A1.5 or A3.5 frozen meaning
- Add CRM UI mount requirement
- Activate external integrations for this baseline

---

## Supersession

New ADR + approved sprint required. Do not mutate A1.5 or A3.5 freeze docs.
