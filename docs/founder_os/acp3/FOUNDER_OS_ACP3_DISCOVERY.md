# Founder OS ACP-3 — Discovery Notes (Repository Grounding)

## Baseline verification

- Branch: `founder-os-acp3-durable-runtime`
- HEAD: `1444dae9c4914df556e5c570a527d8203c28a542`
- Tag `founder-os-acp2-v1.0` peels to the same commit (annotated tag object may differ).

## Existing persistent facts used

| Fact | Role |
|------|------|
| `AgentActionLog` | Append-only orchestration + ACP-3 recovery provenance |
| `ApprovalRequest` | Authoritative human approval |
| Domain (`Contact.lead_score`, etc.) | Optional completion proof for replay-safe effects |
| Deterministic idempotency keys | Duplicate invocation / tick safety |
| Env gates | Pause / kill / resume |

## Persistence decision

New WorkItem DB model / queue / Redis / Celery **not** introduced.
Required ACP-3 guarantees satisfied via facts + reconciliation.

## Celery

Present but dormant/unwired for commercial heartbeat — ACP-3 does not activate it.
