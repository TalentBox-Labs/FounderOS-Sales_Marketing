# OPERATOR VALUE CHAIN SCOPE v1.0

**STATUS: FROZEN**  
**Invariant ID:** OF1.5-SCOPE-001

## Two statuses (must not be conflated)

| Scope | Chain | Status |
|-------|-------|--------|
| **Bounded operator flow** | Demand → Revenue Decision | **COMPLETE** |
| **Total Founder OS value chain** | Audience → Demand → Revenue Decision | **PARTIAL** |

**Remaining upstream break:** Audience → Demand  

OF1 / OF1.5 do **not** expose `POST /api/v1/marketing/qualified-demand/handoff`.  
No web-form / inbound capture.

## Prohibition

Code and documentation MUST NOT treat “Founder Operating Flow COMPLETE” as “Founder OS End-to-End Value Chain COMPLETE” until Audience → Demand is separately implemented and frozen.

Regression: `tests/test_of1_5_operator_flow_baseline_freeze.py` (`test_freeze_value_chain_scope_not_conflated`).
