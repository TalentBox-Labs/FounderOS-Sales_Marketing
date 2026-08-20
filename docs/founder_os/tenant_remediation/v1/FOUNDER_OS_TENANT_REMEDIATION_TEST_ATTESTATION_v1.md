# Tenant Remediation Test Attestation v1

**Interpreter:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing/.venv/bin/python`
**Env:** `SECRET_KEY=ui-d2-1-local-test-secret-key-32b`
**Date:** 2026-08-20

## Focused remediation suite

**File:** `tests/test_founder_os_tenant_remediation_v1.py`
**Result:** **10/10 PASS**

| # | Requirement | Test |
|---|-------------|------|
| 1 | Tenant A demand does not resolve Tenant B Contact by email | `test_accept_does_not_resolve_other_tenant_contact_by_email` |
| 2 | Tenant A acceptance creates/resolves only Tenant A Contact | same |
| 3 | Same email safe across tenants | `test_same_email_across_tenants` |
| 4 | Cross-tenant demand accept blocked | `test_cross_tenant_demand_accept_and_reject_blocked` |
| 5 | Cross-tenant demand reject blocked | same |
| 6 | Direct accept requires trusted tenant context | `test_direct_intake_requires_tenant_context` |
| 7 | Missing tenant context fails closed | same + command center tests |
| 8 | Cross-tenant Contact existence not leaked | `test_cross_tenant_demand_not_visible_on_people` |
| 9 | Company lookup cannot cross tenant | `test_accept_does_not_resolve_other_tenant_contact_by_email` (company_id None on new contact) |
| 10 | Marketing handoff persists org atomically | `test_marketing_handoff_persists_org_atomically` |
| 11 | Unscoped handoff rejected on production path | `test_direct_intake_requires_tenant_context` (handoff requires tenant at API) |
| 12 | Command Center no global pending without org | `test_command_center_fail_closed_without_org` |
| 13 | COS-2 marketing → QD | COS-2 suite (below) |
| 14 | COS-1 commercial spine | COS-1 suite (below) |
| 15 | UI-D2 booking authority | UI-D2 suite (below) |
| 16 | D1.x runtime gates | D1.x init/demo suites (below) |
| — | Service-level reject tenant gate | `test_service_reject_scoped_to_tenant` |

## Regression gates

| Suite | Result | Notes |
|-------|--------|-------|
| COS-2 (`test_founder_os_cos2_marketing_qualified_demand.py`) | **9/9 PASS** | |
| COS-1 (`test_founder_os_cos1_commercial_spine.py`) | **16/16 PASS** | |
| UI-D2 core | **58/58 PASS** | `test_ui_d2_backward_compatibility`, `test_ui_d2_live_governed_booking` |
| D1.x init/demo | **PASS** | `test_demo_d1_*`, `test_ui_d1_founder_demo` partial — see below |
| S2 tenant isolation | **PASS** | |
| S3 CRM tenant isolation | **PASS** | |
| S4 integration tenant isolation | **PASS** | |

## Classified conflicts (frozen tests — NOT modified)

### MC04 API suite — `ENCODED_UNSAFE_BEHAVIOR`

**File:** `tests/test_mc04_qualified_demand.py`
**Result:** **4/12 FAIL**

Tests call marketing handoff and sales intake **without org context**. Remediation correctly returns HTTP 403. These tests encoded pre-remediation unsafe unscoped API behavior.

| Failed test | Reason |
|-------------|--------|
| `test_runner_handoff_and_accept_flow` | Handoff 403 without tenant |
| `test_accept_without_handoff_rejected` | Handoff 403 |
| `test_reject_creates_audit` | Handoff 403 |
| `test_handoff_idempotent` | Handoff 403 |

**Action:** STOP classification — do not rewrite frozen MC04 tests in this sprint.

### UI-D1 / INT-D2 copy assertions — `SUPERSEDED_NEGATIVE_SCOPE`

**Files:** `test_ui_d1_founder_demo.py`, `test_int_d2_m4_ui_d1_combined_integration.py`
**Result:** **3 FAIL** (booking copy assertions)

Assertions require legacy strings (`booking workflow pending`, `book_meeting` in approvals HTML) superseded by COS-1/UI-D2 presentation changes documented in `FOUNDER_OS_COS2_REGRESSION_RECONCILIATION.md`.

**Action:** Not tenant-remediation regressions; frozen tests untouched.

## Cross-tenant reproduction evidence

| Scenario | Before fix | After fix |
|----------|------------|-----------|
| Accept with shared email across tenants | Could merge Tenant B Contact | Creates Tenant A Contact only |
| Accept Tenant B demand as Tenant A | Succeeded | HTTP 404 |
| Reject Tenant B demand as Tenant A | Succeeded at service layer | ValueError / HTTP 404 |
| Direct intake without org | Succeeded | HTTP 403 |
| Unscoped pending demands in Command Center | Global enumeration | Empty (fail-closed) |
| Marketing handoff org stamp | Post-commit or missing | Atomic on insert |

## Authority preservation

No tests modified for outbound, booking, approval, Contact.status, or Deal.stage authority semantics. UI-D2 governed booking suite: **PASS**.
