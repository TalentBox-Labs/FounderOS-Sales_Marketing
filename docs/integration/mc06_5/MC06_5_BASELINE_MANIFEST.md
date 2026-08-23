# MC06.5 — Baseline Manifest

**Baseline:** FOUNDER OS COMMERCIAL OUTCOME v1.0  
**Status:** FROZEN  
**Date:** 2026-08-13

---

## Frozen version

**v1.0**

---

## Artifacts

| Path | Role |
|------|------|
| `docs/integration/mc06_5/COMMERCIAL_OUTCOME_BASELINE_v1.0.md` | Behavioral baseline |
| `docs/integration/mc06_5/COMMERCIAL_OUTCOME_OWNERSHIP_CONTRACT_v1.0.md` | Ownership |
| `docs/integration/mc06_5/COMMERCIAL_OUTCOME_AUTHORITY_CONTRACT_v1.0.md` | Authority |
| `docs/integration/mc06_5/COMMERCIAL_OUTCOME_IDEMPOTENCY_CONTRACT_v1.0.md` | Idempotency / duplicates |
| `docs/integration/mc06_5/COMMERCIAL_OUTCOME_PROVENANCE_AUDIT_CONTRACT_v1.0.md` | Provenance + audit |
| `docs/integration/mc06_5/COMMERCIAL_OUTCOME_KNOWN_TEST_EXCEPTIONS.md` | Exceptions register |
| `docs/integration/mc06_5/MC06_5_BASELINE_MANIFEST.md` | This manifest |
| `docs/integration/mc06_5/MC06_5_*` | Attestation pack |

MC06 implementation notes (not freeze SoT): `docs/integration/mc06/*`

---

## Runtime / API (frozen behavior SoT)

| Path |
|------|
| `revenue_os/services/commercial_outcome_service.py` |
| `runner_api_routers/commercial_outcome.py` |
| `runner_api.py` (router include only) |
| `revenue_os/automation/events.py` (`COMMERCIAL_OUTCOME_*` only) |

---

## Persistence (frozen)

`AgentActionLog` / table `agent_action_log`  
action types: `commercial_outcome_handoff` · `commercial_outcome_accepted` · `commercial_outcome_rejected`

---

## Tests

| Path | At freeze |
|------|-----------|
| `tests/test_mc06_5_commercial_outcome_baseline_freeze.py` | **22/22** |
| `tests/test_mc06_commercial_outcome.py` | **28/28** |

Sibling frozen suites unchanged: A3.5 15/15, A4.5 15/15, MC04.5 12/12, A1.5 15/17, UI2.5 20/20.

---

## Change control

Amendments require ADR + approved sprint.  
Do not mutate A1.5 / A3.5 / A4.5 / MC04.5 / UI2.5 meaning.

---

## MC06.5 sprint delta

| Item | Count |
|------|------:|
| Feature code changes | 0 |
| Runtime changes | 0 |
| DB migrations | 0 |
| Previous frozen contract changes | 0 |

---

## Post-freeze recommendation (not executed)

Do not start Revenue OS expansion, cockpit work, MC04.1, or another checkpoint in this sprint.
