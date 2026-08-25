# Post-Separation Tech Debt

Issues noticed during the frontend/backend repository separation (see `docs/REPOSITORY_SEPARATION_REPORT.md`) that were **not** fixed as part of that work, per its explicit scope (organization only, no product/code changes). Listed here for a separate task.

1. **Two competing DB migration mechanisms.** `alembic.ini` + `migrations/` exist, but schema evolution actually happens via `Base.metadata.create_all()` (new tables) plus a hand-rolled `_migrate_missing_columns()` raw-SQL helper in `runner_api.py` (new columns). Worth deciding on one path.

2. **Two parallel auth systems on the same endpoints.** A legacy shared-bearer-token check (`_verify_api_key`, `RUNNER_API_KEY`) and a newer session/tenant-cookie system (`require_tenant_context`) coexist, sometimes both gating the same handler. Worth a real consolidation decision.

3. **`src/` (CrewAI content pipeline) vs. `revenue_os/marketing/` + the newly-integrated Marketing Agent crew (`runner_api_routers/marketing_agents.py`) have overlapping content-generation capability** — `src/marketing_crew.py`'s 5 agents (content strategist, blog writer, social copywriter, image director, SEO optimiser) duplicate 4 of the Marketing Agent crew's agents (Content Strategy, Content Writer, LinkedIn Content, Social Media), which are currently stubbed out specifically to avoid shipping two competing generators. See `docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md` for the existing product context; this needs an explicit product decision (replace/merge/keep both), not something to resolve as part of a repo-organization task.

4. **No frontend test suite or CI job.** `frontend/package.json` has no test runner configured, and `.github/workflows/test.yml` only builds/tests the backend — `npm run build` is only ever invoked inside the Docker build stage.

5. **Legacy Jinja2-templated CMS dashboard has a live bug**, already tracked by existing skipped tests (`tests/test_routers_integration.py`): `GET /` with an empty tracker throws `TypeError('unhashable type: dict')` from Jinja2's template cache — a Starlette/Jinja2 version-compatibility issue, not a test-staleness issue.

6. **`revenue_os/main.py` is a second, historically "dead" FastAPI app entry point**, now deliberately kept as a tested legacy-app containment boundary under governance work (REV-ORCH M0) rather than removed — worth revisiting whether it should exist as a real second surface or be formally retired.

7. **No formalized API contract between frontend and backend.** No OpenAPI client generation, no shared schema — the only contract is implicit in `frontend/src/api.js`'s hand-written calls matching `runner_api_routers/*.py` route signatures. Now that frontend and backend are separate repos with independent release cadences, a drift-detection mechanism (contract tests, generated client, or at minimum a documented versioning policy) would be worth adding.

8. **Two Docker Compose files** (`docker-compose.yml`, `docker-compose.demo.yml`) with overlapping but not identical service definitions — not consolidated as part of this task.
