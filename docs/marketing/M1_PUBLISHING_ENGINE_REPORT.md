# M1 — Publishing Engine (Phase 1) Implementation Report

Date: 2026-08-09  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
Architecture: **v2.1** ([Architecture_ADR_002.md](../architecture/Architecture_ADR_002.md))  
Sprint: M1 — Publishing Engine Phase 1

---

## Summary

Publishing Engine Phase 1 delivers **publication orchestration only**:

- Read editorially approved bundles
- Validate publish readiness
- Create publish jobs + queue
- Channel registration + adapter interfaces
- Manual publish / retry / cancel
- Append-only audit trail
- Queue + detail UI

**Not implemented (by design):** Website Engine, Social Engine, Campaign Engine, Celery, n8n, scheduling, AI publishing, external channel APIs, Markdown/HTML/SEO/RSS/sitemap.

---

## Files modified / created

| Path | Change |
|------|--------|
| `src/tools/publishing_engine.py` | **NEW** — state machine, jobs, channels, adapters, audit |
| `runner_api_routers/publishing.py` | **NEW** — additive `/api/v1/publishing` API |
| `runner_api.py` | Include `publishing_router` only |
| `runner_api_routers/ui.py` | `/publishing` queue + `/publishing/{job_id}` detail |
| `templates/publishing_queue.html` | **NEW** |
| `templates/publishing_detail.html` | **NEW** |
| `templates/base.html` | Nav link: Publishing |
| `tests/test_publishing_engine.py` | **NEW** — focused M1 tests |
| `docs/marketing/M1_PUBLISHING_ENGINE_REPORT.md` | **NEW** — this report |

**Untouched:** Website Engine (none exists), Social Engine adapters beyond `NOT_IMPLEMENTED`, Editorial/Content Studio contracts, Celery, Redis, Revenue OS.

---

## Architecture compliance (v2.1)

| Rule | Compliance |
|------|------------|
| Publishing owns orchestration only | **YES** |
| Website Engine owns render/site publish | **YES** — website adapter is PLACEHOLDER; no render |
| Social Engine owns social publishing | **YES** — adapters return `NOT_IMPLEMENTED` |
| No campaign / Celery / n8n | **YES** |
| Editorial approval required before job | **YES** — reads Editorial decision audit |
| Editorial approve ≠ auto-publish | **YES** — separate manual publish command |
| Additive APIs only | **YES** |

---

## Publishing state machine

```
Editorial Approved (prerequisite checkpoint)
        ↓
Publish Pending          ← job created
        ↓
Publishing               ← manual publish started
        ↓
   ┌────┴────┐
Published   Failed
              ↓
            Retry        ← retry command → Publishing again
```

Also: `cancelled` from `publish_pending` / `failed` / `retry`.

No scheduling. No automation. No AI publishing.

---

## Channels

| Channel | Adapter (M1) | Owner (destination) |
|---------|--------------|---------------------|
| website | `PLACEHOLDER` (orchestration recorded; no render) | Website Engine |
| linkedin | `NOT_IMPLEMENTED` | Social Engine |
| twitter | `NOT_IMPLEMENTED` | Social Engine |
| instagram | `NOT_IMPLEMENTED` | Social Engine |
| newsletter | `NOT_IMPLEMENTED` | Email Engine |

No external APIs called.

---

## API inventory (additive)

Prefix: `/api/v1/publishing`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/channels` | Registered channels + adapter mode |
| GET | `/jobs` | Publish queue (`include_terminal` optional) |
| POST | `/jobs` | Create job (requires editorial approval) |
| GET | `/{job_id}` | Job detail + audit |
| POST | `/{job_id}/publish` | Manual publish |
| POST | `/{job_id}/retry` | Retry failed job |
| POST | `/{job_id}/cancel` | Cancel pending/failed/retry |

Existing APIs unmodified.

---

## UI

| Route | Purpose |
|-------|---------|
| `/publishing` | Queue + create job form |
| `/publishing/{job_id}` | Detail: bundle, target, status, audit, Manual Publish / Retry / Cancel |

---

## Audit fields

Each audit event records:

- Bundle ID (`bundle_id`)
- Requested By
- Timestamp (`utc_timestamp`)
- Channel
- State
- Errors
- Retry Count

Storage: `output/publishing/audit.jsonl` + per-job snapshots under `output/publishing/jobs/`.

---

## Tests

File: `tests/test_publishing_engine.py`

Coverage: job creation, queue, status transitions, website placeholder, social NOT_IMPLEMENTED, audit, retry, cancel, permissions (AI blocked), invalid channel, duplicate publish, API + UI, editorial readiness unchanged.

Focused: **16 passed**

---

## Regression results

```bash
SECRET_KEY=… HEARTBEAT_ENABLED=0 .venv/bin/python -m pytest tests/ -q
```

| Metric | Result |
|--------|--------|
| Passed | **296** |
| Failed | **8** (historical: crews / utilities) |
| Errors | **4** (historical: orchestration / prospecting) |
| New M1 failures | **0** |

---

## Rollback strategy

1. Remove `publishing_router` include from `runner_api.py`.
2. Delete `runner_api_routers/publishing.py`, `src/tools/publishing_engine.py`, UI routes/templates/nav, tests.
3. Optionally archive `output/publishing/` (safe to retain as audit evidence).
4. No DB migrations to reverse.

---

## Architecture impact

| Dimension | Impact |
|-----------|--------|
| Architecture v2.1 | Respected; no ADR change required |
| Website Engine | Untouched |
| Social Engine | Untouched (interface stubs only) |
| Runtime outside Publishing Engine | Additive router/UI only |
| API (existing) | Unchanged |
| Database | None |

---

## Final verdict

# **PASS**

Publishing Engine Phase 1 implemented. Architecture v2.1 boundaries held.  
**READY FOR M2 — WEBSITE ENGINE.**
