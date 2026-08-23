# SALES A2 — Workflow Gap Map

**Sprint:** SALES A2  
**Date:** 2026-08-13  
**Lifecycle language:** Frozen A1 domain (Contact/Deal/Pipeline ops) — not invented generic CRM stages

---

## Founder Sales lifecycle (repository)

```
Prospect / capture → Qualify (score) → Engage (activity/outreach) → Open Deal
  → Pipeline stage ops → Close (won/lost) → Revenue / CS handoff
```

Manual intake via runner CRM / Jinja prospecting is the **current** entry (Marketing `QualifiedDemand` not implemented).

---

## Stage map

| Stage | Required capability | Status | UI | API | Persist | Manual workaround | Missing dep | Cross-OS | Impact if absent |
|-------|---------------------|--------|----|----|---------|-------------------|-------------|----------|------------------|
| Capture / prospect | C01–C03, C02 | LIVE | `/sales` | LIVE | DB | Manual contact create | — | — | Low — operable |
| Qualify | C12 | LIVE PARTIAL gate | API | LIVE | DB | Manual status | Human gate gap | Rev Contact.status | Medium — auto-status debt |
| Engage | C07–C09, C11 | LIVE | `/sales`/SPA | LIVE | DB | Manual notes | Send needs n8n | Approvals Rev | Medium for send |
| Open Deal | C05, C13 | PARTIAL / LIVE | SPA unmounted | Create YES | DB | API create | Stage path | Rev Deal SoT | Medium |
| **Pipeline stage ops** | **C20 / MC05** | **API_ONLY / MISSING on runner** | Display-only SPA | JWT PUT only | DB | SQL / JWT app / recreate deal | Runner PATCH | Sales ops / Rev entity | **HIGH — largest break** |
| Close | MC06 / JWT CLOSED_WON | PARTIAL | No | JWT path | DB | Manual DB/JWT | Stage ops first | CommercialOutcome | High after stages |
| CS / revenue handoff | C17, MC06 | LIVE read / MISSING write | SPA | Health API | computed | Manual CS | Outcome event | Revenue | Medium |
| Marketing demand in | MC04 | MISSING | No | No | No | Manual contact | Contract emitter | Marketing | Medium — not blocking ops today |

---

## Largest workflow breaks (ranked)

1. **Cannot advance Deal.stage on primary runner CRM** (C20/MC05) — pipeline ops blocked for Founder OS shell path.  
2. **No Marketing→Sales automated intake** (MC04) — compensated by manual capture.  
3. **No closed-won CommercialOutcome → Client/Customer** (MC06) — premature without (1).  
4. **Outreach send external** (C10) — approvals exist; n8n CONFIG REQUIRED.  
5. **CRM SPA unmounted** (C18) — UX gap; frozen RETAIN_AND_REFACTOR_LATER; not first unblocker if API stage works.

**Workflow Gaps Identified: 5** (major breaks above)

---

## Implication for A3

Closing gap (1) maximizes COMPLETE/CONNECT reuse (`advance_deal_stage`, JWT PUT) without Marketing implementation or CRM mount.
