# UI-D1.5 Screen Contract v1.0

**STATUS: FROZEN**

## Route ownership

| Route | Handler | Template | Read composition |
|-------|---------|----------|------------------|
| `GET /login` | `identity.page_login` | `login.html` | none |
| `GET /command` | `ui.page_founder_command` | `founder_command.html` | `build_command_center_snapshot` |
| `GET /demand` | `ui.page_founder_demand` | `founder_demand.html` | `build_demand_contacts_snapshot` |
| `GET /contacts/{contact_id}` | `ui.page_founder_contact` | `founder_contact.html` | `build_contact_workspace_snapshot` |
| `GET /pending-approvals` | `ui.page_founder_approvals` | `founder_approvals.html` | `build_approvals_snapshot` |
| `GET /activity` | `ui.page_founder_activity` | `founder_activity.html` | `build_activity_snapshot` |
| `GET /operator` | `ui.page_operator` | `operator.html` | `build_operator_flow_snapshot` |

HTML GET gates for founder commercial screens use `founder_login_redirect()` when `FOUNDER_OS_REQUIRE_LOGIN` is true (default outside pytest).

## Command Center cards (canonical sources only)

Pending approvals, demand intake, contacts, deals, recent replies, meeting interest, follow-up signals, recent activity. Empty copy is honest. No random/fake KPIs.

## Contact workspace panels

Contact details, company/context, revenue workflow stages, research/outreach actions (canonical APIs), follow-up state, latest reply + recommended next action (advisory), meeting-interest / booking eligibility, deals, activity timeline.

Missing optional data: safe empty states. Cross-tenant: `not_found` without leaking foreign records.

## Approvals

Canonical `GET/POST /api/v1/approvals*`. UI posts `{}`. No second approval system.

## Activity

Org-scoped `AgentActionLog` labels. Event `detail` is not dumped to HTML.
