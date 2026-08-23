# R1A — Removal Manifest (LEDGER)

**Date:** 2026-08-12  
**Sprint:** R1A  
**Approval:** Coordinator — HIGH-confidence gate re-verified 2026-08-12  
**Scope:** Only R0 C-01..C-06

Historical governance docs that *mention* these paths remain retained (not removal candidates).

---

## Items approved for removal

| ID | Exact path | Classification | Reason | Evidence | Size | Restore | Owner | Approval |
|----|------------|----------------|--------|----------|------|---------|-------|----------|
| C-01 | `src/artifact_crew.py.old` | REMOVE — HIGH | Backup beside live `artifact_crew.py`; not importable as module | `rg` 0 code/test refs; docs-only RETIRE notes | ~7.6 KB | `git checkout HEAD -- src/artifact_crew.py.old` | Marketing / FORGE | APPROVED |
| C-02 | `src/distribution_crew.py.old` | REMOVE — HIGH | Same | Same | ~6.1 KB | `git checkout HEAD -- …` | Marketing / FORGE | APPROVED |
| C-03 | `src/editor_crew.py.old` | REMOVE — HIGH | Same | Same | ~8.9 KB | `git checkout HEAD -- …` | Marketing / FORGE | APPROVED |
| C-04 | `src/generation_crew.py.old` | REMOVE — HIGH | Same | Same | ~9.6 KB | `git checkout HEAD -- …` | Marketing / FORGE | APPROVED |
| C-05 | `src/marketing_crew.py.old` | REMOVE — HIGH | Same | Same | ~10.5 KB | `git checkout HEAD -- …` | Marketing / FORGE | APPROVED |
| C-06 | `revenue_os/pipeline/__init__.py` (+ empty package dir) | REMOVE — HIGH | Empty package; 0 `revenue_os.pipeline` imports | `rg` + `find` (only empty `__init__.py` + pycache) | 0 bytes file | `git checkout HEAD -- revenue_os/pipeline/` | Revenue / FORGE | APPROVED |

### Hard-delete gate (all six)

| Criterion | Result |
|-----------|--------|
| No runtime reference | PASS |
| No dynamic import | PASS |
| No test dependency | PASS |
| No deployment dependency | PASS |
| No template/UI dependency | PASS |
| No configuration dependency | PASS |
| No governance/history *requirement* of the file itself | PASS (docs retain history) |
| No recovery/rollback requirement | PASS (git restore) |
| No user data | PASS |
| No secret-recovery dependency | PASS |
| No migration/reference *requirement* to keep binary | PASS |
| Behavior unchanged after removal | Asserted; verified post-clean |

---

## Explicitly NOT in this manifest

Archive candidates, orphan templates, unused deps, broken routes, Hashnode, `output/qa_reports` (tracked), CMS sibling repos, governance freezes.
