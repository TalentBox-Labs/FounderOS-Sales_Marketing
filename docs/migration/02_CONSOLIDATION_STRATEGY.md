# 02 — Consolidation Strategy

**Canonical destination:** Founder OS Architecture Baseline v1.0 (frozen)  
**Capability source:** CMS_OS_V1 (documentation pack; implementation locus documented as `workcrew-cms-os`)  
**Rule:** Repository A remains the product. Repository B supplies capabilities only.

---

## Evidence preamble

- Founder capabilities: executable in `TB-FounderOS-Sales_Marketing` (Sprint A baseline).
- CMS capabilities: documented in `CMS_OS_V1`; where docs name `workcrew-cms-os`, sibling tree was used only to corroborate existence of dashboard/n8n/agents/content artifacts.
- CMS_OS_V1 itself has **no** Python runtime modules.

---

## Executive OS

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder Paperclip/executive APIs (`/api/v1/paperclip`, `revenue_os/executive`) |
| **Migration approach** | Keep Founder. Optionally later absorb CMS CEO strategy *playbooks* as Knowledge content — not OpenClaw runtime |
| **Expected destination** | `Executive OS` under Founder |
| **Temporary compatibility** | None required for CMS |
| **Final owner** | Executive OS (Founder) |

---

## Sales OS

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder CRM, prospecting, outreach, sales agents |
| **Migration approach** | KEEP FOUNDER — CMS has no sales CRM capability evidence |
| **Expected destination** | `Sales OS` |
| **Temporary compatibility** | N/A |
| **Final owner** | Sales OS (Founder) |

---

## Revenue OS

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder `revenue_os` package + hermes/forecasting/automation |
| **Migration approach** | KEEP FOUNDER |
| **Expected destination** | `Revenue OS` |
| **Temporary compatibility** | N/A |
| **Final owner** | Revenue OS (Founder) |

---

## Marketing OS — Content Studio

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder week bundles, tracker, Jinja weeks/pipeline UI, React CRM adjacent pages |
| **Migration approach** | MERGE — retain Founder content filesystem + pipeline APIs; migrate CMS pipeline-board / calendar / content-detail UX patterns and content inventory practices |
| **Expected destination** | `Marketing OS / Content Studio` |
| **Temporary compatibility** | Dual UI (Jinja + any imported dashboard patterns) until Content Studio slice completes |
| **Final owner** | Marketing OS — Content Studio |

---

## Marketing OS — Editorial Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder GenerationCrew, EditorCrew, QACrew, validators |
| **Migration approach** | KEEP FOUNDER for generation/edit runtime; MERGE CMS QA handoff rituals and scorecard expectations into Founder approvals/QA contract |
| **Expected destination** | `Editorial Engine` |
| **Temporary compatibility** | Existing CrewAI YAML/agents remain |
| **Final owner** | Editorial Engine |

---

## Marketing OS — Publishing Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder hashnode tools, go-live, social_publisher, marketing publish/dry-run |
| **Migration approach** | MIGRATE FROM CMS multi-platform orchestrator (preview/schedule/publish-all/platform APIs) into Founder Publishing Engine; keep Founder Hashnode/go-live |
| **Expected destination** | `Publishing Engine` |
| **Temporary compatibility** | Keep `/marketing/publish` + social_publisher while CMS publish APIs are ported; fix Founder marketing generate path as Founder-internal REWRITE (not CMS migrate) |
| **Final owner** | Publishing Engine |

---

## Marketing OS — Campaign Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder WhatsApp broadcasts; no CEO→CMO campaign brief engine |
| **Migration approach** | MIGRATE FROM CMS campaign brief / plan handoff process into Campaign Engine; KEEP Founder WhatsApp campaigns |
| **Expected destination** | `Campaign Engine` |
| **Temporary compatibility** | Process docs may land in Knowledge OS until engine APIs exist |
| **Final owner** | Campaign Engine |

---

## Marketing OS — SEO Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder generation SEO agent + SEO keyword API + week SEO plans |
| **Migration approach** | KEEP FOUNDER; optionally MERGE CMS seo-brief templates |
| **Expected destination** | `SEO Engine` |
| **Temporary compatibility** | None |
| **Final owner** | SEO Engine |

