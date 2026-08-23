# Founder OS COS-4 Implementation Plan

**STATUS:** IMPLEMENTED
**Branch:** `founder-os-cos4`
**Baseline tag:** `founder-os-cos3-v1.0` (`fa8db7e`)

## Objective

Deliver **Commercial Funnel & Pipeline Intelligence** — a tenant-safe, read-only composition layer answering whether commercial demand is converting into pipeline and recorded outcomes, and where workflow is stuck.

## Scope

| In scope | Out of scope |
|----------|--------------|
| Org-scoped funnel counts (demand / pipeline / outcome bands) | ARR, MRR, cash, finance-grade expected revenue |
| Open pipeline stage distribution | Probabilistic / ML forecast |
| Deterministic attention reason codes | Lead/opportunity scores |
| Integration with Command Center + COS-3 decision loop | Company workspace |
| MC06 outcome pending states | Deal workspace (deferred) |
| Recent commercial movement from org-scoped AgentActionLog | Attribution SoT |
| | New persistent analytics tables |

## Implementation shape

1. `revenue_os/services/commercial_funnel_intelligence.py` — pure composer
2. `founder_ui_read_model.build_command_center_snapshot` — wires `commercial_funnel`
3. `templates/founder_command.html` — executive funnel panel
4. `tests/test_founder_os_cos4_commercial_funnel_intelligence.py` — contract proofs
5. `docs/founder_os/cos4/*` — governance docs

## Non-goals

- No models, migrations, or background jobs
- No Company enumeration (Company lacks `organization_id`)
- No Hermes global pipeline endpoints
- No weakening of human/booking/outbound authority
