# SaaS S0 — Secrets Isolation

**Sprint:** SaaS S0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY

## Current state

| Store | Scope |
|-------|-------|
| Env (OpenAI, n8n, SMTP, LinkedIn token, CF tokens, …) | **GLOBAL** per deployment |
| Credentials vault (`ConnectorCredentialRecord`) | **GLOBAL** — PK = `connector_name` |
| Fernet key | Derived from instance `SECRET_KEY` |
| Outlook Azure `tenant_id` | Field inside global connector config — **not** SaaS tenancy |

## Multi-tenant implication

When tenants connect LinkedIn / Google / GSC / email / publishing:

Secrets must become **`(organization_id, connector_name)`** (or workspace-scoped), never overwrite a single global connector row.

## Recommended future architecture (not implemented)

```
Organization
  └── ConnectorCredential (org_id, connector_name, encrypted payload)
Platform
  └── Platform-only secrets (billing provider, etc.)
```

Current Secret Isolation: **GLOBAL / INSTANCE**
