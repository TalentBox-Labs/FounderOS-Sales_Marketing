# Founder OS COS-5 Action Eligibility Matrix

**STATUS:** BINDING FOR COS-5 v1

Hard rule: INLINE_GOVERNED requires mandatory tenant + human authority + audit.

| Action | Existing endpoint/service | Mandatory tenant? | Human authority? | Auditable? | Eligible inline? | Reason |
|--------|---------------------------|-------------------|------------------|------------|------------------|--------|
| QualifiedDemand accept | `POST /api/v1/operator/actions/qualified-demand/accept` → `accept_qualified_demand` | **YES** (`require_tenant_mutation` + `scoped_demand_handoff`) | YES (trusted operator) | YES (`qualified_demand_accepted`) | **YES** | Meets all three |
| QualifiedDemand reject | `POST /api/v1/operator/actions/qualified-demand/reject` | **YES** | YES | YES (`qualified_demand_rejected`) | **YES** | Meets all three |
| Approval approve | `POST /api/v1/approvals/{id}/approve` → `decide` | **YES** (`require_tenant_context` + `get_approval_for_tenant`) | YES (`is_human` + human mutation authority) | YES (ApprovalRequest + logs) | **YES** | Meets all three |
| Approval reject | `POST /api/v1/approvals/{id}/reject` | **YES** | YES | YES | **YES** | Meets all three |
| Booking propose | `POST …/booking/propose` | YES (contact tenant) | Proposal only | YES (ApprovalRequest) | **NO** | Keep on contact workspace; Command navigates |
| Booking execute | Approval executor after approve | Via approval path | YES | YES | **NO direct** | Only via Approval approve (existing) |
| Follow-up propose | `POST …/follow-up/propose` | YES | Proposal | YES | **NO** | Navigate to person workspace |
| Follow-up / outbound send | Approval / send executors | Via approval | YES | YES | **NO direct** | No silent send from Command |
| Commercial outcome accept/reject | Operator `/actions/commercial-outcome/*` | **NO** (`optional_tenant_mutation`) | YES | YES | **NO** | optional_tenant excluded |
| Deal stage | Operator `/actions/deal/stage` | **NO** (`optional_tenant_mutation`) | YES | YES | **NO** | optional_tenant excluded |
| Contact status | Operator `/actions/contact-status` | **NO** (`optional_tenant_mutation`) | YES | YES | **NO** | optional_tenant excluded |
| Outbound send (direct) | integrations / WhatsApp | Mixed | Often gated | Mixed | **NO** | Not Command-eligible |

## Summary

- **INLINE:** QD accept/reject, Approval approve/reject
- **NAVIGATE:** booking review, follow-up
- **EXCLUDED:** optional_tenant mutations, silent book/send, deal/contact/CO direct mutation
