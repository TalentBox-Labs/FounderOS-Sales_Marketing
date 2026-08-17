# S3 — CRM Read Isolation

## Scoped list endpoints

- `GET /contacts` — `apply_contact_org_filter`
- `GET /deals` — `apply_deal_org_filter`
- Search/filter params applied **after** server org scope

## Scoped get endpoints

- `GET /contacts/{id}` — `scoped_contact` + scoped related deals/activities
- `GET /deals/{id}` — `scoped_deal` + scoped contact/activities

## Aggregates

- `GET /pipeline` — `get_pipeline_health(organization_id=...)`
- `GET /followups` — `get_followups(organization_id=...)`

## Activities

- List filtered by tenant-linked contact/deal when org resolved
- `contact_id` / `deal_id` query params validated via scoped lookup first
