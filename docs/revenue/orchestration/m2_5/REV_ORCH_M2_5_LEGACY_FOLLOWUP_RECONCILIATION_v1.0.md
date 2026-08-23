# REV-ORCH M2.5 — Legacy Follow-Up Reconciliation v1.0

**STATUS: FROZEN**  
**CANONICAL_FOLLOWUP_ENGINE = M2 governed workflow**

## Path classification

| Path | Classification | Notes |
|------|----------------|-------|
| `POST .../follow-up/propose` → WorkflowOrchestrator | CANONICAL | Human-gated M2 |
| `GET .../follow-up/eligibility` | CANONICAL | Policy inspect; no AI/send |
| `run_follow_up_to_outreach` / `_run_follow_up_proposal` | SUBORDINATE | Implementation under orchestrator |
| `run_follow_up_proposal_scheduled` | SUBORDINATE | Scheduler wake; same proposal path; no send |
| `job_scan_follow_up_eligibility` | SUBORDINATE / INFRASTRUCTURE | Scan + wake only |
| `followups.get_followups` / `GET /followups` | LEGACY_CONTAINED | Read-only dashboard aggregation |
| Copilot `_handle_followups` | LEGACY_CONTAINED | Read-only |
| `sales_agents.build_followup_sequence` | LEGACY_CONTAINED | Creates OutreachSequence/SequenceStep; no send; tenant via `_load_contact` |
| `POST /api/v1/agents/sales/{id}/sequence` | LEGACY_CONTAINED | Requires TenantContext; does not call n8n |
| `sales_agents.handle_latest_reply` | LEGACY_CONTAINED | Objection draft → ApprovalRequest `send_reply_email`; not M2 cadence |
| `ai_service.generate_followup_sequence` | LEGACY_CONTAINED | Draft helper for sales_agents only |
| CrewAI `src/sdr_crew.py` follow-up copy | LEGACY_CONTAINED | Not wired to M2 orchestrator or n8n send |

## Authority bypass

Legacy sequence **cannot** send outbound, cannot approve, cannot ignore M2 reply-stop (it is not the cadence engine). Cross-tenant sequence build returns `ok: false`.

**UNSAFE_REACHABLE: 0**  
**UNKNOWN: 0**
