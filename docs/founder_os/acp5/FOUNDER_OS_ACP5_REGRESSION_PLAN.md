# Founder OS ACP-5 — Regression Plan

**Baseline:** `founder-os-acp4-v1.0` @ `954af7b34590a45991dd098afb21235dfef71fd2`

## Focused ACP-5 tests (design; not written yet)

Categories (~18–22 cases):

1. Proposal from eligible follow-up
2. Missing org fail closed
3. Cross-tenant proposal blocked
4. HUMAN_REQUIRED creates/surfaces ApprovalRequest
5. No outbound effect before approval
6. Approved effect invokes existing executor once
7. Rejected approval → no effect
8. Authority downgrade while waiting blocks
9. Tenant deactivation while waiting blocks
10. Concurrent approval single effect (ACP-4)
11. ACP-4 claim/fence preserved on propose
12. Retryable failure surfaces
13. Exhausted failure surfaces
14. Ambiguous external effect not replayed
15. Prohibited Hermes deal-create plan never executable / not planned as runnable
16. Command surfaces founder-required attention
17. Founder can distinguish waiting vs completed
18. No new persistent SoT / models / migrations
19. No authority expansion assertions (catalog modes unchanged for send/book execute)
20. Optional: booking propose files approval without calendar execute

## Frozen regression matrix (must stay green)

ACP-4 · ACP-3 · ACP-2 · ACP-1 · COS-5 · COS-4 · COS-3 · tenant remediation · COS-2 · COS-1 · MC04 v2 · UI-D2 · S3 · S3.5

Frozen earlier tests: **do not modify** unless PROTECTED SURFACE CONFLICT (stop and report).

## Regression command sketch (future)

Reuse established pytest matrix from ACP-4 freeze evidence, plus new `tests/test_founder_os_acp5_*.py` focused suite.
