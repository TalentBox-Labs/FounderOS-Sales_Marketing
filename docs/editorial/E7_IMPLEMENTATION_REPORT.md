# E7 — Editorial Approval Engine (Phase 1) Implementation Report

Date: 2026-08-09  
Canonical repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
Sprint: E7 — Editorial Approval Engine (Phase 1)

---

## Founder Decisions (ratified)

| ID | Decision |
|----|----------|
| FDR-001 | Phase-scoped promote only |
| FDR-002 | Human approval only; AI may recommend, never approve |
| FDR-003 | Editorial approval does **not** authorize publishing |

ADR: [ADR_EDITORIAL_APPROVAL_SEMANTICS.md](../architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md) → **Accepted**  
Record: [F0_FOUNDER_DECISION_RECORD.md](../governance/F0_FOUNDER_DECISION_RECORD.md)

---

## Scope delivered

- Editorial Approval Engine over **existing** content bundles / staging / readiness evidence
- Display states: Draft, Review, Approved, Rejected, Needs Changes, Ready
- Additive APIs under `/api/v1/editorial/...` (existing readiness contract unchanged)
- UI: pending queue + approval detail with decision buttons and notes
- Append-only decision audit (`output/editorial_decisions/`)
- Approve → phase-scoped `promote_staged` only; reject / request-changes → audit only
- **No** publishing, scheduling, campaign, Sales OS, Revenue OS approvals, OpenClaw, Celery, or Redis changes

---

## Files modified

| Path | Change |
|------|--------|
| `src/tools/editorial_approval.py` | **NEW** — decision store, state derivation, human gate, promote wrapper |
| `runner_api_routers/editorial.py` | Additive pending/detail/approve/reject/request-changes endpoints |
| `runner_api_routers/ui.py` | UI routes `/editorial`, `/editorial/pending`, `/editorial/{id}` |
| `templates/base.html` | Nav link: Editorial Approval |
| `templates/editorial_pending.html` | **NEW** — pending queue |
| `templates/editorial_detail.html` | **NEW** — detail + decision UI + audit table |
| `tests/test_editorial_approval.py` | **NEW** — focused E7 tests |
| `docs/architecture/adr/ADR_EDITORIAL_APPROVAL_SEMANTICS.md` | Status → Accepted |
| `docs/governance/F0_FOUNDER_DECISION_RECORD.md` | Ratified FDR-001/002/003 |
| `docs/editorial/E7_IMPLEMENTATION_REPORT.md` | **NEW** — this report |

**Not modified:** Content Studio APIs, readiness response shape, Celery, Redis, Sales/Revenue routers, publish/go-live helpers.

---

## Endpoints added

Prefix: `/api/v1/editorial` (Founder convention; additive only)

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/pending` | Pending queue (non-Approved states) |
| GET | `/{content_id}` | Approval detail + audit + readiness snapshot |
| POST | `/{content_id}/approve` | Human approve → phase-scoped promote |
| POST | `/{content_id}/reject` | Human reject → audit only |
| POST | `/{content_id}/request-changes` | Human needs-changes → audit only |

**Unchanged:** `GET /api/v1/editorial/readiness/{content_id}`

Request body (POST): `{ "approver": string, "notes"?: string, "phase"?: "2a"|"2b"|"3", "staging_root"?: string }`

Every response sets `authorizes_publish: false` (FDR-003).

---

## UI components added

| Route | Template | Purpose |
|-------|----------|---------|
| `/editorial` | `editorial_pending.html` | Pending queue |
| `/editorial/pending` | same | Alias |
| `/editorial/{content_id}` | `editorial_detail.html` | Detail, decision buttons, notes, audit |

Nav: Overview → **Editorial Approval**

UI reads builders / existing artifacts only; decisions POST to additive APIs.

---

## Audit model

Append-only JSONL: `output/editorial_decisions/decisions.jsonl`  
Latest snapshot: `output/editorial_decisions/{content_id}_{phase}_latest.json`

Each record includes:

| Field | Required |
|-------|----------|
| approver | yes |
| utc_timestamp | yes |
| decision | yes (`approve` / `reject` / `request_changes`) |
| notes | yes (may be empty string) |
| bundle | yes (staging path or `input/{id}`) |
| phase | yes (`2a` / `2b` / `3`) |
| promotion | metadata (`attempted`, `ok`, `exit_code`, `publishes: false`) |
| authorizes_publish | always `false` |

Approve also continues to write existing `output/promotion_audit/` via `promote_staged`.

---

## Tests added

File: `tests/test_editorial_approval.py`

Coverage:

- Approval (promote invoked, phase-scoped)
- Rejection
- Needs Changes / request-changes
- Promotion metadata + no publish flag
- Audit field completeness
- Permissions (AI/automation blocked; missing approver)
- Duplicate approvals (409)
- Invalid transitions (missing staging, invalid phase)
- Readiness endpoint unchanged
- UI pending + detail pages

Focused run: **33 passed** (`test_editorial_approval.py` + `test_editorial_readiness.py`)

---

## Regression results

Command:

```bash
SECRET_KEY=… HEARTBEAT_ENABLED=0 .venv/bin/python -m pytest tests/ -q
```

| Metric | Result |
|--------|--------|
| Passed | **280** |
| Failed | **8** (historical leave-behinds: crews unit, utilities unit) |
| Errors | **4** (historical: orchestration / prospecting API env) |
| New E7 failures | **0** |
| Readiness / Content Studio regressions | **0** |

Historical failures (unchanged class):

- `tests/test_crews_unit.py` (QA/Editor output format)
- `tests/test_utilities_unit.py` (file ops / markdown)
- `tests/test_orchestration_api.py` (errors)
- `tests/test_prospecting_ui.py` (errors)

**Verdict on E7 delta:** no new regressions introduced.

---

## Architecture impact

| Area | Impact |
|------|--------|
| Editorial Engine | Decision layer + HTTP surface added |
| Promote CLI | Reused; not rewritten |
| Tracker.csv | **Not mutated** by approve/reject/request-changes |
| Publishing | **No path** from editorial approval |
| Revenue OS `/approvals` | Untouched |
| Celery / Redis / OpenClaw | Untouched |
| Content Studio / Kanban / Readiness | Additive consumers only; contracts preserved |

States are an **Editorial Engine display/decision layer**, not a CMS Sheets import or tracker lifecycle rewrite.

---

## Rollback plan

1. Remove routes from `runner_api_routers/editorial.py` (leave readiness) and UI routes/templates/nav.
2. Delete or quarantine `src/tools/editorial_approval.py` and `tests/test_editorial_approval.py`.
3. Optionally archive `output/editorial_decisions/` (append-only; safe to retain).
4. Revert ADR status only if governance requires (prefer leave Accepted + note rollback).
5. Promote audits already written under `output/promotion_audit/` remain valid historical evidence — do not delete.

No DB migrations; rollback is file/router delete only.

---

## Final verdict

# **PASS**

E7 Phase 1 Editorial Approval Engine delivered under FDR-001 / FDR-002 / FDR-003 with additive APIs, UI, audit, focused tests green, and no new full-suite regressions.
