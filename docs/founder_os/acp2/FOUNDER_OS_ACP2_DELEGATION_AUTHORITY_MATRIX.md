# Founder OS ACP-2 — Delegation Authority Matrix

| Parent mode | Child kind | Result |
|-------------|------------|--------|
| AUTONOMOUS | AUTONOMOUS (same org) | Allowed if ACP-1 passes + depth OK |
| AUTONOMOUS | HUMAN_REQUIRED (outbound/book) | WAITING_HUMAN — no effect |
| AUTONOMOUS | PROHIBITED (Hermes Deal / contact status) | BLOCKED |
| HUMAN_REQUIRED | AUTONOMOUS child | Child capped to HUMAN_REQUIRED |
| PROHIBITED | any | BLOCKED |
| any | cross-tenant org | PROHIBITED (child forced to parent org) |

Depth default: **2**. Exceeded → `delegation_depth_exceeded`.

Provenance: `root_work_id`, `parent_work_id`, `requesting_agent`, `assigned_agent` on `acp2_work_delegated`.
