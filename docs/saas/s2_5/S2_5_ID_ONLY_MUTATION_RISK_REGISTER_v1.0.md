# S2.5 — ID-Only Mutation Risk Register v1.0

**Identified:** 9  
**Critical S2 mitigated:** 8/8  
**Ninth risk classification:** DEFERRED_TO_S3

## Reconciliation: why 9 identified but 8/8 mitigated

Risks 1–8 are **bounded Founder UI proxy mutations** (operator, cockpit, MDG). Risk 9 is the **ungated CRM REST API** — explicitly out of S2 scope and deferred to S3.

The denominator **8/8** refers to critical risks **within the S2 bounded slice**, not all risks in the repository.

## Full register

| # | Route / surface | Target | Mutation | Tenant-owned | S2 status | Guard | Test |
|---|-----------------|--------|----------|--------------|-----------|-------|------|
| 1 | `POST /api/v1/operator/actions/contact-status` | Contact | status | YES | MITIGATED | `scoped_contact()` | S2 + S2.5 |
| 2 | `POST /api/v1/cockpit/actions/contact-status` | Contact | status | YES | MITIGATED | `scoped_contact()` | S2.5 |
| 3 | `POST /api/v1/operator/actions/deal/stage` | Deal | stage | YES | MITIGATED | `scoped_deal()` | S2 + S2.5 |
| 4 | `POST /api/v1/operator/actions/deal/create` | Deal | create | YES | MITIGATED | `scoped_contact()` + `assign_new_deal_org()` | S2 guards |
| 5 | `POST .../qualified-demand/accept\|reject` | QD handoff | decision | YES (audit) | MITIGATED | `scoped_demand_handoff()` | S2 + S2.5 |
| 6 | `POST .../commercial-outcome/accept\|reject` | CO handoff | decision | YES (audit) | MITIGATED | `scoped_outcome_handoff()` | S2 + S2.5 |
| 7 | `POST .../commercial-outcome/handoff` | Deal→CO | handoff | YES | MITIGATED | `scoped_deal()` + stamp | S2 guards |
| 8 | `POST /api/v1/mdg/manual-demand/register` | QD handoff | register | YES (audit) | MITIGATED | `after_demand_register()` | S2 + S2.5 |
| 9 | `POST/PATCH /api/v1/crm/*` | Contact/Deal/Activity | various | YES | **DEFERRED_TO_S3** | none (API key only) | documented residual |

## Ninth risk detail

**Classification:** DEFERRED_TO_S3  
**Reason:** CRM API serves unmounted CRM SPA backend; S2 bounded slice intentionally excluded it. Documented in `S2_5_RESIDUAL_TENANCY_RISK_REGISTER_v1.0.md`.  
**Severity:** HIGH (cross-tenant possible if multi-org data + API key leaked)
