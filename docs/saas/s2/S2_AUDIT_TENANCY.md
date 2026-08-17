# SaaS S2 — Audit Tenancy

## Store

`AgentActionLog.organization_id` (nullable, backfilled on bootstrap)

## Provenance

Tenant-owned operations stamp organization on:

- QualifiedDemand handoff (manual register)
- QualifiedDemand accept/reject
- CommercialOutcome handoff / accept/reject

## Attributable fields

- Human: `IdentityContext` + `requested_by` (server-bound, frozen S1.5)
- Organization: `TenantContext.organization_id`
- Action: `action_type`, `target_id`

## Cross-tenant audit visibility

Read models filter `AgentActionLog` by `organization_id` when tenant resolved.

## Frozen MC04.5 / MC06.5

No semantic changes to handoff payloads; outer wrapper stamps `organization_id` post-write where missing.
