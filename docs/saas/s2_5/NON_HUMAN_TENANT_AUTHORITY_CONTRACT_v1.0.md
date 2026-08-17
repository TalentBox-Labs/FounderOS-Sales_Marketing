# Non-Human Tenant Authority Contract v1.0

**Status:** FROZEN

## Identity classes

| Class | Human authority | Tenant mutations |
|-------|-----------------|------------------|
| HUMAN (session) | YES (HUMAN_ONLY paths) | YES when membership + role allow |
| SERVICE (RUNNER_API_KEY) | **NO** | NO |
| AGENT | **NO** | NO |
| AI | **NO** | NO |

## Prohibited spoofing vectors

Non-human identities must not gain human authority via:

- `requested_by` in client body
- `organization_id` / `tenant_id` in body, query, or headers
- `user_id` impersonation metadata
- forged human display names without session

## requested_by server binding (S1.5 preserved)

- `bind_requested_by()` rejects non-human principals
- MDG / operator / cockpit proxies derive operator from `resolve_trusted_human()`
- Client `requested_by` fields absent from mutation bodies

## Tenant mutation gate

`require_tenant_mutation_role()` rejects non-human `IdentityContext` before role check.

## Global service operations

Heartbeat, agent seed, connector hydration operate without tenant context — global/internal by design.
