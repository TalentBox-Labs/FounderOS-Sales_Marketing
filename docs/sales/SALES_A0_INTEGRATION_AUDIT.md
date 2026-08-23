# SALES A0 — Integration Audit (CIPHER)

**Sprint:** SALES A0  
**Date:** 2026-08-13  
**Mode:** AUDIT ONLY — no external activation

---

## Inventory

| ID | Integration | Class | Evidence | Setup |
|----|-------------|-------|----------|-------|
| I01 | PostgreSQL / SQLAlchemy CRM DB | **IMPLEMENTED** | `revenue_os/database.py`, models | CONFIGURATION REQUIRED (DB up) |
| I02 | API-key auth (runner CRM) | **IMPLEMENTED** | `_verify_api_key` on CRM routes | CONFIGURATION REQUIRED |
| I03 | JWT auth (`revenue_os.main`) | **PARTIAL** | Parallel stack; not primary runner | CONFIGURATION REQUIRED |
| I04 | n8n outbound email / workflows | **PARTIAL** | `integrations/n8n.py`; approvals handoff | CONFIGURATION REQUIRED |
| I05 | SMTP email notifier | **PARTIAL** | `integrations/email.py` | CONFIGURATION REQUIRED |
| I06 | Gmail credentials path | **PARTIAL** | config `GMAIL_CREDENTIALS_PATH` | CONFIGURATION REQUIRED |
| I07 | LinkedIn enrichment (Proxycurl) | **PARTIAL** | `linkedin_enrichment.py` | CONFIGURATION REQUIRED |
| I08 | LinkedIn UGC publisher (RevenueOS) | **DEAD_CODE** / adjacent | `social_publisher.LinkedInPublisher` — not Marketing SoT; not Sales CRM path | Do not activate as Sales |
| I09 | Google Calendar | **PARTIAL** | `integrations/calendar.py` | CONFIGURATION REQUIRED |
| I10 | WhatsApp community tooling | **PARTIAL** | `whatsapp_community.py` + SPA Marketing | CONFIGURATION REQUIRED |
| I11 | ChromaDB search index | **PARTIAL** | RAG/search persist dir | Optional |
| I12 | OpenAI / Gemini (sales agents) | **PARTIAL** | config keys; agents consume AI | CONFIGURATION REQUIRED |
| I13 | Credentials vault | **PARTIAL** | `credentials_vault.py` | CONFIGURATION REQUIRED |
| I14 | HubSpot / Salesforce / Pipedrive | **NOT_IMPLEMENTED** | No provider adapters found | — |

**External Integrations: 14** (inventoried rows)  
**External Setup Required: 8** (I01–I07, I09–I10, I12–I13 counted as needing config for production Sales — consolidate to **8** core: DB, API key, n8n, SMTP/Gmail, Proxycurl, Calendar, WhatsApp, LLM keys)

Core setup list (8):

1. Database  
2. Runner API key  
3. n8n (outreach delivery)  
4. Email (SMTP and/or Gmail)  
5. Proxycurl (enrichment)  
6. Calendar (optional meetings)  
7. LLM keys (agents)  
8. Vault/connector secrets hygiene  

---

## CRM provider note

No third-party CRM sync. Founder CRM **is** the in-repo SQL model under `revenue_os`.

---

## Paid tools

No new paid aggregator required for A0. Proxycurl is optional enrichment (external commercial API if enabled later — Founder approval).
