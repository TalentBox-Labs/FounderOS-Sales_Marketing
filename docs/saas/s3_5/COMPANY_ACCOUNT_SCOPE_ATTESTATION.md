# Company / Account Scope Attestation

**Classification:** NOT_IN_SCOPE

## Evidence

1. **No CRM Company routes** — grep of `runner_api_routers/` finds zero `/companies` endpoints.
2. **Company model exists** as sales CRM entity (`revenue_os.models.contact.Company`), linked via `Contact.company_id`.
3. **Company mutation path:** only as side-effect of `POST /contacts/{id}/enrich` when Proxycurl returns employer data — operates on **tenant-scoped contact** first.
4. **Organization ≠ Company** — SaaS tenant boundary is `Organization`; sales Company is customer entity (S2.5 manifest).

## Why NOT_IN_SCOPE

- No list/read/mutation API surface for Company as standalone resource
- No pipeline view for Company
- Sales Company capability remains contact-linked only

## Blocker check

If a live tenant-sensitive Company route existed unguarded → freeze would be BLOCKED.  
**Result:** No such route found. Freeze proceeds.
