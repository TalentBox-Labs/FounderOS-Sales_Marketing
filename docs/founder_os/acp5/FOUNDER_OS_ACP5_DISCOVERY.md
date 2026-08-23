# Founder OS ACP-5 — Multi-Agent Capability-Gap Discovery

**Branch:** `founder-os-acp5-discovery`
**HEAD / `founder-os-acp4-v1.0`:** `954af7b34590a45991dd098afb21235dfef71fd2`
**Working tree at discovery start:** clean
**Pass type:** documentation only — ACP-4 immutable; no production / test / model / migration changes

## Mission framing

| Milestone | Question answered |
|-----------|-------------------|
| ACP-1 | May this agent/effect execute? |
| ACP-2 | How is authorized work assigned, delegated, retried, escalated, observed? |
| ACP-3 | How can governed work be reconciled/recovered without a second workflow SoT? |
| ACP-4 | How can multiple production executors safely process the same autonomous commercial runtime? |
| **ACP-5** | What capability gap still prevents founders from operating **routine sales through agents**, given that execution is already safely governed? |

ACP-5 is **not** an authority expansion milestone.
ACP-5 is **not** a distributed-runtime redesign.

## Product intent (binding)

Founder OS is intended to support routine company sales operations where:

- AI agents/subagents perform the **ordinary operational workload**
- founders **supervise**, intervene on exceptions, and provide human authority
  **only where governance intentionally requires it**

Discovery therefore distinguishes:

1. **DELIBERATE_HUMAN_GOVERNANCE** — repository contracts explicitly require human authority
2. **COVERAGE_GAP / FALSE_HITL** — manual work that exists because automation/product coverage is incomplete
3. **SAFE_BUT_UNOPERABLE** — agents can execute safely (ACP-1..4) but founders cannot run routine sales *through* the agent system

**Do not** classify required founder approvals as automation defects.
**Do not** excuse routine manual operational work as “human-in-the-loop” unless contracts explicitly require human authority.

## Primary architecture question (answered)

**Given ACP-4 freeze, what is the highest-leverage capability that closes the gap between “agents can execute safely” and “founders can operate routine sales through the agent system”?**

**Answer: a founder-supervised sales agent operating loop** — compose existing AUTONOMOUS propose/read plays + handoffs into existing HUMAN_REQUIRED approvals + make ACP oversight operable on Command — **without** widening authority, activating Celery/Redis, or inventing a new workflow SoT.

## Surfaces inspected

- `revenue_os/services/acp2_effect_catalog.py`
- `revenue_os/services/acp2_work_contract.py`
- `revenue_os/services/acp1_autonomous_boundary.py`
- `revenue_os/scheduler.py` (`initialize_heartbeat` jobs)
- `revenue_os/services/hermes_planner.py` (`ACTION_REGISTRY`, `generate_plan`)
- `revenue_os/services/approvals.py`
- `revenue_os/services/acp2_oversight.py` / `founder_ui_read_model.py`
- `templates/founder_command.html`
- `runner_api_routers/revenue_orchestration.py` / `revenue_orchestration_service.py`
- COS-1..5 commercial spine / decision-loop docs and Command composition
- ACP-4 freeze docs under `docs/founder_os/acp4/`

## Frozen ACP-4 guarantee (immutable input)

```
AT_LEAST_ONCE_DISCOVERY
+ SINGLE_CURRENT_CLAIM (PostgreSQL pg_try_advisory_xact_lock)
+ CURRENT_AUTHORITY_REVALIDATION (claimed paths)
+ CURRENT_TENANT_REVALIDATION
+ CURRENT_APPROVAL_REVALIDATION
+ PAUSE/KILL PROCESS FENCING
+ PAUSE/KILL DISTRIBUTED = CONFIG-DEPENDENT
+ IDEMPOTENT_EFFECT_EXECUTION
+ STALE_EXECUTOR_FENCING (claimed paths)
+ ACP-3 RECONCILIATION
```

Not claimed: distributed exactly-once; distributed pause/kill consensus.

## Verdict (one line)

**Safe autonomous band exists; operable founder-supervised sales loop does not.**
