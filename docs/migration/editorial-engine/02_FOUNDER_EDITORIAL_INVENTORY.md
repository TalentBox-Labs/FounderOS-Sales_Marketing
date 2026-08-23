# E6A — Founder Editorial Inventory

Evidence-only inventory of executable Founder editorial capabilities.

---

## Capability table

| Capability | Owning module | Entry point | Inputs | Outputs | Dependencies | Tests | Runtime usage | Classification |
|------------|---------------|-------------|--------|---------|--------------|-------|---------------|----------------|
| BaseCrew | `src/base_crew.py` | abstract `run()` | YAML agents/tasks, LLM env | crew text + optional validation | CrewAI, yaml | `test_crews_unit.py`, `test_utilities_unit.py` | Parent of crews | IMPLEMENTED |
| EditorCrew (2B) | `src/editor_crew.py` | CLI `--staging-root`; `run_phase_2b_editor` | staging `04_Draft.md`, QA reports, SEO plan | staging `05_Final.md` | `agents_editor.yaml`, `tasks_editor.yaml` | `test_editor_*`, `test_crews_unit.py` | CLI OK; `POST /edit` omits staging args | PARTIAL |
| QACrew | `src/qa_crew.py` | `run_qa_agent`; pipeline soft-fail | draft/final per runtime | `{week}_CrewAI_QA.md` | `agents.yaml`, `tasks.yaml`, `crew_contract` | `test_crews_unit.py`, `test_crew_contract.py`, `test_pipeline_runner.py` | Only if `enable_crewai_qa` | IMPLEMENTED (optional) |
| Legacy procedural QA | `src/crew.py` | `run_qa_agent` | same | QA md | same YAML | `test_crew.py`, `test_crew_qa_input.py` | Superseded by QACrew in pipeline | LEGACY / TRANSITIONAL |
| GenerationCrew (2A) | `src/generation_crew.py` | CLI `--output-root`; `run_phase_2a_chain` | tracker, seed | staging 01–04 | generation YAML | `test_generation_crew.py` | CLI OK; `POST /generate` omits output-root | PARTIAL |
| ArtifactCrew (2A alt) | `src/artifact_crew.py` | CLI only | tracker, week_runtime | claimed 01–04 | phase2a YAML | `test_artifact_crew_guard.py` | No API; write path incomplete vs generation | PARTIAL |
| research_mapper | `src/tools/research_mapper.py` | `run_mapper`; pipeline | research + SEO paths | `*_Research_Map.md` | runtime_config | via validate_all / pipeline | DEFAULT validator #1 | IMPLEMENTED |
| draft_validator | `src/tools/draft_validator.py` | `run_validator` | draft | `*_Draft_Validation.md` | banned claims | integration | DEFAULT #2; promote 2a | IMPLEMENTED |
| structure_checker | `src/tools/structure_checker.py` | `run_structure_check` | final | `*_Structure_Check.md` | H1/H2/FAQ rules | no dedicated unit | DEFAULT #3; promote 2b | IMPLEMENTED |
| metadata_checker | `src/tools/metadata_checker.py` | `run_metadata_check` | final | `*_Metadata_Check.md` | `final_frontmatter_lint` | `test_metadata_checker.py` | DEFAULT #4 | IMPLEMENTED |
| final_frontmatter_lint | `src/tools/final_frontmatter_lint.py` | `lint_final_front_matter` | FM dict | pass/fail | schema constants | `test_final_frontmatter_lint.py` | library | IMPLEMENTED |
| publish_checklist_checker | `src/tools/publish_checklist_checker.py` | `run_checklist_check` | `09_Publish_Checklist.md` | checklist report | section markers | distribution tests (partial) | DEFAULT #5; human still required | IMPLEMENTED |
| content_quality_checker | `src/tools/content_quality_checker.py` | CLI / validate_staged 2c | `05_Final.md` | quality score report | heuristics | `test_content_quality_checker.py` | Not in DEFAULT_VALIDATORS; not in promote | PARTIAL |
| pipeline_runner | `src/tools/pipeline_runner.py` | `run_validation_pipeline` / `run_pipeline` | runtime validators | reports; tracker on full run | VALIDATOR_MODULES, optional QACrew | `test_pipeline_runner.py` | `/validate`, `/run` | IMPLEMENTED |
| pipeline_orchestrator | `src/tools/pipeline_orchestrator.py` | `run_with_summary` | active_week | summary JSON | pipeline_runner | `test_pipeline_orchestrator.py` | `/run` | IMPLEMENTED |
| validate_staged | `src/tools/validate_staged.py` | CLI phases 2a/2b/2c/3 | staging_root, week | staging QA reports | staging_overlay | overlay tests | promote prerequisite | IMPLEMENTED |
| promote_staged | `src/tools/promote_staged.py` | CLI; requires `--approver` | staging, week, phase | copy → `input/` + audit | validate_staged | audit tests | **No HTTP** | IMPLEMENTED |
| promotion_audit | `src/tools/promotion_audit.py` | with promote | diffs, runs | `output/promotion_audit/` | promote | `test_promotion_audit.py` | with promote | IMPLEMENTED |
| tracker_updater | `src/tools/tracker_updater.py` | after full pipeline | active_week | `status=QA Passed`, `qa_status=PASS` | tracker.csv | pipeline tests | full `/run` only | IMPLEMENTED |
| API `/validate` | `runner_api_routers/pipeline.py` | POST | week? | ok/stdout/stderr | pipeline_runner | integration | UI | IMPLEMENTED |
| API `/edit` | `pipeline.py` | POST | week? | subprocess | `python -m src.editor_crew` **no staging** | none success | UI buttons | UNREACHABLE / BROKEN as wired |
| API `/generate` | `pipeline.py` | POST | week? | subprocess | generation **no output-root** | none success | UI | UNREACHABLE / BROKEN as wired |
| API `/run` | `pipeline.py` | POST | week? | validators+QA+tracker | orchestrator | integration | dashboard | IMPLEMENTED |
| API `/qa` | — | UI references | — | — | — | — | nav dead | DEAD / UNREACHABLE |
| Content Studio read | `content_studio.py` + UI | GET | tracker + artifacts | JSON/HTML | tracker, input | `test_content_studio_*` | display only | IMPLEMENTED (not executor) |
| sheet_sync | `src/tools/sheet_sync.py` | CLI | tracker + FM | Sheets mirror | gspread | sheet sync tests | post-pipeline ops | OUTSIDE editorial gate |
| `*.py.old` crews | `src/*.old` | none | — | — | — | — | superseded | LEGACY / DEAD |

---

## Coverage summary

| Bucket | Assessment |
|--------|------------|
| Deterministic validation | COMPLETE for default 5-pack |
| Draft → final (CLI staging) | COMPLETE process; API PARTIAL/broken |
| CrewAI QA | IMPLEMENTED optional |
| Editorial UI/API orchestration | PARTIAL / LIMITED (broken generate/edit; missing /qa) |
| Overall Founder editorial | **PARTIAL** (strong core, weak HTTP surface) |
