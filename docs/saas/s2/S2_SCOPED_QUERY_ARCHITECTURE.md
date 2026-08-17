# SaaS S2 — Scoped Query Architecture

## Pattern

```
TenantContext
  → optional_tenant_mutation() / resolve_tenant_context()
  → tenant_mutation_guard (scoped_* helpers)
  → tenant_scoped_access (organization_id + object_id lookup)
  → frozen domain operation (unchanged)
```

## Modules

| Module | Responsibility |
|--------|----------------|
| `tenant_scoped_access.py` | `get_contact_for_tenant`, `get_deal_for_tenant`, QD/CO handoff lookup, audit stamping |
| `tenant_mutation_guard.py` | Router-facing guards, post-mutation org stamps |
| `cockpit_read_model.py` / `operator_flow_read_model.py` | Read filtering by `organization_id` |

## Legacy compatibility

When `tenant is None`, guards fall back to ID-only lookup (pre-S2 env-operator / freeze tests).

## Prohibited

Rewriting frozen MC04.5 / MC06.5 / A3.5 / A4.5 service semantics to accept client tenant input.
