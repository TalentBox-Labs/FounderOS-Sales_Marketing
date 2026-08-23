# Founder OS INT-D2 — M4 + UI-D1 Combined Integration Gate v1.0

**STATUS:** CERTIFIED  
**MODE:** Repository-grounded certification only (no booking UI, no frozen-contract change)  
**Branch:** `develop`  
**HEAD:** `6c06e28`  
**Ancestors:** `4b182e4` (M4/M4.5) and `f3fae11` (UI-D1/UI-D1.5) are ancestors of `develop`.

## Combined baseline

| Stream | Present | Evidence |
|--------|---------|----------|
| REV-ORCH M4/M4.5 | YES | Booking eligibility, BookingWorker, `ApprovalRequest.action_type=book_meeting`, tenant calendar resolution, provider slot revalidation, calendar executor, `docs/revenue/orchestration/m4*`, M4/M4.5 tests |
| UI-D1/UI-D1.5 | YES | Command Center, Demand/Contacts, Contact Revenue Workspace, Approval Inbox, Activity/Provenance, cockpit `data['items']` fix, founder read model, `scripts/seed_founder_demo.py`, `docs/ui/d1*` |

## Combined product state (intentional)

| Capability | Combined |
|------------|----------|
| Meeting interest visibility | YES |
| Booking eligibility visibility | YES |
| Availability UI | NO |
| Booking UI | NO |

Contact workspace shows badges + “booking workflow pending”. No propose/availability controls. Approval Inbox renders `book_meeting` generically (`title` + `action_type`) without assuming send-email.

## Route coexistence

UI routes (`/command`, `/demand`, `/contacts/{contact_id}`, `/pending-approvals`, `/activity`) and M4 routes (`/api/v1/revenue/contacts/{contact_id}/booking/{eligibility,availability,propose}`) mount together. UI does not call booking APIs. Duplicate OpenAPI operation IDs in `runner_api.py` are pre-existing Jinja/proxy IDs, not M4↔UI path collisions.

## Authority / tenancy (preserved)

- Browser `decided_by` is not passed into `decide()`; tenant comes from session `TenantContext`.
- UI cannot establish tenant via payload. Cross-tenant contact/activity/approval/booking reads and proposes return not-found / 422.
- AI cannot self-approve. Calendar credentials remain tenant-owned. Demo seed adds no calendar credentials and creates no live events.

## Demo seed

`scripts/seed_founder_demo.py` remains valid (org, founder user, contact, demand handoff). M4-aware booking demonstration data is a **UI-D2 requirement only**.

## Tests

| Suite | Result |
|-------|--------|
| INT-D2 combined | 5/5 |
| M4.5 freeze | 24/24 |
| M4 focused | 17/17 |
| UI-D1.5 freeze | 22/22 |
| UI-D1 focused | 8/8 |
| Focused frozen matrix (M3.5+M3+M2.5+S4.5+authority+cockpit) | 163/163 |
| Full regression | 1110 passed; 9 failed; 0 errors |

Historical failures unchanged vs UI-D1.5 sqlite envelope: `crews_unit` ×3, `utilities_unit` ×5, `test_mdg1_manual_demand_registration::test_jinja_shell_not_react`. New regressions: **0**.

## Change budget (this gate)

Production / templates / migrations / models / SoTs / integrations / credentials / frozen contracts: **0**. Combined tests added: **5**. This certification doc: **1**.

## UI-D2 readiness

**READY.** Next action is UI-D2 booking-surface implementation on this combined baseline. Do not treat INT-D2 as that implementation.
