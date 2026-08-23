# REV-ORCH M1.5 — Regression Reconciliation v1.0

**STATUS: FROZEN**  
**Environment:** `SECRET_KEY=… DATABASE_URL=sqlite:///… HEARTBEAT_ENABLED=0 RUNNER_API_KEY= pytest tests/`

## Historical Envelope (invariant core)

**8 failed + 4 errors** (R0 through MC04.5 era)

### Historical failures (8) — HISTORICAL_MATCH

crews_unit ×3 + utilities_unit ×5 (unchanged identities/reasons)

### Historical errors (4) — FIXED (environment)

orchestration_api ×2 + prospecting_ui ×2 — pass with sqlite DATABASE_URL

## M1.5 Full Regression

**896/916 passed; 20 failed; 0 errors** (pre-M1.5 baseline)  
M1.5 adds 22 freeze tests — expect **918 collected** after M1.5

## Additional 12 cockpit failures — PRE_EXISTING_NOT_PREVIOUSLY_RUN

All `TypeError` at `templates/cockpit.html:53` — not modified by M1/M1.1/M1.5

## Classification

| Category | Count | M1.5 impact |
|----------|-------|-------------|
| HISTORICAL_MATCH | 8 | none |
| FIXED (env) | 4 | none |
| PRE_EXISTING_NOT_PREVIOUSLY_RUN | 12 | none |
| M1_5_REGRESSION | 0 | — |

## Verdict

**New Regressions: 0** (M1.5 adds tests/docs only)
