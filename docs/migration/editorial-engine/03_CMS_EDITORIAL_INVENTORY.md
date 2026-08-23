# E6A — CMS Editorial Inventory

Reference repository: `/Users/krishna/Documents/workcrew-cms-os`  
Executable evidence preferred over docs-only claims.

CMS editorial = **two stacks**: (A) OpenClaw + Flask + Sheets, (B) `reference-design/` Founder duplicate.

---

## Capability table

| Capability | Source file/module | Entry point | Inputs | Outputs | Dependencies | Runtime evidence | Tests | Notes |
|------------|-------------------|-------------|--------|---------|--------------|------------------|-------|-------|
| Editor agent (OpenClaw) | `agents/editor/SOUL.md` | OpenClaw persona load | brief, SEO, research | draft md / handoffs | OpenClaw, `brand/voice.md` | Historical content + scorecards | None | Ritual, not Python crew |
| QA agent (OpenClaw) | `agents/qa/SOUL.md` | OpenClaw | draft + sources | scorecard; FAIL→Editor / PASS→CEO | 6 test md files | `reports/qa/*-qa-scorecard.md` | Ritual only | Gatekeeper persona |
| Hallucination gate | `tests/hallucination-gate.md` | QA ritual | draft + sources | PASS/FAIL | QA SOUL | Scorecards | None | CMS UNIQUE ritual |
| Brand voice test | `tests/brand-voice.md` | QA ritual | draft | score / rewrite | `brand/voice.md` | Scorecards | None | CMS UNIQUE ritual |
| CTA clarity | `tests/cta-clarity.md` | QA ritual | draft | PASS/FAIL | QA SOUL | Scorecards | None | |
| Visual/caption | `tests/visual-caption.md` | QA ritual | assets/copy | PASS/FAIL | QA SOUL | Scorecards | None | |
| Link capture | `tests/link-capture.md` | QA ritual | links/CTAs | PASS/FAIL | QA SOUL | Scorecards | None | |
| Grammar/fluency | `tests/grammar-fluency.md` | QA ritual | draft | PASS/FAIL | QA SOUL | Scorecards | None | |
| Brand voice guide | `brand/voice.md` | Editor/QA reference | — | voice rules | — | Used by SOULs | None | Adapt into Brand Engine |
| Human gateway / handoffs | `AGENTS.md`, Cos/CEO SOULs | OpenClaw + human | week/task | approval before publish | Sheets, n8n | Critical handoffs 1–7 | None | Process value |
| Sheets stage machine | `dashboard/sheets_integration.py`, `app.py` STAGES | Flask stage APIs | content_id, stage | Sheets updates | gspread | Dashboard | smoke/integration (stages) | IDEA→…→PUBLISHED |
| Checklist UX | `content_detail.html`, edit templates | Flask UI | checklist flags | progress UI | Sheets | Dashboard | partial | UX reference |
| Dashboard QA module | `dashboard/crewai_qa.py` | Intended `POST /api/qa/<id>` — **missing route** | article dict | QAReport → Sheets | Ollama/OpenAI, gspread | UI button unwired | None | DEAD API wiring |
| EditorCrew (ref) | `reference-design/src/editor_crew.py` | `python -m src.editor_crew` | draft staging | `05_Final.md` | CrewAI | Founder-parity | fence strip etc. | SUPERSEDED |
| QACrew (ref) | `reference-design/src/qa_crew.py` | pipeline optional | draft/final | CrewAI QA md | CrewAI | Founder-parity | Founder tests | SUPERSEDED |
| Validators (ref) | `reference-design/src/tools/*_checker.py` etc. | CLI / pipeline | artifacts | QA reports | runtime | Founder-parity | integration | SUPERSEDED |
| Nested clone tree | `workcrew-cms-os/workcrew-cms-os/` | — | — | — | — | Accidental duplicate | — | RETIRE |

---

## CMS-native editorial flow (behavioral)

```
OpenClaw Cos/CEO dispatch
  → Researcher / SEO / Editor (SOUL)
  → QA 6 rituals → scorecard
  → Human gateway
  → Sheets stages + Flask checklist
  → n8n publish pack (OUT OF SCOPE for Editorial Engine)
```

## reference-design flow

Matches Founder Phase 2A→2B→validators→optional QA→tracker (duplicate).

---

## CMS unique value (evidence-backed only)

1. Six QA ritual markdowns under `tests/*.md`
2. OpenClaw Editor/QA SOUL process language
3. `brand/voice.md` + brand-voice ritual coupling
4. Human gateway protocol in `AGENTS.md` / Cos-CEO SOULs
5. Flask stage/checklist UX patterns (not Sheets SoT)

**Not unique:** CrewAI editor/QA/validators in `reference-design/` (Founder already owns).
