# Founder OS ACP-5 — Governance vs Coverage Distinctions

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`

## Rule

If a repository contract (effect catalog, ACP-1 boundary, COS authority matrix, HUMAN_ONLY mutation gate) **explicitly requires** human authority → classify **DELIBERATE_HUMAN_GOVERNANCE**.

If humans still perform the step only because no agent play / scheduler / Command handoff exists, while catalog mode is AUTONOMOUS or the step is propose/read → classify **COVERAGE_GAP** (false-HITL).

## Deliberate human governance (not defects)

| Surface | Evidence |
|---------|----------|
| Approval decide | `WORK_APPROVAL_DECIDE`, `approvals.decide` |
| Outbound / follow-up / booking execute | `ExecutionMode.HUMAN_REQUIRED` in `acp2_effect_catalog.py` |
| QD decide | `WORK_QD_DECIDE`, COS-5 INLINE |
| Hermes deal create | `WORK_HERMES_DEAL_CREATE` PROHIBITED |
| Contact status / deal stage autonomous | PROHIBITED / HUMAN_ONLY HTTP |
| LinkedIn silent auto-send | Executor returns manual delivery |

## Coverage gaps (not governance)

| Surface | Evidence |
|---------|----------|
| Unscheduled `booking_propose` | Catalog AUTONOMOUS; absent from `initialize_heartbeat` |
| Manual `research-to-outreach` | API/workflow; not a Hermes/heartbeat play |
| Hermes qualify recommend without Command item | `action_qualify_high_scorers` recommend-only; not in decision composition as operable handoff |
| Hermes goals calling blocked deal create | `generate_plan` for `pipeline_value` / `deals_closed` |
| Command missing agent orchestration UI | `founder_ui_read_model` sets `agent_orchestration`; `founder_command.html` has no match |
| Sales crew ad hoc invocation | `sales_agents` draft+approve without routine cadence |

## Product test for ACP-5 candidates

Ask: does this change let founders **supervise agents doing ordinary sales work**, while keeping deliberate gates?

- If yes → candidate
- If it removes a deliberate gate → reject
- If it only improves infra without operability → lower priority than the operating loop
