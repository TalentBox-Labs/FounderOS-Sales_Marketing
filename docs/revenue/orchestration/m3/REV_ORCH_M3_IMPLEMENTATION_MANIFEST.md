# REV-ORCH M3 — Implementation Manifest

**Parent:** `2cefad0`

## New files

- `revenue_os/services/reply_routing.py`
- `tests/test_rev_orch_m3_governed_reply_handling.py`
- `docs/revenue/orchestration/m3/*`

## Modified

- `revenue_os/services/revenue_workers.py` — ReplyAnalysisWorker
- `revenue_os/services/ai_service.py` — `analyze_inbound_reply`
- `revenue_os/services/revenue_orchestration_service.py` — M3 run/inspect/wake
- `revenue_os/agents/orchestration.py` — M3 workflow + extra context
- `runner_api_routers/n8n_webhooks.py` — Activity+EmailActivity, dedupe, wake
- `runner_api_routers/revenue_orchestration.py` — latest-assessment GET

## Change budget

New SoTs/models/migrations/integrations/credentials/frozen-contract changes: 0

## Reuse

Activity, EmailActivity.message_id, AgentActionLog, ApprovalRequest (unchanged outbound), Contact.tags M2.5 stop tokens, S4 n8n binding, A4/A3/MC04.5 human mutation APIs.
