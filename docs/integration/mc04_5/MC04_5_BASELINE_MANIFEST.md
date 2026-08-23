# MC04.5 — Baseline Manifest

**Baseline:** FOUNDER OS QUALIFIED DEMAND HANDOFF v1.0  
**Status:** FROZEN  
**Date:** 2026-08-13

---

## Frozen version

**v1.0**

---

## Artifacts

| Path | Role |
|------|------|
| `docs/integration/mc04_5/QUALIFIED_DEMAND_HANDOFF_BASELINE_v1.0.md` | Behavioral baseline |
| `docs/integration/mc04_5/QUALIFIED_DEMAND_HANDOFF_CONTRACT_v1.0.md` | Contract |
| `docs/integration/mc04_5/MC04_5_BASELINE_MANIFEST.md` | This manifest |
| `docs/integration/mc04_5/MC04_5_*` | Attestation pack |

---

## Runtime / API (frozen behavior SoT)

| Path |
|------|
| `revenue_os/services/qualified_demand_service.py` |
| `runner_api_routers/qualified_demand.py` |
| `runner_api.py` (router include only) |

---

## Tests

| Path | At freeze |
|------|-----------|
| `tests/test_mc04_qualified_demand.py` | 12/12 |

Sibling frozen suites unchanged: A4.5 15/15, A3.5 15/15.

---

## Authority / ownership / idempotency

| Rule | Reference |
|------|-----------|
| Human gate all endpoints | `MC04_5_AUTHORITY_ATTESTATION.md` |
| Marketing owns pre-accept | `MC04_5_OWNERSHIP_ATTESTATION.md` |
| Sales owns post-accept Contact | same |
| demand_id idempotency | `MC04_5_IDEMPOTENCY_ATTESTATION.md` |
| No shared SoT | Contract v1.0 |

---

## Known historical exceptions (A1.5)

2 × `test_prospecting_ui.py` — ENVIRONMENT_DEPENDENCY — verified 2/2 MATCH  
See `A1_5_EXCEPTION_RECONCILIATION.md`.

---

## Regression at freeze

439/451 passed; 8 failed; 4 errors; **0 new regressions**

---

## MC04.5 sprint delta

| Item | Count |
|------|------:|
| Feature code changes | 0 |
| Runtime changes | 0 |
| DB migrations | 0 |

---

## Change control

Amendments require ADR + approved sprint. Do not mutate A1.5/A3.5/A4.5 or Sales↔Marketing boundary meaning.

---

## Post-freeze recommendation (not executed)

1. **UI1** — Founder OS Unified Shell & Executive Cockpit Audit  
2. **CP3** — Cross-OS Priority Checkpoint
