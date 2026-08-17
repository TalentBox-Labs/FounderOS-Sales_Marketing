# S3 — Connector Credential Boundary

## Current state

Global vault: `credentials_vault.py` / `connector_credentials` table — no `organization_id`.

## S3 audit

CRM enrich (`/contacts/{id}/enrich`) uses Proxycurl via global credentials but operates on **tenant-scoped contact** first. Org A cannot enrich Org B contact (404).

No S3-covered route triggers connector execution using another tenant's semantic context.

## Classification

**SAFE_FOR_S3** — global credentials remain; cross-tenant object access blocked before connector invocation.

## Future

Tenant secret isolation deferred to dedicated security sprint (S2.5 FUTURE_SECURITY).
