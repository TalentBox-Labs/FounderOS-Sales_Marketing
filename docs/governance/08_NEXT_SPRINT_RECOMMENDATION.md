# 08 — Next Sprint Recommendation

Sprint P0 — Documentation only  
Date: 2026-08-09

---

## Recommendation

### Unblocking (governance — if FDR incomplete)

**Complete Founder Decision Record** ([F0_FOUNDER_DECISION_RECORD.md](F0_FOUNDER_DECISION_RECORD.md)) for FDR-001, FDR-002, FDR-003.  
No code. Required before E7.

### Next implementation sprint (after FDR)

**Sprint E7 — Editorial Approval Command**

Thin, evidence-aligned approve/promote surface over existing `promote_staged` + `promotion_audit`.  
No publish. No lifecycle invention. No CMS/OpenClaw/Sheets.

### Safe parallel implementation sprint (anytime under Toolchain v1.0)

**Sprint T1 — Ruff Tooling Install**  
ADD NOW tool; OSS license confirmation in PR; no app behavior change.

---

## E7 — Objective

Expose Editorial Approval as a controlled command that:

- Attests phase-scoped staged artifact promotion (unless FDR selects otherwise)  
- Records approver per FDR-002 policy  
- Writes/uses existing promotion audit  
- Does **not** authorize Publishing Engine (unless FDR-003 explicitly chooses coupling — out of default E7)

---

## Files expected to change (E7)

| File | Likely change |
|------|----------------|
| `runner_api_routers/editorial.py` | Additive approve/promote endpoint(s) |
| `runner_api.py` | Router wire only if needed |
| `src/tools/promote_staged.py` | Call from API **or** thin wrapper — prefer subprocess/CLI reuse; minimize edits |
| `src/tools/promotion_audit.py` | Only if FDR requires extra fields (prefer none in E7) |
| `tests/test_editorial_approval.py` (new) | Focused approve tests |
| `docs/migration/editorial-engine/E7_*.md` | Implementation record |
| Optional: templates (read-only link) | Low priority |

**Avoid:** Content Studio contract files, Kanban, readiness field renames, go_live/hashnode, Crew YAML, DB/Alembic.

---

## Maximum blast radius

| Area | Radius |
|------|--------|
| API | Additive Editorial routes only |
| Filesystem | Same as CLI promote (staging → `input/`) when invoked |
| DB | **NONE** expected |
| Auth | Per FDR-002 (string vs Shared Platform) |
| Publishing | **NONE** under FDR-003 A/B default |
| Frozen CS/Kanban/Readiness | Unchanged |

---

## Regression scope

1. New E7 focused tests  
2. `tests/test_editorial_readiness.py`  
3. `tests/test_content_studio_api.py` + UI/Kanban  
4. `tests/test_promotion_audit.py` (if present)  
5. Relevant `tests/test_routers_integration.py`  
6. Full pytest; compare to 265/273 baseline family (8 historical failures)

---

## Rollback strategy

| Step | Action |
|------|--------|
| 1 | Remove new Editorial approve routes / revert `editorial.py` + `runner_api.py` include |
| 2 | Delete new tests/docs |
| 3 | Leave `promote_staged` CLI intact (pre-E7 path) |
| 4 | FS promotions already performed are ops artifacts — do not auto-delete `input/` |

---

## Success criteria

- [ ] FDR-001/002/003 recorded and ADR updated as needed  
- [ ] Approve command works for happy path + explicit errors  
- [ ] No publish/go-live side effects  
- [ ] No DB migrations  
- [ ] Readiness + Content Studio + Kanban tests still green  
- [ ] Focused E7 tests pass  
- [ ] Full regression: no new failures beyond known 8  
- [ ] Architecture UNCHANGED  

---

## If E7 must wait

Run **T1 Ruff** or **Sales/CRM test hardening** per [04_PARALLEL_DEVELOPMENT_GUIDE.md](04_PARALLEL_DEVELOPMENT_GUIDE.md).
