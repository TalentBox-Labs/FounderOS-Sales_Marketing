# Founder OS ACP-5 — Implementation Plan

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`
**Mode:** Plan only — **DO NOT IMPLEMENT** in this pass

## Recommended V1 scope (precise)

1. **Command oversight:** Render existing `snapshot["agent_orchestration"]` (+ pause/kill) on Founder Command; keep COS-5 INLINE approve/reject for pending approvals already in `decision_items`.
2. **Primary play operability:** Ensure follow-up propose → pending approval → INLINE decide → existing send executor → refresh is founder-operable from Command without operator/debug.
3. **Hermes plan sanitization:** Remove/replace PROHIBITED `create_deals_for_qualified` from `generate_plan` templates.
4. **Booking propose (conditional):** Include only if a bounded claimed scan→`_run_booking_proposal`→ApprovalRequest path can mirror follow-up without new calendar authority or new SoT. If availability/calendar coupling expands scope → **exclude from v1**.

**Exclude from v1:** research-to-outreach automation, authority expansion, Celery/Redis, new models/migrations, generic dashboards.

## Phased work (future implementation sprint)

| Phase | Work | Done when |
|-------|------|-----------|
| P0 | Command template/CSS for agent_orchestration summary + gates | Founder answers four attention questions |
| P1 | Wire/verify follow-up approval INLINE path + empty/error states | Full primary play without debug surfaces |
| P2 | Hermes `generate_plan` sanitization + tests | No prohibited deal-create in plans |
| P3 | Optional booking_propose claimed job **or** DEFER with documented reason | Propose-only; execute still HUMAN_REQUIRED |

## Forecasted implementation surfaces (do not modify yet)

| Surface | Why likely |
|---------|------------|
| `templates/founder_command.html` (+ CSS if needed) | Render `agent_orchestration`; no new SoT |
| `revenue_os/services/founder_ui_read_model.py` | Possibly shape/labels only if template needs stable fields — prefer consume as-is |
| `revenue_os/services/acp2_oversight.py` | Only if missing reason codes/counts for UI; prefer no semantic change |
| `revenue_os/services/commercial_decision_loop.py` | Only if follow-up approval items need clearer reason codes |
| `revenue_os/services/hermes_planner.py` | `generate_plan` sanitization |
| `revenue_os/scheduler.py` | Optional booking scan job if P3 included |
| `revenue_os/services/revenue_orchestration_service.py` | Optional scheduled booking helper mirroring `run_follow_up_proposal_scheduled` |
| COS-5 command routers | Prefer **no** new mutation endpoints; reuse approvals approve/reject |
| `approvals.py` / ACP-4 claim modules | Prefer **no** change (already frozen) |

**Not forecasted as required:** new models, alembic, Celery tasks, Redis, second approval service, MCP/A2A.

## Persistence / architecture gates

- New SoT: **NO**
- If blocked: return `ACP5_PERSISTENCE_EXCEPTION_REQUEST` and stop
- ACP-4 claim/fence + ACP-3 recovery: **preserve**

## Implementation Decision

**GO** (for a bounded implementation sprint after this contract freeze of docs)

Architecture conflicts: **NONE** identified vs ACP-4/COS-5 contracts.
