# 09 — Marketing OS

Evidence of marketing-related assets and entry points in the repository.

---

## Content

| Item | Evidence |
|------|----------|
| Week content bundles | `input/W*/{02_SEO_Plan,03_Research,04_Draft,05_Final,09_Publish_Checklist}.md` |
| Tracker | `tracker.csv` |
| Runtime profiles | `data/week_runtime/*.json`, `data/runtime_config.json` |
| Marketing generation output | `output/marketing/` |
| Marketing crew | `src/marketing_crew.py` |
| Agent/task YAML | `src/agents_marketing.yaml`, `src/tasks_marketing.yaml` |
| Generation/editor crews (editorial content) | `src/generation_crew.py`, `src/editor_crew.py` |

---

## SEO

| Item | Evidence |
|------|----------|
| SEO plans in week folders | `input/*/02_SEO_Plan.md` |
| SEO agents in generation YAML | `seo_agent` keys |
| SEO optimiser in marketing YAML | `seo_optimiser` |
| SEO API | `runner_api_routers/seo.py` → `/api/v1/seo` (keywords, checks, summary) |
| SEO models | `revenue_os/models/seo.py` (`SEOKeyword`, `SEORankCheck`) |
| Obsidian SEO notes | `obsidian_vault/05 - SEO & Research/` |
| Docs | `docs/MARKETING_STRATEGY_AEO_GEO.md` |

---

## Publishing

| Item | Evidence |
|------|----------|
| Publish checklist artifacts | `input/*/09_Publish_Checklist.md` |
| Checklist checker tool | `src/tools/publish_checklist_checker.py` |
| Hashnode publish tool | `src/tools/hashnode_publish.py` |
| Social publisher | `revenue_os/integrations/social_publisher.py` |
| Marketing publish/dry-run API | `POST /marketing/publish`, `/marketing/dry-run` |
| Go-live helper | `src/tools/go_live_helpers.py`; `POST /go-live` |
| Promote staged | `src/tools/promote_staged.py` |

---

## Campaigns / automation (marketing-adjacent)

| Item | Evidence |
|------|----------|
| Email automation module | `revenue_os/marketing/email_automation.py` |
| Lead nurturing module | `revenue_os/marketing/lead_nurturing.py` |
| Automation workflows API | `/api/v1/automation` |
| Marketing spend analytics | `MarketingSpendRecord`; `/api/v1/analytics-depth/spend` |
| Docs | `docs/MARKETING_TACTICAL_PLAYBOOK.md`, `docs/AUTOMATION_WORKFLOWS.md` |

---

## Editorial

| Item | Evidence |
|------|----------|
| Editor crew | `src/editor_crew.py` + `agents_editor.yaml` / `tasks_editor.yaml` |
| QA crew / contract | `src/qa_crew.py`, `src/crew_contract.py` |
| Front matter lint | `src/tools/final_frontmatter_lint.py` |
| Content quality checker | `src/tools/content_quality_checker.py` |
| UI week/file views | `templates/weeks.html`, `week_detail.html`, `file_view.html` |

---

## Brand

| Item | Evidence |
|------|----------|
| Brand voice vault note | `obsidian_vault/07 - Brand Voice/Brand Voice Guide.md` |
| Marketing request `brand` field | used in `runner_api_routers/marketing.py` logging/params |
| Personas | `obsidian_vault/06 - Audience & Personas/` |

---

## Social

| Item | Evidence |
|------|----------|
| Social copywriter agent | `agents_marketing.yaml` → `social_copywriter` |
| Social posts model | `revenue_os/models/content.py` → `SocialPost` |
| Revenue OS social API | `revenue_os/api/v1/social.py` (`/api/v1/social/...`) |
| Env tokens | LinkedIn, Instagram, YouTube in `.env.example` |
| WhatsApp content posts | `runner_api_routers/whatsapp.py` content endpoints |

---

## Email

| Item | Evidence |
|-------|----------|
| Email integration | `revenue_os/integrations/email.py` |
| Integrations email routes | `/api/v1/integrations/email/*` |
| Marketing email automation | `revenue_os/marketing/email_automation.py` |
| Outreach generate-email | `/api/v1/outreach/generate-email` |

---

## Distribution

| Item | Evidence |
|------|----------|
| Distribution crew | `src/distribution_crew.py` + distribution YAML |
| Distribution bundle checker | `src/tools/distribution_bundle_checker.py` |
| Tests | `tests/test_distribution_crew_guard.py`, `tests/test_distribution_bundle_checker.py` |

---

## Analytics (marketing)

| Item | Evidence |
|------|----------|
| Analytics UI | `templates/analytics.html`; frontend `Analytics.jsx` |
| Analytics API | `/analytics/*`, `/api/v1/analytics-depth/*` |
| Attribution/LTV/CAC | analytics_depth router |
| Docs | existing docs under `docs/` for forecasting/reporting |

---

## Entry points (marketing)

| Entry | Path |
|-------|------|
| HTTP generate | `POST /marketing/generate` |
| HTTP dry-run | `POST /marketing/dry-run` |
| HTTP publish | `POST /marketing/publish` |
| UI | `GET /marketing` |
| SEO API | `/api/v1/seo/*` |
| Crew CLI | `python -m` patterns via marketing router subprocess; `MarketingCrew` in `src/marketing_crew.py` |
| Content pipeline generate/edit | `POST /generate`, `POST /edit` |
