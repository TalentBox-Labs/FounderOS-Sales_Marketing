# S4.5 — Residual Integration Risk Register v1.0

| Risk | Severity | Classification |
|------|----------|----------------|
| Env-backed OpenAI/Gemini agents | MEDIUM | GLOBAL_BY_DESIGN / NOT_MULTI_TENANT_READY |
| n8n outbound (`N8N_WEBHOOK_BASE_URL`) | MEDIUM | GLOBAL_BY_DESIGN |
| Editorial/publishing reads | MEDIUM | GLOBAL_BY_DESIGN (S3.5) |
| Gmail OAuth callback without session | LOW | GLOBAL_BY_DESIGN |
| Legacy unbound n8n dev path | LOW | GLOBAL_BY_DESIGN |

**Critical:** NONE  
**High:** NONE  

Env connectors cannot cause cross-tenant vault credential use on tenant-owned request paths (verified: separate resolution chain).
