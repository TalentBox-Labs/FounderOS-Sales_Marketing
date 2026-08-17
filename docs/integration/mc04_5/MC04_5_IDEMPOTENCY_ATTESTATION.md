# MC04.5 — Idempotency Attestation (LEDGER)

**Sprint:** FOUNDER OS MC04.5  
**Date:** 2026-08-13

---

## Test evidence (MC04 suite re-run: 12/12)

| # | Scenario | Test | Result |
|---|----------|------|--------|
| 1 | Same handoff twice | `test_handoff_idempotent` | **PASS** |
| 2 | Same accept twice | `test_accept_idempotent` | **PASS** |
| 3 | Reject without Contact | `test_reject_creates_audit` | **PASS** |
| 4 | Duplicate email | `test_duplicate_email_merges_not_duplicates` | **PASS** |
| 5 | Accept without handoff | `test_accept_without_handoff_rejected` | **PASS** 422 |
| 6 | Handoff no CRM | `test_register_handoff_does_not_create_contact` | **PASS** |

## Deterministic repeat behavior

| Operation | Repeat outcome |
|-----------|------------------|
| Handoff | `idempotent: true`, single audit row |
| Accept | Same `contact_id` |
| Reject | `idempotent: true` |

## Duplicate Sales entity prevention

- Email merge: **1 Contact** for duplicate email
- demand_id accept idempotency: **no second Contact** on replay

**Idempotency Contract: FROZEN**  
**Duplicate Safety Contract: FROZEN**
