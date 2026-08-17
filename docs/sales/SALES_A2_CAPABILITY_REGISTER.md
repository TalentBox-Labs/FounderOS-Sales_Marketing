# SALES A2 — Capability Register

**Sprint:** SALES A2 — Capability & Implementation Priority Review  
**Date:** 2026-08-13  
**Mode:** Analysis only — no implementation  
**Authoritative prior:** SALES A0 matrix + A1.5 freeze (contracts unchanged)

---

## Count reconciliation vs A0

| Class (A2 normalized) | A0 | A2 | Notes |
|-----------------------|---:|---:|-------|
| LIVE | 12 | **12** | C01–C03, C07–C09, C11–C15, C17 unchanged |
| PARTIAL | 6 | **6** | C04–C06, C10, C16, C18 |
| API_ONLY | 4 | **4** | C19–C22 |
| MISSING CORE | 9 | **9** | A0 expanded list (not only C26–C28) |
| PLACEHOLDER | 1 | 1 | C23 — not in A2 priority candidate set |
| DEAD_CODE / RETIRED | 2 | 2 | C24–C25; I08 retired at integration layer |

A0 matrix also had NOT_IMPLEMENTED (3) = C26–C28, which are **subset** of the 9 missing-core gaps. A2 does **not** rewrite A0 history; missing-core remains the 9-item product gap list.

**Normalized candidate-relevant inventory: Live 12 · Partial 6 · API-Only 4 · Missing Core 9**

---

## Register (normalized)

