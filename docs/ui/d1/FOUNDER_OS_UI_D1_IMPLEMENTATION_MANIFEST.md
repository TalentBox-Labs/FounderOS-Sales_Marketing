# UI-D1 Implementation Manifest

## Added

| Path | Role |
|------|------|
| `revenue_os/services/founder_ui_read_model.py` | Read composition |
| `templates/founder_command.html` | Command Center |
| `templates/founder_demand.html` | Demand & Contacts |
| `templates/founder_contact.html` | Contact workspace |
| `templates/founder_approvals.html` | Approval inbox |
| `templates/founder_activity.html` | Activity |
| `tests/test_ui_d1_founder_demo.py` | UI-D1 tests |
| `scripts/seed_founder_demo.py` | Demo seed |
| `docs/ui/d1/*` | Documentation |

## Modified

| Path | Change |
|------|--------|
| `templates/cockpit.html` | Fix `data['items']` Jinja collision |
| `templates/base.html` | Founder nav, org badge, mobile toggle, shared CSS |
| `runner_api_routers/ui.py` | Routes + `_founder_page_context` |

## Zero

- New persistent SoTs
- DB models / migrations
- External integrations
- Frozen contract changes
- Frontend framework
