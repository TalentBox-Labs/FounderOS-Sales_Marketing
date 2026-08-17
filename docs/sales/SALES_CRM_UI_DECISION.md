# Sales OS — CRM UI Architecture Decision

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Status:** DECIDED  
**ADR:** [Architecture_ADR_004.md](../architecture/Architecture_ADR_004.md)

A0: **Existing CRM UI: UNMOUNTED**

---

## Evidence summary

| Factor | Finding |
|--------|---------|
| Source | `frontend/` (`workcrew-crm-frontend`) — 17 pages, React 18 + Vite 5 |
| Build | Script exists; `frontend/dist` **absent** locally |
| Mount | `runner_api.py` mounts `/app` iff dist exists; else **503** |
| Nav | Jinja shell links `/sales`, **not** `/app` |
| Backend assumption | Same-origin `runner_api` `/api/v1/crm/*` — **aligned** with primary gateway |
| Gap | Runner CRM lacks deal **stage update** API; SPA kanban non-writable |
| Docker | Builds dist in image — not abandoned |
| Dual stack | SPA does not use JWT `revenue_os.main` — good for consolidation target |

---

## Decision

**CRM UI Disposition: RETAIN_AND_REFACTOR_LATER**

### Rationale

1. **RETAIN** — Substantial reusable asset; not dead code.  
2. **Not RETAIN_AND_MOUNT_LATER alone** — mounting today would expose read-only/partial CRM without stage APIs and before Sales/Revenue adapter consolidation.  
3. **Not REBUILD_LATER** — Jinja `/sales` covers prospecting; full CRM rebuild would duplicate SPA value.  
4. **Not RETIRE** — Would discard 17 screens and `frontend/src/api.js` contract work.

**Refactor later** means: align SPA with canonical Sales/Revenue contracts, add runner (or Sales facade) stage mutation APIs, human gates for mutations, then build dist + optional nav link.

---

## Founder Internal UI Shell (future)

| Surface | Role |
|---------|------|
| `/sales` | **Live** — Prospecting / SDR ops (Jinja) — remains Sales entry |
| `/app` | **Future** — Full CRM SPA when mounted post-refactor |
| `/pipeline` | **Marketing** content pipeline — never Sales deal pipeline |
| Nav | Add `/app` or “CRM” only when dist + contract ready |

Target: single shell (`base.html`) with Sales prospecting + optional CRM sub-app — not parallel unlinked SPA.

---

## Explicit A1 prohibitions (honored)

- Do **not** mount `/app`  
- Do **not** redesign UI  
- Do **not** build replacement UI  

---

## Verdict

**CRM UI Disposition: RETAIN_AND_REFACTOR_LATER**
