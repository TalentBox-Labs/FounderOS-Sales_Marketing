# M2.5 — Website Engine Core Baseline Freeze Summary

**Date:** 2026-08-10  
**Sprint type:** Certification / governance only  
**Architecture:** v2.1 / ADR-002 (FROZEN)  
**Agents:** [A — Contract Freeze](9041b382-adc9-471c-959c-e24a6df5559c) · [B — Provider Readiness](1b2e8419-6683-41ab-ad8b-cccdea8063d8) · [C — Regression Audit](97acadd0-6145-4f70-8ae2-8d408d2e1af1)

**Code / runtime / DB / provider implementation changes:** **NONE**

---

## Baseline status

| Item | Status |
|------|--------|
| Website Engine Core v1.0 | **FROZEN** |
| Publishing Engine v1.0 | Unchanged (orchestration-only; website adapter PLACEHOLDER) |
| Architecture v2.1 | Authoritative |
| Cross-agent file conflicts | **0** |

---

## Contracts frozen

Document: [M2_5_WEBSITE_ENGINE_BASELINE.md](M2_5_WEBSITE_ENGINE_BASELINE.md)

1. Canonical website content model  
2. Provider-neutral publication interface  
3. Slug / canonical URL contract  
4. Metadata contract  
5. Render contract  
6. Sitemap contract  
7. RSS contract  
8. Website publish result contract  

---

## Tests

| Suite | Result |
|-------|--------|
| Focused (website + publishing + editorial + content studio) | **60/60** |
| Full regression | **308/320**; **8** failed; **4** errors |
| New regressions vs M2 | **0** |
| Historical failures | Unchanged (crews 3, utilities 5, orchestration 2 err, prospecting 2 err) |

Audit: [M2_5_ARCHITECTURE_REGRESSION_AUDIT.md](M2_5_ARCHITECTURE_REGRESSION_AUDIT.md)

---

## Architecture

**PASS** — Publishing orchestration-only; Website Engine owns website behavior; no SEO Engine / Social / Campaign / external HTTP / DB / API contract regressions.

---

## Provider recommendation

Document: [M2_5_WEBSITE_PROVIDER_READINESS.md](M2_5_WEBSITE_PROVIDER_READINESS.md)

**Recommended First Provider:** **STATIC**

Promote existing M2 stub (`output/website/` from `input/{week}/` Markdown) into a static-site adapter before WordPress/Ghost self-hosted HTTP adapters.

---

## Rollback boundary

Governance-only sprint: remove or supersede M2.5 docs if needed.  
No application rollback required (no code changes in M2.5).  
M2 Website Engine Core code remains as previously shipped; freeze docs certify it.

---

## Next sprint

**M3 — Website Provider Adapter** (STATIC first), without expanding frozen Core contracts unless a new baseline is opened.

---

## Final verdict

**READY FOR M3 WEBSITE PROVIDER ADAPTER**
