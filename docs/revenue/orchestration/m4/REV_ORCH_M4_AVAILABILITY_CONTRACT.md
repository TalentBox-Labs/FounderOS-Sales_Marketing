# REV-ORCH M4 — Availability Contract

## Function: `get_tenant_availability(organization_id, duration_minutes=30)`

- Requires tenant-scoped calendar connector
- Returns normalized UTC ISO8601 slot list
- No persistent availability SoT
- BookingWorker consumes normalized slots as input only

## Isolation
Availability query uses organization_id from TenantContext only.
Cross-tenant availability read blocked by credential vault scoping.
