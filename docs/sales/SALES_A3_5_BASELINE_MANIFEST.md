# SALES A3.5 — Baseline Manifest

**Baseline:** SALES RUNNER DEAL STAGE UPDATE v1.0  
**Status:** FROZEN  
**Date:** 2026-08-13  
**ADR:** [Architecture_ADR_007.md](../architecture/Architecture_ADR_007.md)

Parent: Sales OS Architecture Baseline v1.0 — **UNCHANGED**

---

## Frozen artifacts

| Path | Role |
|------|------|
| `docs/sales/SALES_RUNNER_DEAL_STAGE_BASELINE_v1.0.md` | Behavioral baseline |
| `docs/sales/SALES_RUNNER_DEAL_STAGE_CONTRACT_v1.0.md` | Interface contract |
| `docs/sales/SALES_A3_5_BASELINE_MANIFEST.md` | This manifesto |
| `docs/sales/SALES_A3_5_KNOWN_TEST_EXCEPTIONS.md` | Exceptions + A3 suite |
| `docs/architecture/Architecture_ADR_007.md` | Freeze ADR |
| `docs/sales/a3_5/A3_5_*` | Attestation pack |

## Implementation files (frozen behavior SoT)

| Path |
|------|
| `runner_api_routers/crm.py` — `PATCH .../deals/{id}/stage` |
| `revenue_os/services/deal_automation_service.py` — `apply_deal_stage_update` / `advance_deal_stage` |
| `revenue_os/models/deal.py` — canonical Deal / DealStage |

## Tests

| Suite | Result at freeze |
|-------|------------------|
| `tests/test_a3_runner_deal_stage.py` | 15/15 |
| A1.5 focused (4 files) | 15/17 |
| Full regression | 412/424; 8 failed; 4 errors |

## Known historical exceptions (A1.5)

See `SALES_A1_5_KNOWN_TEST_EXCEPTIONS.md` — **2** ENVIRONMENT_DEPENDENCY errors on `test_prospecting_ui.py` (verified MATCH in A3.5 reconciliation).

## Prohibited authority expansion

- Agent/AI deal-stage mutation  
- CommercialOutcome silent creation  
- CRM mount as side effect  
- External integration activation for this baseline  

## Dependency boundaries

| Boundary | Rule |
|----------|------|
| Marketing | No dependency |
| Revenue | Deal SoT; Sales ops only |
| Shared | API key auth |
| External | None required |

## Supersession

New ADR + approved sprint required to change frozen behavioral contract. Do not mutate A1.5 freeze docs.
