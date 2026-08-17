# 04 — Content Studio Read Baseline

**Capability freeze:** Content Studio Read API (Sprint E2)  
**Evidence:** [E2_IMPLEMENTATION.md](../content-studio/E2_IMPLEMENTATION.md), [09_FIRST_IMPLEMENTATION_UNIT.md](../content-studio/09_FIRST_IMPLEMENTATION_UNIT.md), [10_SPRINT_E1_VERDICT.md](../content-studio/10_SPRINT_E1_VERDICT.md)

---

## Purpose

Expose Founder content inventory as JSON for Content Studio consumers without mutating source of truth and without importing CMS runtime.

Owning domain: **Marketing OS → Content Studio**.

---

## Endpoints

| Method | Path |
|--------|------|
| GET | `/api/v1/content-studio/content` |
| GET | `/api/v1/content-studio/content/{content_id}` |

Router module: `runner_api_routers/content_studio.py`  
Auth: `_verify_api_key` (Founder convention)

---

## Response contract

### List — `200`

```json
{
  "ok": true,
  "count": <int>,
  "items": [ <item>, ... ]
}
```

### Detail — `200`

```json
{
  "ok": true,
  "item": <item>
}
```

### Errors

| Code | Condition |
|-----:|-----------|
| 404 | Content id not in tracker |
| 400 | Invalid id format (`_validate_week_id`) |

### Item fields

From `tracker.csv` plus derived artifact flags:

`content_id`, `title`, `status`, `qa_status`, `current_step`, `next_step`, `draft_path`, `qa_output_path`, `final_output_path`, `artifact_folder`, `artifacts`

`artifacts` = boolean map from `_week_artifacts` (folder = `artifact_folder` if set, else `content_id`).

**Not exposed:** slug, CMS stage enum, publish_date, channels, author (unsupported on Founder tracker).

---

## Read-only guarantee

PASS (E2 tests + implementation review).

Endpoints only:

- read `tracker.csv` via `_read_tracker`
- check `input/` file presence via `_week_artifacts`
- validate id format

Do **not** write tracker, modify `input/`, invoke `_run` / publish / Celery business tasks / Sheets / DB writers.

---

## Source of truth

| Store | Role |
|-------|------|
| `tracker.csv` | Content inventory rows |
| `input/` | Week/content artifact files |

No alternate SoT introduced.

---

## Explicit exclusions

| Excluded | Status |
|---------|--------|
| Writes | No |
| Stage transitions | No |
| Publish / schedule | No |
| Google Sheets SoT | No |
| Flask CMS runtime | No |
| Database persistence changes | No |
| Lifecycle mutation | No |
| n8n / OpenClaw | No |

---

## Validation evidence

| Check | Result |
|-------|--------|
| Focused tests | 8/8 |
| Integration suite | 18/18 |
| Runtime smoke list/detail | PASS |
| Full suite | 228 passed; 8 known failed; 0 errors |
