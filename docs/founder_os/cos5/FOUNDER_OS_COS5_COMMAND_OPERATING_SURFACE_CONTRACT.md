# Founder OS COS-5 Command Operating Surface Contract

**STATUS:** IMPLEMENTED
**Composer:** `revenue_os/services/command_operating_surface.py`
**Surface:** `build_command_center_snapshot` → `/command`

## Founder questions

| Question | Answered by |
|----------|-------------|
| What needs me? | COS-3 decision items |
| Why? | decision reason + command action reason |
| What can I do here? | INLINE_GOVERNED actions |
| What requires another surface? | NAVIGATE_GOVERNED |
| What happened after I acted? | Refresh snapshot + existing AgentActionLog / ApprovalRequest |

## CommandAction (in-memory)

| Field | Meaning |
|-------|---------|
| `key` | Stable action key |
| `label` | Founder-facing button/link text |
| `action_type` | Presentation action id |
| `execution_mode` | `INLINE_GOVERNED` \| `NAVIGATE_GOVERNED` \| `INFORMATION_ONLY` |
| `subject_id` | demand_id / approval id / contact_id |
| `endpoint` | Existing API path (inline only) |
| `href` | Existing Founder route (navigate/info) |
| `requires_reason` | Reject reason required |

## Eligibility rule (hard)

INLINE only if existing path has:

1. mandatory tenant enforcement
2. human authority
3. audit/provenance

## Inline eligible (v1)

| Action | Endpoint |
|--------|----------|
| QD accept | `POST /api/v1/operator/actions/qualified-demand/accept` |
| QD reject | `POST /api/v1/operator/actions/qualified-demand/reject` |
| Approval approve | `POST /api/v1/approvals/{id}/approve` |
| Approval reject | `POST /api/v1/approvals/{id}/reject` |

## Navigate-only

| Signal | Destination |
|--------|-------------|
| Meeting interest / booking | `/contacts/{id}#contact-booking-panel` |
| Follow-up | `/contacts/{id}` |

## Fail closed

No organization_id → empty decision items / no command actions.

## Non-goals

No new mutation services, models, migrations, queues, or autonomous execution.
