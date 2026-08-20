# Tenant Remediation Manifest v1

**Baseline tag:** `founder-os-cos2-v1.0`
**Baseline commit:** `9cafb2f55352578eba6dd03ce908776744baa0b4`
**Working branch:** `founder-os-tenant-remediation-v1`
**Commit/tag/merge:** NONE (per sprint STOP)

## Changed files

| Path | Change |
|------|--------|
| `revenue_os/services/qualified_demand_service.py` | Org-scoped contact lookup; atomic handoff org; handoff tenant gates; Company skip when scoped |
| `revenue_os/services/tenant_mutation_guard.py` | `require_tenant_mutation()` fail-closed helper |
| `runner_api_routers/qualified_demand.py` | Tenant guards on marketing handoff + sales intake |
| `runner_api_routers/manual_demand.py` | Pass org to handoff when tenant present |
| `runner_api_routers/operator_flow.py` | Pass org to accept/reject when tenant present |
| `runner_api_routers/cockpit.py` | Pass org to accept/reject when tenant present |
| `revenue_os/services/operator_flow_read_model.py` | Fail-closed pending demands without org |
| `revenue_os/services/founder_ui_read_model.py` | Fail-closed command center pending without org |
| `scripts/seed_founder_demo.py` | Atomic org on handoff register |
| `tests/test_founder_os_cos2_marketing_qualified_demand.py` | Org passed at handoff register |
| `tests/test_founder_os_tenant_remediation_v1.py` | **NEW** — 10 focused security tests |

## New documentation

| Path |
|------|
| `docs/founder_os/tenant_remediation/v1/FOUNDER_OS_TENANT_REMEDIATION_PLAN_v1.md` |
| `docs/founder_os/tenant_remediation/v1/FOUNDER_OS_QUALIFIED_DEMAND_TENANT_CONTRACT_v1.md` |
| `docs/founder_os/tenant_remediation/v1/FOUNDER_OS_MARKETING_HANDOFF_TENANT_CONTRACT_v1.md` |
| `docs/founder_os/tenant_remediation/v1/FOUNDER_OS_COMPANY_TENANCY_DEBT_v1.md` |
| `docs/founder_os/tenant_remediation/v1/FOUNDER_OS_TENANT_REMEDIATION_TEST_ATTESTATION_v1.md` |
| `docs/founder_os/tenant_remediation/v1/FOUNDER_OS_TENANT_REMEDIATION_MANIFEST_v1.md` |

## Protected area audit

| Area | Modified |
|------|----------|
| New models | **NO** |
| Migrations | **NO** |
| Frozen tests | **NO** |
| Canonical models | **NO** |
| Authority semantics (outbound/booking/approval/workflow) | **NO** |
| M1–M4 orchestration | **NO** |

## Diff summary (code)

~211 insertions, ~51 deletions across 10 code/test files (+ 6 docs, 1 new test file).

## Residual risks

1. Legacy unscoped service paths when `organization_id=None` (MC04 unit tests, env-operator OF1/MDG1)
2. Company model lacks tenant key — enrichment disabled on scoped accept
3. MC04 API frozen tests conflict with fail-closed production behavior
4. Unscoped historical handoff rows (pre-remediation) invisible to org-scoped reads but not migrated

## Recommended next action

1. Tag remediation freeze after review (`founder-os-tenant-remediation-v1.0`)
2. Update MC04 API contract/tests in a dedicated sprint (or supersede with tenant-scoped MC04 v2 tests)
3. Plan Company `organization_id` migration before re-enabling company_hint bind
4. Proceed to COS-3 only after remediation sign-off
