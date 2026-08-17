# 04 — Retirement Plan

Analysis only. **Do not delete anything in this sprint.**

Legend: **KEEP UNTIL MIGRATION** | **SAFE TO REMOVE** (future, after validation) | **RETIRE AFTER SLICE** |

---

## Transitional components

| Component | Role today | Mark | Evidence |
|-----------|------------|------|----------|
| `runner_api.py` duplicate `@app` HTML/API handlers | Overlap with included routers | KEEP UNTIL MIGRATION | Router inventory A.6; first-registered router wins |
| `runner_api_routers/marketing.py` module string `revenue_os.agents.marketing_crew` | Stale generate path | KEEP UNTIL MIGRATION → fix in Slice 0 then retire stale string | Module file absent; `src.marketing_crew` exists |
| `runner_api.py` `@app.post("/marketing/generate")` using `src.marketing_crew` | Compatibility path | KEEP UNTIL MIGRATION (until router path corrected and duplicates removed) | Dual paths evidenced |
| `revenue_os.integrations.webhooks` empty `APIRouter` on `revenue_os.main` | Import compatibility / empty mount | KEEP UNTIL MIGRATION | GAP-010 A.6: manager used by integrations router; empty router on secondary app |
| `src/*.py.old` crew backups | Historical copies | SAFE TO REMOVE (after confirming no imports) | Five `.old` files; not imported by name |
| CMS Flask `dashboard/app.py` (documented locus) | CMS publishing portal | KEEP UNTIL MIGRATION (as reference until Slices 1 & 3 done) | CMS_OS_V1 + sibling dashboard |
| CMS OpenClaw agent SOUL directories | Persona/process packs | KEEP UNTIL MIGRATION (as playbook source) | `AGENTS.md` |
| CMS n8n workflow JSON library | Automation assets | KEEP UNTIL MIGRATION | CMS docs + sibling `n8n-workflows/` |
| Founder Jinja pipeline/weeks UI | Ops UI | KEEP UNTIL MIGRATION (until Content Studio replaces) | `templates/`, UI router |
| Google Sheets legacy tracker ID in CMS TOOLS.md | Deprecated tracker | RETIRE AFTER SLICE (ops cutover) | CMS `TOOLS.md` marks legacy sheet deprecated |

---

## Legacy / duplicate modules (Founder)

| Item | Future deletion candidate | Condition |
|------|---------------------------|-----------|
| Duplicate prospecting/orchestration/marketing `@app` handlers in `runner_api.py` | Yes | After single router ownership proven by tests |
| Stale marketing module path string | Yes | After Slice 0 |
| Empty webhooks `APIRouter` if secondary app unused | Yes | If `revenue_os.main` not deployed |
| `src/*.py.old` | Yes | After no references |
| Parallel social publish implementations (post-merge) | Possible | After Social/Publishing Engine consolidation leaves one client |

---

## Stale imports / references

| Reference | Classification | Evidence |
|-----------|----------------|----------|
| `revenue_os.agents.marketing_crew` | Stale import / incomplete migration | Included marketing router subprocess |
| CMS Google Sheets legacy ID | Legacy | `TOOLS.md` |
| OpenClaw workspace paths in CMS recovery doc | Legacy host paths | `README_RECOVERY.md` `/root/.openclaw/...` |

---

## CMS-side retirement (after capability migration into Founder)

Do not delete CMS trees in this sprint. Future candidates once Founder slices absorb capabilities:

| CMS capability locus | Retire when |
|----------------------|-------------|
| Flask dashboard publish APIs | Founder Publishing + Content Studio validated |
| Per-platform n8n workflows duplicated in Founder | Founder Automation owns imported workflows |
| OpenClaw agent runtime (if never adopted) | Explicit decision to DEFER permanently |
| Duplicate content copies outside Founder `input/` | Content Studio cutover complete |

---

## Adapters expected during migration (temporary)

| Adapter type | Mark |
|--------------|------|
| n8n webhook URL env bridge (already in Founder) | KEEP UNTIL MIGRATION |
| CMS publish API client wrapper inside Founder (if introduced in later sprints) | KEEP UNTIL MIGRATION |
| Content ID mapping (CMS `W01-001` ↔ Founder week IDs) | KEEP UNTIL MIGRATION |

---

## Explicit non-retirement

| Item | Reason |
|------|--------|
| Founder `revenue_os` CRM/sales/CSM | No CMS equivalent; KEEP FOUNDER |
| Founder CrewAI crews | Canonical AI Platform |
| Founder Docker/Compose stack | Canonical Shared/Operations runtime |
| Architecture Baseline docs under `docs/architecture-audit/` | Frozen evidence package |
