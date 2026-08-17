# M0 ApprovalRequest Reuse Attestation

**Sprint:** REV-ORCH M0  
**Date:** 2026-08-17  
**Verdict:** **PASS** (reuse confirmed; gaps documented for M1)

---

## Model

**Path:** `revenue_os/models/approvals.py` — `ApprovalRequest`  
**Service:** `revenue_os/services/approvals.py`  
**Router:** `runner_api_routers/approvals.py`

---

## Lifecycle

| State | Semantics |
|-------|-----------|
| `pending` | Awaiting human decision |
| `approved` | Human approved; executor runs **synchronously** in `decide()` |
| `rejected` | Archived; no execution |

**Approval → execution separation:** **PARTIAL PASS** — logically separate (decide then execute), but **same synchronous call stack** on approve. No async queue between approval and n8n handoff.

---

## Fields

| Field | Purpose |
|-------|---------|
| `requested_by` | Agent/service identity (e.g. `cold_email_agent`) |
| `action_type` | Key into `EXECUTORS` registry |
| `title`, `description` | Human-readable queue item |
| `target_type`, `target_id` | Dedup key + entity reference |
| `payload` | Executor input (email body, contact_id, etc.) |
| `decided_by`, `decided_at`, `decision_note` | Human decision provenance |
| `execution_result` | Post-execution outcome JSON |

---

## Tenant Relationship

**Gap:** `ApprovalRequest` has **no `organization_id` column**.

Implication for M1: list/filter approvals must join through `target_id` → Contact.organization_id or add org to payload validation. Not a new SoT — enhancement to query scope.

---

## Registered Executors

| action_type | Executor | Side effect |
|-------------|----------|-------------|
| `send_outreach_email` | `_execute_send_outreach_email` | n8n `send-email` |
| `send_reply_email` | Same (dedup isolation) | n8n |
| `send_linkedin_message` | Manual delivery marker | No auto-send |
| `create_deal` | `create_deal_from_contact` | Deal SoT (human approved) |

---

## Duplicate Safety

`request_approval()` collapses pending requests by `(action_type, target_id)`.

Evidence: `approvals.py` lines 101–112.

---

## Audit Logging

Every transition logged via `log_agent_action()`:
- `approval_requested`
- `approval_approved` / `approval_rejected`

---

## sales_agents Integration

All outbound draft agents file ApprovalRequest:

| Agent | action_type |
|-------|-------------|
| Cold email | `send_outreach_email` |
| LinkedIn | `send_linkedin_message` |
| Follow-up / objection | `send_reply_email` |

**PASS:** Future M1 outbound flow can use existing ApprovalRequest without new approval SoT.

---

## Gaps for M1 (not M0 blockers)

1. No `organization_id` on ApprovalRequest — tenant filter needed
2. No expiry/TTL on pending requests
3. No idempotency key on n8n execution (see idempotency contract)
4. `decide()` does not revalidate approver membership/role
5. Approve API uses API key, not full TenantContext + human session

---

## Reuse Attestation

| Criterion | Status |
|-----------|--------|
| Existing model sufficient | **YES** |
| New approval SoT required | **NO** |
| AI draft → Approval → send path exists | **YES** |
| Human gate before n8n | **YES** |

**Overall:** **PASS**

---

*End of M0 ApprovalRequest Reuse Attestation*
