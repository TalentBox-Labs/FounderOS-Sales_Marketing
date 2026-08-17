# R1F — UI / Route / Frontend Re-Audit (NOVA)

**Sprint:** R1F  
**Date:** 2026-08-13  
**Mode:** MEASUREMENT ONLY

---

## Runtime Smoke (TestClient)

| Path | Status | Classification |
|------|-------:|----------------|
| `/` | 200 | ACTIVE shell |
| `/marketing` | 200 | FIXED (was 500 in R0) |
| `/pipeline` | 200 | ACTIVE |
| `/publishing` | 200 | ACTIVE |
| `/seo` | 200 | ACTIVE |
| `/seo/technical` | 200 | ACTIVE |
| `/health` | 200 | ACTIVE API/health |
| `/content-studio` | 200 | ACTIVE |
| `/editorial` | 200 | ACTIVE |
| `/app` | **503** `not_built` | **OPTIONAL** CRM — non-blocking (R1C.1) |

Registered FastAPI routes: **60**.

`frontend/dist`: **absent** (expected; ignored).

---

## Navigation / Stale Links

R1C corrections still hold:

- No live nav to broken `/health` HTML expectation as primary nav defect
- `/qa-report`, `/marketing/run` detail invent, pipeline `sheet-sync` / `qa:` stages removed or commented per R1C
- Templates retain explanatory comments, not live broken hrefs

**Active broken routes remaining: 0**

---

## Templates

| Item | R0 | Current |
|------|----|---------|
| `templates/orchestration_run.html` | Orphan | **Connected** via `runner_api.py` TemplateResponse |
| Template count (`templates/*.html`) | — | 21 |

**Orphan templates remaining: 0**

---

## Optional Frontend Gaps

| Gap | Blocking? |
|-----|-----------|
| React CRM build / `frontend/dist` | **No** — explicit 503 contract |
| Future Social UI surfaces | N/A — not in scope |

Runtime must **not** be scored FAIL for absent optional CRM.

---

## Runtime Classification

**Runtime: PASS**

Core Jinja Marketing OS operator shell healthy. Optional `/app` is deferred product surface, not a regression.
