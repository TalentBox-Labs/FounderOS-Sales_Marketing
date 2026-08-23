# Founder OS ACP-4 — External Effect Audit

Dormant Celery email tasks are **not activated** by this audit.

## EMAIL / GMAIL inbound (`WORK_GMAIL_INBOUND`)

| Item | Finding |
|------|---------|
| Executor | `integrations/gmail_sync.sync_inbox` via heartbeat orchestrate |
| Organization source | Scheduler org list / per-org WorkItem |
| ACP-1 mode | AUTONOMOUS / PROPOSE |
| Idempotency | Skip if `EmailActivity.message_id` already seen in batch |
| Deterministic key | Yes — org + hour logical_key on WorkItem |
| External idempotency | Gmail message IDs |
| Request ID recorded? | message_id on Activity |
| Completion evidence | Activity rows + orch success log |
| Retry | Scheduler/reconcile |
| Timeout | Provider/client dependent |
| Ambiguity | Partial sync possible |
| Safe blind replay? | **NO** (duplicate Activities possible without unique constraint) |
| Provenance | `acp2_work_*` + gmail activity writes |

## EMAIL outbound (approval path)

| Item | Finding |
|------|---------|
| Executor | `_execute_send_outreach_email` → n8n `send-email` |
| Organization source | Approval / contact org |
| ACP-1 mode | HUMAN_REQUIRED / EXECUTE_GOVERNED |
| Idempotency | Optional `idempotency_key` in payload — **not DB-enforced** |
| Deterministic key | Follow-up keys exist in follow_up_eligibility |
| External idempotency | Depends on n8n/provider |
| Request ID recorded? | Partial via approval `execution_result` |
| Completion evidence | Approval executed flags; not always provider receipt |
| Safe blind replay? | **NO** |
| Provenance | ApprovalRequest + AgentActionLog |

## BOOKING execute

| Item | Finding |
|------|---------|
| Executor | `_execute_book_meeting` → calendar create |
| Mode | HUMAN_REQUIRED |
| Idempotency | Soft: Activity body contains key; key passed to calendar helper |
| External idempotency | **Not proven** in calendar create API usage |
| Safe blind replay? | **NO** |
| Provenance | Approval + Activity |

## WEBHOOKS

| Item | Finding |
|------|---------|
| Present | `revenue_os/integrations/webhooks.py` delivery retries with sleep |
| ACP orchestration | Not the heartbeat commercial control plane |
| Safe blind replay? | Treat as **NO** unless delivery store proves otherwise |

## CRM external API

No separate third-party CRM mutate path beyond in-DB Deal/Contact and calendar/email integrations above for ACP commercial jobs.
