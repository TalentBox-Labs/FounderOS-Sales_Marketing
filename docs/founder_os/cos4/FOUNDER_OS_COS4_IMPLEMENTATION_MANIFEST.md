# Founder OS COS-4 Implementation Manifest

**Baseline tag:** `founder-os-cos3-v1.0`
**Baseline commit:** `fa8db7e4f382f1b29b49f11e1fa203e2229454fb`
**Branch:** `founder-os-cos4`

## New files

| Path | Role |
|------|------|
| `revenue_os/services/commercial_funnel_intelligence.py` | Compose-only funnel/pipeline/outcome snapshot |
| `tests/test_founder_os_cos4_commercial_funnel_intelligence.py` | COS-4 contract + tenant + authority + semantic proofs |
| `docs/founder_os/cos4/*` | Plan, manifest, contract, attestations |

## Modified files

| Path | Change |
|------|--------|
| `revenue_os/services/founder_ui_read_model.py` | `commercial_funnel` on Command Center snapshot |
| `templates/founder_command.html` | Commercial funnel & pipeline panel |

## Semantic correction v1

| Defect | Fix |
|--------|-----|
| QD raw event counts / duplicate pending | Unique `demand_id` reconciliation; `dedupe_pending_demands`; event totals under `event_counts` |
| CO raw event counts as realized | Unique `outcome_id` accepted/rejected; handoffs labeled as events only |
| Unknown/non-sales stages as OPEN | Explicit `SALES_OPEN` / `SALES_WON` / `SALES_LOST` / `NON_SALES`; unknown ignored |

## Protected area audit

| Area | Modified |
|------|----------|
| New persistent SoTs | **NO** |
| New models | **NO** |
| Migrations | **NO** |
| Frozen historical tests | **NO** |
| Canonical models | **NO** |
| COS-3 decision loop semantics | **NO** (integrated, not replaced) |
| Tenant remediation contracts | **NO** |
| Booking / outbound / mutation authority | **NO** |

## Residual risks

1. `Deal.organization_id` nullable on legacy rows — org filter may omit orphan deals
2. Company tenancy debt unchanged — no company-level aggregation
3. Attention for follow-up/meeting depends on optional rev-orch inspection on Command Center path
