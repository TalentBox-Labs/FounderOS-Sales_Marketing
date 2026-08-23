# 01 — Sprint C Baseline

Verification time: 2026-08-09 (local)  
Repository: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
Mode: read-only verification (no source modifications; no git network ops)

---

## C1 — Local repository baseline

| Check | Result | Evidence |
|-------|--------|----------|
| Branch | `develop` | `git branch --show-current` |
| HEAD | `e1efc0892ea13dad856b952110c7cc38d24565c3` | `git rev-parse HEAD` |
| Matches expected frozen SHA | YES | Exact match to `e1efc0892ea13dad856b952110c7cc38d24565c3` |
| Tag on HEAD | `v0.1-stable` | `git tag --points-at HEAD` |
| Working tree | Dirty (untracked docs only) | `git status --short` → `?? docs/architecture-audit/`, `?? docs/migration/` (and later `?? docs/runtime-verification/`) |
| Latest commit subject | `stabilize platform after repository consolidation` | `git log -5 --oneline --decorate` |

No commits made. No remotes modified.

---

## C2 — Environment baseline

| Item | Result |
|------|--------|
| System `python` | NOT VERIFIED / not found |
| System `python3` | 3.9.6 (`/usr/bin/python3`) |
| Project venv | `.venv` PRESENT — Python **3.12.13**, pip **26.2.1** |
| Dependency files | `requirements.txt`, `requirements-api.txt`, `requirements-revenue.txt` PRESENT |
| `pyproject.toml` / Poetry / Pipfile | MISSING |

No package upgrades performed for this sprint.

---

## C3 — Configuration / secret safety (presence only)

Host shell (no `.env` file):

| Variable | Status |
|----------|--------|
| DOTENV_FILE | MISSING |
| DATABASE_URL | MISSING |
| REDIS_URL | MISSING |
| SECRET_KEY | MISSING |
| OPENAI_API_KEY | MISSING |
| ANTHROPIC_API_KEY | MISSING |
| GEMINI_API_KEY | MISSING |
| WORKCREW_CREWAI_MODEL | MISSING |
| WORKCREW_CREWAI_API_KEY | MISSING |
| WORKCREW_OLLAMA_BASE_URL | MISSING |
| RUNNER_API_KEY | MISSING |
| HEARTBEAT_ENABLED | MISSING |
| POSTGRES_PASSWORD | MISSING |
| N8N_WEBHOOK_BASE_URL | MISSING |
| N8N_API_KEY | MISSING |

Running API container (names only via `printenv` emptiness check):

| Variable | Status |
|----------|--------|
| DATABASE_URL | PRESENT |
| REDIS_URL | PRESENT |
| SECRET_KEY | PRESENT |
| OPENAI_API_KEY | MISSING |
| ANTHROPIC_API_KEY | MISSING |
| GEMINI_API_KEY | MISSING |
| WORKCREW_CREWAI_MODEL | MISSING |
| WORKCREW_CREWAI_API_KEY | MISSING |
| WORKCREW_OLLAMA_BASE_URL | MISSING |
| RUNNER_API_KEY | MISSING |
| HEARTBEAT_ENABLED | PRESENT |

Host Ollama HTTP API reachable at `http://127.0.0.1:11434/api/tags` (model `llama3.1:8b` listed). Container does not show CrewAI/Ollama env PRESENT.

---

## Compose note (startup attempt)

- `docker compose config --services` → `redis`, `db`, `beat`, `worker`, `api`
- Initial `docker compose ps` empty
- `docker compose up -d --build` built images then **failed** binding host `5432` (already allocated)
- Pre-existing stack already running under longer container names (`…-https-githubcom-cyril-s-thomas-s-m-csm-os-*`) with API healthy on `:8000`
- Verification proceeded against that **already running** stack; newly Created containers from the failed bind were left Created (not started)
