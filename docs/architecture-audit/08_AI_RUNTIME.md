# 08 — AI Runtime

Evidence-only traces of AI execution paths present in the repository.

---

## Prompt / config locations

### YAML agent configs (`src/`)
| File | Agent keys observed |
|------|---------------------|
| `agents.yaml` | `qa_agent` |
| `agents_generation.yaml` | `strategist_agent`, `seo_agent`, `research_agent`, `writer_agent` |
| `agents_phase2a.yaml` | same four agent keys |
| `agents_editor.yaml` | `editor_agent` |
| `agents_distribution.yaml` | `distribution_agent` |
| `agents_marketing.yaml` | `content_strategist`, `blog_writer`, `social_copywriter`, `image_director`, `seo_optimiser` |

### YAML task configs (`src/`)
| File |
|------|
| `tasks.yaml` |
| `tasks_generation.yaml` |
| `tasks_phase2a.yaml` |
| `tasks_editor.yaml` |
| `tasks_distribution.yaml` |
| `tasks_marketing.yaml` |

### Inline system prompts (Python)
- `revenue_os/services/ai_service.py` — `_SYSTEM_SDR` and message strings for cold email / related helpers
- Other service modules contain prompt strings for chat completions (e.g. copilot/sales agents — file presence: `copilot.py`, `sales_agents.py`)

### LLM provider wiring
- CrewAI: `src/base_crew.py::_build_llm` → `crewai.LLM`
- OpenAI SDK: `revenue_os/services/ai_service.py` (`from openai import OpenAI`) when `OPENAI_API_KEY` set
- RAG: `revenue_os/services/rag_service.py` + Chroma via `search_service.py`

---

## Crew classes

| Class | File | YAML pair (constructor usage pattern) |
|-------|------|----------------------------------------|
| `BaseCrew` | `base_crew.py` | abstract |
| `GenerationCrew` | `generation_crew.py` | generation / phase2a YAML |
| `EditorCrew` | `editor_crew.py` | editor YAML |
| `QACrew` | `qa_crew.py` | `agents.yaml` / `tasks.yaml` |
| `MarketingCrew` | `marketing_crew.py` | marketing YAML |
| `DistributionCrew` | `distribution_crew.py` | distribution YAML |
| `ArtifactCrew` | `artifact_crew.py` | phase2a-style keys |
| `SDRCrew` | `sdr_crew.py` | (extends BaseCrew) |
| `CSMCrew` | `csm_crew.py` | (extends BaseCrew) |

Legacy procedural helpers also exist in `src/crew.py` (QA-oriented).

---

## Pipeline A — Content validation (+ optional CrewAI QA)

```
HTTP POST /validate  (or /run, /run-pipeline)
  → runner_api_routers.pipeline
  → subprocess: python -m src.tools.pipeline_runner  (or pipeline_orchestrator)
  → src.tools.pipeline_runner.run_pipeline
  → validators under src/tools/*
  → optional CrewAI QA (runtime flag enable_crewai_qa; tests reference _maybe_run_crewai_qa)
  → filesystem: output/qa_reports/*
  → JSON/text response tails from subprocess stdout/stderr
```

CLI alternate: `python -m src.main` → `run_pipeline()`.

Orchestration persistence of summary: `output/pipeline_orchestrator_run.json`.

---

## Pipeline B — Generation (Phase 2A)

```
HTTP POST /generate
  → runner_api_routers.pipeline.run_generate
  → optional runtime_apply for week
  → subprocess: python -m src.generation_crew
  → GenerationCrew.build_agents_and_tasks / run_generation / run_phase_2a_chain
  → Agents: strategist, seo, research, writer (YAML)
  → Tools: get_active_content, staging overlay, filesystem read/write under staging/output
  → Provider: CrewAI LLM (env WORKCREW_CREWAI_*)
  → Persistence: staging markdown artifacts (e.g. draft paths under output/generated or configured roots)
  → HTTP: {ok, stdout, stderr}
```

---

## Pipeline C — Editor (Phase 2B)

```
HTTP POST /edit
  → runner_api_routers.pipeline.run_edit
  → subprocess: python -m src.editor_crew
  → EditorCrew.run_phase_2b_editor
  → Agent: editor_agent (YAML)
  → Tools/helpers: SEO canonical section, CTA hints, validator report collection, fence strip
  → Provider: CrewAI LLM
  → Persistence: staging `05_Final.md`
  → HTTP: {ok, stdout, stderr}
```

---

## Pipeline D — Marketing generate / publish

```
HTTP POST /marketing/generate
  → runner_api_routers.marketing.marketing_generate
  → subprocess: python -m revenue_os.agents.marketing_crew <topic> <keyword> ...
  → (module path as coded in router)

HTTP POST /marketing/dry-run|/publish
  → SocialPublisher from revenue_os.integrations.social_publisher
  → external social APIs when credentials present
```

Note: repository contains `src/marketing_crew.py` (`MarketingCrew`).  
A Python module path `revenue_os.agents.marketing_crew` was **not found** as a file during inventory (see `13_ARCHITECTURE_GAPS.md`).

---

## Pipeline E — Copilot chat

```
HTTP POST /api/v1/copilot/chat
  → runner_api_routers.copilot
  → revenue_os.services.copilot.chat
  → may call rag_service.answer_question / OpenAI depending on code paths
  → activity logging via activity_log
  → JSON response dict
```

---

## Pipeline F — Outreach / sales AI helpers

```
HTTP POST /api/v1/outreach/generate-email
  → outreach router
  → AI email helpers (ai_service / related)

HTTP POST /api/v1/agents/sales/{contact_id}/...
  → agents router
  → revenue_os.agents.execution / sales_agents services
  → OpenAI or fallbacks per ai_service patterns

HTTP POST /api/v1/hermes/sdr-outreach
  → hermes router
  → src.sdr_crew.SDRCrew
  → CrewAI LLM
```

---

## Pipeline G — Knowledge ask / RAG

```
HTTP POST /api/v1/knowledge-base/ask
  → knowledge_base router
  → rag/search services
  → ChromaDB persistence under data/chroma_db
  → response JSON
```

---

## Pipeline H — GTM orchestration backends

```
HTTP POST /api/v1/orchestration/plan|/run
  → orchestration router
  → go_to_market_orchestrator / orchestration_runtime
  → may call Hermes/OpenClaw URLs and n8n.trigger_workflow
  → logs via orchestration runtime
```

---

## Orchestration components (non-CrewAI)

| Component | Path |
|-----------|------|
| Heartbeat jobs | `revenue_os/scheduler.py` |
| Celery tasks | `revenue_os/tasks/{leads,outreach,agents}.py` |
| Automation workflows | `revenue_os/automation/*` |
| Agent registry/safeguards | `revenue_os/agents/*` |

---

## Provider summary (evidence)

| Provider | Used by |
|----------|---------|
| CrewAI + Ollama-compatible LLM env | `src` crews |
| OpenAI Chat Completions | `ai_service` and related services when key present |
| ChromaDB | search/rag |
| Gemini key flag | settings / MCP hub status |
| Anthropic client module | **Repository evidence not found** |
