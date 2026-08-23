# S3.5 — CRM Cross-Tenant Attack Matrix v1.0

**Orgs:** A (`org-a`), B (`org-b`)  
**Users:** A_OWNER, A_VIEWER, B_OWNER  
**Objects:** Contact A/B, Deal A/B

| # | Attack | Actor | Expected | Verified |
|---|--------|-------|----------|----------|
| 1 | List contacts | A_OWNER | only A | PASS |
| 2 | GET Contact B | A_OWNER | 404 | PASS |
| 3 | PATCH Contact B status | A_OWNER | 404 | PASS |
| 4 | PATCH Contact A status | A_VIEWER | 403 | PASS |
| 5 | List deals | B_OWNER | only B | PASS |
| 6 | PATCH Deal B stage | A_OWNER | 404 | PASS |
| 7 | Search contacts "example" | A_OWNER | no B emails | PASS |
| 8 | Pipeline summary | A_OWNER | total_deals=1 | PASS |
| 9 | Spoof org_id in JSON body | A_OWNER | ignored, 404 | PASS |
| 10 | Create contact | A_OWNER | org stamped A | PASS |
| 11 | A_OWNER role in A → access B | A_OWNER | 404 on B IDs | PASS |

**Failure semantics:** 404 cross-tenant object access; 403 VIEWER mutation.

**Evidence:** `tests/test_saas_s3_crm_tenant_isolation.py`, `tests/test_saas_s3_5_crm_tenant_isolation_baseline_freeze.py`
