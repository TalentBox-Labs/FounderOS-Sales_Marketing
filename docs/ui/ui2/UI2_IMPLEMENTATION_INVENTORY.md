# UI2 — Implementation Inventory

**Sprint:** UI2 — Executive Cockpit v1  
**Date:** 2026-08-13

## Reused assets

| Asset | Path | Reuse |
|-------|------|-------|
| Jinja shell | `templates/base.html` | Extended nav + Founder OS presentation |
| UI router | `runner_api_routers/ui.py` | Added `GET /cockpit` |
| Card/stat/table CSS | `base.html` inline | Cockpit panels |
| Toast + fetch helpers | `base.html` | Action feedback |
| Editorial pending builder | `runner_api_routers/editorial.py` | Attention queue |
| Publishing queue | `src/tools/publishing_engine.py` | Attention queue |
| SEO engines | `src/tools/seo_engine` | Marketing/SEO panel |
| CRM models | Revenue `Contact`, `Deal` | Sales snapshot |
| MC04 audit | `AgentActionLog` | QualifiedDemand queue |
| Heartbeat scheduler | `revenue_os/scheduler.py` | Governance panel |
| MC04 accept service | `accept_qualified_demand` | Action 1 |
| A4 status service | `apply_contact_status_update` | Action 2 |
| API key auth | `_verify_api_key` | Cockpit API routes |

## New files (bounded)

| File | Purpose |
|------|---------|
| `revenue_os/services/cockpit_read_model.py` | Server-side read composition |
| `runner_api_routers/cockpit.py` | Trusted-operator mutation proxies |
| `templates/cockpit.html` | Cockpit UI |
| `tests/test_ui2_executive_cockpit.py` | Focused UI2 tests |

## Not modified

- React CRM SPA (`frontend/`) — unmounted
- Frozen MC04/A3/A4 service semantics
- Database schema
- JWT CRM API
