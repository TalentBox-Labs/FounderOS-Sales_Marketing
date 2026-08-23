# R1C — Route & Template Hygiene Report

**Date:** 2026-08-12  
**Coordinator:** Lead Engineering Coordinator  
**Agents:** NOVA (audit) · FORGE (fixes) · SENTINEL (tests) · ATLAS (architecture guard)  
**Cross-Agent Conflicts:** 0

---

## 1. Scope

Disposition of R0’s **6 broken routes**, **1 orphan template**, associated stale nav/controls, and false-positive check. No UI redesign, no React rebuild, no frozen-contract changes.

---

## 2. Pre-R1C baseline

| Metric | Value |
|--------|-------|
| Route count | 58 |
| Full regression | 388/400; 8 failed; 4 errors |
| Runtime | PARTIAL (`/marketing` 500; `/app` 404) |
| Architecture | PASS |

Historical failure identities recorded in `/tmp/r1c_pre_ids.txt` (same set as R0/R1A/R1B).

---

## 3–4. Original R0 findings & re-verification

See `R1C_ROUTE_AUDIT.md`. All **6/6** still present; **0 false positives**.

---

## 5. Broken routes resolved (5)

| # | Finding | Resolution |
|---|---------|------------|
| 1 | `/weeks/{id}/qa-report` | Removed stale link in `week_detail.html` |
| 2 | `/marketing/run/{slug}` | Removed View link; show slug text only |
| 3 | `POST /qa` | Removed pipeline stage + STAGE_ENDPOINTS entry |
| 4 | `POST /sheet-sync` | Removed pipeline stage + STAGE_ENDPOINTS entry |
| 6 | `GET /marketing` 500 | `ui.py` now passes `runs` + `integration_status` |

---

## 6. Broken routes deferred (1)

| # | Finding | Class | Reason |
|---|---------|-------|--------|
| 5 | `GET /app` | FRONTEND BUILD GAP | `frontend/dist` absent; R1C must not rebuild/mount React CRM |

---

## 7. False positives

**0**

---

## 8. API-only classifications

| Route | Note |
|-------|------|
| `GET /health` | JSON liveness — no HTML expected; removed from sidebar |

**API-Only Routes Correctly Classified: 1**

---

## 9. Frontend build gaps

**1** — `/app` deferred.

---

## 10. Stale navigation corrections

1. QA Report link removed  
2. Marketing run View link removed  
3. Health sidebar item removed  
4. Pipeline “CrewAI QA” stage removed  
5. Pipeline “Sheet Sync” stage removed  

**Stale Navigation Links Corrected/Removed: 5**

---

## 11. Orphan template disposition

| Template | Action |
|----------|--------|
| `orchestration_run.html` | **KEEP** — reconnected `GET /orchestration/run/{run_id}` to Jinja template; Jinja failures block hardened |

**Removed: 0 · Deferred: 0**

---

## 12. Files modified

- `runner_api_routers/ui.py`
- `runner_api.py` (orchestration handler only)
- `templates/week_detail.html`
- `templates/marketing.html`
- `templates/pipeline.html`
- `templates/base.html`
- `templates/orchestration_run.html`
- `tests/test_r1c_route_hygiene.py` (new)
- `docs/audit/R1C_ROUTE_AUDIT.md`
- `docs/audit/R1C_ROUTE_TEMPLATE_HYGIENE_REPORT.md`

## 13. Files removed

**0**

---

## 14. Route inventory

| | Count |
|--|------:|
| Before | 58 |
| After | 58 |

(No new product routes; `/app` still unmounted.)

---

## 15. Focused tests

`tests/test_r1c_route_hygiene.py` + frozen engines: **113 passed**

## 16. Full regression

**397 passed; 8 failed; 4 errors** (409 collected = 388 baseline + 9 new R1C tests)

## 17. Historical failure comparison

`diff` of failure/error identities: **IDENTITIES UNCHANGED**

## 18. Runtime status

| Path | Status |
|------|--------|
| `/`, `/marketing`, `/pipeline`, `/publishing`, `/seo`, `/weeks`, `/health` | **200** |
| `/app` | **404** (deferred) |

**Runtime: PARTIAL** — remaining blocker: React `/app` (out of R1C scope).

**Remaining Runtime Blockers: 1**

## 19. Architecture verification (ATLAS)

Architecture v2.2 and OS/engine boundaries **UNCHANGED**. No module responsibility moves.

## 20. Frozen contracts

Publishing / Website / SEO Readiness / Technical SEO / Editorial / Deployment / Website prod baselines: **UNCHANGED**

## 21. Behavior

Outside corrected defects (stale links, marketing context, orchestration template wiring): **UNCHANGED**. No fake UI invented.

## 22. Cross-agent conflicts

**0**

## 23. Rollback

```bash
git checkout HEAD -- \
  runner_api_routers/ui.py runner_api.py \
  templates/week_detail.html templates/marketing.html \
  templates/pipeline.html templates/base.html \
  templates/orchestration_run.html
# remove tests/test_r1c_route_hygiene.py and docs/audit/R1C_* if reverting entirely
```

**Rollback: READY**

## 24. Remaining runtime/UI debt

1. `GET /app` / React CRM mount (future frontend sprint)  
2. Shadowed duplicate `@app` HTML handlers in `runner_api.py` (R1D candidate)  
3. Unused `_render_orchestration_run_detail` inline helper (dead after reconnect; R1D)  
4. CMS branding strings (Founder decision)  

## 25. Recommendation for R1D

**R1D — DEAD CODE & UNUSED DEPENDENCY CLEANUP**

---

## Verdict

**R1C ROUTE & TEMPLATE HYGIENE COMPLETE — READY FOR R1D**
