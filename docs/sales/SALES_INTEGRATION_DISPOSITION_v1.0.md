# Sales Integration Disposition v1.0

**STATUS: FROZEN**  
**VERSION: v1.0**  
**Sprint:** SALES A1.5  
**Date:** 2026-08-13  
**Source:** [SALES_INTEGRATION_DISPOSITION.md](SALES_INTEGRATION_DISPOSITION.md) (A1) — 14/14

**Does not:** authenticate, activate, purchase, or commit credentials.

---

## Frozen totals

| Class | Count |
|-------|------:|
| RETAIN_CORE | **4** |
| RETAIN_OPTIONAL | **6** |
| DEFER | **3** |
| RETIRE | **1** |
| **Total** | **14** |

**External Integrations Activated: 0**

---

## Frozen register

| ID | Name | Repository presence | Disposition | Owning OS | Activation | Credential requirement | Future decision gate |
|----|------|---------------------|-------------|-----------|------------|------------------------|----------------------|
| I01 | PostgreSQL / SQLAlchemy | `revenue_os/database.py`, models | **RETAIN_CORE** | Revenue (SoT) / Shared infra | Active when DB configured | `DATABASE_URL` | Ops only |
| I02 | Runner API-key auth | `runner_api_routers` + utils | **RETAIN_CORE** | Shared Platform | Active when key set | API key env | Auth freeze respect |
| I03 | JWT stack (`revenue_os.main`) | `revenue_os/api/v1/*` | **DEFER** | Revenue / Sales dual | Not primary runner | JWT | Consolidation sprint |
| I04 | n8n workflows | `integrations/n8n.py` | **RETAIN_OPTIONAL** | Automation Platform | Inactive until configured | `N8N_*` | Founder enable |
| I05 | SMTP notifier | `integrations/email.py` | **RETAIN_OPTIONAL** | Shared / Sales ops | Inactive until configured | SMTP | Founder enable |
| I06 | Gmail API path | config + sync paths | **RETAIN_OPTIONAL** | Shared | Inactive until configured | `GMAIL_CREDENTIALS_PATH` | Founder enable |
| I07 | Proxycurl LinkedIn enrich | `linkedin_enrichment.py` | **RETAIN_OPTIONAL** | Sales (enrich) | Inactive until configured | Vault key | **Paid** — Founder + Toolchain |
| I08 | RevenueOS LinkedIn UGC publisher | `social_publisher.py` | **RETIRE** | Marketing Social SoT | Must not activate as Sales | — | Marketing Social path only |
| I09 | Google Calendar | `integrations/calendar.py` | **RETAIN_OPTIONAL** | Sales ops optional | Inactive until configured | OAuth | Founder enable |
| I10 | WhatsApp community | `whatsapp_community.py` | **DEFER** | Marketing-adjacent | Not Sales core | Config | Product decision |
| I11 | ChromaDB search | RAG/search | **RETAIN_OPTIONAL** | Shared / AI | Optional local | Persist dir | Optional |
| I12 | OpenAI / Gemini | AI config + agents | **RETAIN_CORE** | AI Platform | Usage when keys set | API keys | **Paid** usage — Founder |
| I13 | Credentials vault | `credentials_vault.py` | **RETAIN_CORE** | Shared Platform | Local when configured | Vault master | Security hygiene |
| I14 | HubSpot / Salesforce / Pipedrive | None | **DEFER** | Future adapter | NOT_IMPLEMENTED | N/A | Explicit product ADR |

---

## Change control

Reclassifying any integration requires ADR amendment to ADR-005 / this freeze. Existence of code alone does not authorize RETAIN_CORE or activation.
