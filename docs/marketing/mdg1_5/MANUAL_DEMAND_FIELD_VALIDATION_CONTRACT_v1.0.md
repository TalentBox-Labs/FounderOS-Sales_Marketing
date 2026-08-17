# MANUAL DEMAND FIELD / VALIDATION CONTRACT v1.0

**STATUS: FROZEN**  
**Source:** `ManualDemandRegisterBody` + adapter in `runner_api_routers/manual_demand.py`

| Field | Class | Rule |
|-------|-------|------|
| email | REQUIRED | min 3; must contain `@` and `.` in domain; lowercased |
| name | OPTIONAL | max 255 |
| phone | OPTIONAL | max 50 |
| company_name | OPTIONAL | max 255 → `company_hint.name` |
| company_domain | OPTIONAL | max 255 → `company_hint.domain` |
| source | REQUIRED (default `manual`) | Must be in `SOURCE_TO_CONTACT` keys |
| source_detail | OPTIONAL | Free text → `content_attribution.source_detail` |
| context_note | OPTIONAL | → `marketing_qualification.notes` |
| demand_id | OPTIONAL | UUID for idempotent retry; else server UUID |
| occurred_at | DERIVED | Server UTC ISO |
| channel | DERIVED | `manual_founder_registration` |
| content_attribution.registration_mode | DERIVED | `manual_founder_ui` |
| content_attribution.manually_supplied | DERIVED | `true` |
| requested_by | DERIVED | Server operator only |
| UTM / campaign / referrer / lead score | UNSUPPORTED | Never fabricated |
| consent | UNSUPPORTED on this form | Always `None` |

## Error behavior

| Condition | HTTP |
|-----------|------|
| Missing/invalid email or source | 422 |
| Invalid demand_id | 422 |
| Operator env invalid | 503 |
| API key required, absent | 401 |
| Service HumanAuthorityError | 403 |

Success only when `register_marketing_handoff` returns successfully.
