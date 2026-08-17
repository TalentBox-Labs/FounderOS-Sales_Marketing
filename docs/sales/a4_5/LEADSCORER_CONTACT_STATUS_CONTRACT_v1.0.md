# LEADSCORER / CONTACT.STATUS CONTRACT v1.0

**STATUS: FROZEN**  
**Sprint:** SALES A4.5  
**Date:** 2026-08-13  
**Parent:** Sales OS Architecture Baseline v1.0 (A1.5) — **UNCHANGED**  
**Sibling:** Runner Deal Stage Update v1.0 (A3.5) — **UNCHANGED**

**Core invariant:** MACHINE MAY RECOMMEND. HUMAN MUST DECIDE. SYSTEM MUST RECORD.

---

## 1. LeadScorer Contract

| Rule | Evidence |
|------|----------|
| Existing `LeadScorer` reused | `LeadScorer.calculate_score` in `lead_scoring_service.py` |
| No duplicate scoring engine in A4 path | Hermes/runner use `lead_scoring_service`; legacy `scoring_service.py` is separate Celery/JWT path (pre-existing) |
| Output is advisory | `suggest_status_from_score` returns recommendation enum; no persistence |

---

## 2. Score / Mutation Separation Contract

| Rule | Evidence |
|------|----------|
| Score MUST NOT mutate `Contact.status` | `score_contact` sets `lead_score` only; returns `status_changed: False` |
| Batch scoring MUST NOT promote | `score_contacts_batch` tracks `suggested_qualified`, not mutations |
| High score MUST NOT auto-qualify | `test_high_score_does_not_auto_qualify_via_score_endpoint` |

---

## 3. Human Authority Contract

| Rule | Evidence |
|------|----------|
| Status mutation requires authenticated runner caller | `_verify_api_key` on `PATCH /api/v1/crm/contacts/{id}/status` |
| Human identity required | `requested_by` field + `is_human_approver` |

---

## 4. Agent Prohibition Contract

| Rule | Evidence |
|------|----------|
| AI/agent/automation requester rejected | 403 for `agent`, `ai:*`, `bot` |
| Hermes planner qualify | Returns `eligible` list; `status_mutated: False` |
| Heartbeat / batch score | Score only via `score_contact` |
| Celery enrich | No auto-promotion |

---

## 5. Contact.status Validation Contract

| Rule | Evidence |
|------|----------|
| Valid enum required | `ContactStatus(req.status.strip().lower())` → 422 on invalid |
| Malformed UUID rejected | 422 |
| Missing contact rejected | 404 |
| Same status = deterministic noop | `changed: False`; no audit event on noop |

---

## 6. Canonical Model Contract

| Rule | Evidence |
|------|----------|
| Revenue `Contact` model | `revenue_os/models/contact.py` |
| Lead ≡ Contact alias | No parallel Lead table |
| No shadow model | A4 adds no new entities |

---

## 7. Audit Contract

| Event | When |
|-------|------|
| `LEAD_SCORED` | Successful score via runner POST |
| `CONTACT_STATUS_CHANGED` | Successful human status change only (`changed: True`) |
| Payload includes | `requested_by`, `old_status`, `new_status`, `lead_score`, optional `notes` |

Failed mutations (403/422/404) do not emit success audit.

---

## 8. Marketing Boundary Contract

A4 endpoints and services do not read or write Marketing-owned demand state.

---

## 9. Revenue Boundary Contract

| Allowed | Prohibited |
|---------|------------|
| `Contact.lead_score` update (score path) | Deal stage mutation |
| `Contact.status` update (human gate) | CommercialOutcome |
| EventBus contact events | External integration activation |

---

## 10. Runner Boundary Contract

| Rule | Evidence |
|------|----------|
| Runner orchestrates; does not embed scoring rules | Delegates to `LeadScorer` / `score_contact` |
| Business logic in service layer | `apply_contact_status_update` |

---

## Residual paths (documented, out of v1.0 slice)

Pre-existing ungated writers not remediated in A4:

- JWT `PUT /api/v1/contacts/{id}` status field
- n8n `meeting.booked` webhook

These are **not** LeadScorer-path regressions; future sprint scope.

---

## Supersession

Amendments require explicit ADR + approved sprint. Do not mutate A1.5 or A3.5 freeze documents.
