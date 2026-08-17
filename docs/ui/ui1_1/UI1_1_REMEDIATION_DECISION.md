# UI1.1 — Remediation Decision

**Sprint:** UI1.1  
**Date:** 2026-08-13  
**Gate status:** **APPROVED FOR IMPLEMENTATION**

---

## Decision matrix (required fields)

| Field | Value |
|-------|-------|
| Architecture Impact | **NONE** |
| Database Migration | **NO** |
| External Integration Required | **NO** |
| Frozen Contract Change | **NO** |

---

## UI1-B1 — JWT PUT status block

| Field | Decision |
|-------|----------|
| Root cause | Legacy JWT CRM API allows arbitrary field updates including `status` |
| Minimal fix | Return 403 when PUT attempts to change `status`; strip unchanged status from payload |
| Preserves frozen behavior | Runner `PATCH /crm/contacts/{id}/status` unchanged; A4.5 semantics intact |
| Domain ownership | Revenue OS Contact model unchanged |
| New capability | None — removes unauthorized path |
| Code files | `revenue_os/api/v1/contacts.py` |
| Tests | `tests/test_ui1_1_mutation_authority.py::test_jwt_put_contact_status_change_blocked` |

---

## UI1-B2 — n8n meeting.booked demotion

| Field | Decision |
|-------|----------|
| Root cause | Automation webhook directly assigned `ContactStatus.QUALIFIED` |
| Minimal fix | Log recommendation; emit `LEAD_SCORED` signal with `human_gate_required: true`; no DB status write |
| Preserves frozen behavior | Human qualify still via runner PATCH only |
| Domain ownership | n8n remains signal ingress; Revenue Contact SoT unchanged |
| New capability | None — removes auto-qualify |
| Code files | `runner_api_routers/n8n_webhooks.py` |
| Tests | `tests/test_ui1_1_mutation_authority.py::test_n8n_meeting_booked_does_not_mutate_status` |

---

## UI1-B3 — Service-layer authority gate

| Field | Decision |
|-------|----------|
| Root cause | Human gate enforced only at HTTP router; service functions trusted caller-supplied identity |
| Minimal fix | New `mutation_authority.py` with `require_human_mutation_authority()`; required `requested_by` on canonical mutators |
| Preserves frozen behavior | Runner routes already pass `requested_by`; frozen API request/response schemas unchanged |
| Domain ownership | No cross-OS boundary change |
| New capability | None — closes internal bypass |
| Code files | `revenue_os/services/mutation_authority.py`, `lead_scoring_service.py`, `deal_automation_service.py`, `qualified_demand_service.py`, `runner_api_routers/crm.py` |
| Tests | `tests/test_ui1_1_mutation_authority.py` (service + runner adversarial cases) |

---

## Explicit non-changes

- No Executive Cockpit routes
- No CRM React mount
- No new global authorization framework
- No editorial/publishing contract changes (already gated at service layer)
- No agent authority expansion

---

## Implementation verdict

All three bypasses remediated with minimal diff. **No STOP condition triggered.**
