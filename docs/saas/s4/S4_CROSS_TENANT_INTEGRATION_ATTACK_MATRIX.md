# S4 — Cross-Tenant Integration Attack Matrix

| Attack | Expected | Result |
|--------|----------|--------|
| Org B loads Org A credential | DENY | PASS |
| connector_name only | DENY | PASS |
| n8n bound to A + Contact B ID | 404 | PASS |
| forged payload organization_id | ignored | PASS |
| global fallback for tenant enrich | None | PASS |
