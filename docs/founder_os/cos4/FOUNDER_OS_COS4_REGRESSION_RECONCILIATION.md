# Founder OS COS-4 Regression Reconciliation

**Gate run:** COS-4 focused (incl. semantic correction v1) + COS-3 + tenant remediation + COS-2 + COS-1 + MC04 v2 + D1.x + S3 tenant isolation

## COS-4 focused

`tests/test_founder_os_cos4_commercial_funnel_intelligence.py`

Covers: tenant isolation, read-only authority, funnel mapping, attention semantics, Company safety, Command Center integration, COS-3 coexistence, **semantic correction v1** (QD/CO unique-id reconciliation, sales stage classification).

## Semantic correction proofs

| Proof | Test |
|-------|------|
| Duplicate QD handoff ≠ inflate pending | `test_duplicate_qd_handoff_does_not_inflate_pending` |
| Duplicate QD accept ≠ inflate accepted | `test_duplicate_qd_accept_does_not_inflate_accepted` |
| Duplicate QD reject ≠ inflate rejected | `test_duplicate_qd_reject_does_not_inflate_rejected` |
| Accept/reject removes pending | `test_accepted_rejected_removed_from_pending` |
| Duplicate CO handoff ≠ realized unique | `test_duplicate_co_handoff_does_not_inflate_unique_outcomes` |
| CO accept reconciles to one outcome | `test_co_accepted_rejected_reconciles_to_one_outcome` |
| Unknown stage not open | `test_unknown_deal_stage_is_not_open` |
| Recruitment not open pipeline | `test_recruitment_stage_not_in_open_pipeline_band`, `test_recruitment_placed_not_open_commercial_pipeline` |
| Sales open / won / lost | `test_canonical_sales_open_stage_is_open`, `test_closed_won_is_won`, `test_closed_lost_is_lost` |

## Regression suites (representative combined gate)

| Suite | Result |
|-------|--------|
| COS-3 decision loop | PASS |
| Tenant remediation v1 | PASS |
| MC04 tenant v2 | PASS |
| COS-2 marketing QD | PASS |
| COS-1 commercial spine | PASS |
| D1.x demo init | PASS |
| S3 CRM tenant isolation | PASS |

## Frozen tests

No frozen historical tests modified.
