# Founder OS ACP-4 — Failure Injection Plan

Design-only. Implement in the ACP-4 coding sprint (not this pass).

1. Two workers discover same logical work
2. Two workers attempt claim — exactly one proceeds
3. Worker loses claim before execution — no effect
4. Stale worker after KILL — fence rejects
5. Stale worker after PAUSE — fence rejects
6. Stale worker after authority downgrade (AUTONOMOUS→HUMAN_REQUIRED) — reject
7. Stale worker after tenant deactivation — reject
8. Crash before effect — no success provenance; peer may claim
9. Crash after effect before provenance — AMBIGUOUS or domain-proved; no blind replay
10. Duplicate external request — idempotent or ambiguous, never silent double-send assumed safe
11. Duplicate DB mutation — conditional/idempotent
12. Overlapping scheduler interval (two processes) — claim serializes
13. Overlapping reconciliation — claim serializes
14. Lease expiration/reclaim — if using xact locks: session end; peer reclaim + fence
15. HUMAN_REQUIRED duplicate workers around ApprovalRequest
16. Rejected approval — no execute
17. PROHIBITED work — never executes
18. Missing tenant — fail closed
19. Cross-tenant claim attempt — fail closed
20. Retry exhaustion — observable, no infinite loop
21. Ambiguous external timeout — human review
22. Bounded resume backlog — ≤ configured limit; ×N workers still claim-safe
23. Worker restart mid-job
24. Duplicate success provenance — dedupe
25. Old generation/fence rejected — observable oversight event

Also preserve ACP-1/2/3 regression suites unchanged.
