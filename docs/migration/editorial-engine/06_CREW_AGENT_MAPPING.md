# E6A — Crew / Agent Mapping

No prompt modifications in E6A.

---

## Founder agents / tasks

| Agent / task artifact | Role | Classification |
|----------------------|------|----------------|
| `src/agents_editor.yaml` | Editor persona for Phase 2B | KEEP |
| `src/tasks_editor.yaml` | Draft→final + frontmatter rules | KEEP |
| `src/editor_crew.py` | Orchestrates editor | KEEP (fix API wiring later) |
| `src/agents.yaml` + `src/tasks.yaml` | QA auditor + PASS/FAIL contract | KEEP |
| `src/qa_crew.py` | QACrew | KEEP |
| `src/crew.py` | Legacy procedural QA | RETIRE (after callers confirmed none) / DEFER delete |
| `src/agents_generation.yaml` + `tasks_generation.yaml` | Gen 2A | KEEP (SEO Engine / generation; handoff into Editorial) |
| `src/generation_crew.py` | Phase 2A chain | KEEP |
| `src/agents_phase2a.yaml` + `tasks_phase2a.yaml` | ArtifactCrew alt | DEFER / MERGE into generation path later |
| `src/artifact_crew.py` | Alt 2A | DEFER (partial write path) |
| `src/*.py.old` | Old crews | RETIRE |

---

## CMS agents / tasks

| Artifact | Role | Classification |
|----------|------|----------------|
| `agents/editor/SOUL.md` | OpenClaw editor ritual | ADAPT (process language into Founder docs/prompts later — not runtime) |
| `agents/qa/SOUL.md` | OpenClaw QA gatekeeper | ADAPT |
| `tests/{hallucination-gate,brand-voice,cta-clarity,visual-caption,link-capture,grammar-fluency}.md` | 6 critical tests | ADAPT → editorial checklist / future validators |
| Cos/CEO SOULs + `AGENTS.md` | Dispatch + human gateway | ADAPT (approval ADR input) |
| `reference-design/src/editor_crew.py` + YAML | Duplicate Founder | RETIRE / SUPERSEDED |
| `reference-design/src/qa_crew.py` + YAML | Duplicate | RETIRE / SUPERSEDED |
| `dashboard/crewai_qa.py` | Weaker SEO+grammar QA | RETIRE for Founder path |

---

## Overlap / conflicts

| Topic | Finding |
|-------|---------|
| Overlapping agents | Founder Editor/QA ≡ CMS reference-design Editor/QA |
| Overlapping tasks | Same staging artifact contracts (01–05) |
| Conflicting prompts | OpenClaw SOUL rituals ≠ CrewAI YAML; do not auto-merge text |
| Duplicate responsibilities | CMS dashboard QA vs Founder QACrew+validators |
| Unique CMS behavior | 6 ritual tests + human gateway language + scorecard shape |
| Reusable validation | Founder deterministic tools already canonical |

**Do not migrate CMS OpenClaw runtime into Editorial Engine.**
