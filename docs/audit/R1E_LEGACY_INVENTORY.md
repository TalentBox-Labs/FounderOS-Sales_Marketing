# R1E — Legacy / Migration Inventory (SCOUT)

**Date:** 2026-08-12  
**Re-baselined from R0 “28” findings against post-R1D tree**

Legend: KEEP-AC = ACTIVE COMPATIBILITY · KEEP-GH = GOVERNANCE/HISTORICAL · KEEP-ME = MIGRATION EVIDENCE · KEEP-RR = ROLLBACK/RECOVERY · DF-FD = DEFER FOUNDER DECISION · DF-NV = DEFER NEEDS VERIFICATION · STALE-REF = STALE BUT REFERENCED · ARCH = ARCHIVE candidate (not moved)

| ID | Path / theme | Type | Purpose | Refs | Runtime | Test | Deploy | Gov | Rollback | Migr evid | Future | Classification | Action | Conf |
|----|--------------|------|---------|------|---------|------|--------|-----|----------|-----------|--------|----------------|--------|------|
| L01 | `/Users/krishna/Documents/workcrew-cms-os` | ext repo | CMS reference | docs | No | No | No | Yes | Yes | Yes | Archive later | KEEP-ME / DF-FD | KEEP local; archive timing Founder | HIGH |
| L02 | `/Users/krishna/Documents/CMS_OS_V1` | ext repo | Docs pack | docs | No | No | No | Yes | Yes | Yes | Archive later | KEEP-ME / DF-FD | KEEP | HIGH |
| L03 | Path name `Workcrew_CMS_OS` | naming | Absent alias | docs | No | No | No | Yes | No | Yes | — | KEEP-GH | Note only | HIGH |
| L04 | API/UI “WorkCrew CMS OS” | branding | Product title | `runner_api.py`, `ui.py`, templates | Yes | Yes | Yes | Yes | No | No | Rename | KEEP-AC / DF-FD | KEEP | HIGH |
| L05 | README / ROADMAP WorkCrew | docs | Product narrative | root md | No | No | Partial | Yes | No | No | Rename | DF-FD | KEEP | HIGH |
| L06 | `frontend` npm `workcrew-crm-frontend` | naming | CRM package | package.json | Optional | No | Docker | Yes | No | No | Rename | KEEP-AC / DF-FD | KEEP | HIGH |
| L07 | `render.yaml` / Docker `workcrew-crm*` | naming | Deploy IDs | render/Docker | Deploy | No | Yes | Yes | Yes | No | Rename | KEEP-AC / DF-FD | KEEP | HIGH |
| L08 | `WORKCREW_*` env prefix | config | CrewAI/Sheets | `.env.example`, crews | Yes | Yes | Yes | Yes | No | No | Rename sprint | KEEP-AC | KEEP | HIGH |
| L09 | `marketing_crew` blog `workcrew.ai/blog` | runtime URL | Default brand blog | `src/marketing_crew.py` | Yes | Partial | No | Yes | No | No | Domain FD | STALE-REF / DF-FD | DEFER update | HIGH |
| L10 | OpenAPI contact `workcrew.ai` | metadata | API docs identity | `runner_api.py` | Docs surface | Yes | No | Yes | No | No | Rename | STALE-REF / DF-FD | DEFER | HIGH |
| L11 | `site_origin` deprecated hosts | safety | Block deprecated hosts | `site_origin.py`, SEO tests | Yes (deny) | Yes | No | Yes | No | Yes | Keep deny | KEEP-AC | KEEP | HIGH |
| L12 | `input/**` FM canonicals `workcrew.ai` | content | Historical posts | input tree | Content | Yes | Publish | Yes | Yes | Yes | Content migr | KEEP-ME / DF-FD | KEEP | HIGH |
| L13 | `hashnode_publish.py` | tool | Blog publish CLI | tools, tests, go_live | Optional | Yes | Ops | Yes | No | Yes | FD retire | KEEP-AC / DF-FD | KEEP | HIGH |
| L14 | `social_publisher.HashnodePublisher` | integration | Marketing publish | revenue_os | Optional | Yes | No | Yes | No | Yes | Consolidate later | KEEP-AC / DF-FD | KEEP | HIGH |
| L15 | Marketing router Hashnode status | API | Integration flag | marketing.py | Yes | Yes | No | No | No | No | — | KEEP-AC | KEEP | HIGH |
| L16 | `sheet_sync` / Google Sheets tools | ops mirror | Not SoT | sheet tools, tests | Optional | Yes | Ops | Yes | No | Yes | Keep mirror | KEEP-AC | KEEP | HIGH |
| L17 | tracker.csv SoT vs Sheets | policy | Founder SoT | migration docs | Yes | Yes | No | Yes | Yes | Yes | — | KEEP-ME | KEEP | HIGH |
| L18 | Publishing PLACEHOLDER / NOT_IMPLEMENTED | contract | Frozen channel stubs | publishing_engine | Yes | Yes | No | Yes | No | No | Social/Email | KEEP-AC | KEEP | HIGH |
| L19 | StubWebsiteProvider | compat | Dev/stub provider | website_engine | Dev | Yes | No | Yes | No | No | Retire later | KEEP-AC | KEEP | HIGH |
| L20 | `src/*.py.old` | backup | Legacy crews | — | No | No | No | Hist | git | Yes | — | REMOVE done R1A | already gone | HIGH |
| L21 | Flask in-repo | absence | CMS was Flask | — | No | No | No | Yes | No | Yes | — | KEEP-GH (non-finding) | N/A | HIGH |
| L22 | Dual `@app` marketing/HTML handlers | shadow | Duplicate FastAPI | runner_api.py | Shadowed | Partial | No | Yes | No | No | R1D defer | STALE-REF | DEFER | HIGH |
| L23 | `revenue_os.agents.marketing_crew` string | hist fix | D0 repair comment | marketing.py comment | No | No | No | Yes | No | Yes | — | KEEP-GH | KEEP comment | HIGH |
| L24 | Obsidian vault WorkCrew branding | notes | Operator vault | obsidian_vault | Optional | No | No | Hist | No | No | — | KEEP-GH | KEEP | MED |
| L25 | `docs/migration/**` pack | evidence | CMS→Founder | 50 md | No | No | No | Yes | Yes | Yes | — | KEEP-ME | KEEP | HIGH |
| L26 | `docs/architecture-audit/**` | evidence | Baseline freeze | audit docs | No | No | No | Yes | Yes | Yes | — | KEEP-GH | KEEP | HIGH |
| L27 | Root Phase narrative docs (14) | stale docs | Pre-v2.2 product | docs/*.md root | No | No | No | Soft | No | Partial | Index | KEEP-GH / ARCH cand | KEEP; index | MED |
| L28 | n8n bridge vs CMS n8n library | platform | Automation | n8n routers | Yes | Yes | Yes | Yes | No | Yes | — | KEEP-AC | KEEP | HIGH |

**Reviewed: 28/28**

### Tallies (primary class)

| Class | N |
|-------|--:|
| Active compatibility (KEEP) | 12 |
| Governance/historical retained | 8 |
| Migration evidence retained | 5 |
| Archive candidates (not moved) | 3 (L01,L02,L27) |
| Deferred Founder decision | 9 (overlapping themes) |
| Removed this sprint | 0 |
| Already removed (R1A L20) | 1 theme |

**workcrew.ai active runtime emitters (non-deny-list):** L09, L10, L13 strings, go_live helpers → count **4** primary surfaces (plus content FM L12 as content SoT, not code).

**Hashnode/old provider runtime remnants:** L13–L15 (+ social Hashnode) → **3**

**CMS/Sheets runtime remnants:** L16 (+ related tools) → **1** family active (mirror, not SoT)
