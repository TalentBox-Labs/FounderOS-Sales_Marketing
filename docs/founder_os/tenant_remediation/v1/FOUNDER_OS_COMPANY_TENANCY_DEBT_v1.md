# Company Tenancy Debt v1

**Status:** DEFERRED ARCHITECTURE DEBT
**Sprint decision:** No Company migration in tenant remediation v1

## Current schema

`Company` has no `organization_id` column. Company rows are globally unique by name/domain lookup in legacy MC04 accept paths.

## Proven risk (COS-2 audit)

During `accept_qualified_demand`, legacy code could:

```python
db.query(Company).filter(Company.name == hint.name).first()
db.query(Company).filter(Company.domain == hint.domain).first()
```

Tenant A demand acceptance could bind Tenant B's Company record to a newly created Contact.

## v1 containment (implemented)

When trusted `organization_id` is present on accept:

- `_resolve_company_hint()` returns `None`
- New Contact is created without `company_id`
- Enrichment completeness is sacrificed for tenant safety

When `organization_id` is absent (legacy unscoped service calls):

- Prior global Company lookup behavior preserved for MC04 frozen unit tests only

## Acceptance path safety without migration

| Concern | v1 outcome |
|---------|------------|
| Cross-tenant Company bind on accept | **Blocked** when org-scoped |
| Cross-tenant Company lookup leak | **Blocked** — no lookup when org-scoped |
| In-tenant Contact create/link | **Safe** via org-filtered email match |
| Demo seed Company | Global demo Company unchanged; not auto-bound on scoped accept |

## Deferred work (post-remediation)

1. Add `Company.organization_id` (or equivalent tenant key) via migration
2. Scope Company CRUD and lookup helpers in `tenant_scoped_access`
3. Re-enable company_hint resolution under tenant-safe lookup
4. Backfill demo/production Company rows with org ownership
5. Add cross-tenant Company isolation tests at CRM layer

## Explicit non-action this sprint

- No new Company ownership model
- No Account/Prospect abstraction
- No automatic Company creation from marketing handoff under tenant scope

**Principle:** Tenant safety beats enrichment completeness.
