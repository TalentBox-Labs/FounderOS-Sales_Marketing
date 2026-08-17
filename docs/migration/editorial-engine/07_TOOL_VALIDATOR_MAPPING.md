# E6A — Tool / Validator Mapping

Do not move tools in E6A.

| Tool | Owner (proposed) | Current caller | Editorial relevance | CMS equivalent | Duplication | Canonical decision |
|------|------------------|----------------|---------------------|----------------|-------------|-------------------|
| `research_mapper` | EDITORIAL ENGINE | pipeline_runner, validate_staged 2a | High — research/SEO plan gate | ref same tool | SUPERSEDED ref | KEEP FOUNDER |
| `draft_validator` | EDITORIAL ENGINE | pipeline, promote 2a | High — draft quality | ref + banned claims ≈ brand ritual | Partial overlap with CMS brand-voice | KEEP FOUNDER; ADAPT ritual extras |
| `structure_checker` | EDITORIAL ENGINE | pipeline, promote 2b | High | ref same | SUPERSEDED ref | KEEP FOUNDER |
| `metadata_checker` | EDITORIAL ENGINE | pipeline, promote 2b | High — FM | ref same | SUPERSEDED | KEEP FOUNDER |
| `final_frontmatter_lint` | EDITORIAL ENGINE | metadata_checker | High | ref same | SUPERSEDED | KEEP FOUNDER |
| `publish_checklist_checker` | EDITORIAL ENGINE / Publishing boundary | pipeline DEFAULT | Medium — structure only; human approval still required | CMS checklist UX | UX ADAPT; tool KEEP | KEEP FOUNDER tool |
| `content_quality_checker` | EDITORIAL ENGINE | validate_staged 2c only | High body score | ref same | SUPERSEDED | KEEP; DEFER default wiring |
| `validate_staged` | EDITORIAL ENGINE | promote CLI | High | ref same | SUPERSEDED | KEEP |
| `promote_staged` | EDITORIAL ENGINE | CLI | High — mutation boundary | CMS Sheets stage | Different model | KEEP FOUNDER |
| `promotion_audit` | EDITORIAL ENGINE | promote | High audit | none equivalent | FOUNDER UNIQUE | KEEP |
| `pipeline_runner` | EDITORIAL ENGINE + AI PLATFORM glue | `/validate`, `/run`, main | High | ref same | SUPERSEDED | KEEP |
| `pipeline_orchestrator` | EDITORIAL ENGINE | `/run` | Medium | ref same | SUPERSEDED | KEEP |
| `validation_runner` | — | alias | Low | — | TRANSITIONAL | DEFER retire alias |
| `tracker_updater` | EDITORIAL ENGINE | full pipeline | Medium state | Sheets QA columns | Different SoT | KEEP tracker |
| `sheet_sync` | OUTSIDE Editorial SoT | CLI | Low (mirror) | CMS Sheets primary | LEGACY CMS SoT | RETIRE as editorial dependency |
| CMS `crewai_qa.py` | — | unwired UI | Low | Founder QACrew | WEAKER DUPLICATE | RETIRE |
| CMS 6 ritual md | EDITORIAL ENGINE (future adapt) | OpenClaw | High process | Founder partial via validators | CMS UNIQUE shape | ADAPT |
