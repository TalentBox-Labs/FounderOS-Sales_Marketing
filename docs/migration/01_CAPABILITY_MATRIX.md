# 01 — Capability Matrix

**Canonical product:** Repository A — `TB-FounderOS-Sales_Marketing` (Founder OS; Architecture Baseline v1.0 FROZEN)  
**Capability source:** Repository B — `CMS_OS_V1`  
**Sprint:** B — Analysis only  

### Evidence boundary (CMS_OS_V1)

| Fact | Evidence |
|------|----------|
| `CMS_OS_V1` tree contains **0** `.py` files | `find CMS_OS_V1 -name '*.py'` → 0 |
| Capabilities below for CMS are taken from CMS_OS_V1 documentation (`README.md`, `PROJECT_REVIEW.md`, `MULTI_PLATFORM_STATUS.md`, `AGENTS.md`, `TOOLS.md`, `README_RECOVERY.md`, guides) | Files present under `/Users/krishna/Documents/CMS_OS_V1` |
| CMS_OS_V1 README / TOOLS.md name `workcrew-cms-os` as the implementation workspace / GitHub source of truth | `README.md` directory structure; `TOOLS.md` GitHub row |
| Where a CMS capability requires executable corroboration, sibling tree `/Users/krishna/Documents/workcrew-cms-os` was checked only as the locus CMS_OS_V1 documents — **not** as a replacement canonical product | Dashboard `app.py` routes, `n8n-workflows/` count, `agents/`, `content/`, `brand/` observed |

Status values: Already Exists in Founder | Better in Founder | Better in CMS | Partial in Founder | Partial in CMS | Duplicate | Missing | Legacy | Not Applicable  

Decision values: KEEP FOUNDER | MIGRATE FROM CMS | MERGE | REWRITE | RETIRE | DEFER  

---

## Capability matrix

