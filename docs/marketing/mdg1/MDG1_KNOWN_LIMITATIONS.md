# MDG1 — Known Limitations

**Sprint:** MDG1  
**Date:** 2026-08-13

1. Does **not** capture public website audience automatically.
2. Does **not** implement inbound security (rate limit, Turnstile) — not needed for trusted operator UI.
3. Does **not** create Contact until explicit Sales accept on `/operator`.
4. Does **not** qualify demand (no MQL engine); notes are manually asserted only.
5. Attribution beyond manually entered source/source_detail is unavailable.
6. OF1.5 freeze still states operator composition has “no Audience→Demand capture” meaning **public** capture; MDG1 registration lives on a separate surface/router.
7. Multi-tenant SaaS identity is out of scope — still `FOUNDER_OS_OPERATOR_NAME` per deployment.
