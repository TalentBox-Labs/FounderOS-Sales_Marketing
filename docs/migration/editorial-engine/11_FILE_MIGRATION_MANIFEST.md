# E6A — File Migration Manifest

CMS paths under `/Users/krishna/Documents/workcrew-cms-os/`.  
Do not implement.

---

## CMS files

| Source | Classification | Founder destination | Capability | Dependencies | Files affected (if done) | API impact | DB impact | Runtime impact |
|--------|----------------|---------------------|------------|--------------|--------------------------|------------|-----------|----------------|
| `agents/editor/SOUL.md` | ADAPT | docs / future prompt appendix under Editorial | editor ritual language | none runtime | docs or YAML (later) | NONE | NONE | none if docs-only |
| `agents/qa/SOUL.md` | ADAPT | same | QA gateway language | — | docs | NONE | NONE | none |
| `tests/hallucination-gate.md` | ADAPT | Editorial checklist / future validator | QA ritual | — | docs or tool (later) | NONE initially | NONE | none |
| `tests/brand-voice.md` | ADAPT | Brand Engine + Editorial checklist | brand ritual | Brand Voice Guide | docs | NONE | NONE | none |
| `tests/cta-clarity.md` | ADAPT | Editorial checklist | CTA ritual | — | docs | NONE | NONE | none |
| `tests/visual-caption.md` | ADAPT | Editorial checklist | visual ritual | — | docs | NONE | NONE | none |
| `tests/link-capture.md` | ADAPT | Editorial checklist | link ritual | — | docs | NONE | NONE | none |
| `tests/grammar-fluency.md` | ADAPT | Editorial checklist | grammar ritual | — | docs | NONE | NONE | none |
| `brand/voice.md` | ADAPT | Brand Engine (vault) | brand definition | Brand Guide | vault/docs | NONE | NONE | none |
| `AGENTS.md` + Cos/CEO SOULs | ADAPT / REFERENCE ONLY | Approval ADR inputs | human gateway | — | ADR docs | NONE | NONE | none |
| `dashboard/templates/pipeline.html` | REFERENCE ONLY | Content Studio / pipeline UX ideas | stage UX | — | templates later | possible UI | NONE | UI only |
| `dashboard/templates/content_detail.html` | REFERENCE ONLY | Content Studio detail UX | checklist panel | — | templates later | possible UI | NONE | UI only |
| `dashboard/templates/content_edit.html` | OUT OF SCOPE / DEFER | write UI not in first unit | edit form | Sheets | — | write APIs | NONE | high if copied |
| `dashboard/app.py` (STAGES) | REFERENCE ONLY | Approval ADR | stage enum | Sheets | — | — | NONE | — |
| `dashboard/sheets_integration.py` | RETIRE (as SoT) | — | Sheets SoT | gspread | — | — | NONE | avoid |
| `dashboard/crewai_qa.py` | SUPERSEDED BY FOUNDER | — | weak QA | Ollama/OpenAI | — | — | NONE | avoid |
| `reference-design/src/editor_crew.py` + YAML | SUPERSEDED BY FOUNDER | — | editor | CrewAI | — | — | NONE | avoid |
| `reference-design/src/qa_crew.py` + YAML | SUPERSEDED BY FOUNDER | — | QA | CrewAI | — | — | NONE | avoid |
| `reference-design/src/tools/*validator*` | SUPERSEDED BY FOUNDER | — | validators | — | — | — | NONE | avoid |
| `reference-design/src/tools/promote_staged.py` etc. | SUPERSEDED BY FOUNDER | — | promote | — | — | — | NONE | avoid |
| Nested `workcrew-cms-os/workcrew-cms-os/**` | RETIRE | — | clone noise | — | — | — | NONE | — |
| OpenClaw skills / n8n publish | OUT OF SCOPE | AUTOMATION / Publishing | — | OpenClaw/n8n | — | — | NONE | — |
| `reports/qa/*` | REFERENCE ONLY | historical shape | scorecards | — | — | NONE | NONE | none |

---

## Founder files proposed for **first unit** (E6B candidate — not E6A)

See `14_FIRST_IMPLEMENTATION_UNIT.md`. Expected touch set is small and Founder-native (read API + tests + docs). CMS sources for that unit are REFERENCE ONLY (scorecard field ideas).