---

## Marketing OS — GEO Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Strategy document + `geo` request fields; no dedicated engine module |
| **Migration approach** | DEFER productization; KEEP FOUNDER strategy + request fields |
| **Expected destination** | `GEO Engine` (future) |
| **Temporary compatibility** | Continue using `geo` parameters |
| **Final owner** | GEO Engine (deferred) |

---

## Marketing OS — AEO Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Strategy document only |
| **Migration approach** | DEFER engine build; content practices may use Social/Brand engines |
| **Expected destination** | `AEO Engine` (future) |
| **Temporary compatibility** | Strategy doc remains guidance |
| **Final owner** | AEO Engine (deferred) |

---

## Marketing OS — Social Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder social_publisher + env-based LinkedIn/Instagram/YouTube |
| **Migration approach** | MERGE CMS platform packaging + n8n publish workflows into Founder Social Engine APIs |
| **Expected destination** | `Social Engine` |
| **Temporary compatibility** | n8n workflows callable from Founder bridge during transition |
| **Final owner** | Social Engine |

---

## Marketing OS — Email Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder email integration + marketing email modules |
| **Migration approach** | MERGE CMS newsletter package formats |
| **Expected destination** | `Email Engine` |
| **Temporary compatibility** | None critical |
| **Final owner** | Email Engine |

---

## Marketing OS — Brand Engine

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Obsidian brand voice + marketing brand parameter |
| **Migration approach** | MERGE CMS `brand/voice` + voice QA gate into Brand Engine checks used by Editorial |
| **Expected destination** | `Brand Engine` |
| **Temporary compatibility** | Dual voice docs until consolidated |
| **Final owner** | Brand Engine |

---

## Customer Success OS

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder CSM APIs |
| **Migration approach** | KEEP FOUNDER |
| **Expected destination** | `Customer Success OS` |
| **Temporary compatibility** | N/A |
| **Final owner** | Customer Success OS |

---

## Operations OS

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder pipeline API, heartbeat, metrics, Docker |
| **Migration approach** | KEEP FOUNDER for runtime ops; MERGE useful CMS stage-batch ops concepts into Content Studio/Publishing |
| **Expected destination** | `Operations OS` |
| **Temporary compatibility** | CMS Flask dashboard may run side-by-side only if explicitly stood up — not required for Founder canonical runtime |
| **Final owner** | Operations OS |

---

## Knowledge OS

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder KB + RAG + Obsidian vault |
| **Migration approach** | KEEP FOUNDER; ingest CMS editorial docs/playbooks as knowledge articles where useful |
| **Expected destination** | `Knowledge OS` |
| **Temporary compatibility** | CMS markdown guides may remain external reference |
| **Final owner** | Knowledge OS |

---

## AI Platform

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder CrewAI + agents + copilot |
| **Migration approach** | KEEP FOUNDER runtime. DEFER OpenClaw Gateway adoption. Optionally port CMS agent SOUL constraints as prompt/policy assets |
| **Expected destination** | `AI Platform` |
| **Temporary compatibility** | Do not run OpenClaw as second production AI fabric without a future approved decision |
| **Final owner** | AI Platform |

---

## Automation Platform

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder automation engine + n8n bridge + Celery/heartbeat |
| **Migration approach** | MERGE CMS n8n workflow library into Founder-managed automation assets; KEEP Founder engine |
| **Expected destination** | `Automation Platform` |
| **Temporary compatibility** | Import CMS workflow JSONs behind Founder n8n bridge |
| **Final owner** | Automation Platform |

---

## Shared Platform

| Item | Detail |
|------|--------|
| **Current canonical implementation** | Founder FastAPI, auth, DB, Redis, middleware, config |
| **Migration approach** | KEEP FOUNDER as sole shared platform |
| **Expected destination** | `Shared Platform` |
| **Temporary compatibility** | Adapters only for imported CMS publish clients |
| **Final owner** | Shared Platform |
