# Founder OS COS-2 Regression Reconciliation

| Envelope | Result |
|----------|--------|
| COS-2 focused | `tests/test_founder_os_cos2_marketing_qualified_demand.py` |
| COS-1 focused | `tests/test_founder_os_cos1_commercial_spine.py` |
| UI-D2 live + backward compat | previously certified filenames |
| D1.x | `test_demo_d1_init_db.py`, `test_demo_d1_1_init_demo_metrics.py`, `test_demo_d1_2_founder_company_seed.py` |
| UI-D1.5 live demo freeze | template absence of booking strings; seed still uses `register_marketing_handoff` |

No frozen test files modified.

INT-D2 activity still receives `action_type` strings in HTML (`data-testid="activity-event-type"`).

Seed now stamps QD handoff `organization_id` and includes stored qualification/attribution. D1.2 company seed assertions are unrelated to QD payload fields.

UI-D1 / UI-D1.5 copy assertions that require pre-COS-1 booking language (`booking workflow pending`, Command Center `Booking eligible`) or forbid `book_meeting` in founder_approvals remain **SUPERSEDED_NEGATIVE_SCOPE** vs UI-D2/COS-1. Frozen files untouched.

`test_demand_screen_renders` is satisfied by rendering People chrome even when org context is unavailable (empty lists; no unscoped query).
