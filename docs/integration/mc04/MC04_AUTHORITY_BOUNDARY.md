# MC04 — Authority Boundary (SENTINEL)

**Sprint:** FOUNDER OS MC04  
**Date:** 2026-08-13

## Human gates

| Operation | Gate |
|-----------|------|
| Marketing handoff | `is_human_approver(requested_by)` |
| Sales accept | `is_human_approver(requested_by)` |
| Sales reject | `is_human_approver(requested_by)` |

## Agent prohibition

| Action | Blocked identities |
|--------|-------------------|
| Handoff / intake | `agent`, `bot`, `ai:*`, empty |

## AI permitted

- Analyze/recommend off-system (not MC04 endpoints)

## AI prohibited

- Register handoff autonomously
- Accept/reject intake autonomously
- Auto Contact.status promotion (intake sets `LEAD` only)
- Deal creation
- Revenue mutation

**Verdict: PASS**
