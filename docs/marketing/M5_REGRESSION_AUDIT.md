# M5 — Regression Audit (Sentinel)

**Agent:** Sentinel  
**Sprint:** M5  
**Date:** 2026-08-10  

**Environment:** `SECRET_KEY=test-secret-m5` · `HEARTBEAT_ENABLED=0`

---

## Results

| Suite | Result |
|-------|--------|
| Deployment tests (`test_website_deployment.py`) | **7/7** |
| Focused (website + static + deployment + publishing + routers integration) | **65/65** |
| Full regression (`tests/`) | **327/339** · **8 failed** · **4 errors** |

---

## New regressions

**0** — failures/errors match historical baseline (crews_unit, utilities_unit, orchestration_api, prospecting_ui).

---

## Boundary checks

| Area | Change |
|------|--------|
| Website Engine Core | **NONE** |
| Static Provider | **NONE** |
| Publishing Engine | **NONE** |
| DB / API routers | **NONE** (M5 scope) |

---

## Verdict

**Regression: PASS**
