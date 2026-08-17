# REV-ORCH M3 — Legacy Reply Reconciliation

| Path | Class | Notes |
|------|-------|-------|
| `POST /webhooks/n8n/email.replied` + wake | CANONICAL transport + SUBORDINATE wake | Tenant from binding |
| `WorkflowOrchestrator` M3 workflow | CANONICAL | |
| `run_inbound_reply_handling` | SUBORDINATE | |
| `sales_agents.handle_latest_reply` | LEGACY_CONTAINED | Tenant-scoped; drafts + ApprovalRequest send_reply_email; no status mutation |
| `POST /api/v1/agents/sales/{id}/handle-reply` | LEGACY_CONTAINED | require_tenant_context |
| `ai_service.classify_and_draft_reply` | LEGACY_CONTAINED | Used by sales_agents only |
| CrewAI reply copy | LEGACY_CONTAINED | Not wired to M3 |

UNSAFE_REACHABLE: 0. UNKNOWN: 0.
