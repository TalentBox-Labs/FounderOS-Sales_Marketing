# MDG1 — Manual Founder Demand Registration

**Sprint:** FOUNDER OS MDG1  
**Date:** 2026-08-13  
**Type:** CONNECT_EXISTING  
**Status:** IMPLEMENTED

## Implementation boundary

```
Trusted Founder UI  GET /operator/demand/register
        ↓
Ephemeral form model (ManualDemandRegisterBody)
        ↓
Trusted proxy  POST /api/v1/mdg/manual-demand/register
        ↓
Frozen MC04.5  register_marketing_handoff → AgentActionLog
        ↓
Existing OF1.5 Operator Flow accept/reject → Contact → …
```

No new persistent Demand SoT. No public capture. OF1.5 operator_flow router POST set unchanged.

## Topology

Manual Demand Registration → QualifiedDemand handoff → Contact (on accept) → Deal → Closed-Won → CommercialOutcome → Revenue Decision

Audience → Demand remains **MANUAL_OPERABLE** (not automated public capture). Total value chain still not COMPLETE for public audience.

## Field mapping

| UI field | MC04.5 field | Class |
|----------|--------------|-------|
| email | person.email | REQUIRED |
| name | person.name | OPTIONAL |
| phone | person.phone | OPTIONAL |
| company_name | company_hint.name | OPTIONAL |
| company_domain | company_hint.domain | OPTIONAL |
| source | source (allowlist) | REQUIRED (default `manual`) |
| source_detail | content_attribution.source_detail | OPTIONAL |
| context_note | marketing_qualification.notes | OPTIONAL |
| demand_id | demand_id | OPTIONAL (server UUID if omitted) |
| — | occurred_at | DERIVED (server UTC) |
| — | channel | DERIVED `manual_founder_registration` |
| — | content_attribution.registration_mode | DERIVED `manual_founder_ui` |
| — | requested_by | DERIVED `FOUNDER_OS_OPERATOR_NAME` |
| UTM / campaign / referrer | — | NOT SUPPORTED (not fabricated) |

## Human authority

Server `_trusted_cockpit_operator()` only. Body has no `requested_by`. Spoofed client metadata ignored. Agent/AI operator env → 503.

## Provenance

`content_attribution.manually_supplied=true`. Missing UTM stays missing.

## Idempotency

Same `demand_id` → MC04.5 idempotent handoff (`idempotent: true`). No duplicate AgentActionLog row.

## Negative scope

Public forms · CAPTCHA · social/email ingest · SaaS tenancy · CRM SPA · Deal/Revenue auto-mutation · new SoT · Lovable.

## SaaS forward-compatibility

| Choice | Note |
|--------|------|
| Instance-global operator env | Later SaaS needs per-user identity — do not bake client-trusted identity |
| AgentActionLog target_id = demand_id | Tenant column absent today; migration would be additive later |
| Separate `/api/v1/mdg` prefix | Keeps OF1.5 freeze intact; easy to tenant-wrap later |

**SaaS Forward-Compatibility: PASS** (no permanent single-user lock-in beyond existing instance model)

## Files changed

| File | Change |
|------|--------|
| `runner_api_routers/manual_demand.py` | NEW proxy |
| `templates/operator_demand_register.html` | NEW UI |
| `runner_api_routers/ui.py` | GET page |
| `runner_api.py` | Mount router |
| `templates/operator.html` | Link only |
| `tests/test_mdg1_manual_demand_registration.py` | Focused tests |
| `docs/marketing/mdg1/*` | Docs |

## Tests

`tests/test_mdg1_manual_demand_registration.py`
