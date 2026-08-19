# Founder OS COS-1 Authority Attestation

COS-1 did not change ApprovalRequest executors, WorkflowOrchestrator pipelines, or calendar create.

| Control | Status |
|---------|--------|
| AI research/draft/propose | Unchanged contact buttons |
| Human approval for send/book | Unchanged |
| `JSON.stringify({})` on approve/reject | Preserved in `founder_approvals.html` |
| Client `decided_by` / `requested_by` | Must not become human identity (existing + COS-1 spoof test) |
| Contact.status auto-write | Not introduced; booking approve does not promote lead |
| Booking pending/rejected cannot execute | Existing executor gate; COS-1 tests |
| Stale slot / idempotency / credentials | UI-D2 / M4.5 unchanged |
| Advisory next action | Still labeled advisory only |

Frozen SUPERSEDED_NEGATIVE_SCOPE tests untouched.
