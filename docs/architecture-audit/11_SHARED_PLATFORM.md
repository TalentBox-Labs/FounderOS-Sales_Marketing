# 11 — Shared Platform

Evidence of cross-cutting utilities and infrastructure used by multiple domains.

---

## Configuration

| Item | Evidence |
|------|----------|
| Revenue settings | `revenue_os/config.py` (`Settings` dataclass, `load_dotenv`) |
| Runtime config | `data/runtime_config.json`; loaders in `src/tools/runtime_paths.py` |
| Week profiles | `data/week_runtime/*.json`; `src/tools/runtime_apply.py` |
| Env template | `.env.example` |
| Compose/Render env | `docker-compose.yml`, `render.yaml` |

---

## Authentication

| Item | Evidence |
|------|----------|
| Runner API key verify | `runner_api_routers/utils.py::_verify_api_key` (`HTTPBearer`, `hmac.compare_digest`, `RUNNER_API_KEY`) |
| JWT auth | `revenue_os/auth.py` (bcrypt, jose JWT, `get_current_user`) |
| User model | `revenue_os/models/user.py` |
| Auth routes | `revenue_os/api/v1/auth.py` |
| Middleware auth ValueError mapping | `runner_api_routers/middleware.py` |

---

## Logging / observability

| Item | Evidence |
|------|----------|
| Structured logging middleware | `runner_api_routers/middleware.py` |
| Metrics router | `runner_api_routers/metrics.py` |
| Observability helpers | `src/observability.py` |
| Docs | `docs/OBSERVABILITY.md` |
| Health endpoints | `/health`, `/api/v1/health`, `/api/v1/system/health*` |

---

## Middleware

| Item | Evidence |
|------|----------|
| CORS | both FastAPI apps |
| StructuredLoggingMiddleware | `runner_api` |
| Auth dependencies | per-route `Depends` |

---

## Base classes / common helpers

| Item | Evidence |
|------|----------|
| `BaseCrew` | `src/base_crew.py` |
| Crew contract helpers | `src/crew_contract.py` |
| SQLAlchemy `Base` | `revenue_os/models/base.py` |
| Router utils (`_run`, `_tail`, `_read_tracker`, `_load_runtime`, week validation) | `runner_api_routers/utils.py` |
| CSV / tracker readers | `src/tools/csv_reader.py`, `runtime_tracker.py` |
| Staging overlay | `src/tools/staging_overlay.py` |
| Activity log | `revenue_os/services/activity_log.py` |
| Credentials vault | `revenue_os/services/credentials_vault.py` |

---

## Database infrastructure

| Item | Evidence |
|------|----------|
| Engine/session | `revenue_os/database.py` |
| Alembic | `alembic.ini`, `migrations/` |
| Startup create_all / column patches | `revenue_os/main.py`, `runner_api.py` |

---

## Utilities (content tooling shared by crews)

Located under `src/tools/`:

- Validators: `structure_checker`, `metadata_checker`, `draft_validator`, `research_mapper`, `content_quality_checker`, `distribution_bundle_checker`, `final_frontmatter_lint`, `publish_checklist_checker`
- Pipeline: `pipeline_runner`, `pipeline_orchestrator`, `validation_runner`, `validate_staged`, `validate_all_tracker_weeks`
- Runtime: `runtime_paths`, `runtime_apply`, `runtime_manager`, `runtime_tracker`
- Publish/sync: `hashnode_publish`, `sheet_sync`, `google_sheet_sync`, `google_sheets_verify`, `reader_tab_sync`, `sheet_orphan_cleanup`, `promote_staged`, `promotion_audit`, `go_live_helpers`
- Data: `csv_reader`, `tracker_updater`

---

## Infrastructure artifacts

| Item | Evidence |
|------|----------|
| Docker | `Dockerfile`, compose files |
| CI | `.github/workflows/test.yml` |
| Pre-commit | `.pre-commit-config.yaml` |
| Scripts | `scripts/*` |
| Templates | `templates/*` |
| OpenAPI schema helpers | `src/openapi_schemas.py` |
