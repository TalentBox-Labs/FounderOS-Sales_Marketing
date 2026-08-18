# UI-D1.5 Tenant Security Attestation v1.0

**STATUS: FROZEN**

Server `resolve_tenant_context` / `require_tenant_context` remain canonical. UI read models pass `organization_id` from that context. Client cookies that name a non-membership org fail membership check (403) and cannot load foreign contacts.

## Frozen tests

| Attack | Expected | Enforcement |
|--------|----------|-------------|
| Tenant B GET `/contacts/{A}` | `contact-not-found`; no email/reply leak | `get_contact_for_tenant` |
| Tenant B view of A's reply assessment | Hidden (not_found workspace) | same + `inspect_latest_reply_assessment` tenant filter |
| Tenant B GET `/pending-approvals` | A's approval title absent | `list_requests(..., organization_id=)` |
| Tenant B GET `/activity` | A's contact id / events absent | `_org_scoped_actions` org filter |
| Tenant B POST approve A's request | 403/404/409; status remains pending | `get_approval_for_tenant` |
| Cookie spoof org A while logged in as B | Fail-closed: no A contact payload (HTML unavailable / membership 403) | membership check; UI does not compose foreign org_id |

UI-only hiding is not the control. Backend tenant scoped access is the control.
