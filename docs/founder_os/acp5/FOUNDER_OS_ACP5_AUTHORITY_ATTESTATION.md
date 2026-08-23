# Founder OS ACP-5 — Authority Attestation

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`

## Attestation

ACP-5 **does not expand authority**.

| Domain | Before ACP-5 | After ACP-5 v1 (planned) |
|--------|--------------|---------------------------|
| Outbound / follow-up send | HUMAN_REQUIRED via ApprovalRequest | **UNCHANGED** |
| Booking execute | HUMAN_REQUIRED via ApprovalRequest | **UNCHANGED** |
| Booking propose | AUTONOMOUS catalog; API-triggered | May add claimed scheduled propose — still propose-only |
| Deal create (Hermes) | PROHIBITED | **UNCHANGED** (plans sanitized) |
| Contact status / deal stage autonomous | PROHIBITED | **UNCHANGED** |
| QD decide | INLINE human | **UNCHANGED** |
| Approval decide | Human + ACP-4 serialization | **UNCHANGED** |
| Pause/kill | Process/env CONFIG-DEPENDENT distributed | **UNCHANGED** |

## Non-authority signals (must not grant power)

- Hermes plan steps
- Command attention codes
- Urgency ordering in decision_items
- Agent assignment eligibility hints in catalog
- Founder “ready” NAVIGATE items

## Preserved human governance

Approval decide · outbound/follow-up/booking execute · QD accept/reject · Hermes deal create prohibited · status/stage human-only mutations.

## ACP-4 / ACP-1

All protected autonomous propose paths remain behind claim + fence.
Past eligibility ≠ current authority.
