# S3 — Editorial / Publishing Read Isolation

## Audit result

Editorial pending (`build_editorial_pending`) reads filesystem content tracker — **GLOBAL_BY_DESIGN**, not tenant-owned.

Publishing queue (`pe.list_queue`) is platform-wide artifact state — **GLOBAL_BY_DESIGN**.

## S3 action

**DEFERRED** — no organization linkage exists on content artifacts. Adding tenant semantics would require new SoT design (out of S3 scope).

## Cockpit impact

Cockpit editorial/publishing attention items remain global when tenant resolved. Documented as residual MEDIUM risk for multi-tenant content in S4+.
