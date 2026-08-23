# UI2.5 — Cockpit Action Authority v1.0

**STATUS: FROZEN**  
**Version:** v1.0

---

## Exposed actions

### A. QualifiedDemand Accept

| Layer | Frozen behavior |
|-------|-----------------|
| UI | `acceptDemand()` → cockpit POST only |
| Cockpit proxy | `POST /api/v1/cockpit/actions/qualified-demand/accept` |
| Auth | `_verify_api_key` on API |
| Human identity | `FOUNDER_OS_OPERATOR_NAME` env (server-trusted) |
| Canonical mutation | `accept_qualified_demand(db, demand_id, operator, notes)` |
| Service gate | `require_human_mutation_authority` (UI1.1) |
| Client `requested_by` | **Not in schema — ignored if sent** |
| Audit | `AgentActionLog` + EventBus `CONTACT_IMPORTED` |
| MC04.5 rules | No auto-qualify; no Deal; idempotent accept |

### B. Contact.status Human Update

| Layer | Frozen behavior |
|-------|-----------------|
| UI | `updateContactStatus()` → cockpit POST only |
| Cockpit proxy | `POST /api/v1/cockpit/actions/contact-status` |
| Auth | `_verify_api_key` on API |
| Human identity | `FOUNDER_OS_OPERATOR_NAME` env |
| Canonical mutation | `apply_contact_status_update(..., requested_by=operator)` |
| Service gate | `require_human_mutation_authority` (UI1.1) |
| Score auto-qualify | **Prohibited** — display recommendation only |
| Audit | EventBus `CONTACT_STATUS_CHANGED` |

## Prohibited cockpit mutations (frozen NOT EXPOSED)

| Capability | Cockpit exposure |
|------------|------------------|
| QualifiedDemand reject | NOT EXPOSED |
| Deal stage PATCH | NOT EXPOSED |
| Editorial approve/reject | NOT EXPOSED (link to `/editorial` only) |
| Publishing promote | NOT EXPOSED (link to `/publishing` only) |
| Marketing handoff register | NOT EXPOSEED |
| Revenue mutation | NOT EXPOSED |

## Security freeze (UI1.1 preserved)

| Vector | Status |
|--------|--------|
| Direct service/domain bypass | BLOCKED |
| Agent mutation | BLOCKED |
| AI mutation | BLOCKED |
| Spoofed human metadata | BLOCKED |
| Valid authorized human | PASS (when operator configured) |
| Audit integrity | PASS |
| State integrity | PASS |

## Cockpit is NOT mutation authority

Cockpit routes are **authorized interfaces** into frozen runner/service authority. Authority enforcement remains at canonical service boundaries established in UI1.1.
