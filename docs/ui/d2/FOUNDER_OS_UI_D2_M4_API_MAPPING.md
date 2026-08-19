# UI-D2 M4 API Mapping

| UI action | M4 endpoint | Notes |
|-----------|-------------|-------|
| Eligibility (server render) | `GET .../booking/eligibility` | Used in read model, not browser on load |
| View availability | `GET .../booking/availability` | Tenant-scoped; requires eligibility |
| Submit proposal | `POST .../booking/propose` | Optional `selected_slot`; creates ApprovalRequest |
| Approve booking | `POST /api/v1/approvals/{id}/approve` | Empty body `{}`; session tenant |
| Reject booking | `POST /api/v1/approvals/{id}/reject` | Empty body `{}` |

Execution after approve: `approvals._execute_book_meeting` → `create_tenant_calendar_event` with provider slot revalidation.
