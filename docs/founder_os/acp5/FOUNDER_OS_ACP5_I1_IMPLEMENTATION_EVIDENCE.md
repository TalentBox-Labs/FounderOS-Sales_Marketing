# Founder OS ACP-5-I1 — Implementation Evidence

**Branch:** `founder-os-acp5-discovery`
**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`
**Slice:** B — Command oversight + existing follow-up loop proof + Hermes plan sanitization

## Implemented scope

1. Project existing `snapshot.agent_orchestration` on Founder Command (`templates/founder_command.html`)
2. Prove existing follow-up propose → ApprovalRequest → decide → send executor path via focused tests (no backend rewrite)
3. Sanitize `hermes_planner.generate_plan` so PROHIBITED `create_deals_for_qualified` is not planned as executable work; replaced with permitted qualify recommend + at-risk observation
4. Focused ACP-5-I1 tests

## Files changed

| File | Role |
|------|------|
| `templates/founder_command.html` | Agent operating status projection |
| `revenue_os/services/hermes_planner.py` | `generate_plan` sanitization |
| `tests/test_founder_os_acp5_i1_command_oversight.py` | Focused tests |
| `docs/founder_os/acp5/*` | Evidence / prior discovery+contract |

**Not changed:** approvals, ACP-4, ACP-3, ACP-2 catalog/orchestration core, scheduler follow-up path, booking/calendar, models, migrations, frozen tests.

## Authority / tenant attestation

- AUTHORITY_EXPANSION: NO
- Outbound send: HUMAN_REQUIRED / EXECUTE_GOVERNED via existing `decide` + `_execute_send_outreach_email`
- Follow-up propose: AUTONOMOUS (unchanged)
- Deal create: still PROHIBITED at execution; no longer planned as executable Hermes work
- Tenant model: unchanged; Command remains org-scoped; cross-tenant decide fails closed

## Command projection contract

Uses existing `compose_orchestration_summary` fields only:

- counts: awaiting_human, succeeded, failed, retryable, blocked, exhausted, ambiguous_effect
- pause/kill gates
- short lists: awaiting_human, succeeded_recently, failed, retryable, exhausted, ambiguous_effect

Explicit copy: projection does not grant authority.

## Hermes sanitization

| Metric | Before | After |
|--------|--------|-------|
| pipeline_value | score, qualify, **create_deals** | score, qualify, **check_deals_at_risk** |
| deals_closed | **create_deals**, check_deals_at_risk | **qualify_high_scorers**, check_deals_at_risk |

Defense in depth: `hermes_action_allowed` + PROHIBITED orchestration path unchanged.

## Deferred

- Booking propose/execute automation in agent loop
- Research-to-outreach automation
- Hermes qualify → Command decision-item promotion
- Celery/Redis, new SoT, authority expansion

## Remaining gaps

- Existing GoalStep rows in DB may still reference old deal-create action_type until goals are recreated
- Command does not invent new agent work; it only projects logs
