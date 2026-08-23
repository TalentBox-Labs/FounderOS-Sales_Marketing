# 02 — API Certification (Sprint D1)

Date: 2026-08-09  
Method: local `TestClient(runner_api:app)` against D0-fixed code; Docker `:8000` probed separately (pre-D0 image, ~46h uptime)

---

## Contract surface (no intentional changes)

D0 changed only the marketing subprocess module/flags.  
Response shape for `POST /marketing/generate` remains: `ok`, `stdout`, `stderr`, `output_path`.

---

## Local TestClient (fixed code) — authoritative for D0

| Endpoint | HTTP | Result | Notes |
|----------|-----:|--------|-------|
| `GET /health` | 200 | PASS | `status=ok`, `service=WorkCrew CMS OS` |
| `GET /api/v1/health` | 200 | PASS | `status=ok`, `service=WorkCrew CMS OS API` |
| `GET /weeks` | 200 | PASS | HTML |
| `GET /pipeline` | 200 | PASS | HTML |
| `GET /marketing` | 500 | Known | Jinja `integration_status` undefined in `templates/marketing.html` (UI context gap in `ui.py`); **not** part of D0 file change |
| `GET /api/v1/crm/contacts` | 200 | PASS | `ok=true` |
| `GET /api/v1/hermes/revenue-summary` | 200 | PASS | `ok=true` |
| `POST /marketing/generate` | 200 | PASS (path) | Contract keys present; stale `ModuleNotFound` **absent** (see 04) |
| Auth (`RUNNER_API_KEY` unset) | open | Known | Soft auth when key missing (same as Sprint C) |

---

## Docker live stack `:8000` (pre-D0 image)

| Endpoint | HTTP | Classification |
|----------|-----:|----------------|
| `GET /health` | 200 | Environment / healthy |
| `GET /api/v1/health` | 200 | Environment — metrics-shaped body (`overall/healthy`) differs from local simple liveness (Known Sprint C drift) |
| `GET /weeks` | 200 | OK |
| `GET /pipeline` | 200 | OK |
| `GET /marketing` | 500 | Known (same UI template gap) |
| `GET /api/v1/crm/contacts` | 404 | Environment — running image lag / route mismatch vs local HEAD |
| `GET /api/v1/hermes/revenue-summary` | 200 | OK |
| `POST /marketing/generate` | 200 body `ok:false` | Environment — **still** `No module named revenue_os.agents.marketing_crew` because API container **not rebuilt** with D0 |

**Important:** Docker API does **not** include the D0 repair until rebuild/restart. D1 certifies D0 against local fixed code (TestClient), consistent with D0 verification method.

---

## Authentication

| Mode | Observation |
|------|-------------|
| No `RUNNER_API_KEY` | Marketing/generate and generate accepted (open) on local TestClient |
| Key set mid-process after import | Subsequent writes returned 401 (middleware reads env); probe artifact only — not a contract change |

No auth contract changes in D0.

---

## API certification verdict

| Scope | Verdict |
|-------|---------|
| Health / UI weeks & pipeline / revenue | PASS (local) |
| Marketing generate contract (fixed code) | PASS — no contract change; import blocker cleared |
| Marketing HTML UI | Known failure (pre-existing) |
| Live Docker API image | PARTIAL / Environment (pre-D0) |

**No D0-induced API contract regressions.**
