# UI-D1.5 Baseline Manifest

**STATUS: FROZEN v1.0**  
**Parent:** `1e446ac`  
**Branch:** ui-d1

## Frozen production surface (from UI-D1, unchanged in D1.5)

| Path | Role |
|------|------|
| `runner_api_routers/ui.py` | Founder routes + `_founder_page_context` |
| `revenue_os/services/founder_ui_read_model.py` | Read composition |
| `templates/base.html` | Product nav + org badge |
| `templates/cockpit.html` | `data['items']` fix |
| `templates/founder_*.html` | Five new founder templates |
| `templates/operator.html` | Linked OF1.5 workflow |
| `templates/login.html` | Login |
| `scripts/seed_founder_demo.py` | Dev/demo seed |

## This sprint (UI-D1.5)

| Kind | Paths |
|------|-------|
| Tests | `tests/test_ui_d1_5_live_demo_baseline_freeze.py` |
| Docs | `docs/ui/d1_5/*` |

## Zero (this sprint)

Feature/UI production code, runtime, SoTs, models, migrations, integrations, credentials, frozen revenue contracts: **0**

## Cross-stream

M4 booking: **CROSS_STREAM_DEPENDENCY** — not imported, not implemented.

## Cross-agent conflicts

**0**
