# Founder OS COS-3 Implementation Manifest

**Baseline tag:** `founder-os-tenant-remediation-v1.1`
**Baseline commit:** `0d436d3bebad08d059450cb13e119d72a1c989f1`
**Branch:** `founder-os-cos3`
**Commit/tag/merge:** NONE (per sprint STOP)

## New files

| Path | Role |
|------|------|
| `revenue_os/services/commercial_decision_loop.py` | Compose-only decision items |
| `tests/test_founder_os_cos3_commercial_decision_loop.py` | Focused COS-3 proofs |
| `docs/founder_os/cos3/*` | Plan, contract, attestations, manifest, scope reconciliation |

## Modified files

| Path | Change |
|------|--------|
| `revenue_os/services/founder_ui_read_model.py` | Decision loop on Command Center; fail-closed activity without org |
| `templates/founder_command.html` | Primary commercial decisions surface |

## Protected area audit

| Area | Modified |
|------|----------|
| New persistent SoTs | **NO** |
| New models | **NO** |
| Migrations | **NO** |
| Frozen COS-1/COS-2/tenant tests | **NO** |
| Canonical models | **NO** |
| Booking / outbound / mutation authority | **NO** |

## Scope reconciliation

See `FOUNDER_OS_COS3_SCOPE_RECONCILIATION.md`.

**Architecture model deviations:** none.
**Roadmap sequencing supersession:** COS-3 Commercial Decision Loop precedes deferred Company/Deal workspace work.

## Residual risks

1. Company still lacks tenant key — decision items only pass through already-safe `company_hint_name` / scoped people enrichment elsewhere
2. Non-intake operator mutations still use optional tenant (pre-existing, out of COS-3)
3. Company/Deal workspace slice from historical roadmap remains deferred — tracked in scope reconciliation doc
