# UI2 — Adversarial Validation

**Sprint:** UI2  
**Date:** 2026-08-13

| Attempt | Result |
|---------|--------|
| Forged `requested_by` in POST body | **BLOCKED** — ignored; server operator used |
| Hidden-field manipulation | N/A — no requested_by fields in forms |
| Direct POST without cockpit page | Allowed via API (same proxy); requires API key + operator env |
| Agent operator env (`agent:hermes`) | **BLOCKED** — 503 |
| Unconfigured operator | **BLOCKED** — 503 |
| Replay accept (idempotent) | **PASS** — no duplicate CRM state |
| Invalid contact status | **BLOCKED** — 422 |
| API/DB unavailable | **PASS** — panels show unavailable, not fake zero |
| Stale/partial panel data | **PASS** — per-panel state labels |
| Agent mutation via UI | **BLOCKED** |
| AI mutation via UI | **BLOCKED** |

**Verdict:** UI2 action paths safe; read panels truthful under failure.
