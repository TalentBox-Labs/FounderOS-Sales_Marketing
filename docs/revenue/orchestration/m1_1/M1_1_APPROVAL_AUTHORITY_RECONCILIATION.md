# M1.1 Approval Authority Reconciliation

**Sprint:** REV-ORCH M1.1  
**Date:** 2026-08-17

---

## Problem

`decide()` legacy path (no session tenant) accepted client `decided_by`, allowing identity spoofing on API-key-only approve/reject.

## Resolution

### Service layer (`approvals.py`)

`_human_decider()` when `tenant is None`:
- **Raises `HumanAuthorityError`** — session tenant required
- Client `decided_by` cannot establish human authority

### Router layer (`runner_api_routers/approvals.py`)

`approve` and `reject` endpoints:
- Always call `require_tenant_context(http_request)` before `decide()`
- No fallback to client `decided_by`

### Preserved

- Session-bound approver from `TenantContext.identity` (display_name / email)
- `get_approval_for_tenant` on decide
- Outbound payload validation before n8n
- Idempotent re-approve skip

## Attack Matrix (post-M1.1)

| Attack | Result |
|--------|--------|
| Agent `decided_by` without session | **403 BLOCKED** |
| Human name spoof without session | **403 BLOCKED** |
| Cross-tenant approval | **404 BLOCKED** (tenant-scoped lookup) |
| Unapproved outbound | **BLOCKED** (pending gate) |
| Rejected outbound | **BLOCKED** (no executor) |

## Verdict

**Legacy decide() Authority: CONTAINED**  
**Client decided_by Spoofing: BLOCKED**
