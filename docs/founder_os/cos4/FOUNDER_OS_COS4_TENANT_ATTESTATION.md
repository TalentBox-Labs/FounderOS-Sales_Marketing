# Founder OS COS-4 Tenant Attestation

**STATUS:** BINDING

## Mandatory tenant context

Every production-reachable COS-4 path requires `organization_id`.

Missing or invalid org → `state=unavailable`, empty funnel (fail closed).

## Scoped reads

| Source | Scope mechanism |
|--------|-----------------|
| Deal / Contact | `build_operator_flow_snapshot(organization_id=…)` |
| QD / CO counts | `AgentActionLog.organization_id == org_uuid` |
| Approvals | Passed from org-filtered `list_requests(organization_id=…)` |
| Recent movement | Org-scoped activity list from Command Center |

## Company boundary

COS-4 **does not** query `Company` rows. No global name/domain lookup. Presentation hints from other surfaces are not re-used as aggregate roots.

## No global fallback

Composer never calls unscoped `db.query(Deal).all()` or equivalent when org is absent.
