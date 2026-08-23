# Founder OS ACP-5 — Operating Loop Contract

**Branch:** `founder-os-acp5-discovery`
**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`
**Mode:** Contract only — no production implementation in this pass
**ACP-4:** IMMUTABLE

## Name

**Founder-Supervised Sales Agent Operating Loop**

## Objective

Close the gap between “agents can execute safely” and “founders can operate routine sales through agents” by composing existing ACP-1..4, COS Command, ApprovalRequest, and AgentActionLog — **without expanding autonomous authority**.

## Loop shape (canonical)

```
DISCOVER / PROPOSE (AUTONOMOUS, claimed)
  → COMPOSE AGENT WORK (existing WorkItem identity)
  → SURFACE FOUNDER ATTENTION (Command)
  → HAND OFF TO EXISTING ApprovalRequest
  → HUMAN DECIDE (INLINE_GOVERNED where already allowed)
  → EXECUTE ONLY VIA EXISTING EXECUTORS
  → PROVENANCE (AgentActionLog)
  → COMMAND REFRESH / NEXT ATTENTION
```

No second orchestration authority. No new workflow SoT.

## Persistence defaults

| Item | Default |
|------|---------|
| New persistent SoT | **NO** |
| New models | **0** |
| Migrations | **0** |
| Celery / Redis | **NOT activated** |
| `ACP5_PERSISTENCE_EXCEPTION_REQUEST` | **NOT required** for v1 |

Proposal representation = existing `ApprovalRequest` + ACP-2 provenance on `AgentActionLog` + domain eligibility facts.

## Authority (non-amplification)

Assignment, planning, UI presence, urgency, and attention **never** imply authority.

Every ACP-5 action must resolve to an existing mode:

| Mode | Use in ACP-5 |
|------|----------------|
| AUTONOMOUS | Propose/read plays only (`follow_up_propose`, optional `booking_propose`, existing score/Gmail/risk) |
| HUMAN_REQUIRED / EXECUTE_GOVERNED | Send / book execute via `approvals.decide` + `EXECUTORS` |
| PROHIBITED | Hermes deal create; autonomous contact status / deal stage |
| INLINE_GOVERNED | Command approval approve/reject (COS-5) |
| NAVIGATE_GOVERNED | Person workspace for non-inline review paths already COS-5 |

## Tenant

- Every loop item is `organization_id`-scoped
- Missing tenant → **FAIL CLOSED**
- Cross-tenant handoff → **FAIL CLOSED**
- Approval payload/target must bind same org
- Command composes only requested org
- No Contact-derived tenant activation

## ACP-4 / ACP-3 boundaries

- Protected autonomous propose/execute paths use `orchestrate_claimed` / existing fence
- Human approval execution preserves ACP-4 `decide()` serialization (row lock + `approval_execute` claim)
- Ambiguous external effects reuse ACP-3 reconciliation — **no blind replay**, **no exactly-once claim**

## Recommended V1 scope (single bounded slice)

**A.** Surface existing `agent_orchestration` (+ decision-loop approvals) on Founder Command so founders can answer: What are agents doing? What requires me? What happened? What next?

**B.** Make the **follow-up propose → approval → governed send → provenance → Command refresh** path operable end-to-end from Command (primary play; already mostly wired in scheduler + approvals).

**C.** Include **booking_propose** only as the same propose→ApprovalRequest→HUMAN_REQUIRED execute pattern (no silent calendar write). Prefer schedule/compose via existing `_run_booking_proposal` under `orchestrate_claimed` if implementation stays bounded; otherwise DEFER calendar-availability complexity.

**D.** Sanitize Hermes `generate_plan` so PROHIBITED `create_deals_for_qualified` is not planned as runnable work.

## Explicit out of scope (v1)

Autonomous outbound send · autonomous booking execute · autonomous Deal create/stage · autonomous Contact status · new research SoT · new CRM · new workflow engine · Redis · Celery · broker · distributed pause consensus · model gateway · MCP · A2A · agent marketplace · generic monitoring dashboard

## Contract answers (18)

1. **Start event:** Heartbeat `job_scan_follow_up_eligibility` finds org-scoped eligible contacts via `scan_eligible_follow_ups` (or equivalent Command-triggered propose using the same service path).
2. **Composer:** `run_follow_up_proposal_scheduled` → `run_followup_worker` draft composition (`revenue_orchestration_service.py` / `revenue_workers.py`).
3. **Proposal SoT:** `ApprovalRequest` row + provenance (`followup_proposal_scheduled` / `worker_followup_proposal` / ACP-2 waiting logs). No second SoT.
4. **Approval create condition:** Eligible follow-up + successful draft → `request_approval(..., action_type="send_outreach_email", payload includes organization_id, contact_id, idempotency_key, workflow_kind=rev_orch_m2_follow_up)`.
5. **Modes:** Propose = AUTONOMOUS (`WORK_FOLLOW_UP_PROPOSE`); Send = HUMAN_REQUIRED (`WORK_FOLLOW_UP_SEND` / approval executor).
6. **Approved effect:** `approvals.decide(approve=True)` → `EXECUTORS["send_outreach_email"]` → `_execute_send_outreach_email` (existing n8n handoff + activity).
7. **ACP-4 claim/fence:** Propose path already uses `orchestrate_claimed`. Approve path uses ACP-4 hardened `decide()` claim `approval_execute:{id}`; claimed HUMAN_REQUIRED fence remains org-bound.
8. **Success proof:** Approval `execution_result.executed` + AgentActionLog success / outbound activity provenance; ACP-2 `_already_succeeded` where idempotency key present.
9. **Ambiguous effect:** ACP-3 `AMBIGUOUS_EFFECT` — no blind replay; surface on Command via orchestration/reconcile buckets.
10. **Attention before/after:** Before = `requires_founder` approval decision item + `awaiting_human` orchestration bucket; after approve/reject = decision item leaves pending; succeeded/failed/ambiguous appear in orchestration summary + recent activity.
11. **Authority change while waiting:** Pre-effect fence / decide path revalidates; if mode narrower or kill/pause → block; do not execute stale send.
12. **Tenant inactive while waiting:** Fence / tenant resolution fail closed; Command composes empty/blocked for that org.
13. **Retry/exhaustion:** ACP-3 retryable/exhausted buckets via `compose_orchestration_summary` / reconcile; founder sees failed / retryable / exhausted — no infinite silent retry.
14. **Operate from Command:** V1 target = YES for follow-up loop (INLINE approve/reject + visible agent state). NAVIGATE may remain for person-detail draft review if body preview not yet inline.
15. **Intentionally human:** Approval decide; outbound/follow-up/booking **execute**; QD decide; Deal create; Contact status / Deal stage mutations.

See companion docs for attention codes, action matrix, E2E play, tenant/authority attestations, implementation + regression plans.
