# R0 — Legacy / Migration Remnants (SCOUT)

**Date:** 2026-08-11 · **Mode:** AUDIT ONLY

---

## Local reference repos (OUTSIDE this tree)

| Path | Status | Recommendation |
|------|--------|----------------|
| `/Users/krishna/Documents/workcrew-cms-os` | EXISTS (~large Flask CMS) | **KEEP** → ARCHIVE when Founder declares parity |
| `/Users/krishna/Documents/CMS_OS_V1` | EXISTS (docs pack, 0 py) | **KEEP** → ARCHIVE |
| `Workcrew_CMS_OS` path | ABSENT | Name mismatch only |

**DO NOT DELETE in R0.** Requires Founder decision for archive timing.

---

## Remnant classes (in-repo)

| Theme | Class | Examples |
|-------|-------|----------|
| WorkCrew CMS branding | ACTIVE COMPATIBILITY + FOUNDER DECISION | API title, templates, README |
| `workcrew.ai` hosts | STALE RUNTIME + FOUNDER DECISION | marketing crew defaults, content FM |
| Hashnode publish | ACTIVE COMPATIBILITY + FOUNDER DECISION (retire?) | `hashnode_publish.py` |
| Sheets mirror tools | ACTIVE COMPATIBILITY (not SoT) | `sheet_sync*` |
| Publishing PLACEHOLDER / NOT_IMPLEMENTED | ACTIVE COMPATIBILITY (contracts) | `publishing_engine.py` |
| `src/*.py.old` | **SAFE REMOVE CANDIDATE** | 5 files |
| Flask in this repo | ABSENT | CMS sibling only |
| Dual marketing handlers | STALE RUNTIME | `runner_api.py` duplicates |
| Historical `revenue_os.agents.marketing_crew` | HISTORICAL DOCUMENTATION | Fixed to `src.marketing_crew` |

---

## Founder decisions required (legacy)

1. Brand rename WorkCrew → Founder OS  
2. Domain/`workcrew.ai` content migration  
3. Hashnode retention vs Website Engine SoT  
4. Archive timing for CMS sibling trees  
5. Infra rename `workcrew-crm*`

**Legacy Migration Remnants (distinct findings tracked):** **28** (branding surfaces, host refs, tools, docs citations, sibling repos, stubs, naming).
