# SEO Readiness API Contract v1.0

**Sprint:** S1.5 freeze  
**Agent:** NOVA  
**Status:** FROZEN  
**Router:** `runner_api_routers/seo.py`  
**Prefix:** `/api/v1/seo`

---

## 1. Readiness endpoints (frozen, read-only)

| Method | Path | Auth | Mutates |
|--------|------|------|---------|
| `GET` | `/api/v1/seo/readiness` | `_verify_api_key` | **No** |
| `GET` | `/api/v1/seo/readiness/{slug}` | `_verify_api_key` | **No** |

No POST/PUT/PATCH/DELETE readiness endpoints exist.

---

## 2. GET `/api/v1/seo/readiness`

### Request

- Query parameters: none (uses default Website artifact root)
- Body: none

### Behavior

Calls `analyze_site()` over `output/website/` (default artifact root).

### Success response (200)

Additive fields on `SiteReadinessResult.to_dict()`:

```json
{
  "ok": true,
  "production_seo_activation": "BLOCKED",
  "artifact_root": "...",
  "configured_origin": "...",
  "status": "DOMAIN_BLOCKED|ERROR|WARNING|PASS",
  "page_count": 0,
  "truncated": false,
  "max_pages": 200,
  "pages": [ /* PageReadinessResult.to_dict() */ ],
  "read_only": true,
  "mutates_content": false,
  "submits_to_search_engines": false
}
```

---

## 3. GET `/api/v1/seo/readiness/{slug}`

### Request

| Param | Location | Description |
|-------|----------|-------------|
| `slug` | path | Artifact directory name |

### Success response (200)

```json
{
  "ok": true,
  "production_seo_activation": "BLOCKED",
  "slug": "...",
  "canonical_url": "...",
  "configured_origin": "...",
  "status": "...",
  "score": 0,
  "score_breakdown": { "...": "..." },
  "ok": true,
  "seo_ready": false,
  "indexing_activation_allowed": false,
  "title": "...",
  "description": "...",
  "errors": [],
  "warnings": [],
  "domain_blockers": [],
  "info": [],
  "checks": { "<rule_id>": { "id": "...", "status": "...", "message": "...", "field": "...", "recommendation": "...", "evidence": {} } },
  "read_only": true,
  "mutates_content": false,
  "submits_to_search_engines": false
}
```

Note: JSON key `ok` appears both as engine field (`PageReadinessResult.ok`) and API envelope; envelope sets `ok: true` after merge — consumers should treat `status` / `seo_ready` / `domain_blockers` as readiness truth.

### Error behavior

| Condition | HTTP | Detail |
|-----------|------|--------|
| Missing `{slug}/index.html` | 404 | `Page artifact not found: {slug}` |

---

## 4. CheckResult schema (frozen)

| Field | Type |
|-------|------|
| `id` | string |
| `status` | PASS\|WARNING\|ERROR\|DOMAIN_BLOCKED\|NOT_APPLICABLE\|INFO |
| `message` | string |
| `field` | string |
| `recommendation` | string |
| `evidence` | object |

---

## 5. Out-of-scope routes on same prefix (not part of readiness freeze)

Pre-existing keyword tracking (Revenue OS style) remains on the same router:

| Method | Path | Mutates |
|--------|------|---------|
| GET | `/api/v1/seo/keywords` | no |
| POST | `/api/v1/seo/keywords` | yes (keyword log) |
| GET | `/api/v1/seo/keywords/{id}` | no |
| DELETE | `/api/v1/seo/keywords/{id}` | yes |
| POST | `/api/v1/seo/keywords/{id}/checks` | yes |
| GET | `/api/v1/seo/summary` | no |

**Readiness freeze assertion:** readiness routes are GET-only and do not mutate Website/content artifacts. Keyword mutations are a separate historical surface and do not implement SEO readiness activation, indexing, or publishing.

---

## 6. Guarantees

- No search-engine submission  
- No sitemap ping  
- No content rewrite  
- `production_seo_activation` always reported `"BLOCKED"` on readiness endpoints in current code
