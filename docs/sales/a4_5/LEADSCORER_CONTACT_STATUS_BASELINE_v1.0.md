# LEADSCORER / CONTACT.STATUS BASELINE v1.0

**STATUS: FROZEN**  
**Sprint:** SALES A4.5  
**Date:** 2026-08-13  
**Implementation sprint:** SALES A4 (COMPLETE_EXISTING)

**Parent:** Sales OS Architecture Baseline v1.0 (A1.5 / ADR-005) — **UNCHANGED**  
**Sibling:** Runner Deal Stage Update v1.0 (A3.5 / ADR-007) — **UNCHANGED**

---

## Frozen behavioral flow

```
Lead / Contact
  → LeadScorer.calculate_score (existing)
  → score + suggested_status (recommendation)
  → human decision (requested_by + is_human_approver)
  → apply_contact_status_update
  → EventBus CONTACT_STATUS_CHANGED
```

**Invariant:** A score MUST NOT directly mutate `Contact.status`.

---

## Frozen endpoints

| Method | Path | Authority |
|--------|------|-----------|
| POST | `/api/v1/crm/contacts/{contact_id}/score` | API key; score only |
| PATCH | `/api/v1/crm/contacts/{contact_id}/status` | API key + human `requested_by` |

---

## Frozen implementation SoT

| File | Function / endpoint |
|------|---------------------|
| `revenue_os/services/lead_scoring_service.py` | `LeadScorer`, `score_contact`, `apply_contact_status_update` |
| `runner_api_routers/crm.py` | `score_contact_endpoint`, `update_contact_status_endpoint` |
| `revenue_os/models/contact.py` | `Contact`, `ContactStatus` |
| `src/tools/editorial_approval.py` | `is_human_approver` |

---

## Frozen test suite

| File | Result at freeze |
|------|------------------|
| `tests/test_a4_runner_contact_status.py` | **15/15** |

---

## Regression attestation at freeze

| Suite | Result |
|-------|--------|
| A4 focused | 15/15 |
| A3.5 frozen | 15/15 |
| A1.5 focused (4 files) | 15/17 (2 known exceptions) |
| Full regression | 427/439; 8 failed; 4 errors |
| Historical failures | UNCHANGED |
| New regressions | 0 |

---

## Prohibited without architecture review

- Agent/AI autonomous Contact.status mutation via LeadScorer path
- Re-coupling score → status auto-promotion
- New scoring engine duplication
- CRM SPA mount as side effect
- DB schema migration for this capability
- External integration activation
- Mutation of A1.5 or A3.5 frozen contract meaning

---

## Supersession

New ADR + approved sprint required to change frozen behavioral contract.
