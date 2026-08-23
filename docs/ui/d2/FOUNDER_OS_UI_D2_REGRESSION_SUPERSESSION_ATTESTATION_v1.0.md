# Founder OS UI-D2 Regression Supersession Attestation v1.0

**STATUS:** ATTESTED
**Branch:** `ui-d2`
**Mode:** Documentation only — historical test files remain unchanged from HEAD
**Scope:** Final full-regression envelope after UI-D2 live governed booking + UI-D2.1 backward-compatibility repair

This attestation records the reconciled UI-D2 regression envelope. It does not modify production code, templates, tests, or frozen artifacts.

---

## 1. Final full regression

| Metric | Count |
|--------|-------|
| Passed | **1135** |
| Failed | **14** |
| Warnings | **49** |
| Errors | **0** |

---

## 2. Historical unchanged failures (9)

These failures predate UI-D2. They are not caused by booking UI, read-model booking presentation, or UI-D2.1 compatibility repair. They remain as previously documented historical exceptions.

| Cluster | Count | Identity |
|---------|-------|----------|
| crews_unit | ×3 | `tests/test_crews_unit.py` Editor/QA crew output-format assertions |
| utilities_unit | ×5 | `tests/test_utilities_unit.py` file-ops / markdown-structure assertions |
| mdg1 Jinja shell | ×1 | `tests/test_mdg1_manual_demand_registration.py::test_jinja_shell_not_react` |

These nine failures match the historical envelope already recorded in UI-D1 / UI-D1.5 reconciliation (`docs/ui/d1_5/FOUNDER_OS_UI_D1_5_REGRESSION_RECONCILIATION_v1.0.md`).

---

## 3. Superseded negative-scope assertions (5)

UI-D2 intentionally introduces a governed booking surface. Frozen historical tests that certified **absence** of that surface now fail. The tests themselves were **not** edited.

| Test | Frozen file |
|------|-------------|
| `test_int_d2_booking_eligible_visible_without_booking_ui` | `tests/test_int_d2_m4_ui_d1_combined_integration.py` |
| `test_booking_eligibility_shown_without_booking_action` | `tests/test_ui_d1_5_live_demo_baseline_freeze.py` |
| `test_no_fake_availability_ui` | `tests/test_ui_d1_5_live_demo_baseline_freeze.py` |
| `test_human_authority_preserved` | `tests/test_ui_d1_5_live_demo_baseline_freeze.py` |
| `test_meeting_interest_display_only` | `tests/test_ui_d1_founder_demo.py` |

---

## 4. Supersession record (per test)

### 4.1 `test_int_d2_booking_eligible_visible_without_booking_ui`

| Field | Record |
|-------|--------|
| Original milestone intent | INT-D2: certify combined M4 + UI-D1 integration **without** a booking UI. Eligibility and meeting interest may show; booking workflow remains pending. |
| Exact negative capability asserted | Contact workspace contains “booking workflow pending”; no “Propose booking”; no `/booking/propose`; no `contactAction('booking')`. |
| Why UI-D2 supersedes that absence | UI-D2 adds a tenant-safe governed booking panel on Contact Revenue Workspace, including availability load and `/booking/propose` submission **for human approval**. |
| Authority/security still enforced | Cross-tenant booking/approval blocked; pending/rejected bookings cannot execute; AI remains proposal-only; human Approval Inbox required before calendar create. |

### 4.2 `test_booking_eligibility_shown_without_booking_action`

| Field | Record |
|-------|--------|
| Original milestone intent | UI-D1.5 live-demo freeze: show booking **eligibility** as display-only next-action signal. |
| Exact negative capability asserted | “booking workflow pending” copy; no “book a meeting”; no slot selection; availability UI absent (or only “not available”). |
| Why UI-D2 supersedes that absence | Eligible contacts now receive a governed booking panel with “View availability” and slot review **before** approval. Absence of booking action is no longer the product contract. |
| Authority/security still enforced | Availability is tenant-scoped M4 API; slots are not invented client-side as authority; submit-for-approval does not book; Outlook/no-connector fail closed. |

### 4.3 `test_no_fake_availability_ui`

| Field | Record |
|-------|--------|
| Original milestone intent | UI-D1.5 freeze: founder templates must not contain a fake calendar-booking surface. |
| Exact negative capability asserted | Template source must not contain `book_meeting`, “slot selection”, or “calendar booking”. |
| Why UI-D2 supersedes that absence | Approval Inbox and Contact Workspace now **intentionally** mention `book_meeting` and availability as real M4-backed UI, not a mock. |
| Authority/security still enforced | No direct browser calendar-create route; connector credentials never rendered; stale/past slots blocked at M4.5 execution; generic send-email / unknown action types still render. |

