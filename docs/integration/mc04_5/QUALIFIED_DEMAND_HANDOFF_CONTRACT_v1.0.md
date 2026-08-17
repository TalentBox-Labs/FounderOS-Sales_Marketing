# QUALIFIED DEMAND HANDOFF CONTRACT v1.0

**STATUS: FROZEN**  
**Baseline:** FOUNDER OS QUALIFIED DEMAND HANDOFF v1.0  
**Date:** 2026-08-13  
**Parent contracts:** Sales↔Marketing boundary v1.0 (A1.5) — **UNCHANGED**

**Core invariant:** Marketing-owned qualification → bounded handoff → Sales acceptance → canonical Contact ownership → audit. **Not a shared SoT.**

---

## Producer / Consumer

| Role | Component |
|------|-----------|
| **Producer** | Marketing operator via `POST /api/v1/marketing/qualified-demand/handoff` |
| **Consumer** | Sales operator via `POST /api/v1/sales/intake/demand/accept` or `/reject` |

---

## Ownership

| Phase | Marketing | Sales |
|-------|-----------|-------|
| Before handoff | Qualification + attribution | — |
| After handoff register | Payload immutable in audit | — |
| After accept | Read-only provenance on Contact | Contact SoT |
| After reject | Unchanged | Audit only |

**No shared writable record.**

---

## Input contract

Minimum payload per frozen A1 contract: `demand_id`, `occurred_at`, `source`, `person.email`, optional `channel`, `company_hint`, `marketing_qualification`, `consent`, `content_attribution`.

`demand_id` must be UUID.

---

## Acceptance semantics

- Requires prior handoff registration for `demand_id`
- Human `requested_by` + API key
- Creates Contact with `status=LEAD` or merges by email
- Sets `ContactSource` from `source` mapping
- **No** auto-qualify, **no** Deal, **no** Revenue mutation
- Emits accept audit + optional EventBus event

---

## Rejection semantics

- Requires prior handoff
- Human gate
- Audit only; **no** Contact create
- Idempotent on repeat reject

---

## Idempotency / Duplicate / Retry

| Case | Behavior |
|------|----------|
| Same handoff twice | Idempotent register |
| Same accept twice | Same `contact_id` |
| Same email, new demand | Merge Contact |
| Accept after reject blocked path | Reject before accept only |
| Retry after commit failure | Safe via audit lookup |

---

## Audit / Provenance

| Event | action_type |
|-------|-------------|
| Handoff | `qualified_demand_handoff` |
| Accept | `qualified_demand_accepted` |
| Reject | `qualified_demand_rejected` |

Provenance copied to Contact `notes` on accept/merge.

---

## Authority

- `is_human_approver` required on all three endpoints
- Agent/AI/bot → 403

---

## Error semantics

| Code | Condition |
|------|-----------|
| 403 | Non-human requester |
| 422 | Invalid payload, missing handoff, reject after accept |

---

## Isolation guarantees

| Guarantee | Status |
|-----------|--------|
| No shared SoT | **PROHIBITED** |
| Canonical Contact preserved | **YES** |
| Marketing state protection | Handoff does not write CRM |
| Sales state protection | No pre-accept Contact mutation |
| Revenue isolation | No CommercialOutcome / Deal auto-create |

---

## Supersession

New ADR + approved sprint required to change frozen behavioral contract.
