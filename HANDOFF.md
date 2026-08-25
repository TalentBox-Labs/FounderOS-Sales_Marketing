# Handoff — Recent Session Work

This document summarizes the work done in the most recent working session, for whoever picks this up next. It's a pointer/summary, not a replacement for the detailed docs it links to.

## 1. CI recovery + test-suite health

The full backend test suite was brought from a non-functional CI pipeline (billing-locked, then missing dependencies, then missing `SECRET_KEY`, then no Postgres service) to fully green: **1453 passed, 4 pre-existing skips (documented in-line), 0 failed**. Each CI blocker and each category of test drift (tenant-membership fixtures, an inverted 403/503 authorization-check ordering bug, template/UI staleness, crew/utilities drift) was root-caused and fixed individually — see the closed/merged PR history (`#8`–`#22`) on [`founderos-backend`](https://github.com/TalentBox-Labs/founderos-backend) for the specifics of each.

## 2. Repository separation — backend/frontend split

This used to be a single monorepo (`TalentBox-Labs/FounderOS-Sales_Marketing`, now renamed `founderos-backend`) with the React frontend nested at `frontend/`. It's now two repos:

- **[`founderos-backend`](https://github.com/TalentBox-Labs/founderos-backend)** — this repo. FastAPI backend, `revenue_os/`, `runner_api_routers/`, the legacy `src/` CrewAI content pipeline, Jinja-templated founder/operator pages, Celery workers.
- **[`founderos-frontend`](https://github.com/TalentBox-Labs/founderos-frontend)** — the React/Vite CRM SPA, with its own preserved git history from when it lived at `frontend/` here.

`frontend/` here is now a **git submodule** pointing at the frontend repo. Run `git submodule update --init --recursive` after cloning. The production Docker build is unchanged in logic — `Dockerfile` still builds `frontend/` as stage 1 — it just now needs the submodule checked out first.

**Read first:** [`docs/CURRENT_ARCHITECTURE.md`](docs/CURRENT_ARCHITECTURE.md) (the pre-separation baseline — what existed and how it fit together), [`docs/REPOSITORY_SEPARATION_REPORT.md`](docs/REPOSITORY_SEPARATION_REPORT.md) (exactly what moved and what didn't), [`docs/POST_SEPARATION_TECH_DEBT.md`](docs/POST_SEPARATION_TECH_DEBT.md) (issues noticed but deliberately not fixed — out of scope for a repo-organization task).

Verified end-to-end: full local `docker build .` succeeds, container boots, `/health` returns 200, 31 agents register, heartbeat starts.

## 3. Marketing Agent crew (16 agents + orchestrator)

Integrated a previously-unpushed local feature: 16 of 20 planned marketing agents (Market Research, Community Engagement, Brand Monitoring, Partnership/Influencer, Customer Persona, SEO Strategy, GEO, Product Marketing, Video Strategy, Creative Design, Email/WhatsApp Marketing, Campaign Manager, Marketing Automation, Analytics & Attribution, CRO) plus a Marketing Orchestrator that chains them, registered as a daily heartbeat job. Endpoints at `/api/v1/marketing-agents/*` (`runner_api_routers/marketing_agents.py`), all tenant-scoped via `require_tenant_context()`.

**4 agents are deliberately stubbed**, not built: Content Strategy, Content Writer, LinkedIn Content, Social Media. These overlap `src/marketing_crew.py`'s existing `content_strategist`/`blog_writer`/`social_copywriter` agents — shipping a second, competing content generator wasn't a call to make unilaterally. They return `{"ok": false, "reason": "Superseded by src/marketing_crew.py..."}` and the orchestrator degrades gracefully around them.

**Open decision, needs a human call:** whether to replace `src/marketing_crew.py` with these 4 agents, merge the two, or keep both. See `docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md` for the existing product context on this area.

## 4. FounderOS rebrand

The product was previously called "WorkCrew CRM" / "WorkCrew" in most user-facing text; it's called **FounderOS**. Renamed across both repos: doc titles, marketing copy, the frontend nav/login/tab title, `package.json` name, the Render service name (`render.yaml`, service now `founderos-backend`).

**Deliberately left unrenamed** (confirmed functional, not branding — renaming these would be a real behavior change, not a rebrand):
- `WORKCREW_*` environment variables (`WORKCREW_CREWAI_MODEL`, `WORKCREW_OLLAMA_BASE_URL`, `WORKCREW_RUNTIME_CONFIG`, `WORKCREW_GOOGLE_SHEET_ID`, `WORKCREW_PROMOTION_APPROVER`, `WORKCREW_PROMOTE_FORCE`)
- The literal `"WorkCrew CMS OS"` / `"WorkCrew CRM API"` strings — the actual `/health` response and FastAPI OpenAPI title, asserted by 3 test files
- `api.workcrew.ai` / `workcrew.ai/*` / `*@workcrew.ai` — unknown whether this is a real owned domain; nobody should guess a replacement
- `"workcrew"` as a `BRANDS` enum value in `src/marketing_crew.py` — a real, separate client brand this platform generates content for (alongside `"hirestack"` and `"founder"`), **not** the platform's own former name
- `revenue_os/integrations/slack.py`'s `"WorkCrew"` / `"WorkCrew Alerts"` / `"WorkCrew Metrics"` bot-username defaults — real runtime behavior sent to Slack, not yet reviewed for renaming
- `render.yaml`'s database name (`workcrew-crm-db`), `output/sales/prospecting_presets.json`'s `"brand": "workcrew"` data key, and all archival docs (`docs/audit/`, `docs/migration/`, `docs/architecture-audit/`, `input/`, `obsidian_vault/`) — historical records, not live branding

## 5. Pending items — need a human decision or action

- **Render dashboard rename**: `render.yaml`'s service name is updated to `founderos-backend`, but the *live* Render service (if deployed) needs renaming in the Render dashboard directly — a Blueprint config change alone won't rename an already-deployed service, it may create a duplicate on next sync.
- **Marketing agent dedup decision** (see §3) — Content Strategy/Writer/LinkedIn/Social agents are stubbed pending a product call.
- **Slack bot branding** (see §4) — not yet reviewed for rename.
- [PR #20](https://github.com/TalentBox-Labs/founderos-backend/pull/20) on `founderos-backend`, "Founder OS: checkpoint through Command Center V2 I1 projection" — a colleague's (`sahilkhiwani`) in-progress checkpoint, explicitly marked "NO MERGE AUTHORIZED IN THIS GATE." Not part of this session's work; leave alone unless told otherwise.

## 6. Verification state

Both repos' `Main` branches are green on CI as of this handoff. Full backend suite: 1453 passed / 4 skipped / 0 failed. Frontend: builds clean, 0 npm vulnerabilities, manually click-tested (login, dashboard, contact create round-trip, deals pipeline, marketing agent UI) with zero console errors.
