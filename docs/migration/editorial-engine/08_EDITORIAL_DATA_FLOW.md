# E6A — Editorial Data Flow

Behavior comparison, not folder structure.

---

## Founder flow (executable)

```
[Phase 2A] POST /generate (BROKEN as wired) OR CLI generation_crew --output-root
  → staging: 01_Brief, 02_SEO_Plan, 03_Research, 04_Draft
        │
        ▼
CLI validate_staged --phase 2a
  → research_mapper + draft_validator → staging QA reports
        │
        ▼ APPROVAL #1: promote_staged --approver (CLI only; no HTTP)
  → copy 01–04 → input/{week}/
        │
        ▼
[Phase 2B] POST /edit (BROKEN as wired) OR CLI editor_crew --staging-root
  → staging 05_Final.md
        │
        ▼
validate_staged --phase 2b (+ optional 2c content_quality)
  → structure + metadata (+ quality)
        │
        ▼ APPROVAL #2: promote_staged --final-only --approver
  → copy 05_Final.md → input/{week}/
        │
        ▼
POST /validate | POST /run | python -m src.main
  → DEFAULT_VALIDATORS (± optional QACrew if enable_crewai_qa)
  → QA reports under output/qa_reports/
  → on full run: tracker status=QA Passed, qa_status=PASS
        │
        ▼ APPROVAL #3: human publish checklist / go-live (Publishing)
  → optional sheet_sync CLI (mirror; not gate)
```

| Stage | API | Service | Crew | Tools | Artifacts in | Artifacts out | State mutation | Approval |
|-------|-----|---------|------|-------|--------------|---------------|----------------|----------|
| Generate | `/generate` (broken) | pipeline subprocess | GenerationCrew | — | tracker | staging 01–04 | staging FS | none |
| Edit | `/edit` (broken) | pipeline subprocess | EditorCrew | SEO hint | staging draft | staging final | staging FS | none |
| Validate | `/validate` | pipeline_runner | — | 5 validators | input paths | qa_reports | **no tracker** | none |
| Full run | `/run` | orchestrator | optional QACrew | validators | input | reports + tracker | status/qa_status | none auto-publish |
| Promote | **none** | promote_staged CLI | — | validate_staged | staging | input/ + audit | FS copy | **approver required** |
| Go-live | `/go-live` | go_live_helpers | — | — | URL | tracker steps | current_step possible | human URL |

Ambiguous / NOT VERIFIED:
- Live LLM kickoff success in CI (mostly mocked/guarded)
- Full promote e2e in automated suite beyond unit/audit tests
- Whether UI operators understand staging requirement

---

## CMS flow (behavioral)

```
OpenClaw Cos/CEO → Researcher/SEO/Editor SOUL
  → QA 6 rituals → scorecard (reports/qa)
  → Human gateway
  → Sheets stages + Flask checklist/edit
  → n8n publish (OUT OF SCOPE)
```

Parallel unused path: `reference-design` ≈ Founder pipeline (duplicate).

Dashboard `POST /api/qa/<id>`: **NOT VERIFIED as live** (route missing).

---

## Comparison (behavior)

| Concern | Founder | CMS |
|---------|---------|-----|
| Primary automation | CrewAI + deterministic validators + FS promote | OpenClaw rituals + Sheets |
| Approval | CLI `--approver` + human publish | Human gateway + Sheets stages |
| SoT | tracker.csv + `input/` | Google Sheets (CMS-native) |
| Duplicate stack | Canonical | `reference-design/` copy of Founder |
