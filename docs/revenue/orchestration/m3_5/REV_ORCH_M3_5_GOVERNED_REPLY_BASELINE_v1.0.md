# REV-ORCH M3.5 — Governed Reply Handling Baseline v1.0

## Status: FROZEN

## Parent Baseline
- Commit: `6b8e58e`
- Title: complete REV-ORCH M3 governed reply handling and qualification transition
- Branch: `rev-orch-m3-5`

## Frozen Flow

```
POST /webhooks/n8n/email.replied
→ _verify_n8n_auth (X-N8N-Secret or Bearer)
→ resolve_n8n_organization_id (trusted integration binding)
→ tenant-scoped Contact resolution (_resolve_scoped_contact / _resolve_contact_by_email)
→ Activity + EmailActivity persistence (deduplication via message_id)
→ wake_inbound_reply_handling()
→ WorkflowOrchestrator.execute_revenue_workflow(REV_ORCH_M3_WORKFLOW_KEY)
→ _handle_m3_inbound_reply → run_inbound_reply_handling()
→ ReplyAnalysisWorker (ai_service.analyze_inbound_reply)
→ route_reply_assessment() — deterministic routing policy
→ OPT_OUT tag mutation if applicable (policy-bound, narrowly scoped)
→ AgentActionLog provenance
→ recommendation returned (no CRM authority mutation)
```

## Canonical Authority

| Component | Authority |
|-----------|-----------|
| WorkflowOrchestrator | Canonical orchestration |
| ReplyAnalysisWorker | SPECIALIZED_AI_WORKER, PROPOSAL_ONLY |
| Deterministic routing | Policy enforcement layer |
| Contact.status mutation | Human-only (frozen A4/A4.5) |
| Deal.stage mutation | Human-only (frozen A3/A3.5) |
| QualifiedDemand | Human-only (frozen MC04.5) |
| n8n | EXECUTOR_ONLY |
| Booking | NOT_IMPLEMENTED |

## Frozen Contracts

- AI Authority: PROPOSAL_ONLY
- Tenant Resolution: Integration binding via X-N8N-Secret
- Deduplication: EmailActivity.message_id (provider or SHA256 fallback with contact_id scope)
- Reply Classification: 8-type taxonomy with UNKNOWN failsafe
- Qualification: Recommendation only, no autonomous mutation
- OPT_OUT: Policy-bound tag mutation (unsubscribed only), tenant-scoped, idempotent
- Booking: Negative scope — BOOKING_ELIGIBLE signal only
- M2.5 Compatibility: Reply-stop, cadence, approval all preserved

## Freeze Tests

`tests/test_rev_orch_m3_5_governed_reply_baseline_freeze.py` — 30 adversarial tests
