# UI2.5 — Cockpit Source Manifest v1.0

**STATUS: FROZEN**  
**Version:** v1.0  
**Verified integrations:** 8

---

## Authoritative sources (frozen)

| # | Source name | Owning OS | Function / API | R/W | SoT | Panel(s) | Degraded behavior |
|---|-------------|-----------|----------------|-----|-----|----------|-------------------|
| 1 | QualifiedDemand audit | Cross (MC04) | `_load_pending_qualified_demands()` → `AgentActionLog` | Read | `AgentActionLog` | Attention, Marketing/SEO | Attention `unavailable` if DB down |
| 2 | CRM Contacts | Sales | `_load_sales_snapshot()` → `Contact` ORM | Read | Revenue `Contact` | Sales, Attention | Sales `unavailable`; no fake zero |
| 3 | CRM Deals | Sales | `_load_sales_snapshot()` → `Deal` ORM | Read | Revenue `Deal` | Sales, Commercial Flow | Same as contacts |
| 4 | Editorial pending | Marketing | `build_editorial_pending()` | Read | Editorial staging/JSONL | Attention | Log error; skip item |
| 5 | Publishing queue | Marketing | `publishing_engine.list_queue()` | Read | Publishing engine jobs | Attention | Log error; skip item |
| 6 | SEO readiness | Marketing | `seo_engine.analyze_site()` | Read | Website artifacts | Marketing/SEO | Panel `error` + message |
| 7 | Technical SEO | Marketing | `seo_engine.analyze_technical_site()` | Read | Website artifacts | Marketing/SEO | Panel `error` + message |
| 8 | Heartbeat scheduler | Platform | `scheduler.status()`, `heartbeat_enabled()` | Read | In-process scheduler | Governance | Static governance still renders |

## Derived / static (not separate SoT)

| Item | Type | Notes |
|------|------|-------|
| High-score attention items | Derived from Contact (#2) | Recommendation only; no auto-qualify |
| Commercial flow stages | Composed from #1–#3 + static Revenue honesty | Revenue stage always `emerging` / NOT YET ACTIVE |
| Social status | Static honesty | `blocked` — not live |
| Governance frozen baseline list | Static documentation | Not runtime SoT |
| UI1.1 authority marker | Static attestation | Reflects UI1.1 freeze |

## Mutation sources (cockpit proxy only)

| Action | Canonical write path | Cockpit mutates? |
|--------|---------------------|------------------|
| QD Accept | `accept_qualified_demand()` | Yes (via proxy) |
| Contact.status | `apply_contact_status_update()` | Yes (via proxy) |
| All others | Frozen elsewhere | **No cockpit exposure** |

## UI2 count reconciliation

UI2 reported **11** data sources (UI1 widget map). Repository implements **8** distinct authoritative integrations. The 3 not implemented as separate sources:

1. Agent activity log (heartbeat runs used instead in governance)
2. Standalone lead-score API (derived from Contact query)
3. Commercial flow as independent SoT (composition only)

**Frozen count for baseline:** **8**
