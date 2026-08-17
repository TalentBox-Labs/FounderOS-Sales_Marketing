# M5.5 — Local Verification Ladder

**Agent:** Sentinel — Local Release Verification  
**Sprint:** M5.5  
**Date:** 2026-08-10  
**Repository:** `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
**CI:** Remote Git CI **unavailable** — local ladder is authoritative for this freeze  

**Environment (all pytest steps):**

```text
SECRET_KEY=test-secret-m5-5
HEARTBEAT_ENABLED=0
Interpreter: .venv/bin/python
```

---

## Summary

| Metric | Result | Baseline compare |
|--------|--------|------------------|
| Focused suite | **65/65** | M5: 65/65 — **match** |
| Full regression | **327/339** | Expected 327/339 — **match** |
| Failed | **8** | Expected 8 — **match** |
| Errors | **4** | Expected 4 — **match** |
| New regressions | **0** | Expected 0 — **match** |
| Local deploy smoke | **PASS** | — |
| Rollback smoke | **PASS** | — |

---

## Ladder

### 1. Deployment-focused tests

| Field | Value |
|-------|-------|
| Command | `.venv/bin/python -m pytest tests/test_website_deployment.py -q --tb=no` |
| Exit code | **0** |
| Passed | **7** |
| Failed | **0** |
| Errors | **0** |
| Duration | ~**1.0s** (wall) |

---

### 2. Website Engine tests

| Field | Value |
|-------|-------|
| Command | `.venv/bin/python -m pytest tests/test_website_engine.py tests/test_static_provider.py -q --tb=no` |
| Exit code | **0** |
| Passed | **24** |
| Failed | **0** |
| Errors | **0** |
| Duration | ~**0.9s** (wall) |

---

### 3. Publishing Engine tests

| Field | Value |
|-------|-------|
| Command | `.venv/bin/python -m pytest tests/test_publishing_engine.py -q --tb=no` |
| Exit code | **0** |
| Passed | **16** |
| Failed | **0** |
| Errors | **0** |
| Duration | ~**4.3s** (wall) |

---

### 4. Editorial integration tests

| Field | Value |
|-------|-------|
| Command | `.venv/bin/python -m pytest tests/test_editorial_approval.py tests/test_editorial_readiness.py -q --tb=no` |
| Exit code | **0** |
| Passed | **33** |
| Failed | **0** |
| Errors | **0** |
| Duration | ~**4.6s** (wall) |

---

### 5. UI/API integration tests

| Field | Value |
|-------|-------|
| Command | `.venv/bin/python -m pytest tests/test_routers_integration.py tests/test_content_studio_api.py tests/test_publishing_engine.py::TestPublishingAPI tests/test_publishing_engine.py::TestPublishingUI -q --tb=no` |
| Exit code | **0** |
| Passed | **32** |
| Failed | **0** |
| Errors | **0** |
| Duration | ~**4.1s** (wall) |

---

### 6. Full regression suite

| Field | Value |
|-------|-------|
| Command | `.venv/bin/python -m pytest tests/ -q --tb=no` |
| Exit code | **1** (historical failures/errors) |
| Passed | **327** |
| Failed | **8** |
| Errors | **4** |
| Duration | ~**11.6s** (wall) |

**Historical failures (unchanged):**

- `tests/test_crews_unit.py` — 3 tests  
- `tests/test_utilities_unit.py` — 5 tests  

**Historical errors (unchanged):**

- `tests/test_orchestration_api.py` — 2 tests  
- `tests/test_prospecting_ui.py` — 2 tests  

**Interpretation:** No new failures beyond known baseline; exit code 1 is **expected** until historical items are addressed separately.

---

### 7. Local deployment smoke test

| Field | Value |
|-------|-------|
| Command | Inline Python smoke (temp dir): export package A → deploy local → export B → deploy B → rollback deploy A → manifest SHA-256 verify → operator file exclusion |
| Exit code | **0** |
| Result | `SMOKE_OK` |
| Evidence | [M5_5_ROLLBACK_EVIDENCE.md](M5_5_ROLLBACK_EVIDENCE.md) |

---

## Focused certification suite (M5 parity)

| Field | Value |
|-------|-------|
| Command | `.venv/bin/python -m pytest tests/test_website_deployment.py tests/test_website_engine.py tests/test_static_provider.py tests/test_publishing_engine.py tests/test_routers_integration.py -q --tb=no` |
| Exit code | **0** |
| Passed | **65/65** |
| Duration | ~**3.5s** (wall) |

---

## Verdict

**Regression: PASS** (0 new regressions vs 327/339 baseline)  
**Local verification ladder: COMPLETE**
