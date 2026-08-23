# 03 — Migration Slices

Independent, deployable slices preserving Founder Architecture Baseline v1.0.  
Preferred order adjusted only where evidence requires (Slice 0 added for Founder-internal blocker).

---

## Slice 0 — Founder Marketing Path Integrity (prerequisite)

| Field | Content |
|-------|---------|
| **Goal** | Make canonical `/marketing/generate` invoke an existing module path so Publishing/Content slices are not blocked by a known stale import |
| **Capabilities** | Marketing generate entry consistency |
| **Dependencies** | None external; Founder-only |
| **Estimated risk** | Low (path/wiring alignment; behavior already present via `src.marketing_crew` elsewhere) |
| **Blocking issues** | Included router references missing `revenue_os.agents.marketing_crew` (frozen baseline) |
| **Rollback strategy** | Revert router module string; keep prior duplicate `@app` handler |
| **Validation strategy** | API test: generate returns non-module-not-found; integration suite remains green |

**Evidence requiring this slice before CMS publish migration:** Sprint A.6 marketing classification.

---

## Slice 1 — Content Studio

| Field | Content |
|-------|---------|
| **Goal** | Unify content workspace UX (pipeline board / calendar / content detail patterns) onto Founder while keeping Founder tracker + `input/` as source of truth |
| **Capabilities** | Content inventory views; stage visibility; week/content detail actions wired to Founder APIs |
| **Dependencies** | Founder pipeline + weeks APIs stable |
| **Estimated risk** | Medium (UI surface area; dual UI period) |
| **Blocking issues** | CMS dashboard is Flask in documented locus; Founder is FastAPI/Jinja/React — adapter/UI port required |
| **Rollback strategy** | Keep Jinja weeks/pipeline; feature-flag new Studio UI |
| **Validation strategy** | Manual UX checklist + router integration tests for week/pipeline endpoints unchanged |

---

## Slice 2 — Editorial Engine

| Field | Content |
|-------|---------|
| **Goal** | Keep Founder CrewAI generation/edit; import CMS QA handoff rituals into approvals/QA contract |
| **Capabilities** | Generation, edit, QA gates, human gateway mapping |
| **Dependencies** | Slice 1 helpful but not hard-required |
| **Estimated risk** | Medium (contract changes can fail validators) |
| **Blocking issues** | CMS QA scorecard format ≠ Founder `qa_report` contract |
| **Rollback strategy** | Feature-flag new handoff rules; retain existing QACrew contract |
| **Validation strategy** | Existing crew/validator tests + new approval-path tests |

---

## Slice 3 — Publishing Engine

| Field | Content |
|-------|---------|
| **Goal** | Port CMS preview/schedule/publish-all/platform publish APIs into Founder Publishing Engine |
| **Capabilities** | Multi-platform publish orchestration; preview; schedule; Hashnode/go-live retained |
| **Dependencies** | Slice 0; Social credentials; n8n bridge optional |
| **Estimated risk** | High (external networks, credentials, duplicate publish paths) |
| **Blocking issues** | CMS recovery doc: historical infra fragility; Founder already has overlapping social_publisher |
| **Rollback strategy** | Disable new publish routes; fall back to `/marketing/publish` dry-run/publish |
| **Validation strategy** | Dry-run only in CI; staged publish with confirmed flags; no live posts in automated tests |

---

## Slice 4 — Campaign Engine

| Field | Content |
|-------|---------|
| **Goal** | Introduce campaign brief → plan handoffs from CMS process; retain Founder WhatsApp campaigns |
| **Capabilities** | Campaign brief objects; handoff states; link to Content Studio |
| **Dependencies** | Slice 1–2 for content linkage |
| **Estimated risk** | Medium |
| **Blocking issues** | No Founder campaign data model today |
| **Rollback strategy** | Keep process in Knowledge docs only if API incomplete |
| **Validation strategy** | API contract tests for brief CRUD + handoff transitions |

---

## Slice 5 — SEO Engine

| Field | Content |
|-------|---------|
| **Goal** | Strengthen SEO Engine using Founder generation SEO + keyword API; import CMS seo-brief templates |
| **Capabilities** | SEO plans, keyword tracking, brief templates |
| **Dependencies** | Editorial Engine |
| **Estimated risk** | Low |
| **Blocking issues** | None material |
| **Rollback strategy** | Templates-only revert |
| **Validation strategy** | SEO API tests + generation fixture checks |

---

## Slice 6 — Social Engine

| Field | Content |
|-------|---------|
| **Goal** | Consolidate platform packaging + publish clients under Social Engine; merge CMS n8n social workflows |
| **Capabilities** | LinkedIn/Twitter/Instagram packages; buffer workflows |
| **Dependencies** | Slice 3 Publishing Engine; Automation Platform n8n |
| **Estimated risk** | High (OAuth, platform policy) |
| **Blocking issues** | CMS docs require Twitter/Instagram credentials; LinkedIn OAuth flows in CMS dashboard |
| **Rollback strategy** | Per-platform kill switches; keep dry-run |
| **Validation strategy** | Credential-gated manual tests; mock n8n in CI |

---

## Slice 7 — Brand Engine

| Field | Content |
|-------|---------|
| **Goal** | Consolidate brand voice assets and editorial voice gates |
| **Capabilities** | Voice guide, brand validation hooks in Editorial |
| **Dependencies** | Slice 2 |
| **Estimated risk** | Low |
| **Blocking issues** | Dual voice documents (Obsidian vs CMS brand/) |
| **Rollback strategy** | Point Brand Engine back to prior Obsidian guide |
| **Validation strategy** | Unit tests for voice rule checks; sample article lint |

---

## Slice 8 — Revenue integration

| Field | Content |
|-------|---------|
| **Goal** | Connect Marketing/Publishing events to Revenue OS (attribution, content→CRM signals) without migrating CMS sales (none) |
| **Capabilities** | Event hooks from publish → analytics/CRM; hermes/marketing spend linkage |
| **Dependencies** | Slices 3–6; Founder automation EventBus |
| **Estimated risk** | Medium |
| **Blocking issues** | Attribution models partial in Founder analytics-depth |
| **Rollback strategy** | Disable event subscriptions |
| **Validation strategy** | Event emission tests; no CMS dependency |

---

## Deferred (not slices yet)

| Item | Reason (evidence) |
|------|-------------------|
| OpenClaw Gateway as AI Platform | CMS-specific runtime; Founder AI Platform is CrewAI-based |
| AEO Engine / GEO Engine product modules | Strategy docs only in Founder; no CMS engines |
| SEDICI logging system | CMS-specific; Founder has alternate observability |

---

## Recommended first implementation slice

**Slice 0** (Founder path integrity), then **Slice 1 Content Studio**.
