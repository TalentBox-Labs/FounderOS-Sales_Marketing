# SEO Domain Decision — Pending Founder Ratification

**Record type:** Governance / Ledger  
**Agent:** LEDGER  
**Sprint:** S0  
**Related:** FDR-N05 (`docs/governance/FDR_N05_PRODUCTION_WEBSITE_DOMAIN.md`)  
**Date:** 2026-08-11

---

## 1. Founder decisions (S0)

| Item | Decision |
|------|----------|
| **`workcrew.ai`** | **NOT AUTHORIZED** for future Founder OS production use as canonical origin |
| **`founderos-staging.pages.dev`** | **TEMPORARY INFRASTRUCTURE HOST ONLY** — not the future branded canonical origin |
| **Future production domain** | **PENDING FOUNDER RATIFICATION** — must not be guessed by engineering |

---

## 2. Implications

- Engineering must not treat `workcrew.ai` as the target canonical domain in new configuration.
- Engineering must not treat `founderos-staging.pages.dev` as the long-term branded origin.
- Historical M-Series certification documents, deployment evidence, and frozen baselines **are not rewritten**.
- Content bundles may retain historical `canonical_url: https://workcrew.ai/blog/...` until a deliberate migration slice.
- Production SEO activation remains blocked until FDR-N05 is closed with a ratified domain.

---

## 3. Authorized engineering posture

| Action | Allowed |
|--------|---------|
| Configurable origin via `FOUNDER_SITE_ORIGIN` | ✅ |
| Placeholder default `https://example.invalid` | ✅ |
| SEO readiness development on non-production origins | ✅ |
| DNS changes | ❌ |
| Search Console setup | ❌ |
| Declaring a production domain without Founder ratification | ❌ |

---

## 4. Ratification path (Founder)

1. Select production domain (registrar, DNS authority, brand alignment).
2. Record decision in FDR-N05 (close open status).
3. Set `FOUNDER_SITE_ORIGIN` to ratified origin in production environment.
4. Set `FOUNDER_SITE_ORIGIN_RATIFIED=1` only after DNS/TLS cutover plan approved.
5. Run domain migration test plan (`docs/marketing/N0_5_DOMAIN_MIGRATION_TEST_PLAN.md`).

---

## 5. Historical evidence preservation

The following remain valid **historical** records of M-Series state at freeze time:

- `docs/operations/FOUNDER_OS_WEBSITE_V1_PRODUCTION_BASELINE.md`
- `docs/marketing/M_SERIES_COMPLETION.md`
- M6/M7 deployment and smoke-test reports referencing `workcrew.ai` and `founderos-staging.pages.dev`

S0 adds this ledger; it does not amend prior frozen documents.

---

## 6. Status

| Field | Value |
|-------|-------|
| FDR-N05 | OPEN |
| Production SEO | BLOCKED |
| SEO Engine development | ALLOWED (non-production origins) |
