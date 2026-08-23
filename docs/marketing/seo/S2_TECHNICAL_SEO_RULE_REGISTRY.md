# S2 — Technical SEO Rule Registry

**Sprint:** S2 Phase 1  
**Agent:** HERMES  
**Implementation:** `src/tools/seo_engine/technical/`  
**S1.5 readiness contract:** UNCHANGED

---

## Summary

| Metric | Count |
|--------|-------|
| Check families | **10** |
| Technical rule IDs | **72** |

Technical scoring is **independent** of frozen S1 readiness scoring.

```
tech_score = max(0, 100 - 35*CRITICAL - 20*ERROR - 6*WARNING)
```

DOMAIN_BLOCKED does not reduce score; it gates overall status.

---

## Families

1. **CANONICAL** — existence, syntax, identity, duplicates, deprecated/infra/placeholder hosts, unratified origin  
2. **ROBOTS** — page meta, conflicts, accidental index risk, robots.txt presence (site)  
3. **SITEMAP** — parseability, duplicates, hosts, eligibility, noindex inclusion  
4. **STRUCTURED_DATA** — JSON parse, @context/@type, URL consistency  
5. **OPEN_GRAPH** — core fields, og:url integrity (og:image N/A)  
6. **INTERNAL_LINKS** — malformed, broken (local), deprecated/infra hosts, orphans  
7. **CRAWLABILITY** — local evidence only (canonical + sitemap + robots)  
8. **HTTP_ROUTING** — missing index.html, malformed slugs, empty inventory  
9. **FEED** — RSS parse, duplicates, host/origin, canonical conflicts  
10. **CONSISTENCY** — canonical↔sitemap, canonical↔OG, noindex↔sitemap  

---

## Severity / blocking

| Severity | Blocks overall? | Score impact |
|----------|-----------------|--------------|
| DOMAIN_BLOCKED | Yes (highest) | 0 |
| CRITICAL | Yes | −35 |
| ERROR | Yes | −20 |
| WARNING | Soft | −6 |
| INFO / PASS / NOT_APPLICABLE | No | 0 |

---

## Ownership tags

| Tag | Meaning |
|-----|---------|
| SEO_ENGINE | Analysis signal / PASS |
| WEBSITE_ENGINE | Output/markup gap |
| CONTENT | Bundle/FM issue |
| DOMAIN | Governance / origin |
| EXPECTED | Intentional (e.g. noindex) |

Full rule ID list is emitted in engine findings (`tech_*`). Representative IDs:

`tech_canonical_*`, `tech_robots_*`, `tech_sitemap_*`, `tech_jsonld_*`, `tech_og_*`, `tech_link_*`, `tech_crawl_*`, `tech_route_*`, `tech_feed_*`, `tech_consistency_*`, `tech_html_missing`

---

## Applicability notes

- No `robots.txt` emission by Website Engine → `tech_robots_txt_absent` INFO (Website Engine)  
- No live HTTP / Googlebot emulation  
- No search submission  
- og:image not required (`tech_og_image_na`)
