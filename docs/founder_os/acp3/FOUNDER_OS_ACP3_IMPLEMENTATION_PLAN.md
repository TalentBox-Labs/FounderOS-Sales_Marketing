# Founder OS ACP-3 — Implementation Plan

## Repository grounding (completed)

1. Branch `founder-os-acp3-durable-runtime` from ACP-2 baseline.
2. HEAD = `1444dae9c4914df556e5c570a527d8203c28a542` = peeled `founder-os-acp2-v1.0`.
3. Inspected ACP-1/2 contracts, scheduler, AgentActionLog, ApprovalRequest, Hermes,
   Gmail, follow-up, deal-at-risk, founder UI, idempotency, DB session, dormant Celery.
4. Persistence gate: **no new WorkItem table / Redis / Celery control plane**.

## Phases

1. **Contract modules** — recovery classes, bounds, provenance action types.
2. **Reconciliation** — org-scoped classify from AgentActionLog + domain proof helpers.
3. **Durable runtime** — pause/kill gates, bounded resume, scheduler reconcile job.
4. **Scheduler coverage** — gate all commercial jobs; unit-orchestrate residual paths
   (deal-at-risk, gmail, metrics); register `acp3_reconcile`.
5. **Oversight** — expose gates + retryable/ambiguous/requires_founder_action.
6. **Tests + docs + regression**.

## Non-goals

- Authority expansion / Hermes Deal create
- Celery activation
- New persistent SoT without `ACP3_PERSISTENCE_EXCEPTION_REQUEST`
- Unbounded historical replay on resume
