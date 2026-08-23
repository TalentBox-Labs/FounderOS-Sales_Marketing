# UI2 — Action Authority Map

**Sprint:** UI2  
**Date:** 2026-08-13

## Action 1 — QualifiedDemand Accept

| Layer | Implementation |
|-------|----------------|
| UI trigger | `templates/cockpit.html` → `acceptDemand()` |
| Cockpit proxy | `POST /api/v1/cockpit/actions/qualified-demand/accept` |
| Trusted identity | `FOUNDER_OS_OPERATOR_NAME` env (server-only) |
| Canonical mutation | `accept_qualified_demand()` |
| Human gate | `require_human_mutation_authority` + `is_human_approver` |
| Client `requested_by` | **REJECTED** — not in request schema |
| Audit | `AgentActionLog` + EventBus `CONTACT_IMPORTED` |
| Deal creation | **NO** |
| Auto-qualify | **NO** |

## Action 2 — Contact.status Update

| Layer | Implementation |
|-------|----------------|
| UI trigger | `templates/cockpit.html` → `updateContactStatus()` |
| Cockpit proxy | `POST /api/v1/cockpit/actions/contact-status` |
| Trusted identity | `FOUNDER_OS_OPERATOR_NAME` env (server-only) |
| Canonical mutation | `apply_contact_status_update()` |
| Human gate | Service-layer authority (UI1.1) |
| Client `requested_by` | **REJECTED** — not in request schema |
| Score auto-qualify | **NO** — display recommendation only |
| Audit | EventBus `CONTACT_STATUS_CHANGED` |

## Deferred (NOT exposed)

- QualifiedDemand reject
- Deal stage PATCH
- Editorial approve/reject
- Publishing promote
- Marketing handoff register

## Security posture

UI is **not** the security boundary. Backend derives operator from env; spoofed form fields cannot override.
