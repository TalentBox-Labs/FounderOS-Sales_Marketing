# Integration Tenant Isolation Baseline v1.0

**Status:** FROZEN  
**Date:** 2026-08-17  
**Predecessor:** SaaS S4 implementation  
**Preserves:** SaaS S3.5 CRM baseline v1.0 (unchanged)

## Frozen perimeter

| Layer | Status |
|-------|--------|
| Organization-owned connector credentials | FROZEN |
| Tenant-safe vault lookup | FROZEN |
| Global fallback prohibition (tenant-owned) | FROZEN |
| n8n webhook tenant binding | FROZEN |
| Object ownership after org resolution | FROZEN |
| Service/agent/AI authority separation | PRESERVED |
| Audit tenant provenance | FROZEN |

## Residual (documented, not frozen as tenant-safe)

- Env-backed outbound connectors (OpenAI, n8n outbound)
- Editorial/publishing reads (GLOBAL_BY_DESIGN from S3.5)

## Database migrations in S4.5

**0** — attestation only; S4 migration preserved.
