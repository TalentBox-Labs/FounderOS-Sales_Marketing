# UI-D1 API Surface Map

## Composed server-side (read models)

`revenue_os/services/founder_ui_read_model.py` — no HTTP mutation.

## Browser mutations (existing APIs)

| Action | API |
|--------|-----|
| Research → draft | `POST /api/v1/revenue/contacts/{id}/research-to-outreach` |
| Propose follow-up | `POST /api/v1/revenue/contacts/{id}/follow-up/propose` |
| Approve / reject | `POST /api/v1/approvals/{id}/approve\|reject` |
| Operator workflow | `/api/v1/operator/actions/*` (via `/operator`) |

## Read-only inspection (also composed in workspace)

| Data | API |
|------|-----|
| Follow-up eligibility | `GET /api/v1/revenue/contacts/{id}/follow-up/eligibility` |
| Reply assessment | `GET /api/v1/revenue/contacts/{id}/reply/latest-assessment` |
| Approvals list | `GET /api/v1/approvals` |
