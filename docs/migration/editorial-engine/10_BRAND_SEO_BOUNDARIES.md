# E6A — Brand & SEO Boundaries

---

## Brand

| Concern | Owner | Evidence |
|---------|-------|----------|
| Canonical brand voice definition | **BRAND ENGINE** | `obsidian_vault/07 - Brand Voice/Brand Voice Guide.md` |
| CMS brand guide (reference) | REFERENCE → merge into Brand Engine | `workcrew-cms-os/brand/voice.md` |
| Style / banned-phrase **checks** | **EDITORIAL ENGINE** | `draft_validator` BANNED_CLAIMS, `structure_checker` FORBIDDEN_PATTERNS |
| Brand QA checklist section | EDITORIAL / Publishing boundary | `publish_checklist_checker` `# Brand QA` |
| Agent tone in YAML | AI PLATFORM config consumed by Editorial/Generation | `agents_editor.yaml`, generation agents |
| CMS brand-voice ritual | ADAPT into Brand Engine + Editorial checklist | `tests/brand-voice.md` |

**Rule:** Editorial Engine **enforces** style compliance; Brand Engine **owns** definitions.  
CMS brand materials must not create a second brand SoT under Editorial Engine.

---

## SEO

| Concern | Owner | Evidence |
|---------|-------|----------|
| SEO strategy artifact production | **SEO ENGINE** | Generation/Artifact `seo_agent` → `02_SEO_Plan.md` |
| SEO framework docs | SEO ENGINE / Knowledge | vault SEO Framework |
| Research/SEO term gates | EDITORIAL ENGINE (validation) | `research_mapper` |
| Frontmatter SEO fields validation | EDITORIAL ENGINE | `final_frontmatter_lint` / `metadata_checker` (`primary_keyword`, `canonical_url`, …) |
| Editor copies approved canonical URL | EDITORIAL ENGINE (apply validated SEO) | `editor_crew._seo_canonical_section` |
| Rank / AI-visibility tracking API | SEO ENGINE / OTHER | `runner_api_routers/seo.py` |
| CMS SEO agent SOUL | REFERENCE / SEO Engine adapt | CMS `agents/seo/` — not Editorial core |

**Rule:** Editor tools **validate / apply** SEO metadata; they do **not** own SEO strategy.  
Do not redesign SEO Engine in Editorial migration.

---

## Boundary violations (flag only)

- Brand banned lists duplicated across vault guide and validator constants — consolidation ADR optional, not E6A.
- Marketing multi-brand YAML (`agents_marketing.yaml`) is adjacent channel work, not CMS editorial Brand Engine.
