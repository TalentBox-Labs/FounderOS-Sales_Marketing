# Global Credential Fallback Contract v1.0

## Default

`load_credentials(..., allow_global_fallback=False)`

## Tenant-owned rule

When `organization_id` is set and org row missing → **return None** (SAFE FAILURE).

NULL-org row MUST NOT satisfy tenant request unless `allow_global_fallback=True` (not used on tenant paths).

## Attack matrix (frozen)

| Scenario | Expected |
|----------|----------|
| Org A request, only NULL-org credential X | None / not configured |
| Org A has X, Org B requests X | B gets None |
| Org B request, NULL-global X exists | None (no fallback) |
| Startup hydrate | NULL-org rows loaded (GLOBAL_BY_DESIGN) |

## Explicit global paths

- `hydrate_all_connectors()` — process startup only
- `load_credentials(organization_id=None)` — legacy/no-session
- Env-backed catalog connectors — no vault row
