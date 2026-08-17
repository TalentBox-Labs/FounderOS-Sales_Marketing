# E6A — Capability Comparison

Exact one relationship class per row. Evidence required.

| Capability | Founder | CMS | Relationship | Evidence | Canonical decision |
|------------|---------|-----|--------------|----------|-------------------|
| Draft → final editor crew | EditorCrew CLI staging | OpenClaw Editor SOUL + ref EditorCrew | FOUNDER BETTER (executable) / CMS PARTIAL (ritual) | Founder `editor_crew.py`; CMS SOUL no pytest; ref = duplicate | KEEP FOUNDER; ADAPT CMS SOUL language later |
| Deterministic validators | 5-pack + quality 2c | ref validators + ritual 6 tests | FOUNDER COMPLETE (gates); CMS UNIQUE (ritual suite) | `pipeline_runner.DEFAULT_VALIDATORS`; CMS `tests/*.md` | KEEP FOUNDER; ADAPT rituals as checklist/docs |
| CrewAI QA | QACrew optional | dashboard crewai_qa + ref QACrew | FOUNDER BETTER | Founder soft-fail wired; CMS `/api/qa` missing | KEEP FOUNDER; RETIRE CMS dashboard QA path |
| Staging + promote + approver | `promote_staged` + audit | Sheets stage APIs | FOUNDER UNIQUE (filesystem promote) / CMS UNIQUE (Sheets stages) | Founder CLI approver required; CMS Sheets | KEEP FOUNDER promote; RETIRE Sheets SoT; DEFER stage UX |
| Pipeline validate/run API | `/validate`, `/run` | Flask stage/update APIs | FOUNDER BETTER for validation | Founder pipeline.py | KEEP FOUNDER |
| Generate/Edit HTTP | `/generate`, `/edit` broken args | Flask edit metadata | FOUNDER PARTIAL | pipeline.py omits staging flags | ADAPT (fix Founder wiring) — not CMS migrate |
| Content inventory UI | Content Studio read frozen | Flask content detail/pipeline | FOUNDER COMPLETE (read); CMS BETTER (write checklist UX) | CS baseline; CMS templates | KEEP FOUNDER CS; ADAPT UX ideas DEFER |
| Brand voice definition | Obsidian Brand Voice Guide | `brand/voice.md` | DUPLICATE intent | both guides | MERGE BEHAVIOR into Brand Engine; RETIRE CMS ownership |
| Human approval gateway | promote `--approver` + checklist human note | Cos/CEO gateway + Sheets | FOUNDER PARTIAL + CMS PARTIAL | both exist; policy not unified | ADR REQUIRED before merge |
| Publishing | go-live helpers | n8n publish | OUTSIDE Editorial | both | DEFER / Publishing Engine |
| OpenClaw orchestration | not on editorial path | primary CMS agent runtime | CMS UNIQUE (platform) | Founder OpenClaw = GTM only | RETIRE CMS runtime for Founder Editorial |
| Calendar | blocked E5A | CMS calendar demo/Sheets | LEGACY CMS | E5A ADR | DEFER |
| QA report UX | files under `output/qa_reports/` | `reports/qa/*` scorecards | FOUNDER COMPLETE (files); CMS UNIQUE (scorecard shape) | both | KEEP FOUNDER reports; ADAPT scorecard fields optionally |

### Counts (for verdict)

| Class | Approx N |
|-------|----------|
| FOUNDER COMPLETE / BETTER / UNIQUE | 8 |
| CMS UNIQUE | 5 |
| DUPLICATE / SUPERSEDED ref | 6 |
| PARTIAL both / ADR | 2 |
