# Publishing Audit Schema — Baseline v1.0 (Frozen)

**Status:** FROZEN  
**Sprint:** M1.5  
**Date:** 2026-08-09  
**Storage:** `output/publishing/audit.jsonl` (append-only)  
**Writer:** `src/tools/publishing_engine.py` → `append_audit`  
**Parent:** [M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md)

Governance only. No schema changes in M1.5.

---

## Schema version

`schema_version: 1`

---

## Required fields (frozen)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bundle_id` | string | **YES** | Editorial / content bundle id |
| `channel` | string | **YES** | Target channel |
| `requested_by` | string | **YES** | Human requester (Requester) |
| `utc_timestamp` | string | **YES** | ISO-8601 UTC (`…Z`) |
| `state` | string | **YES** | Job state after event |
| `retry_count` | int | **YES** | Retry counter at event time |
| `errors` | string[] | **YES** | Error list (may be empty) |

---

## Additional baseline fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | int | Always `1` in this baseline |
| `audit_id` | string | UUID |
| `event` | string | `job_created` \| `state_change` |
| `job_id` | string | Publish job id |
| `notes` | string | Optional free text |

---

## Example record

```json
{
  "schema_version": 1,
  "audit_id": "…",
  "event": "state_change",
  "utc_timestamp": "2026-08-09T18:00:00Z",
  "job_id": "pub_W99_website_abc123def0",
  "bundle_id": "W99",
  "requested_by": "Krishna Founder",
  "channel": "website",
  "state": "published",
  "errors": [],
  "retry_count": 0,
  "notes": "Published (orchestration)"
}
```

---

## Immutability

- Audit file is **append-only**
- Events are never rewritten in place
- Job snapshots under `output/publishing/jobs/{job_id}.json` may update; audit history remains the forensic trail

---

## Compatibility

Any consumer of Publishing audit MUST tolerate unknown additive keys in a future baseline, but MUST NOT drop the required fields listed above in v1.0 writers.
