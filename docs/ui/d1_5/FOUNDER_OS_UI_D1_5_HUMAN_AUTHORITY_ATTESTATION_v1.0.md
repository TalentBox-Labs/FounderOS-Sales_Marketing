# UI-D1.5 Human Authority Attestation v1.0

**STATUS: FROZEN**

## Frozen UI mutation paths

| UI action | Canonical API | Client identity fields |
|-----------|---------------|------------------------|
| Approve / reject | `POST /api/v1/approvals/{id}/approve\|reject` | none (`JSON.stringify({})`) |
| Research → draft | `POST /api/v1/revenue/contacts/{id}/research-to-outreach` | none |
| Propose follow-up | `POST /api/v1/revenue/contacts/{id}/follow-up/propose` | none |
| Operator commercial actions | `/api/v1/operator/actions/*` | none (server `_trusted_cockpit_operator`) |

`decided_by` on the approvals API cannot establish human authority when session tenant is present (`_human_decider`).

## Recommendations vs CRM state

Contact workspace labels next action **advisory only**. Reply classification does not mutate Contact.status in the UI. M3.5 qualification boundary remains: MEETING_INTEREST is eligibility, not booked/qualified CRM write.

## Controls

Action buttons require `operator.configured` (session human or valid `FOUNDER_OS_OPERATOR_NAME`).
