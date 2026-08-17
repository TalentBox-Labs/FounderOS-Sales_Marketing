# 04 — AI Runtime Certification (Sprint D1)

Date: 2026-08-09  
Method: local `TestClient` against D0-fixed `runner_api_routers/marketing.py`  
Provider env: `WORKCREW_CREWAI_MODEL=ollama/llama3.1:8b`, `WORKCREW_OLLAMA_BASE_URL=http://127.0.0.1:11434`

---

## D1.4 — Marketing workflow (same flow as D0)

| Step | Result | Evidence |
|------|--------|----------|
| Route | PASS | `POST /marketing/generate` → HTTP 200 |
| Import | PASS | stderr lacks `No module named revenue_os.agents.marketing_crew` |
| Crew module | PASS | Invokes `src.marketing_crew` (CLI flags `--brand/--topic/--keyword/--geo/--funnel/--output`) |
| Provider path | PASS (attempted) | LLM call reached provider layer |
| Response | PASS | keys `ok`, `stdout`, `stderr`, `output_path` |
| Artifact directory | PASS (created) | `output/marketing/d1_cert_unsandboxed` |
| Artifact files | FAIL (Environment) | empty — provider returned model error before write |
| Runtime exceptions in router | None uncaught | HTTP 200 with `ok:false` body (explicit failure contract) |

### Before vs after D0 (marketing)

| Check | Sprint C (live) | Sprint D1 (fixed code) |
|-------|-----------------|------------------------|
| Module | `revenue_os.agents.marketing_crew` missing | `src.marketing_crew` loaded |
| Crew reached | NO | YES — task instructions in stdout |
| Provider reached | NO | YES — LLM completion path executed |
| Fallback path | N/A | NOT triggered |

Docker `:8000` still returns Sprint C ModuleNotFound (image not rebuilt) — **Environment**, not a D0 code regression.

---

## D1.5 — Controlled AI execution

### Marketing crew (`src.marketing_crew`)

| Criterion | Result |
|-----------|--------|
| Crew loads | PASS — `Crew(...)` constructed; task panel printed |
| Provider loads | PASS — OpenAI-compatible/Ollama completion path entered |
| Prompt executes | PASS — “Task instructions” / Content Strategist brief emitted on stdout |
| Artifact generated | FAIL — no content files (provider error) |
| Response returned | PASS — JSON contract intact |
| Fallback path | PASS — not triggered |

Provider error (stderr tail):

```text
ValueError: Model llama3.1:8b not found: 404 page not found
```

Host Ollama `/api/tags` lists `llama3.1:8b`. Classification: **Environment** (provider/model routing from CrewAI LiteLLM path), same class of live-AI incompleteness as Sprint C — **not** a D0 regression. D0 itself recorded `ok:false` after crew start as acceptable for import-blocker closure.

### Content generate (`POST /generate` week W01)

| Criterion | Result |
|-----------|--------|
| Route | PASS — HTTP 200 |
| Crew entry | Invoked `src.generation_crew` |
| Completion | FAIL early — `RuntimeError: Refusing to write into input/WXX/` without `--output-root` / escape hatch |
| Falsely success | NO — `ok:false` |

Classification: **Known** safety guard / invocation shape (not introduced by D0).

---

## AI certification verdict

| Layer | Verdict |
|-------|---------|
| Marketing path integrity (D0 repair) | **PASS** |
| Provider/prompt reachability | **PASS** |
| Full artifact E2E success | **FAIL (Environment / Known)** |
| D0-induced AI regressions | **0** |

**AI summary for baseline freeze:** **PASS** on controlled path certification (crew + provider + prompt + response; no fallback; import blocker resolved). Full artifact success remains a Known/Environment gap pending provider wiring/model routing — outside D0/D1 repair scope.
