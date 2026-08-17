# SaaS S2 — Implementation Manifest

## New files

| Path | Purpose |
|------|---------|
| `revenue_os/models/organization.py` | Organization + membership |
| `revenue_os/services/tenant_context.py` | TenantContext dataclass |
| `revenue_os/services/tenant_resolution.py` | Resolution + role gate |
| `revenue_os/services/tenant_scoped_access.py` | org_id + object_id lookups |
| `revenue_os/services/tenant_mutation_guard.py` | Router guards |
| `revenue_os/services/tenant_bootstrap.py` | Bootstrap + backfill |
| `runner_api_routers/tenant.py` | Tenant API |
| `tests/test_saas_s2_tenant_isolation.py` | S2 focused tests |
| `docs/saas/s2/*` | S2 documentation set |

## Modified files

| Path | Change |
|------|--------|
| `revenue_os/models/contact.py` | `organization_id` |
| `revenue_os/models/deal.py` | `organization_id` |
| `revenue_os/models/automation_state.py` | `organization_id` on AgentActionLog |
| `runner_api_routers/cockpit.py` | Tenant guards + filtered snapshot |
| `runner_api_routers/operator_flow.py` | Tenant guards on all mutations |
| `runner_api_routers/manual_demand.py` | Tenant guard + org stamp |
| `runner_api_routers/identity.py` | Org cookie on login/logout |
| `runner_api_routers/ui.py` | Tenant-filtered cockpit/operator reads |
| `revenue_os/services/cockpit_read_model.py` | org filter |
| `revenue_os/services/operator_flow_read_model.py` | org filter |
| `runner_api.py` | Migration patches, tenant router, bootstrap |

## Frozen contract changes

**0** — domain services unchanged; wrappers only.

## Credentials committed

**0**

## External integrations activated

**0**
