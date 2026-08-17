# Publishing API Contract — Baseline v1.0 (Frozen)

**Status:** FROZEN  
**Sprint:** M1.5  
**Date:** 2026-08-09  
**Prefix:** `/api/v1/publishing`  
**Router:** `runner_api_routers/publishing.py`  
**Auth:** Bearer `RUNNER_API_KEY` when configured (`_verify_api_key`)

Governance only. **No API expansion in M1.5.** Backward compatible with M1 implementation.

---

## Frozen endpoint inventory

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/channels` | Channel registry + known states |
| GET | `/jobs` | Publish queue |
| POST | `/jobs` | Create publish job |
| GET | `/{job_id}` | Job detail + audit |
| POST | `/{job_id}/publish` | Manual publish |
| POST | `/{job_id}/retry` | Retry failed/retry job |
| POST | `/{job_id}/cancel` | Cancel pending/failed/retry |

---

## Shared response envelope (`_job_view`)

Returned by POST `/jobs`, GET `/{job_id}`, publish / retry / cancel:

```json
{
  "ok": true,
  "job": { "...job object..." },
  "job_id": "pub_W99_website_…",
  "bundle_id": "W99",
  "channel": "website",
  "state": "publish_pending",
  "audit": [ "...audit records..." ],
  "orchestration_only": true,
  "website_engine": false,
  "social_engine": false
}
```

---

## GET `/channels`

**Response 200**

```json
{
  "ok": true,
  "channels": [
    {
      "channel": "website",
      "owner_engine": "Website Engine",
      "adapter": "placeholder"
    }
  ],
  "states": [
    "editorial_approved",
    "publish_pending",
    "publishing",
    "published",
    "failed",
    "retry",
    "cancelled"
  ]
}
```

---

## GET `/jobs`

**Query**

| Param | Type | Default | Meaning |
|-------|------|---------|---------|
| `include_terminal` | bool | false | Include `published` / `cancelled` |

**Response 200**

```json
{
  "ok": true,
  "count": 0,
  "items": [ "...job objects..." ],
  "orchestration_only": true
}
```

---

## POST `/jobs`

**Request**

```json
{
  "content_id": "W99",
  "channel": "website",
  "requested_by": "Human Name",
  "notes": "optional"
}
```

| Field | Required | Rules |
|-------|----------|-------|
| `content_id` | yes | Week id pattern `W##` / `W##A` |
| `channel` | yes | Registered channel |
| `requested_by` | yes | Human; AI tokens forbidden |
| `notes` | no | string |

**Errors**

| Status | When |
|--------|------|
| 403 | Non-human requester |
| 400 | Missing editorial approval, bad channel/id |
| 422 | Schema validation |

---

## GET `/{job_id}`

**Errors:** 404 if missing.

---

## POST `/{job_id}/publish` | `/retry` | `/cancel`

**Request**

```json
{
  "requested_by": "Human Name",
  "notes": "optional"
}
```

**Errors**

| Status | When |
|--------|------|
| 403 | Non-human requester |
| 404 | Unknown job |
| 409 | Duplicate publish (`published`) |
| 400 | Invalid transition |

---

## Job object (frozen fields — core)

| Field | Type | Notes |
|-------|------|-------|
| `schema_version` | int | `1` |
| `job_id` | string | `pub_{bundle}_{channel}_{hex}` |
| `bundle_id` | string | Content id |
| `channel` | string | Registered channel |
| `channel_owner` | string | Destination engine name |
| `state` | string | State machine value |
| `state_history` | array | Checkpoint trail |
| `requested_by` | string | Creator |
| `notes` | string | |
| `created_at` / `updated_at` | ISO-8601 Z | |
| `retry_count` | int | |
| `errors` | string[] | |
| `editorial_decision_id` | string? | |
| `editorial_phase` | string? | |
| `bundle` | string? | Path hint |
| `adapter_result` | object? | Last adapter payload |
| `cancelled` | bool | |
| `orchestration_only` | bool | always true in v1.0 |
| `website_engine` | bool | always false in v1.0 |
| `social_engine` | bool | always false in v1.0 |
| `campaign_engine` | bool | always false in v1.0 |

---

## Compatibility rules (frozen)

1. Do not rename paths or state strings without a new baseline version.
2. Additive optional response fields are allowed only in a later baseline (not M1.5).
3. Existing Editorial / Content Studio APIs remain unmodified.
4. UI routes `/publishing` and `/publishing/{job_id}` are part of the baseline surface (not REST contract, but freeze-compatible).
