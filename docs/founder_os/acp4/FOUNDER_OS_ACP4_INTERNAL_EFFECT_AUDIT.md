# Founder OS ACP-4 — Internal Effect Audit

| Effect | Transactional? | Unique constraint? | Conditional update? | Duplicate-safe? | Cross-process-safe? | Idempotency key? | Claim needed? | Stale executor risk? |
|--------|----------------|--------------------|---------------------|-----------------|---------------------|------------------|---------------|----------------------|
| lead_score write | Partial (job session) | No on score | Overwrite score | Mostly (same score) | **No** (dual writers) | Yes (ACP-2) | **Yes** (serialize) | **Yes** |
| follow_up propose → ApprovalRequest | Yes on create path | **No** unique (action,target) | Soft pending reuse | Partial | **No** | Yes | **Yes** | Yes |
| contact status (human) | Yes | N/A | Human paths | Human | API concurrency separate | Varies | Human path | Fence if agented |
| deal stage / create | Human / PROHIBITED hermes create | Org stamp ownership | — | Hermes create blocked | Blocked mode | Orch key | Fence still | Authority fence |
| deal_at_risk flag | Emit + log | No | Day logical_key | Soft | **No** | Yes | Yes for single emit | Yes |
| metrics snapshot | Analytics engine + log | Metric id registry | Hour key | Soft duplicate points | **No** | Yes | Optional (C class) | Low commercial harm |
| gmail Activity insert | Own commit | message_id **not** unique | Exists check | Partial | **No** | WorkItem key | Yes | Yes |

## Cross-process conclusion

Internal effects are **not** cross-process-safe by database uniqueness today. Domain overwrites may make lead_score *appear* harmless, but provenance duplication, dual ApprovalRequest races, and dual emits remain unsafe for production multi-replica.
