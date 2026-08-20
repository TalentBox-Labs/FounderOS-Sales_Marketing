# Marketing Handoff Tenant Contract v1

## Purpose

Ensure Marketing → Sales QualifiedDemand handoffs carry tenant identity at persistence time, eliminating the COS-2 gap where `organization_id` was stamped in a second commit (or never stamped on some API paths).

## Write path

### Production API

`POST /api/v1/marketing/qualified-demand/handoff`

1. API key verification (unchanged)
2. Human approver gate (unchanged)
3. **`require_tenant_mutation()`** — fail closed if no org context
4. `register_marketing_handoff(..., organization_id=tenant.organization_id)`

First commit persists:

```python
AgentActionLog(
    action_type="qualified_demand.handoff",
    target_id=demand_id,
    organization_id=<trusted org UUID>,
    detail={"payload": ..., "requested_by": ..., "occurred_at": ...},
)
```

### Manual demand router (MDG1)

`runner_api_routers/manual_demand.py`:

- When `optional_tenant_mutation()` resolves a tenant, pass `organization_id` atomically
- When tenant absent (env-operator legacy), handoff may remain unscoped — explicit legacy path only

### Demo seed

`scripts/seed_founder_demo.py`:

- Passes demo org id to `register_marketing_handoff` at registration time
- Post-registration `stamp_agent_action_log_organization` removed

## Idempotency under tenancy

| Scenario | Result |
|----------|--------|
| Same demand_id, same tenant, repeat handoff | Idempotent OK |
| Same demand_id, different tenant | `ValueError: QualifiedDemand handoff not in tenant scope` |

## Read path (COS-2 unchanged)

Org-scoped Founder read models filter handoffs via `_handoff_payloads_for_org(org_uuid)` — requires stamped `organization_id` on handoff rows for tenant-scoped production data.

## Rejection rules

| Context | Unscoped handoff |
|---------|------------------|
| Production API with login + org cookie | **Rejected** at router (403) |
| Legacy env-operator / MC04 unit tests calling service directly | Allowed (explicit compat) |
| Tenant-scoped UI expecting pending demand | Unscoped rows invisible (fail-safe isolation) |

## Atomicity requirement

**MUST NOT** depend on a second transaction to stamp `organization_id` for tenant-scoped production requests.

`after_demand_register` / `stamp_agent_action_log_organization` remain for legacy callers that cannot pass org at insert time; production paths must not rely on them.
