# M0.5 Agent Handoff Contract

**Sprint:** REV-ORCH M0.5  
**Date:** 2026-08-17  
**Status:** FROZEN

---

## Freeze

```
PEER_TO_PEER_AGENT_AUTHORITY: PROHIBITED
AGENT_HANDOFFS: ORCHESTRATOR_MEDIATED
```

---

## Required pattern

```
Worker A
  → structured output
  → WorkflowOrchestrator
  → validation / policy
  → Worker B (if needed)
```

Not:

```
ResearchAgent ↔ PersonalizationAgent ↔ OutreachAgent ↔ FollowUpAgent
```

uncontrolled conversations.

---

## Repository evidence

| Mechanism | Status vs this freeze |
|-----------|------------------------|
| `AgentCoordinator.send_message` | Inter-agent inbox exists (`runner_api_routers/agents.py`). **Must not** become authority transfer. M1 must not use it for revenue mutations or send. |
| `WorkflowOrchestrator._execute_agent` | Sequential context passing via `context[f"{agent}_result"]`. Acceptable **only** as orchestrator-mediated data, after validation. Today it is a stub. |
| `EventBus` | Subscribers must not invoke workers with privileged authority. Events are triggers, not peer authority. |

---

## Rules

1. Workers do **not** call other workers.
2. Workers do **not** delegate ApprovalRequest filing to another worker as authority.
3. Workers do **not** approve or execute another worker’s proposal.
4. Orchestrator copies **validated fields only** into the next worker’s minimum context.
5. `AgentCoordinator` messages are telemetry/handoff log at most — **not** a second orchestrator.

---

## M1 sequence (orchestrator-owned)

```
ResearchWorker → ResearchProposal
  → orchestrator validates
  → LeadScoringService (deterministic)
  → PersonalizationWorker → OutreachDraft
  → orchestrator validates
  → ApprovalRequest
  → Human
  → OutreachExecutor → n8n
```

PersonalizationWorker may receive a **redacted research summary**, not a live handle to ResearchWorker.

---

*End of M0.5 Agent Handoff Contract*
