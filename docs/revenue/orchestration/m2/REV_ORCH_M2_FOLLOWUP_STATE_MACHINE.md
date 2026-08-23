# REV-ORCH M2 — Follow-Up State Machine

Conceptual states (derived from Activity + ApprovalRequest — no new persistent SoT):

| State | Meaning | Source |
|-------|---------|--------|
| `FOLLOWUP_NOT_DUE` | Initial outbound missing or interval not elapsed | `follow_up_eligibility` |
| `FOLLOWUP_ELIGIBLE` | Policy permits proposal | `follow_up_eligibility` |
| `FOLLOWUP_PROPOSED` | Worker drafted; ApprovalRequest filed | `revenue_orchestration_service` |
| `FOLLOWUP_APPROVAL_PENDING` | Duplicate pending ApprovalRequest | `follow_up_eligibility` |
| `FOLLOWUP_APPROVED` | Human approved (transient during decide) | `ApprovalRequest.status` |
| `FOLLOWUP_REJECTED` | Human rejected | `ApprovalRequest.status` |
| `FOLLOWUP_SENT` | n8n handoff + outbound Activity | `Activity` + `execution_result` |
| `FOLLOWUP_STOPPED` | DNC/unsubscribe tags | `Contact.tags` |
| `FOLLOWUP_REPLY_RECEIVED` | Inbound Activity after outbound | `Activity` direction=inbound |
| `FOLLOWUP_CADENCE_COMPLETE` | Max steps (2) sent | Activity count policy |

Transitions are deterministic and auditable via `AgentActionLog`.
