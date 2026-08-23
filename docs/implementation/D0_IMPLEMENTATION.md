# D0 — Marketing Path Integrity Repair

Sprint D0 implementation record. Architecture Baseline v1.0 unchanged.

---

## Problem

Live `POST /marketing/generate` failed because the included router invoked a non-existent module.

## Evidence from Sprint C

- Live response: `"ok": false` with stderr  
  `No module named revenue_os.agents.marketing_crew`
- Classification: **A — CONFIRMED RUNTIME BLOCKER**
- Existing implementation: `src.marketing_crew` (CLI + `MarketingCrew`)
- Shadowed `@app` handler in `runner_api.py` already used `src.marketing_crew` but was not the live route

---

## Root Cause

`runner_api_routers/marketing.py` subprocess targeted `revenue_os.agents.marketing_crew` with positional args. That module file does not exist. FastAPI registers the included router before the duplicate `@app` handler, so the stale path was live.

---

## Implementation Decision

**Decision order #1 — YES:** point the live router at `src.marketing_crew`.

Also align CLI flags with `src.marketing_crew` argparse (`--brand`, `--topic`, `--keyword`, `--geo`, `--funnel`, `--output`) — required for the existing module to parse arguments (not a business-logic change).

No shim, no module move, no duplicate implementation.

---

## Files Changed

### FILE: `runner_api_routers/marketing.py`

| Field | Content |
|-------|---------|
| **Reason** | Replace missing module path with existing `src.marketing_crew` and matching CLI flags so `/marketing/generate` resolves |
| **Risk** | Low — same crew already used by shadowed `@app` path and unit tests; response JSON shape unchanged (`ok`, `stdout`, `stderr`, `output_path`) |
| **Rollback** | Revert the subprocess command list to prior `revenue_os.agents.marketing_crew` + positional args |

No other application files modified.

---

## Runtime Verification

### Before (Sprint C — Docker API)

| Check | Result |
|-------|--------|
| Module import | FAIL — `No module named revenue_os.agents.marketing_crew` |
| Crew load | NOT REACHED |
| Provider/crew runtime | NOT REACHED |

### After (local TestClient against fixed code)

| Check | Result | Evidence |
|-------|--------|----------|
| HTTP | 200 | TestClient POST `/marketing/generate` |
| Stale module error | ABSENT | `has_module_not_found False` |
| `src.marketing_crew` missing | ABSENT | `has_src_missing False` |
| Crew/provider runtime reached | YES | stdout contains CrewAI task instructions; `provider_or_crew_reached True` |
| Response contract | Unchanged | keys `ok`, `stdout`, `stderr`, `output_path` present |
| Full LLM success | Not required for D0 | `ok False` after crew started (provider/runtime completion separate from import blocker) |

---

## Test Results

### Before (Sprint C)

| Suite | Result |
|-------|--------|
| Integration | 18 passed |
| Marketing-focused | N/A (blocker was runtime import) |

### After (D0)

| Suite | Result |
|-------|--------|
| `TestMarketingRouter` + `TestMarketingCrew` | **5 passed** |
| `tests/test_routers_integration.py` | **18 passed** |

API response shape for marketing generate unchanged (integration structure test still green).

---

## API Compatibility

**Verified**

- Path: `POST /marketing/generate` unchanged
- Auth dependency: unchanged (`_verify_api_key`)
- Request model: unchanged (`MarketingRequest`)
- Response keys: unchanged (`ok`, `stdout`, `stderr`, `output_path`)
- Status codes: 400 for missing topic/keyword; 200 with body for generate attempt

---

## Architecture Impact

**No architectural change.**

Canonical Marketing generation remains `src.marketing_crew` under Founder. Only incorrect live wiring was corrected. No CMS migration, no Content Studio work, no domain redesign.
