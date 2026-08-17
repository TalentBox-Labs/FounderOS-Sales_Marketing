# UI1.1 — Mutation Bypass Register

**Sprint:** UI1.1 — Mutation Boundary & Governance Remediation  
**Date:** 2026-08-13  
**Reconciled against UI1:** 3 bypasses; 2 MEDIUM + 1 LOW governance defects — **matches UI1 evidence**

---

## Summary

| ID | Severity | Status |
|----|----------|--------|
| UI1-B1 | MEDIUM | **CLOSED** |
| UI1-B2 | MEDIUM | **CLOSED** |
| UI1-B3 | LOW | **CLOSED** |

**Governance defects remaining:** 0 MEDIUM, 0 LOW (all remediated)

---

## UI1-B1 — JWT Contact.status PUT bypass

| Field | Value |
|-------|-------|
| **ID** | UI1-B1 |
| **Affected capability** | Contact.status mutation |
| **Owning OS** | Revenue OS |
| **Entry point** | `PUT /api/v1/contacts/{id}` (JWT stack) |
| **Authoritative mutation function** | Direct ORM `setattr(contact, "status", ...)` in `revenue_os/api/v1/contacts.py` |
| **Bypassed guard** | A4.5 human gate (`is_human_approver` + runner `PATCH /crm/contacts/{id}/status`) |
| **Requester types able to exploit** | Any JWT-authenticated user (human or service account) |
| **Human-only requirement** | YES — A4.5 frozen baseline |
| **Agent/AI exposure** | Indirect via authenticated API client |
| **Audit exposure** | No audit on JWT PUT path |
| **Severity** | **MEDIUM** |
| **Frozen contract affected** | A4.5 LeadScorer / Contact.status (authority boundary, not semantics) |
| **Runtime reproducibility** | YES — pre-fix: authenticated PUT with `status: qualified` |
| **Remediation approach** | Reject status field changes on JWT PUT with 403; direct to runner human-gated PATCH |
| **Expected files changed** | `revenue_os/api/v1/contacts.py` |
| **Status** | **CLOSED** |

---

## UI1-B2 — n8n meeting.booked auto-qualify

| Field | Value |
|-------|-------|
| **ID** | UI1-B2 |
| **Affected capability** | Contact.status → QUALIFIED |
| **Owning OS** | Revenue OS (runner automation ingress) |
| **Entry point** | `POST /webhooks/n8n/meeting.booked` |
| **Authoritative mutation function** | Direct `contact.status = ContactStatus.QUALIFIED` in `runner_api_routers/n8n_webhooks.py` |
| **Bypassed guard** | A4.5 human gate; automation must not qualify leads |
| **Requester types able to exploit** | n8n automation (Bearer API key or `X-N8N-Secret`) |
| **Human-only requirement** | YES |
| **Agent/AI exposure** | YES — automation identity `actor=n8n` |
| **Audit exposure** | Audit logged but mutation was unauthorized |
| **Severity** | **MEDIUM** |
| **Frozen contract affected** | A4.5 (authority boundary) |
| **Runtime reproducibility** | YES — pre-fix: webhook with `contact_id` auto-qualified |
| **Remediation approach** | Remove status mutation; emit recommendation event with `human_gate_required: true` |
| **Expected files changed** | `runner_api_routers/n8n_webhooks.py` |
| **Status** | **CLOSED** |

---

## UI1-B3 — Service-layer direct mutation bypass

| Field | Value |
|-------|-------|
| **ID** | UI1-B3 |
| **Affected capability** | Contact.status, deal stage, QualifiedDemand accept/reject/handoff |
| **Owning OS** | Revenue OS + MC04 integration |
| **Entry point** | Direct Python call to domain mutation functions |
| **Authoritative mutation function** | `apply_contact_status_update`, `apply_deal_stage_update`, `accept_qualified_demand`, `reject_qualified_demand`, `register_marketing_handoff` |
| **Bypassed guard** | Router-level `is_human_approver` only (defense at HTTP boundary insufficient) |
| **Requester types able to exploit** | Internal scripts, tests, future agent runtime calling service directly |
| **Human-only requirement** | YES |
| **Agent/AI exposure** | YES — spoofed `requested_by` string |
| **Audit exposure** | Partial — mutations could occur without route audit |
| **Severity** | **LOW** (no live agent path; accepted pattern in A3.5/A4.5/MC04.5 audits) |
| **Frozen contract affected** | A3.5, A4.5, MC04.5 (authority layering, not API contract) |
| **Runtime reproducibility** | YES — pre-fix: `apply_contact_status_update(db, contact, QUALIFIED)` without gate |
| **Remediation approach** | Add `require_human_mutation_authority(requested_by)` at canonical service boundary |
| **Expected files changed** | `revenue_os/services/mutation_authority.py`, `lead_scoring_service.py`, `deal_automation_service.py`, `qualified_demand_service.py`, `runner_api_routers/crm.py` |
| **Status** | **CLOSED** |

---

## UI1 reconciliation

UI1 reported **2 MEDIUM + 1 LOW** governance defects. This register identifies the same three paths with identical severities. No additional bypasses were discovered; no severity upgrades required.