| ID | Name | Purpose | State | Code | API | UI | Persist | Tests | Domain | Mkt | Rev | Ext | Auth | Human | Agent | Defects / debt |
|----|------|---------|-------|------|-----|----|---------|-------|--------|-----|-----|-----|------|-------|-------|----------------|
| C01 | Jinja `/sales` | Prospecting ops shell | LIVE | `templates/sales.html`, `ui.py` | via prospecting | LIVE | presets JSON | sales/prospecting | Sales ops | No | Soft | No | Shell | Ops | No | — |
| C02 | Prospecting plan/import | SDR plan | LIVE | `prospecting.py`, service | LIVE | `/sales` | DB+JSON | `test_sales_api_runner`, prospecting_ui ERR | Sales | No | Soft | Optional MCP | API key / JWT dual | Ops | No | Dual stack tests |
| C03 | Contacts CRM | Person CRUD | LIVE | `crm.py` | LIVE runner | SPA unmounted | DB | thin | Sales ops / Rev SoT | No | Hard SoT | No | API key | Ops | No | No owner FK |
| C04 | Contact enrich | Proxycurl enrich | PARTIAL | enrich route | LIVE | SPA | DB | thin | Sales | No | Soft | **I07 paid** | Vault | Approve | Assist | External setup |
| C05 | Deals list/create/get | Commercial pursuit | PARTIAL | `crm.py` | Create/list; **no stage PATCH** | SPA | DB | thin | Sales ops / Rev SoT | No | Hard | No | API key | Ops | No | Stage gap |
| C06 | Pipeline summary | Stage aggregates | PARTIAL | `GET /crm/pipeline` | Summary only | SPA | DB | thin | Sales ops | No | Soft | No | API key | No | No | Read-only |
| C07 | Activities | Notes/tasks | LIVE | crm activities | LIVE | SPA | DB | thin | Sales / Rev | No | Hard | No | API key | Ops | No | Dual note models |
| C08 | Follow-ups | Operator inbox | LIVE | `followups.py` | LIVE | SPA/Dash | DB | thin | Sales | No | Soft | No | API key | Ops | No | — |
| C09 | Outreach sequences | Sequence CRUD | LIVE | outreach router | LIVE | `/sales`/SPA | DB | routers | Sales | No | Soft | No | API key | Ops | Draft agents | — |
| C10 | Outreach send | Deliver email | PARTIAL | approvals→n8n | Partial | SPA | DB | thin | Sales / Auto | No | Approvals | **I04 n8n** | Config | **Approve** | Draft only | Ext setup |
| C11 | Sales AI assists | Draft research/email | LIVE | `sales_agents.py` | LIVE | SPA | — | agents | Sales / AI | No | Soft | **I12 LLM** | Keys | Draft OK | Assist | Paid usage |
| C12 | Hermes score/qualify | Score/pipeline health | LIVE | hermes + scorers | LIVE | API | DB | hermes | Sales | No | Hard status | No | API key | **Gap: auto status** | Score | Dual scorers |
| C13 | Approvals queue | Human gate | LIVE | approvals | LIVE | SPA | DB | thin | Revenue queue | No | Hard | n8n | API key | **Required** | File only | — |
| C14 | Copilot | Operator assist | LIVE | copilot | LIVE | SPA | — | thin | Sales | No | Soft | LLM | API key | Ops | Assist | Needs `/app` for UI |
| C15 | Goals | Hermes goals | LIVE | goals | LIVE | SPA | DB | thin | Sales/Rev | No | Soft | No | API key | Ops | No | — |
| C16 | Automation surfaces | Event workflows | PARTIAL | EventBus/WF | Partial | SPA | in-mem+DB | thin | Auto/Rev | No | Soft | No | — | Policy | Risk | In-memory |
| C17 | CSM health | Account health | LIVE | `csm.py` | LIVE | SPA | computed | thin | Revenue/CS | No | Hard | No | API key | No | No | — |
| C18 | React CRM SPA | Full CRM UI | PARTIAL | `frontend/` | expects runner | **UNMOUNTED** | — | r1c 503 | Sales UI | No | Soft | No | — | — | — | Frozen disposition |
| C19 | Companies CRUD | Org entity API | API_ONLY | JWT companies | JWT only | None shell | DB | thin | Rev SoT | No | Hard | No | JWT | Ops | No | Not on runner |
| C20 | Deal stage advance | Pipeline ops | API_ONLY | JWT PUT + `advance_deal_stage` | JWT **yes**; runner **no** | SPA display | DB | thin | **Sales ops** | No | Hard entity | Optional webhook | JWT vs key | **HUMAN_ONLY** | Prohibited auto | **Primary gap** |
| C21 | Forecasting APIs | Win/forecast | API_ONLY | forecasting | LIVE | None Jinja | DB | thin | Revenue | No | Hard | No | API key | HUMAN | No | — |
| C22 | JWT dual CRM | Parallel stack | PARTIAL | `revenue_os.main` | Full | PLACEHOLDER static | DB | prospecting_ui | Dual | No | Hard | No | JWT | — | — | ACCEPTED_LEGACY |
| MC01 | `sales_os` package | Code boundary | MISSING | — | — | — | — | — | Arch | No | Soft | No | — | — | — | Deferred post priority |
| MC02 | Lead naming clarity | Alias docs | MISSING* | Resolved A1 alias | — | — | — | — | Domain | No | Soft | No | — | — | — | *Contract-resolved; no build |
| MC03 | Opportunity naming | Alias docs | MISSING* | ≡ Deal A1 | — | — | — | — | Domain | No | Soft | No | — | — | — | *Contract-resolved |
| MC04 | Marketing→Sales handoff | `QualifiedDemand` | MISSING | enum only | No | No | No | No | Boundary | **Hard** | Soft | No | — | Intake | No | BUILD later |
| MC05 | Runner deal stage update | Writable pipeline | MISSING | service exists JWT | Runner gap | No writable | DB | No runner | Sales ops | No | Hard | No | API key | HUMAN | No | = C20 completion |
| MC06 | Close→Customer/Client | `CommercialOutcome` | MISSING | thin CLOSED_WON | Partial JWT | No | DB | No | Boundary | No | **Hard** | No | — | HUMAN | No | After stage ops |
| MC07 | Owner FK / RBAC | Assignment | MISSING | orphan UUID | No | No | Partial | No | Shared | No | Soft | No | RBAC | HUMAN | No | Platform |
| MC08 | Companies operator UI | Org screens | MISSING | JWT API | API_ONLY | No | DB | No | Sales UI | No | Hard | No | — | Ops | No | After/with C19 |
| MC09 | Relational PipelineStage | Stage entity | MISSING | enum+CSV | — | — | Partial | No | Rev model | No | Hard | No | — | — | — | Migration later |

\*MC02/MC03 are product-gap labels from A0; A1/A1.5 **resolved conceptually** — do not BUILD_NEW tables.

---

## Candidate disposition preview

See scorecard. LIVE rows excluded from A3 build priority except as reuse targets.
