# Founder OS COS-3 Commercial Decision Loop Contract

**STATUS:** IMPLEMENTED
**Composer:** `revenue_os/services/commercial_decision_loop.py`
**Surface:** `build_command_center_snapshot` → `/command`

## Canonical item (dict composition — not a table)

| Field | Meaning |
|-------|---------|
| `item_id` | Stable `kind:subject` key |
| `kind` | `qualified_demand` \| `approval` \| `meeting_interest` \| `follow_up` \| `outcome` |
| `commercial_source` | `marketing` \| `sales` \| `revenue` \| `governance` |
| `decision_type` | Repository action/type string |
| `title` | Founder-facing title |
| `reason` | Why it matters (absent if unknown) |
| `person_label` / `company_label` | Only from already-safe presentation fields |
| `proposed_action` | Advisory next step text |
| `authority_state` | `requires_founder` \| `ready` \| `completed` \| `informational` |
| `status` | Derived status string |
| `outcome` | Consequence text when resolved |
| `provenance` | `evidence_type`, `action_type`, `authority_class`, ids |
| `occurred_at` | Timestamp when available |
| `href` | Existing Founder route only |

## Authority bands (deterministic)

1. **requires_founder** — pending approvals, pending QualifiedDemand intake
2. **ready** — booking-eligible meeting interest, eligible follow-up
3. **completed** — accepted/rejected QD, commercial outcome decisions, approval_* logs
4. **informational** — interest without eligibility

No invented scores, confidence, or ARR.

## Fail closed

`compose_commercial_decision_items(..., organization_id=None)` → `[]`
Command Center without org → `state=unavailable`, empty decisions.

## Non-goals

Mutations, new SoT, fabricating company from global Company lookup, autonomous approve/send/book.
