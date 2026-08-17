# Technical SEO API Contract v1.0

**Sprint:** S2.5  
**Status:** **FROZEN v1.0**  
**Router:** `runner_api_routers/seo.py`  
**Prefix:** `/api/v1/seo`  
**Auth:** `_verify_api_key` on all readiness/technical routes

Breaking changes require explicit governance.

---

## 1. Technical SEO endpoints (frozen, read-only)

| Method | Path | Handler | Mutates |
|--------|------|---------|---------|
| `GET` | `/api/v1/seo/technical` | `seo_technical_site` | **No** |
| `GET` | `/api/v1/seo/technical/site` | `seo_technical_site` (alias) | **No** |
| `GET` | `/api/v1/seo/technical/{slug}` | `seo_technical_page` | **No** |

No POST/PUT/PATCH/DELETE technical endpoints.

---

## 2. GET `/api/v1/seo/technical` (+ `/technical/site`)

### Request

- Query: none  
- Body: none  
- Scans default Website artifact root (`output/website/`)

### Success (200)

`TechnicalSiteReport.to_dict()` plus envelope:

```json
{
  "ok": true,
  "artifact_root": "...",
  "configured_origin": "...",
  "status": "DOMAIN_BLOCKED|CRITICAL|ERROR|WARNING|PASS",
  "score": 0,
  "score_breakdown": {},
  "page_count": 0,
  "truncated": false,
  "max_pages": 200,
  "site_findings": [],
  "pages": [],
  "read_only": true,
  "mutates_content": false,
  "submits_to_search_engines": false,
  "s1_readiness_contract": "UNCHANGED",
  "production_seo_activation": "BLOCKED"
}
```

---

## 3. GET `/api/v1/seo/technical/{slug}`

### Request

| Param | Location |
|-------|----------|
| `slug` | path |

Reserved slug values `site` / `readiness` return 404 (avoid alias collision).

### Success (200)

`TechnicalPageReport.to_dict()` plus `ok: true`, `production_seo_activation: "BLOCKED"`.

### Errors

| Condition | HTTP |
|-----------|------|
| Missing `{slug}/index.html` (`tech_html_missing`) | 404 |

---

## 4. Finding object (frozen)

| Field | Type |
|-------|------|
| `id` | string |
| `category` | CANONICAL\|ROBOTS\|…\|CONSISTENCY |
| `severity` | DOMAIN_BLOCKED\|CRITICAL\|ERROR\|WARNING\|INFO\|PASS\|NOT_APPLICABLE |
| `message` | string |
| `artifact` | string |
| `expected` | string |
| `actual` | string |
| `recommendation` | string |
| `evidence` | object |
| `ownership` | SEO_ENGINE\|WEBSITE_ENGINE\|CONTENT\|DOMAIN\|EXPECTED |
| `blocking` | boolean |

---

## 5. Out of scope (same router prefix)

Legacy keyword tracking routes (`/keywords*`, mutating) are **not** part of Technical SEO v1.0.

S1 readiness routes (`GET /readiness`, `GET /readiness/{slug}`) are **independently frozen** under SEO Readiness Engine v1.0 (S1.5).

---

## 6. Guarantees

- Read-only technical analysis  
- No search-engine submission  
- No Internet crawling  
- No artifact mutation  
- Independent technical score (does not alter S1 readiness score)
