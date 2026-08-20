# Founder OS COS-5 Implementation Manifest

**Baseline tag:** `founder-os-cos4-v1.0`
**Baseline commit:** `ffbe4fdc970b6564b4283b8dd7e75d5a1eeee554`
**Branch:** `founder-os-cos5`

## New files

| Path | Role |
|------|------|
| `revenue_os/services/command_operating_surface.py` | CommandAction composition |
| `tests/test_founder_os_cos5_command_operating_surface.py` | Eligibility + tenant + authority proofs |
| `docs/founder_os/cos5/*` | Plan, contract, eligibility, attestations |

## Modified files

| Path | Change |
|------|--------|
| `revenue_os/services/founder_ui_read_model.py` | Attach command actions + summary |
| `templates/founder_command.html` | Inline/nav action UI calling existing APIs |

## Protected area audit

| Area | Modified |
|------|----------|
| New persistent SoTs | **NO** |
| New models | **NO** |
| Migrations | **NO** |
| Frozen prior tests | **NO** |
| Canonical models | **NO** |
| Mutation authority | **NO** (reuses existing) |
| Booking / outbound authority | **NO** |

## Residual risks

1. Operator deal/CO paths remain `optional_tenant` — excluded from inline COS-5
2. Operator still reachable for non-eligible mutations
3. Approval approve may execute underlying executor (existing behavior) — Command only calls `decide`
