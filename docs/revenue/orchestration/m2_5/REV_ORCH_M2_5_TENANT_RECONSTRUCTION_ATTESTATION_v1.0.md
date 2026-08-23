# REV-ORCH M2.5 — Tenant Reconstruction Attestation v1.0

**STATUS: FROZEN**  
**SERVER_TRUSTED_TENANT_RECONSTRUCTION = FROZEN**  
**Cached Tenant Authority: PROHIBITED**

## Trusted source

Current persisted `Contact.organization_id` after reload via `get_contact_for_tenant(db, organization_id, contact_id)`.

## Rules

1. Contact is reloaded at proposal time and again at send time.
2. Current `Contact.organization_id` is authoritative.
3. Client JSON `organization_id` is ignored on API routes (`ResearchToOutreachRequest` unused for authority).
4. Stale cached org id passed to `run_follow_up_proposal_scheduled` fails closed (`get_contact_for_tenant` / org mismatch).
5. Cross-tenant Contact lookup fails closed (HTTP 422 propose / 404 approval).

## Scheduler scan classification

`scan_eligible_follow_ups` is GLOBAL_BY_DESIGN infrastructure scan of contacts that already have `organization_id`. Each candidate is then revalidated with `get_contact_for_tenant`. Scan-list org id is not sufficient authority by itself.

## API path

`require_tenant_context(http_request)` — session-bound TenantContext.
