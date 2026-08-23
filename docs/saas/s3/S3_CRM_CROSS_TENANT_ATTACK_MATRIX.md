# S3 — CRM Cross-Tenant Attack Matrix

| Attack | Actor | Expected | S3 result |
|--------|-------|----------|-----------|
| List contacts | Owner A | only Org A | PASS |
| GET Contact B | Owner A | 404 | PASS |
| PATCH Contact B status | Owner A | 404 | PASS |
| PATCH Contact A status | Viewer A | 403 | PASS |
| List deals | Owner B | only Org B | PASS |
| PATCH Deal B stage | Owner A | 404 | PASS |
| Search contacts | Owner A | no B emails | PASS |
| Pipeline summary | Owner A | count=1 | PASS |
| Spoof org in JSON body | Owner A | ignored, 404 | PASS |
| Create contact | Owner A | org stamped | PASS |

Failure semantics: 404 for cross-tenant object access (non-leaking).
