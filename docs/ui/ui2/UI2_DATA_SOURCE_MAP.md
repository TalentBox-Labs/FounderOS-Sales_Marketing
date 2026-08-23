# UI2 — Data Source Map

**Sprint:** UI2  
**Date:** 2026-08-13

| Panel | Authoritative OS | SoT | Query/API | Read-only aggregate | Mutation | Authority |
|-------|----------------|-----|-----------|---------------------|----------|-----------|
| Attention — QualifiedDemand | Cross (MC04) | `AgentActionLog` | `_load_pending_qualified_demands()` | Yes | Accept via cockpit proxy | Server operator + MC04.5 |
| Attention — high score contacts | Sales | `Contact` | ORM read | Yes | Status via cockpit proxy | Server operator + A4.5 |
| Attention — editorial | Marketing | Editorial JSONL/staging | `build_editorial_pending()` | Yes | Link only | N/A |
| Attention — publishing | Marketing | Publishing engine | `pe.list_queue()` | Yes | Link only | N/A |
| Sales snapshot | Sales | `Contact`, `Deal` | ORM counts | Yes | None | N/A |
| Marketing/SEO | Marketing | SEO engine artifacts | `analyze_site()`, `analyze_technical_site()` | Yes | None | N/A |
| Social status | Marketing | Governance docs | Static honest blocked state | N/A | None | BLOCKED |
| Commercial flow | Cross | Composed read | Derived from panels | Yes | None | N/A |
| Governance | Platform | Scheduler + docs | `scheduler.status()`, static baselines | Yes | None | N/A |

**New SoT:** NO  
**Frontend-derived canonical state:** NO  
**Caching:** NO (live read per request)
