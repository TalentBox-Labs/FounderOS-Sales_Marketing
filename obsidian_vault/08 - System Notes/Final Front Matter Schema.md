---
tags: [system, schema, reference]
created: 2026-06-11
---

# 📋 Final Front Matter Schema

Required YAML block in `05_Final.md`. Validated by `metadata_checker`.

```yaml
---
week_id: W05          # Week identifier matching tracker
article_title: "..."  # Full article title
primary_keyword: ...  # Main target keyword
search_intent: commercial investigation | informational | transactional
funnel_stage: awareness | consideration | decision
status: published | in review | draft
publish_status: published | in review | draft | approved | scheduled | archived | pending | not started | ready
canonical_url: https://workcrew.ai/blog/your-slug
cta_type: free-trial | try_workcrew_free | ...
---
```

### Allowed `publish_status` values
draft · in progress · in review · ready · published · scheduled · archived · pending · not started · approved

### Rules
- No bracket placeholders `[like this]` in any required field
- `canonical_url` must be a valid `https://` URL
- `cta_type` must not be empty

## Related
- [[metadata_checker]] — validator that enforces this schema
- [[AI Agent Roster]] — the Editor agent writes this block