| Domain | Capability | Founder Status | CMS Status | Canonical Source | Decision | Migration Required | Evidence |
|--------|------------|----------------|------------|------------------|----------|-------------------|----------|
| Executive OS | Executive KPI / insights dashboard API | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: `/api/v1/paperclip`, `revenue_os/executive`. CMS docs: no executive KPI API |
| Executive OS | OpenClaw CEO / strategy agent persona | Missing | Better in CMS | CMS (docs) + Founder agents later | DEFER | Partial | CMS: `AGENTS.md` CEO agent. Founder: no CEO SOUL agent pack |
| Sales OS | CRM contacts / deals / activities | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: `/api/v1/crm`, models. CMS: content-ops focus only |
| Sales OS | Prospecting plan / execute / import | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: prospecting router + service. CMS: not documented |
| Sales OS | Outreach sequences + enroll | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: outreach API/models. CMS: not documented |
| Sales OS | SDR / sales AI assists | Partial in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: hermes SDR, agents sales routes, `ai_service`. CMS: none |
| Revenue OS | Deal pipeline health / scoring / forecast | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: hermes, forecasting, lead scoring. CMS: none |
| Revenue OS | Revenue automation / goals / approvals | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: automation, goals, approvals routers. CMS: none |
| Marketing OS — Content Studio | Week/content bundle workspace + tracker | Already Exists in Founder | Better in CMS (ops UX) | Founder runtime + CMS UX patterns | MERGE | Yes | Founder: `input/`, tracker, weeks UI. CMS: content inventory W01–W15, calendar/pipeline board documented + dashboard routes in documented locus |
| Marketing OS — Content Studio | Pipeline board / calendar / content detail portal | Partial in Founder | Better in CMS | CMS → Founder UI | MIGRATE FROM CMS | Yes | Founder: Jinja weeks/pipeline pages. CMS: Flask dashboard pipeline/calendar/content_detail (`MULTI_PLATFORM_STATUS`, `README`, sibling `dashboard/app.py`) |
| Marketing OS — Editorial Engine | Multi-agent draft generation (strategist/SEO/research/writer) | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: `GenerationCrew` + YAML + `/generate`. CMS: Editor/Researcher agents as SOUL personas + content drafts, not CrewAI generation API |
| Marketing OS — Editorial Engine | Editor refine → final | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: `EditorCrew` + `/edit`. CMS: Editor agent + human gateway |
| Marketing OS — Editorial Engine | QA gates / scorecards | Partial in Founder | Better in CMS (editorial QA ritual) | MERGE | MERGE | Yes | Founder: `QACrew`, validators, qa_reports. CMS: QA agent, scorecards, critical handoffs in `AGENTS.md` |
| Marketing OS — Editorial Engine | Brand-voice gated human handoffs | Partial in Founder | Better in CMS | CMS process → Founder approvals | MERGE | Yes | Founder: approvals API exists. CMS: explicit critical handoff list |
| Marketing OS — Publishing Engine | Hashnode / blog publish | Partial in Founder | Partial in CMS | Founder tools + CMS publish ops | MERGE | Yes | Founder: `hashnode_publish`, go-live. CMS: Hashnode status + publish-ready articles documented |
| Marketing OS — Publishing Engine | Multi-platform publish orchestrator (LinkedIn/Twitter/Instagram one-shot) | Partial in Founder | Better in CMS | CMS → Founder Publishing Engine | MIGRATE FROM CMS | Yes | Founder: `social_publisher` + `/marketing/publish` (with known marketing generate path defect). CMS: `publish-all`, platform-specific APIs documented |
| Marketing OS — Publishing Engine | Publish queue / schedule / preview | Partial in Founder | Better in CMS | CMS → Founder | MIGRATE FROM CMS | Yes | Founder: dry-run + schedule-ish integrations. CMS: preview/schedule/queue endpoints documented |
| Marketing OS — Publishing Engine | Google Sheets tracker sync | Already Exists in Founder | Duplicate | Founder | KEEP FOUNDER | No | Founder: sheet sync tools. CMS: Sheets v2 + n8n append workflows |
| Marketing OS — Campaign Engine | Campaign brief → content plan handoff | Missing | Better in CMS | CMS process | MIGRATE FROM CMS | Yes | CMS: CEO→CMO→CoS handoffs. Founder: no campaign brief engine |
| Marketing OS — Campaign Engine | WhatsApp / broadcast campaigns | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: WhatsApp broadcasts API. CMS: not documented |
| Marketing OS — SEO Engine | SEO plan generation in content pipeline | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: SEO agent in generation crew + `02_SEO_Plan.md`. CMS: SEO agent + seo-briefs content |
| Marketing OS — SEO Engine | SEO keyword tracking API | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: `/api/v1/seo`. CMS: no keyword DB API |
| Marketing OS — GEO Engine | Geographic expansion strategy | Partial in Founder | Missing | Founder (docs) | DEFER | No | Founder: `MARKETING_STRATEGY_AEO_GEO.md` strategy only. CMS: no GEO engine |
| Marketing OS — GEO Engine | Runtime GEO targeting in marketing generate | Partial in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: `geo` field on marketing/orchestration requests. No dedicated GEO Engine module |
| Marketing OS — AEO Engine | Author/expertise optimization strategy | Partial in Founder | Missing | Founder (docs) | DEFER | No | Founder: AEO sections in strategy doc. CMS: not framed as AEO engine |
| Marketing OS — Social Engine | LinkedIn / Instagram / Twitter packaging + publish | Partial in Founder | Better in CMS | MERGE | MERGE | Yes | Founder: social publisher + env tokens. CMS: platform packages + n8n workflows + dashboard publish APIs |
| Marketing OS — Email Engine | Newsletter / email content packages | Partial in Founder | Better in CMS (content packs) | MERGE | MERGE | Yes | Founder: email integration + marketing email modules. CMS: `content/email` packages documented |
| Marketing OS — Brand Engine | Brand voice guide + validation | Partial in Founder | Better in CMS | MERGE | MERGE | Yes | Founder: Obsidian brand voice + marketing brand enum. CMS: `brand/voice.md`, brand-voice QA gate |
| Customer Success OS | Account health / recommendations | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: CSM API + `customer_success`. CMS: none |
| Operations OS | Content pipeline run / validate / switch-week | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: pipeline router + orchestrator. CMS: n8n + dashboard stage updates |
| Operations OS | Heartbeat / recurring jobs | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: `scheduler.py`. CMS: CTO heartbeat described in `AGENTS.md` |
| Operations OS | SEDICI audit logging | Missing | Better in CMS | CMS concept | DEFER | Partial | CMS: SEDICI logging throughout docs. Founder: activity_log / observability different model |
| Knowledge OS | Knowledge base CRUD + ask/RAG | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: KB API + Chroma. CMS: Obsidian vault as second brain (`TOOLS.md`) |
| Knowledge OS | Obsidian vault sync / editorial knowledge | Partial in Founder | Duplicate | Founder | KEEP FOUNDER | No | Founder: `obsidian_vault` + sync script. CMS: Obsidian noted |
| AI Platform | CrewAI content crews | Already Exists in Founder | Missing (as CrewAI) | Founder | KEEP FOUNDER | No | Founder: crews under `src`. CMS: OpenClaw agent collective (different runtime) |
| AI Platform | OpenClaw multi-agent collective | Missing | Better in CMS | CMS | DEFER | Partial | CMS architecture is OpenClaw Gateway. Founder does not host OpenClaw |
| AI Platform | Copilot / RAG chat | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: copilot + rag_service |
| AI Platform | Agent registry / safeguards / GTM orchestration | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: agents + orchestration APIs. CMS: handoff protocols |
| Automation Platform | n8n inbound/outbound bridge | Already Exists in Founder | Better in CMS (workflow library) | MERGE | MERGE | Yes | Founder: n8n webhooks + bridge. CMS: 35+ workflow JSONs documented/corroborated |
| Automation Platform | Internal workflow engine | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder: `/api/v1/automation`. CMS: n8n-centric |
| Shared Platform | FastAPI auth (API key + JWT) | Already Exists in Founder | Partial in CMS | Founder | KEEP FOUNDER | No | Founder: dual auth. CMS dashboard: Flask + linkedin oauth helpers |
| Shared Platform | Postgres / Redis / Celery runtime | Already Exists in Founder | Missing | Founder | KEEP FOUNDER | No | Founder compose stack. CMS: Flask + n8n Docker historically |
| Shared Platform | Docker primary API image | Already Exists in Founder | Legacy (CMS infra down per recovery doc) | Founder | KEEP FOUNDER | No | Founder Dockerfile. CMS `README_RECOVERY.md`: Docker/n8n missing on last host |
| Transitional | Duplicate `/marketing/*` handlers + stale module path | Legacy | Not Applicable | Founder cleanup | REWRITE | Yes (Founder-internal) | Frozen baseline GAP: router uses `revenue_os.agents.marketing_crew` missing; `@app` uses `src.marketing_crew` |
| Transitional | `revenue_os.main` empty webhooks router export | Legacy | Not Applicable | Founder | RETIRE | No (later) | Baseline GAP-010 correction |
| Transitional | Duplicate `@app` HTML/API routes in `runner_api.py` | Legacy | Not Applicable | Founder | RETIRE | No (later) | Router inventory A.6 |
| Transitional | OpenClaw agent SOUL packs (CMS) | Not Applicable in Founder | Better in CMS (as content ops playbooks) | CMS reference | DEFER | Partial | Migrate as playbooks/prompts, not OpenClaw runtime, unless future decision |

---

## Summary counts (by Decision)

| Decision | Approx. rows |
|----------|-------------|
| KEEP FOUNDER | Majority of Sales/Revenue/CSM/AI Platform/Shared |
| MIGRATE FROM CMS | Publishing UX, multi-platform orchestrator, campaign brief process, pipeline portal patterns |
| MERGE | Social/Email/Brand/QA ritual/n8n workflow library/Content Studio UX |
| REWRITE | Founder marketing generate path consistency |
| RETIRE | Duplicate Founder route shims (post-migration) |
| DEFER | OpenClaw runtime, AEO/GEO engines as products, SEDICI |
