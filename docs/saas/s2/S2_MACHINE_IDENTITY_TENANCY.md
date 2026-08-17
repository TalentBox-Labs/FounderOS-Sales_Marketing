# SaaS S2 — Machine Identity Tenancy

## Rules (preserved from S1.5)

| Identity | Human authority | Tenant access |
|----------|-----------------|---------------|
| HUMAN (session) | YES (HUMAN_ONLY paths) | Membership-derived |
| SERVICE (`RUNNER_API_KEY`) | **NO** | No automatic multi-tenant access |
| AGENT | **NO** | Global/internal unless explicit future binding |
| AI | **NO** | Global/internal unless explicit future binding |

## S2 enforcement

`require_tenant_mutation_role()` rejects non-human principals for tenant mutations.

## Global/internal operations

Heartbeat, agent registry seed, connector hydration remain global — documented explicitly.
