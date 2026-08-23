# S3 — Post-Implementation Query Isolation Audit

## CRM patterns verified

| Pattern | CRM coverage |
|---------|--------------|
| `db.get(Contact, id)` without org | Replaced with `scoped_contact` when tenant present |
| `db.query(Contact).all()` | Replaced with `apply_contact_org_filter` when tenant present |
| `db.get(Deal, id)` without org | Replaced with `scoped_deal` when tenant present |
| `db.query(Deal).all()` | Replaced with `apply_deal_org_filter` when tenant present |
| Activity by ID | `verify_activity_in_tenant` when tenant present |
| Pipeline health global | Org filter via `organization_id` param |

## Residual unscoped (documented)

- n8n webhooks — contact_id from payload
- Editorial/publishing reads — global content
- Legacy no-tenant CRM path — single-founder API-key-only mode

## CRM ID-only risk #9

**MITIGATED** when TenantContext resolves.
