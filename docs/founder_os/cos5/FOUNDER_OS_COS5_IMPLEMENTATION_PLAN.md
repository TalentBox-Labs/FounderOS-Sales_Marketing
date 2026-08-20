# Founder OS COS-5 Implementation Plan

**STATUS:** IMPLEMENTED
**Branch:** `founder-os-cos5`
**Baseline:** `founder-os-cos4-v1.0` (`ffbe4fd`)

## Objective

Close **Information → Decision → Safe Execution** on Founder Command by composing
existing governed mutation endpoints into Command Center — without a new
orchestration engine, mutation authority, or commercial spine.

## In scope

- CommandAction presentation attached to COS-3 decision items
- INLINE_GOVERNED for eligibility-proof QD accept/reject and Approval approve/reject
- NAVIGATE_GOVERNED for booking / follow-up (person workspace)
- INFORMATION_ONLY for resolved outcomes
- Fail-closed without organization context
- Docs + focused tests

## Out of scope

- Company / Deal workspaces
- optional_tenant operator mutations (deal stage, contact status, commercial outcome)
- New models, migrations, queues
- Booking/send execution from Command
- Cockpit feature growth / Operator deletion

## Implementation shape

1. `revenue_os/services/command_operating_surface.py`
2. Wire via `founder_ui_read_model.build_command_center_snapshot`
3. `templates/founder_command.html` inline/nav actions
4. Existing endpoints only (operator QD + approvals API)
5. `tests/test_founder_os_cos5_command_operating_surface.py`
6. `docs/founder_os/cos5/*`
