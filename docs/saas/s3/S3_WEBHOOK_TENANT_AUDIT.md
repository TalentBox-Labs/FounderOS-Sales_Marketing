# S3 — Webhook Tenant Audit

## Surface

`/webhooks/n8n/*` — authenticated via API key or X-N8N-Secret.

## Status

**LIVE** — mutates Contact by payload `contact_id` without tenant resolution.

## S3 action

**DEFERRED** — safe tenant resolution requires trusted service-to-tenant binding not available without integration-secret redesign. Classified MEDIUM, integration-security sprint.

## Mitigation in S3

Document only. No fake tenant headers from webhook payloads.
