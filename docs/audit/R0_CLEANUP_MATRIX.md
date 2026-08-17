# R0 — Cleanup Matrix

**Date:** 2026-08-11 · **No deletions performed**

Columns: ID · Path · Type · Owner · Classification · Evidence · References · Risk · Action · Confidence · Founder Approval · Rollback

---

## A. SAFE REMOVE CANDIDATES

| ID | Path | Type | Owner | Classification | Evidence | Refs | Risk | Action | Conf | Founder? | Rollback |
|----|------|------|-------|----------------|----------|------|------|--------|------|----------|----------|
| C-01 | `src/artifact_crew.py.old` | backup | Marketing | REMOVE CANDIDATE — HIGH | 0 imports | 0 | None | Delete R1A | HIGH | No | git |
| C-02 | `src/distribution_crew.py.old` | backup | Marketing | REMOVE CANDIDATE — HIGH | 0 imports | 0 | None | Delete R1A | HIGH | No | git |
| C-03 | `src/editor_crew.py.old` | backup | Marketing | REMOVE CANDIDATE — HIGH | 0 imports | 0 | None | Delete R1A | HIGH | No | git |
| C-04 | `src/generation_crew.py.old` | backup | Marketing | REMOVE CANDIDATE — HIGH | 0 imports | 0 | None | Delete R1A | HIGH | No | git |
| C-05 | `src/marketing_crew.py.old` | backup | Marketing | REMOVE CANDIDATE — HIGH | 0 imports | 0 | None | Delete R1A | HIGH | No | git |
| C-06 | `revenue_os/pipeline/` | empty pkg | Revenue | REMOVE CANDIDATE — HIGH | 0 refs | 0 | None | Delete R1A | HIGH | No | git |

**Safe Removal Candidates: 6**

---

## B. ARCHIVE CANDIDATES

| ID | Path | Classification | Action | Conf | Founder? |
|----|------|----------------|--------|------|----------|
| A-01 | `/Users/krishna/Documents/workcrew-cms-os` | KEEP → ARCHIVE | Archive after parity attestation | MED | **YES** |
| A-02 | `/Users/krishna/Documents/CMS_OS_V1` | KEEP → ARCHIVE | Archive docs pack | MED | **YES** |
| A-03 | `output/website-deploy/snapshots/**` | RUNTIME / BACKUP | Keep local; archive off-repo if needed | MED | Optional |
| A-04 | `scripts/bootstrap_remaining_weeks.py` | STALE one-shot | Archive or delete after verify | MED | No |

**Archive Candidates: 4**

---

## C. MOVE / CONSOLIDATE CANDIDATES

| ID | Path | Classification | Action | Conf | Founder? |
|----|------|----------------|--------|------|----------|
| M-01 | `runner_api.py` shadowed `@app` HTML/API | DUPLICATE | Remove after route tests | MED | No |
| M-02 | `ArtifactCrew` + phase2a YAML | DUPLICATE | Merge → GenerationCrew | MED | No |
| M-03 | Hashnode dual clients | DUPLICATE | Consolidate under Publishing | MED | **YES** (channel) |
| M-04 | `/weeks` vs Content Studio nav | DUPLICATE UX | Demote weeks in nav | MED | Optional |
| M-05 | `orchestration_run.html` vs inline | DUPLICATE | Adopt template or delete orphan | MED | No |
| M-06 | Docs indexes | MOVE CANDIDATE (add) | Add INDEX files (not moves) | HIGH | No |
| M-07 | `src/openapi_schemas.py` | NEEDS VERIFICATION | Wire or delete | MED | No |
| M-08 | Root Phase `docs/*.md` | STALE | Quarantine via index | MED | Optional |

**Move/Consolidation Candidates: 8**

---

## D. STALE BUT REFERENCED

| ID | Path | Classification | Action |
|----|------|----------------|--------|
| S-01 | Publishing `_adapter_website` PLACEHOLDER | DEPRECATE — STILL REFERENCED | Future wire sprint |
| S-02 | `POST /go-live` + `go_live_helpers` | DEPRECATE — STILL REFERENCED | Quarantine after Publishing cutover |
| S-03 | `hashnode_publish.py` | DEPRECATE — STILL REFERENCED | Founder channel decision |
| S-04 | `/marketing/publish` + `social_publisher` | DEPRECATE — STILL REFERENCED | Social S1 boundary |
| S-05 | WorkCrew branding strings | STALE RUNTIME | Rename sprint |
| S-06 | `workcrew.ai` in content/marketing | STALE RUNTIME | Domain decision |
| S-07 | StubWebsiteProvider | DEPRECATE — STILL REFERENCED | Keep until tests migrate |
| S-08 | governance `08_NEXT_SPRINT_*` (E7) | STALE | Pointer update |
| S-09 | Architecture_v2.md “current=v2.1” | STALE pointer | Fix banner |
| S-10 | CI install ≠ Docker deps | STALE | Align CI |

**Stale Referenced Items: 10**

---

## E. KEEP — ACTIVE (sample)

Engines listed in HERMES KEEP table; `tracker.csv`; `input/`; primary routers; frozen SEO/Publishing/Website packages; Celery tasks; compose primary path.

---

## F. KEEP — GOVERNANCE / HISTORY

All ADRs, freeze/baseline packs, architecture-audit, migration, runtime-certification, M6 recovery ops, Social S0 / P1 / SEO freeze docs.

---

## G. UNKNOWN / NEEDS VERIFICATION

| ID | Item | Why |
|----|------|-----|
| U-01 | Delete Hashnode now? | Founder channel SoT unclear |
| U-02 | `openai` undeclared transitive | Runtime fragility |
| U-03 | Direct `redis` pin removal | Transitive vs explicit |
| U-04 | Empty alembic `upgrade=pass` migration | Schema reality |
| U-05 | Whether `output/` ever intentionally tracked | Ops evidence |
| U-06 | Render without Celery intentional? | Prod topology |
| U-07 | SDR/CSM route quarantine vs fix | Product use |
| U-08 | Frontend `/app` revive vs retire | Founder UI strategy |

**Unknown / Needs Verification: 8**

---

## Cross-agent conflicts → NEEDS VERIFICATION

1. Hashnode: SCOUT ACTIVE vs HERMES DEPRECATE → **U-01**  
2. `openapi_schemas`: FORGE MEDIUM remove vs possible future wire → **U-07 related / M-07**  
3. Frontend: revive vs archive → **U-08**

**Cross-Agent Conflicts: 3**
