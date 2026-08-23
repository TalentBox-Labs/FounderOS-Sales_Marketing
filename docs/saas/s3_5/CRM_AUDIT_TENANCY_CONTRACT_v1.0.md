# CRM Audit Tenancy Contract v1.0

## Preserved behavior

CRM mutations retain existing audit/event metadata:

| Field | Source |
|-------|--------|
| Actor identity | Human session / `requested_by` (A3/A4) |
| Organization identity | `TenantContext.organization_id` when resolved |
| Target identity | contact_id / deal_id / activity_id |
| Action | Event type (LEAD_CREATED, CONTACT_STATUS_CHANGED, DEAL_STAGE_CHANGED, etc.) |
| Timestamp | Existing model/event timestamps |

## Audit store

**No new audit store.** Reuses EventBus + Activity timeline + existing AgentActionLog architecture from S2.

## Cross-tenant audit visibility

**BLOCKED** — audit queries in cockpit/operator scoped by organization (S2.5 frozen).

## CRM-specific notes

- Enrich creates Activity note on tenant-scoped contact only
- Status/stage changes emit events with `requested_by` in payload
- n8n webhook audit (`actor = "n8n"`) remains **outside** this frozen CRM perimeter (deferred)
