# Website Engine Technical Debt Registry

**Owner layer:** Website Engine  
**Maintained for:** Marketing OS governance / SEO integration  
**Last updated:** 2026-08-11 (S2.5 freeze)

---

## WEBSITE-SEO-ROBOTS-001

| Field | Value |
|-------|-------|
| **ID** | `WEBSITE-SEO-ROBOTS-001` |
| **Capability** | `robots.txt` + page-level robots meta generation |
| **Owner** | Website Engine |
| **Discovered by** | Technical SEO Engine S2 / S2.1 |
| **Detector finding** | `tech_robots_txt_absent`, `tech_robots_meta_absent`, `tech_robots_accidental_index_risk` |
| **Severity** | **MEDIUM** |
| **Status** | **DEFERRED** |
| **Blocks Technical SEO Engine v1.0 freeze** | **NO** |
| **Blocks Production SEO Activation** | Evaluate separately after production domain ratification (likely required for safe public indexing) |

### Observed

- Website Engine `wrap_html_document` does not emit `<meta name="robots">`  
- Static provider does not write `robots.txt`  
- Pages with deprecated/infrastructure canonicals lack `noindex` → accidental index risk warning

### Expected future work

1. robots.txt generation policy (staging vs production)  
2. Page robots metadata generation  
3. Staging / unratified-origin indexing protection (`noindex` or edge `X-Robots-Tag`)  
4. Sitemap declaration policy alignment with robots  
5. Website Engine unit/integration tests  
6. Re-validation via Technical SEO Engine (consume frozen Technical SEO v1.0; do not rewrite it)

### Ownership boundary

SEO Engine **detects** gaps. Website Engine **owns** generation. Do not implement robots emission inside SEO Engine.

### Implementation sprint

**Not assigned** by S2.5. Requires separate Website Engine / deploy-safety prioritization after Marketing OS priority review and/or domain ratification planning.

---

## Index

| ID | Severity | Status |
|----|----------|--------|
| WEBSITE-SEO-ROBOTS-001 | MEDIUM | DEFERRED |