### 4.4 `test_human_authority_preserved`

| Field | Record |
|-------|--------|
| Original milestone intent | UI-D1.5 freeze: UI source must not emit client-controlled `requested_by` / `decided_by`; approval POST body is empty (`JSON.stringify({})`). |
| Exact negative capability asserted | Substring `requested_by` / `decided_by` absent from `founder_approvals.html` and `founder_contact.html` JS/source; empty JSON body; advisory-only next action. |
| Why UI-D2 supersedes that absence | Server-derived display label `requested_by_label` (AI proposal vs Proposal) appears in Approval Inbox markup. This is **not** a client identity field. The historical static-source assertion is obsolete as a proxy for authority. |
| Authority/security still enforced | Approval JS still posts `JSON.stringify({})`. Tenant session binds the human decider. Client `requested_by` / `decided_by` cannot establish human authority (`booking_worker` spoof blocked). UI-D2.1 compatibility test proves runtime, not string absence. |

### 4.5 `test_meeting_interest_display_only`

| Field | Record |
|-------|--------|
| Original milestone intent | UI-D1 founder demo: meeting interest / booking eligible is **display only**. |
| Exact negative capability asserted | “Booking eligible” visible and “booking workflow pending”; no booking UI controls. |
| Why UI-D2 supersedes that absence | Meeting interest remains visible, and eligible contacts now have a governed booking surface instead of pending-workflow copy. |
| Authority/security still enforced | Non-eligible contacts do not get availability controls; Contact/Deal records are not mutated by booking; recommendation text remains advisory until human approval. |

---

## 5. Historical test files unchanged from HEAD

The following frozen files were **not** modified to turn failures green:

- `tests/test_int_d2_m4_ui_d1_combined_integration.py`
- `tests/test_ui_d1_5_live_demo_baseline_freeze.py`
- `tests/test_ui_d1_founder_demo.py`

**Attestation:** historical test files remain unchanged from HEAD.

UI-D2.1 added **new** compatibility tests (`tests/test_ui_d2_backward_compatibility.py`) instead of editing frozen suites.

---

## 6. DB reconciliation

| Fact | Record |
|------|--------|
| Previous full run | 4 PostgreSQL connection errors |
| Sanctioned local mode | Repo-documented `DATABASE_URL=sqlite:///./demo.db` (`DEPLOYMENT.md`, `DEMO_SETUP.md`) |
| Targeted rerun | `tests/test_orchestration_api.py` + `tests/test_prospecting_ui.py` under sanctioned SQLite: **4/4 PASS** |
| Final full regression under SQLite | **0 errors** |

PostgreSQL connectivity failures in the prior envelope are classified as environment errors, not UI-D2 product regressions. They are **not** present in the final SQLite envelope.

---

## 7. Authority evidence

| Suite | Result |
|-------|--------|
| UI-D2 live governed booking + UI-D2.1 compatibility | **30/30 PASS** (22 + 8) |
| Protected authority/security suites | **212/212 PASS** |
| True new regressions | **0** |
| Authority-contract failures | **0** |

Preserved contracts (unchanged M4 / M4.5 / tenant / CRM authority):

- Tenant isolation
- Cross-tenant booking blocked
- Cross-tenant approval blocked
- Client tenant spoof blocked
- Client `requested_by` / `decided_by` spoof blocked
- Human approval required
- AI proposal-only
- Pending booking blocked from execution
- Rejected booking blocked from execution
- Provider slot revalidation preserved
- Booking idempotency preserved
- Contact mutation unchanged
- Deal mutation unchanged
- Secret / credential exposure blocked

---

## 8. Final classification

| Class | Count |
|-------|-------|
| TRUE_REGRESSION | **0** |
| HISTORICAL_UNCHANGED | **9** |
| SUPERSEDED_NEGATIVE_SCOPE | **5** |
| ENVIRONMENT_ERRORS | **0** |

**14 failed = 9 historical unchanged + 5 superseded negative-scope.** No remainder.

---

## 9. Verdict

UI-D2 regression envelope is reconciled.

Historical milestone evidence remains immutable.

UI-D2 intentionally supersedes only prior feature-absence assertions.

Tenant isolation, human approval, AI proposal-only authority, booking idempotency, stale-slot revalidation, Contact/Deal authority, and credential isolation remain preserved.
