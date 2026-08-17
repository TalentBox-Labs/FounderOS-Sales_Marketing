# 03 — Test Results

Environment: local `.venv` Python 3.12.13  
`SECRET_KEY` set for process (ephemeral, not printed)  
`HEARTBEAT_ENABLED=0`  
Command: `python -m pytest …`

---

## Integration suite

```
.venv/bin/python -m pytest tests/test_routers_integration.py -q
```

| Metric | Count |
|--------|------:|
| Collected / passed | 18 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

Result: **18 passed**

---

## Full suite

```
.venv/bin/python -m pytest -q
```

| Metric | Count |
|--------|------:|
| Passed | 216 |
| Failed | 8 |
| Errors | 4 |
| Warnings | 26 |
| Total executed (passed+failed+errors) | 228 |

### Failed tests (classification)

| Test | Class |
|------|-------|
| `TestQACrew::test_qa_crew_validates_output_format` | B stale/obsolete contract |
| `TestEditorCrew::test_editor_crew_validates_output` | B stale/obsolete contract |
| `TestEditorCrew::test_editor_crew_rejects_output_without_frontmatter` | B stale/obsolete contract |
| `TestFileOperations::*` (4) | B / E architecture debt (abstract `BaseCrew` instantiation) |
| `TestDataValidation::test_markdown_structure_validation` | B stale/obsolete contract |

(Classification consistent with prior Sprint A intentional leave-behind; not re-fixed in Sprint C.)

### Errors (4)

| Test | Class |
|------|-------|
| `test_orchestration_api.py` (2) | G environment/runtime / H — failed under local pytest session (DB/auth/env interaction); not diagnosed to production regression in this sprint |
| `test_prospecting_ui.py` (2) | G / H — same session; live Docker prospecting not separately green-proven here |

---

## Focused runtime API checks (live Docker API :8000)

| Check | Result |
|-------|--------|
| GET `/health` | PASS 200 |
| POST `/validate` week W01 | PASS `ok:true` (validators ran) |
| POST `/marketing/generate` | FAIL path integrity (`ok:false`, missing module) — expected for Slice 0 evidence |
| POST `/generate` week W01 | FAIL provider connectivity (`ok:false`, LLM connection error) |
| Webhook subscribe/list | PASS 200 |

No tests were modified.
