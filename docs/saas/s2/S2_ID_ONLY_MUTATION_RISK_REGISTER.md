# SaaS S2 — ID-Only Mutation Risk Register

## Critical risks (S0)

Cross-tenant data leakage via ID-only mutations without `organization_id` scoping.

## Ranked paths (S2 slice)

| # | Endpoint / path | Risk | S2 mitigation |
|---|-----------------|------|---------------|
| 1 | `POST /api/v1/operator/actions/contact-status` | HIGH | `scoped_contact()` |
| 2 | `POST /api/v1/cockpit/actions/contact-status` | HIGH | `scoped_contact()` |
| 3 | `POST /api/v1/operator/actions/deal/stage` | HIGH | `scoped_deal()` |
| 4 | `POST /api/v1/operator/actions/deal/create` | HIGH | `scoped_contact()` + `assign_new_deal_org()` |
| 5 | `POST .../qualified-demand/accept|reject` | HIGH | `scoped_demand_handoff()` |
| 6 | `POST .../commercial-outcome/accept|reject` | HIGH | `scoped_outcome_handoff()` |
| 7 | `POST .../commercial-outcome/handoff` | HIGH | `scoped_deal()` + stamp org |
| 8 | `POST /api/v1/mdg/manual-demand/register` | MEDIUM | `after_demand_register()` stamp |
| 9 | Ungated CRM API mutations | HIGH | **NOT_IN_SCOPE** (residual) |

**Identified:** 9  
**Mitigated in S2 scope:** 8/8 bounded Founder UI proxies
