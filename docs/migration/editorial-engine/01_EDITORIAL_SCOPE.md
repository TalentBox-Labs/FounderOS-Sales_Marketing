# E6A — Editorial Engine Scope

Sprint E6A — Analysis only  
Date: 2026-08-09  
Canonical: `/Users/krishna/Documents/TB-FounderOS-Sales_Marketing`  
CMS reference: `/Users/krishna/Documents/workcrew-cms-os`

No code, test, prompt, API, DB, or Git changes in this sprint.

---

## Target boundary

```
Marketing OS
└── Editorial Engine
```

### In-scope (only if Founder evidence supports)

| Capability | Founder evidence |
|------------|------------------|
| Editorial review / draft refinement | `src/editor_crew.py` + editor YAML |
| Structural editing / QA coordination | validators + optional `src/qa_crew.py` |
| Content validation | `pipeline_runner` DEFAULT_VALIDATORS |
| Draft → final transformation | EditorCrew → `05_Final.md` + `promote_staged` |
| Editorial readiness signals | tracker `status`/`qa_status` + QA reports |
| Style compliance orchestration | validators + brand checklist section |

### Explicitly out of Editorial Engine

| Concern | Actual Founder owner |
|---------|----------------------|
| Generic LLM / CrewAI runtime | AI PLATFORM (`BaseCrew`, env LLM) |
| Auth | SHARED PLATFORM |
| Publishing / go-live | PUBLISHING ENGINE / ops (`go_live_helpers`, human) |
| Social / email / campaign | OTHER / Marketing channels |
| Canonical brand definitions | BRAND ENGINE (vault Brand Voice Guide) |
| SEO strategy production | SEO ENGINE (generation SEO agent + `02_SEO_Plan.md`) |
| Workflow scheduling / Celery / OpenClaw | AUTOMATION PLATFORM |
| Content inventory UI | CONTENT STUDIO (read-only frozen) |
| Calendar | DEFERRED (E5A ADR) |

---

## CMS posture

CMS contributes **process/ritual/prompt** value (OpenClaw SOUL + 6 QA tests + brand voice + human gateway).  
CMS `reference-design/` CrewAI stack is a **Founder duplicate** → SUPERSEDED.  
Sheets / OpenClaw runtime are **not** Editorial Engine SoT for Founder.

---

## Success of E6A

Deliver capability comparison, ownership map, file manifest, risks, and smallest first implementation unit — without implementing Editorial Engine.
