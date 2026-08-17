# R0 — Repository Structure (ATLAS)

**Sprint:** R0 — Complete Repository Integrity Audit  
**Agent:** ATLAS  
**Date:** 2026-08-11  
**Mode:** AUDIT ONLY — no moves/renames/deletes  
**Architecture:** v2.2 FROZEN

---

## CURRENT TREE (top-level)

| Path | Type | Purpose | Owning OS / Engine | Runtime | Test | Governance | Deploy | v2.2 fit | Ownership |
|------|------|---------|--------------------|---------|------|------------|--------|----------|-----------|
| `src/` | code | Crews, tools, Marketing OS engines | Marketing OS + Platform tools | YES | YES | — | YES | ALIGNED | CLEAR |
| `runner_api.py` | code | Primary FastAPI app | Shared Platform | YES | YES | — | YES | ALIGNED | CLEAR |
| `runner_api_routers/` | code | Domain routers + UI | Platform + engines | YES | YES | — | YES | ALIGNED | CLEAR |
| `revenue_os/` | code | CRM / Revenue domain + secondary app | Revenue OS | PARTIAL | YES | — | PARTIAL | ALIGNED (secondary) | AMBIGUOUS vs runner_api |
| `templates/` | UI | Jinja Founder shell | Marketing OS UI | YES | YES | — | YES | ALIGNED | CLEAR |
| `frontend/` | UI | React CRM SPA (dist absent) | Revenue OS UI | NO (unmounted) | NO | — | BUILD | ALIGNED if built | AMBIGUOUS |
| `tests/` | test | Pytest suite | Shared | — | YES | — | — | ALIGNED | CLEAR |
| `docs/` | docs | Architecture, freeze, sprint evidence | Governance | — | — | YES | — | ALIGNED | CLEAR |
| `scripts/` | ops | Fixtures, demo, vault sync | Platform ops | CLI | YES | — | DEMO | ALIGNED | CLEAR |
| `migrations/` | DB | Alembic | Revenue OS | DEPLOY | — | — | YES | ALIGNED | CLEAR |
| `input/` | content | Week content SoT files | Content Studio / pipeline | YES | YES | — | — | ALIGNED | CLEAR |
| `data/` | runtime | week_runtime | Pipeline | YES | YES | — | LOCAL | ALIGNED | CLEAR |
| `output/` | generated | QA, website, deploy packages | Engines | YES | PARTIAL | EVIDENCE | LOCAL | ALIGNED | LOCAL ONLY preferred |
| `obsidian_vault/` | notes | Operator vault | Ops / historical | OPTIONAL | — | HISTORICAL | — | OPTIONAL | AMBIGUOUS |
| `migrations/` | DB | Schema revisions | Revenue OS | YES | — | — | YES | ALIGNED | CLEAR |
| `.github/` | CI | test.yml | Platform | CI | YES | — | YES | ALIGNED | CLEAR |
| `.crewai_home/` / `.crewai_storage/` | generated | CrewAI local creds/cache | Local tooling | LOCAL | — | — | NO | N/A | UNOWNED (local) |
| `.wrangler/` | generated | Cloudflare CLI cache | Deploy ops | LOCAL | — | — | LOCAL | N/A | UNOWNED (local) |
| `.pytest_cache/` / `__pycache__/` / `.venv/` | generated | Tooling | Local | LOCAL | — | — | NO | N/A | LOCAL ONLY |
| `requirements*.txt` | deps | Python deps | Platform | YES | YES | — | YES | ALIGNED | CLEAR |
| `Dockerfile` / `docker-compose*.yml` / `render.yaml` | deploy | Containers / Render | Platform | YES | — | — | YES | ALIGNED | CLEAR |
| `tracker.csv` | data | Content tracker SoT | Content Studio | YES | YES | — | — | ALIGNED | CLEAR |
| Root `*.md` | docs | README, ROADMAP, COVERAGE, DEMO, DEPLOYMENT | Mixed | — | — | PARTIAL | YES | MIXED / STALE | AMBIGUOUS |

**Top-level directories counted:** 21 (including `.git`, caches, venv).

---

## OWNERSHIP MAP (engines → paths)

| Engine / OS | Paths |
|-------------|-------|
| Content Studio | `runner_api_routers/content_studio.py`, `templates/content_studio*`, `tracker.csv`, `input/` |
| Editorial | `src/tools/editorial_approval.py`, `runner_api_routers/editorial.py`, `templates/editorial*` |
| Publishing | `src/tools/publishing_engine.py`, `runner_api_routers/publishing.py`, `templates/publishing*` |
| Website Engine | `src/tools/website_engine/` |
| Deployment Adapter | `src/tools/website_deployment/`, `output/website-deploy/` (runtime) |
| SEO Readiness / Technical | `src/tools/seo_engine/`, `runner_api_routers/seo.py`, `templates/seo*` |
| Pipeline / Crews | `src/*_crew.py`, `src/tools/pipeline_*`, `runner_api_routers/pipeline.py` |
| Revenue OS | `revenue_os/**`, partial routers under `runner_api_routers/` |
| Governance | `docs/**` |

---

## ARCHITECTURE ALIGNMENT

| Check | Result |
|-------|--------|
| Destination Architecture v2.2 | PASS — docs present; engines map to Marketing OS |
| Dual FastAPI apps (`runner_api` vs `revenue_os.main`) | BOUNDARY RISK — both exist; Docker primary = `runner_api` |
| Publishing owns orchestration; Website owns render | ALIGNED in docs; **wire gap** (website adapter PLACEHOLDER) |
| Social Engine | NOT IMPLEMENTED (expected post-S0) |
| Flask CMS in-repo | ABSENT (correct) |

**Architecture Integrity (structure):** PASS with known dual-app and PLACEHOLDER gaps (not architecture version failures).

---

## UNOWNED / AMBIGUOUS FOLDERS

| Path | Issue |
|------|-------|
| `obsidian_vault/` | Not in Platform Agent Registry ownership |
| `.crewai_*`, `.wrangler/` | Local generated; not in `.gitignore` fully |
| `frontend/` without dist | Orphaned relative to live shell |
| Root Phase narrative `docs/*.md` (14) | Compete with Architecture v2.2 |
| `revenue_os/pipeline/` | Empty package |

---

## BOUNDARY VIOLATIONS / RISKS

1. Publishing website channel does not invoke Website Engine (PLACEHOLDER).  
2. `/marketing/publish` + RevenueOS `social_publisher` adjacent to Publishing Engine.  
3. React CRM vs Jinja shell dual UI.  
4. Generated deploy packages under `output/` mixed with source tree.  
5. CMS branding still on live UI/API titles.

**No structural refactor proposed in R0** — see `R0_PROPOSED_REPOSITORY_STRUCTURE.md` for minimal cleanup only.
