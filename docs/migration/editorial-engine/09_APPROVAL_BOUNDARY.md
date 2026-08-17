# E6A — Approval / Permission Boundary

Do not introduce approval policy in E6A. Document exact behavior only.

---

## Founder behavior

| Mechanism | Automatic? | Behavior | Evidence |
|-----------|------------|----------|----------|
| EditorCrew / GenerationCrew | Auto content write to **staging** when CLI args correct | No human gate inside crew | `editor_crew.py`, `generation_crew.py` |
| Validators | Automatic pass/fail reports | Do not publish | `pipeline_runner.py` |
| `POST /validate` | Automatic | **No tracker write** | `pipeline.py` |
| `POST /run` | Automatic | Sets `status=QA Passed`, `qa_status=PASS` on success — **not** publish | `tracker_updater.py` |
| `promote_staged` | **Blocked without approver** | Requires `--approver` or `WORKCREW_PROMOTION_APPROVER`; writes audit; copies into `input/` | `promote_staged.py` L95–114 |
| Publish checklist checker | Automatic structure check | Explicitly notes **human sign-off still required** | `publish_checklist_checker.py` |
| Go-live | Human-supplied URL | Confirmed live recording | `/go-live` |
| HTTP promote | **None** | No promote API | — |

**Human approval:** Yes — promotion approver + publish checklist human note + go-live.  
**Editor approval:** Implicit via running editor + promote; no separate editor-role ACL verified.  
**QA approval:** Deterministic gates + optional CrewAI QA; tracker QA Passed ≠ CMS “approved”.  
**Automatic promotion:** No (approver required).  
**Automatic publishing readiness:** Tracker QA Passed is a pipeline signal, not CMS SCHEDULED/PUBLISHED.

---

## CMS behavior

| Mechanism | Automatic? | Behavior | Evidence |
|-----------|------------|----------|----------|
| OpenClaw QA PASS | Semi | Routes to CEO/human gateway | `agents/qa/SOUL.md`, `AGENTS.md` |
| Sheets stage transitions | Operator/API | IDEA…PUBLISHED via Flask | `dashboard/app.py` STAGES |
| Checklist flags | Operator | brief/draft/edited/seo/assets | content templates |
| n8n publish pack | Event | After APPROVED/PUBLISHED | n8n workflows (OUT OF SCOPE) |
| Dashboard Run QA | Intended auto | **API route missing** | `crewai_qa.py` unwired |

---

## Classification

Canonical **merged** approval semantics (Founder promote + CMS stage machine + OpenClaw gateway) are **not unified**.

**ADR REQUIRED** before:

- importing CMS stage names into Founder Editorial Engine
- auto-promotion without `--approver`
- treating `QA Passed` as publish approval

For the **first read-only Editorial readiness unit**, approval mutation is out of scope → unit can proceed without resolving the ADR, but the ADR remains required before write-path editorial migration.
