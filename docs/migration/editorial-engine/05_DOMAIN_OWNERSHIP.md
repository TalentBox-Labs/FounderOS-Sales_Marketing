# E6A — Domain Ownership

Assign every relevant capability to an **existing** Founder domain. Do not create new domains.

| Capability | Final owner | Notes / boundary violation |
|------------|-------------|----------------------------|
| EditorCrew draft→final | EDITORIAL ENGINE | Currently under `src/` Marketing pipeline — ownership label only; no move in E6A |
| QACrew LLM audit | EDITORIAL ENGINE | Optional gate; AI PLATFORM supplies CrewAI runtime |
| Deterministic validators (research/draft/structure/metadata/checklist) | EDITORIAL ENGINE | Called by pipeline; tools remain in `src/tools/` |
| content_quality_checker | EDITORIAL ENGINE | Phase 2c; not default pipeline |
| promote_staged / promotion_audit | EDITORIAL ENGINE | Approval boundary before canonical `input/` |
| tracker status/qa_status update after validation | EDITORIAL ENGINE + CONTENT STUDIO (read) | Mutation via tracker_updater; Studio displays |
| Content Studio list/detail/kanban | CONTENT STUDIO | Frozen read surfaces — not editorial executor |
| Brand Voice Guide / voice principles | BRAND ENGINE | Vault + future merge of CMS `brand/voice.md` |
| Banned-phrase **enforcement** in validators | EDITORIAL ENGINE | Consumes brand rules; does not own brand definition |
| SEO plan generation (`02_SEO_Plan.md`) | SEO ENGINE | Via generation/artifact SEO agent |
| SEO metadata validation (FM keyword/canonical) | EDITORIAL ENGINE (validate) | Strategy remains SEO Engine |
| Rank/AI-visibility APIs (`runner_api_routers/seo.py`) | SEO ENGINE / OTHER | Not editorial |
| BaseCrew / LLM env | AI PLATFORM | Shared |
| Auth / API keys | SHARED PLATFORM | |
| Celery / OpenClaw GTM | AUTOMATION PLATFORM | OpenClaw **not** editorial path |
| sheet_sync | SHARED / ops mirror | Not Editorial SoT |
| go-live / publish URL | PUBLISHING ENGINE | Human confirmed |
| Marketing multi-brand crews | OTHER EXISTING (Marketing channels) | Adjacent; not CMS editorial core |
| Knowledge base articles | KNOWLEDGE OS | Separate Postgres surface |
| SocialPost schedule/publish | OTHER / social | Not Content Studio editorial |

## Proven boundary violations (flag only — do not fix)

1. **UI `/edit` and `/generate`** invoke crews without staging args → HTTP surface claims editorial execution but cannot succeed as wired (`runner_api_routers/pipeline.py`).
2. **Pipeline UI** links `/qa` and `/sheet-sync` with no routes → false operational surface.
3. **Brand rules duplicated** across vault Brand Voice Guide, agent YAML tone, and validator banned lists — Brand Engine vs Editorial enforcement not formally separated in code layout.
4. **CMS Sheets stage machine** historically owned editorial lifecycle outside Founder tracker — must not re-enter as SoT.

## Calendar

Out of Editorial Engine until E5A date semantics established.
