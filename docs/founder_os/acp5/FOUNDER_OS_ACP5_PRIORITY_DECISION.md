# Founder OS ACP-5 — Priority Decision

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`
**Mode:** Discovery decision only — no implementation in this pass

## Highest-priority ACP-5 candidate

### Name

**Founder-Supervised Sales Agent Operating Loop**

*(Agent plays + handoffs into existing HUMAN_REQUIRED approvals + Command oversight UX)*

### Why this closes the product gap

ACP-1..4 answered: *may this execute safely across workers?*

Founders still cannot *operate routine sales through agents*:

- Heartbeat covers score / follow-up propose / Gmail / risk / metrics only
- Initial outreach draft and booking propose remain per-contact manual triggers
- Hermes goals do not close pipeline/deals (PROHIBITED deal create remains correctly blocked)
- `compose_orchestration_summary` feeds `agent_orchestration` in Command snapshot but `templates/founder_command.html` does not render it

Closing this moves Founder OS from **safe background jobs + human inbox** to **agents run ordinary sales ops; founders decide where governance requires**.

### In scope (discovery recommendation for a later bounded implementation sprint)

1. Define sales **plays** that compose existing AUTONOMOUS catalog work (`lead_score`, `follow_up_propose`, `booking_propose`, Gmail inbound, observational risk) via `orchestrate_claimed`
2. Wire missing AUTONOMOUS propose paths into the operating loop (especially `booking_propose`; research→outreach draft propose where already allowed)
3. Hand off EXTERNAL sends/executes only into existing `ApprovalRequest` / `decide()` (HUMAN_REQUIRED preserved)
4. Surface ACP-2/3/4 oversight on Command using existing `compose_orchestration_summary` (pause/kill, awaiting human, claim/fence rejects, recovery)
5. Promote Hermes qualify recommendations into an operable founder decision/handoff path **without** autonomous Contact.status mutation
6. Preserve ACP-4 claim/fence on all mutating autonomous paths

### Explicitly NOT in scope

| Anti-goal | Reason |
|-----------|--------|
| Widen AUTONOMOUS to send / book-execute / deal-create / contact status / deal stage / QD decide | Authority expansion forbidden under ACP-4 freeze + product intent |
| Activate Celery / Redis as control plane | ACP-4 KEEP_DORMANT; not proven necessary |
| New Work / Lease / second workflow SoT | Prefer WorkItem identity + AgentActionLog + ApprovalRequest |
| Second approval system | Reuse `ApprovalRequest` |
| Distributed exactly-once claims | ACP-4 does not claim this |
| Replace Command with a new dashboard SoT | Extend composition + UI only |
| Treat deliberate approvals as defects | Product intent |

## Deliberate governance — preserve

- Approval approve/reject
- Follow-up / outbound / booking **execute** HUMAN_REQUIRED
- Hermes autonomous deal create PROHIBITED
- Contact status / deal stage autonomous PROHIBITED
- QD accept/reject human authority
- Delegation non-amplification
- Tenant allowlist + ACTIVE org for autonomous work
- Celery dormant for ACP control plane

## Dependency on ACP-4

**Hard.** ACP-5 is an operability milestone on frozen authority and distributed claim semantics. Any implementation must use claimed execution boundaries and must not reopen ACP-1 policy.

## Contract / plan status (reconciled)

Operating-loop contract and implementation plan written under `docs/founder_os/acp5/`:

- `FOUNDER_OS_ACP5_OPERATING_LOOP_CONTRACT.md`
- `FOUNDER_OS_ACP5_IMPLEMENTATION_PLAN.md`
- `FOUNDER_OS_ACP5_ACTION_AUTHORITY_MATRIX.md`
- `FOUNDER_OS_ACP5_FOUNDER_ATTENTION_MODEL.md`
- `FOUNDER_OS_ACP5_END_TO_END_PLAY.md`
- `FOUNDER_OS_ACP5_TENANT_ATTESTATION.md`
- `FOUNDER_OS_ACP5_AUTHORITY_ATTESTATION.md`
- `FOUNDER_OS_ACP5_REGRESSION_PLAN.md`

## Recommended next action

Open a **bounded ACP-5 implementation sprint** per the operating-loop contract:

1. Command oversight UX for existing `agent_orchestration` summary
2. Primary play: follow-up propose → approval → governed send → Command refresh
3. Hermes plan sanitization (suppress PROHIBITED deal-create planning)
4. Booking propose only if bounded; else DEFER
5. Research-to-outreach: DEFER

## Freeze / discovery status

| Item | Status |
|------|--------|
| ACP-4 | FROZEN immutable baseline |
| ACP-5 discovery | COMPLETE |
| ACP-5 contract / plan | COMPLETE (docs only) |
| ACP-5 implementation | NOT STARTED |
