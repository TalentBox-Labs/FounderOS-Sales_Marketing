# Sales OS — Integration Disposition

**Sprint:** SALES A1  
**Date:** 2026-08-13  
**Status:** COMPLETE — 14/14 classified  
**Source:** SALES A0 integration audit (I01–I14)

Classifications: **RETAIN_CORE** · **RETAIN_OPTIONAL** · **DEFER** · **RETIRE**

Nothing activated in A1. No new paid tools.

---

## Disposition table

| ID | Integration | Class | Purpose | Current state | Sales dependency | Credentials | External setup | Paid/free | Replacement risk | Lock-in risk |
|----|-------------|-------|---------|---------------|------------------|-------------|----------------|-----------|-------------------|--------------|
| I01 | PostgreSQL / SQLAlchemy | **RETAIN_CORE** | CRM entity persistence | IMPLEMENTED | Hard | `DATABASE_URL` | Yes (DB) | Free (infra) | High | Low |
| I02 | Runner API-key auth | **RETAIN_CORE** | CRM/prospecting API gate | IMPLEMENTED | Hard | API key env | Yes | Free | Medium | Low |
| I03 | JWT stack (`revenue_os.main`) | **DEFER** | Parallel full CRUD API | PARTIAL | Medium | JWT/user | Yes | Free | Medium — consolidate later | Low |
| I04 | n8n workflows | **RETAIN_OPTIONAL** | Approved outreach delivery | PARTIAL | Medium (send path) | `N8N_*` | Yes | Free (self-host) | Medium | Medium |
| I05 | SMTP notifier | **RETAIN_OPTIONAL** | Email transport | PARTIAL | Low | SMTP config | Yes | Free | Low | Low |
| I06 | Gmail API path | **RETAIN_OPTIONAL** | Email read/sync | PARTIAL | Low | `GMAIL_CREDENTIALS_PATH` | Yes | Free tier | Low | Medium |
| I07 | Proxycurl (LinkedIn enrich) | **RETAIN_OPTIONAL** | Person/company enrich | PARTIAL | Optional enrich | Vault key | Yes | **Paid** if enabled | Low | Medium |
| I08 | RevenueOS LinkedIn UGC publisher | **RETIRE** | Legacy social publish | DEAD/adjacent | **None** for Sales CRM | LI tokens | N/A | Free API | N/A — Marketing Social owns | Medium |
| I09 | Google Calendar | **RETAIN_OPTIONAL** | Meeting scheduling | PARTIAL | Optional | OAuth creds | Yes | Free tier | Low | Medium |
| I10 | WhatsApp community | **DEFER** | Community/marketing adjacent | PARTIAL | Low for core Sales | Config | Yes | Variable | Low | Medium |
| I11 | ChromaDB search | **RETAIN_OPTIONAL** | CRM search index | PARTIAL | Optional | Persist dir | Optional | Free (local) | Low | Low |
| I12 | OpenAI / Gemini | **RETAIN_CORE** | Sales agent assists (via AI Platform) | PARTIAL | Medium | API keys | Yes | **Paid** usage | High | Medium |
| I13 | Credentials vault | **RETAIN_CORE** | Connector secret storage | PARTIAL | Hard | Vault master | Yes | Free | High | Low |
| I14 | HubSpot / Salesforce / Pipedrive | **DEFER** | External CRM sync | NOT_IMPLEMENTED | None today | N/A | N/A | N/A | N/A until required | High if added |

---

## Summary counts

| Class | Count |
|-------|------:|
| RETAIN_CORE | **4** |
| RETAIN_OPTIONAL | **6** |
| DEFER | **3** |
| RETIRE | **1** |
| **Total** | **14** |

**External Integrations Classified: 14/14**

---

## Notes

- Existence of integration code alone does not justify RETAIN_CORE — I08 retired despite code presence.
- I12 consumed through **AI Platform** boundary; Sales must not embed provider logic duplicatively long-term.
- I07 paid dependency requires Founder approval before production enable (Toolchain Baseline).

No integrations activated in A1.
