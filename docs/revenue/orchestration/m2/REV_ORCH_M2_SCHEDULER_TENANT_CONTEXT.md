# REV-ORCH M2 — Scheduler Tenant Context

## Problem

Delayed follow-up work must not rely on ambient request-scoped `TenantContext`.

## Solution

| Path | Tenant reconstruction |
|------|----------------------|
| API propose | `require_tenant_context(http_request)` — session-bound |
| Heartbeat `job_scan_follow_up_eligibility` | `Contact.organization_id` from DB (server-trusted) |
| Scheduled proposal | `run_follow_up_proposal_scheduled(db, org_id, contact_id)` validates `get_contact_for_tenant` and org match |

Client-supplied `organization_id` in JSON body is ignored on API routes (same as M1).

n8n inbound events resolve tenant via `X-N8N-Secret` binding — never from payload `organization_id`.

## Scheduler job

- Name: `scan_follow_up_eligibility`
- Env: `HEARTBEAT_FOLLOWUP_SCAN_SEC` (default 3600)
- Action: scan eligible contacts → file ApprovalRequest only (no send)

Human approval remains required before any outbound side effect.
