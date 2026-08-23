# Publishing Channel Interface — Baseline v1.0 (Frozen)

**Status:** FROZEN  
**Sprint:** M1.5  
**Date:** 2026-08-09  
**SoT:** `src/tools/publishing_engine.py` (`ADAPTERS`, `list_channels`)  
**Parent:** [M1_5_PUBLISHING_BASELINE.md](M1_5_PUBLISHING_BASELINE.md)

Governance only. No adapter implementation changes in M1.5.

---

## Purpose

Publishing Engine registers channels and invokes **channel adapters** during manual publish.  
Adapters are **interfaces** for orchestration results. They do **not** own Website/Social/Email product logic beyond returning a structured result.

---

## Registered channels (frozen)

| Channel id | Owner engine (destination) | M1.5 adapter mode |
|------------|----------------------------|-------------------|
| `website` | Website Engine | `placeholder` |
| `linkedin` | Social Engine | `not_implemented` |
| `twitter` | Social Engine | `not_implemented` (Twitter/X) |
| `instagram` | Social Engine | `not_implemented` |
| `newsletter` | Email Engine | `not_implemented` |

---

## Provider / adapter callable contract (frozen)

```text
adapter(job: dict) -> dict
```

### Required result fields

| Field | Type | Meaning |
|-------|------|---------|
| `ok` | bool | Success for orchestration transition |
| `status` | string | `PLACEHOLDER` \| `NOT_IMPLEMENTED` \| (future codes) |
| `channel` | string | Channel id |
| `owner_engine` | string | Destination engine |
| `message` | string | Human-readable explanation |

### Additional fields (baseline)

| Field | When | Meaning |
|-------|------|---------|
| `website_engine_invoked` | website | Must be `false` until Website Engine exists |
| `rendering_performed` | website | Must be `false` in Publishing Engine |
| `external_api_called` | social/email stubs | Must be `false` |

---

## Website placeholder (frozen behavior)

- Returns `ok: true`, `status: "PLACEHOLDER"`
- Does **not** render Markdown/HTML
- Does **not** deploy, invalidate cache, or call Website Engine
- Job may transition to `published` meaning **orchestration recorded**, not site live

---

## Not-implemented providers (frozen behavior)

- Returns `ok: false`, `status: "NOT_IMPLEMENTED"`
- Job transitions to `failed`
- No LinkedIn / X / Instagram / email APIs called

---

## Stability rules

1. Channel ids above are frozen for v1.0.
2. Adding a new channel requires a new baseline / ADR (not silent).
3. Replacing website `PLACEHOLDER` with Website Engine invocation is an **M2+** change; Publishing Engine must still only orchestrate.
4. Social/Email adapters remain out of Publishing Engine ownership (Architecture v2.1).
