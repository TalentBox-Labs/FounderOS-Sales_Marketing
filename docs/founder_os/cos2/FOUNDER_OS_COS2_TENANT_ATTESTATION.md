# Founder OS COS-2 Tenant Attestation

## Queries introduced/changed

Pending-demand enrichment in `founder_ui_read_model._handoff_payloads_for_org`:

- Requires resolved `organization_id` UUID.
- Filters `AgentActionLog.action_type == qualified_demand_handoff`.
- Filters `AgentActionLog.organization_id == org_uuid`.
- Restricts `target_id` to IDs already in the org-scoped operator-flow pending list.

Company names on People remain COS-1 scoped Contact IDs + `Contact.organization_id`.

Pending demand **does not** query `Company` (company hint is payload text only).

## Fail closed

`build_demand_contacts_snapshot` still returns empty contacts/demands when org UUID cannot resolve and does not open SessionLocal for enrichment.

If org is missing on Command Center, enrichment does not load other orgs’ payload fields via the new helper (helper is not called without org UUID).

## Residual (pre-existing, not widened)

- `register_marketing_handoff` still does not set `organization_id` itself; tenant stamp remains `after_demand_register` / `stamp_agent_action_log_organization` (MDG1 and COS-2 seed/tests).
- `accept_qualified_demand` still matches Contact by email globally (MC04 canonical). COS-2 does not modify that service. Operator path stamps org after accept when tenant context exists.
- `Company` has no tenant key (architecture debt). COS-2 avoids Company lookup for demand cards.
