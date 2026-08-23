# Agent Ownership Matrix v1.0

**Status:** READY (governance)  
**Sprint:** G2  
**Date:** 2026-08-10  
**Parent:** [PLATFORM_AGENT_REGISTRY.md](PLATFORM_AGENT_REGISTRY.md)  
**Execution:** [MULTI_AGENT_EXECUTION_STANDARD.md](MULTI_AGENT_EXECUTION_STANDARD.md)

Governance only. No code changes.

---

## 1. Purpose

Quick-reference ownership so Coordinators can assign non-overlapping write sets.

---

## 2. Agent × domain matrix

| Domain / Zone | Atlas | Forge | Sentinel | Ledger | Beacon | Hermes | Nova | Pulse | Scout | Cipher |
|---------------|:-----:|:-----:|:--------:|:------:|:------:|:------:|:----:|:-----:|:-----:|:------:|
| Architecture docs / ADRs | **P** | R | R | S | S | R | R | R | R | R |
| Governance freezes / registry | S | R | R | **P** | S | R | R | R | R | S |
| Cross-cutting docs hygiene | R | R | R | S | **P** | R | R | R | R | R |
| Publishing Engine code/tests | R | A | R | R | R | **P** | X | X | X | R |
| Website Engine code/tests | R | A | R | R | R | X | **P** | X | R | R |
| Editorial Engine (when assigned) | R | A | R | R | R | X | X | X | S | R |
| Content Studio (when assigned) | R | A | R | R | R | R | R | X | S | R |
| Analytics | R | A | R | R | R | X | X | **P** | R | R |
| Research artifacts | R | A | R | R | R | X | X | X | **P** | R |
| Security / auth reviews | R | R | R | S | R | R | R | R | X | **P** |
| Full regression execution | R | R | **P** | R | R | R | R | R | R | R |
| Regression audit docs | R | R | **P** | S | S | R | R | R | R | S |
| Secrets / credentials | X | X | X | X | X | X | X | X | X | **P** (review only) |
| DB migrations | R | A* | R | R | R | X | X | A* | X | S |
| Celery / Automation Platform ownership | R | A* | R | R | R | X | X | X | X | S |

**Legend**

| Symbol | Meaning |
|--------|---------|
| **P** | Primary owner (default write authority) |
| A | Allowed when Coordinator assigns Forge (or engine agent) for that sprint |
| A* | Allowed only with explicit Founder/Coordinator approval |
| S | Secondary / scribe support |
| R | Read-only evidence |
| X | Forbidden write |

---

## 3. Path defaults (implementation)

| Path pattern | Default owner agent |
|--------------|---------------------|
| `docs/architecture/**` | Atlas |
| `docs/governance/**` | Ledger (Beacon for UI/docs audits) |
| `docs/marketing/M1*` / Publishing_* | Hermes |
| `docs/marketing/M2*` / `M3*` / Website_* | Nova |
| `src/tools/publishing_engine.py` | Hermes |
| `runner_api_routers/publishing.py` | Hermes |
| `templates/publishing_*.html` | Hermes |
| `tests/test_publishing_engine.py` | Hermes (+ Sentinel runs) |
| `src/tools/website_engine/**` | Nova |
| `tests/test_website_engine.py` / `test_static_provider.py` | Nova |
| `src/tools/editorial_approval.py` / editorial routers | Forge under Editorial assignment (not Hermes/Nova) |
| `runner_api_routers/analytics*.py` | Pulse |
| `tests/**` (execution) | Sentinel |
| `*_REGRESSION_AUDIT.md` | Sentinel |

---

## 4. Conflict pairs (do not parallel-write)

| Pair | Risk |
|------|------|
| Hermes ↔ Nova | Publishing adapter vs Website provider wire |
| Hermes ↔ Editorial Forge | Approval vs publish job creation |
| Atlas ↔ Ledger | ADR Accept vs freeze summary wording — serialize |
| Forge ↔ Sentinel | Sentinel must not edit Forge code while testing unless assigned |
| Cipher ↔ Forge on auth files | Serialize; Cipher reviews first |

---

## 5. Escalation quick map

| Issue | First agent | Then |
|-------|-------------|------|
| Architecture law | Atlas | Founder |
| Freeze / FDR | Ledger | Founder |
| Publish orchestration bug | Hermes | Coordinator |
| Website/static bug | Nova | Coordinator |
| New test failures | Sentinel | Forge/Hermes/Nova |
| Secret/auth | Cipher | Founder |
| Docs drift | Beacon | Atlas/Ledger |

---

## 6. Approval chain (short)

Agent → Coordinator → Engine owner → Sentinel → Ledger (freeze) → Founder (gates / Architecture Accept)

---

## 7. Impact (G2)

| Dimension | Impact |
|-----------|--------|
| Architecture | PASS (docs only) |
| Code | 0 |
| Runtime | NONE |
