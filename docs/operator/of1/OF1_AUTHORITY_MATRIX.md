# OF1 — Authority Matrix

**Sprint:** FOUNDER OS OF1  
**Date:** 2026-08-13

| Actor | Read `/operator` | Mutations |
|-------|------------------|-----------|
| Trusted human (`FOUNDER_OS_OPERATOR_NAME`) | Yes | Yes, via frozen services |
| Browser `requested_by` | Ignored | Ignored |
| Agent / AI / spoofed names | Read HTML | 503 (operator unset/invalid) |
| Unauthenticated API (key set) | 401 | 401 |

Every mutation calls `require_human_mutation_authority` inside the frozen service (except Deal create, which still requires trusted operator at the proxy and does not call A3.5).
