# 01 — Module Ownership

Sprint P0 — Execution governance (documentation only)  
Date: 2026-08-09  
Evidence: architecture-audit module map, migration baselines, Editorial/Content Studio freezes, Toolchain Baseline v1.0

**No code changes.**

---

| Module Name | Purpose | Current Status | Owner | Dependencies | Independent? | Risk | Impl. order |
|-------------|---------|----------------|-------|--------------|--------------|------|-------------|
| **Shared Platform** | FastAPI app shell, utils, DB session, Compose, Alembic, metrics helpers | ACTIVE / FROZEN architecture | Shared Platform | Postgres/SQLite, Redis optional | Partial (touched by all HTTP work) | MEDIUM | 1 (stabilize, don’t redesign) |
| **Runtime** | Docker/Compose topology, uvicorn, Celery worker/beat, health | FROZEN runtime baseline | Shared Platform / Infrastructure | Docker, Redis, DB | Yes for ops-only | MEDIUM | 1 |
| **Authentication** | Runner API key + Revenue JWT | ACTIVE dual model | Shared Platform | SECRET_KEY, bcrypt/jose | Soft — avoid parallel auth redesign | HIGH if changed | 1 (freeze; no redesign) |
| **AI Runtime** | CrewAI BaseCrew, LLM env, agents YAML | ACTIVE; pin conflict GAP-007 | AI Platform | CrewAI, Ollama/OpenAI/Gemini | Soft with Editorial/Marketing crews | HIGH | 2 (hygiene before new crews) |
| **Content Studio** | Read API + list/detail/kanban UI | FROZEN baselines (read + kanban) | Marketing OS / Content Studio | tracker.csv, input/, content_studio router | Yes for read-only extensions | LOW | 2 (additive read only) |
| **Editorial Engine** | Validators, editor/QA crews, promote, readiness API | Readiness FROZEN; Approval ADR PROPOSED | Marketing OS / Editorial Engine | AI Runtime, tracker, qa_reports, promote_staged | Soft with Content Studio display | HIGH (mutation) | 3 (after FDR-001/002/003) |
| **Marketing OS** | Marketing crew, pipeline UI, week ops | PARTIAL; D0 path fixed | Marketing OS | AI Runtime, pipeline routers | Soft with Editorial | MEDIUM | 3–4 |
| **Publishing** | go_live_helpers, hashnode_publish, checklist human gate | PARTIAL; separate from Editorial Approval | Publishing Engine | Editorial artifacts, FM | Soft after Editorial promote | HIGH | 4 (after FDR-003) |
| **Campaigns** | Campaign orchestration | LIMITED / NOT VERIFIED as mature engine | Marketing OS | Publishing, Automation | Soft | HIGH | 5+ |
| **Sales OS** | Prospecting, outreach, SDR crews | ACTIVE partial | Sales / Revenue OS | CRM, AI Runtime, approvals (Revenue) | Soft with CRM | MEDIUM | Phase 3 |
| **CRM** | Contacts/deals React SPA + CRM routers | ACTIVE | Revenue OS / CRM | Auth, DB | Soft with Shared Platform mount | MEDIUM | Phase 3 |
| **Revenue OS** | Models, services, automation, forecasting, CSM | ACTIVE large surface | Revenue OS | DB, Redis, Celery | Soft — large blast radius | HIGH | Phase 4 (after Sales core) |
| **Analytics** | Analytics routers/services, reporting | PARTIAL | Revenue OS / Analytics | DB, CRM data | Soft | MEDIUM | Phase 4–6 |
| **Integrations** | n8n, webhooks, LinkedIn/WhatsApp helpers | PARTIAL | Automation / Integrations | External creds | Soft | MEDIUM | Phase 5 |
| **Automation** | Celery tasks, heartbeat, automation events, n8n bridge | ACTIVE partial | Automation Platform | Redis, Celery | Soft with Revenue events | HIGH | Phase 5 |
| **Knowledge Base** | KB routers, Chroma/RAG services | PARTIAL (dep present, wiring uneven) | Knowledge OS | ChromaDB, AI Runtime | Soft | MEDIUM | Phase 6 |

### Ownership notes

- **Do not create new product domains** beyond approved architecture.
- Content Studio and Editorial Engine sit under **Marketing OS** but keep separate owners for sprint scoping.
- Revenue OS `/api/v1/approvals` is **not** Editorial Approval (E6C ADR).
