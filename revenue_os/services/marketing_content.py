"""Content Writer, LinkedIn Content, Social Media, Video Strategy, and
Creative Design agents.

Content Writer publishes into the real Knowledge Base (M6) — searchable
and RAG-able like any other article, not throwaway text. Anything destined
for an external channel (LinkedIn, social platforms) is filed to the
Approvals queue rather than posted directly: there's no compliant
automated-posting API for either without app review the platform doesn't
have configured, so a human reviews and posts by hand. Planning-only
outputs (video scripts, creative briefs) don't touch an external channel
at all, so they're just returned + logged for the record.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

AGENT_CONTENT_WRITER = "content_writer_agent"
AGENT_LINKEDIN_CONTENT = "linkedin_content_agent"
AGENT_SOCIAL_MEDIA = "social_media_agent"
AGENT_VIDEO_STRATEGY = "video_strategy_agent"
AGENT_CREATIVE_DESIGN = "creative_design_agent"


def _log_insight(db: Any, agent_name: str, category: str, title: str, summary: str, *, organization_id: str) -> None:
    from revenue_os.models.marketing import MarketingInsight
    from revenue_os.services.tenant_scoped_access import tenant_org_uuid

    db.add(MarketingInsight(
        organization_id=tenant_org_uuid(organization_id), agent_name=agent_name, category=category,
        title=title[:500], summary=summary,
    ))


_DEFERRED_REASON = (
    "Superseded by src/marketing_crew.py's existing content agents — "
    "see docs/marketing/P1_MARKETING_OS_PRIORITY_DECISION.md for the dedup decision needed before this ships."
)


# ── Agent 6: Content Writer (deferred — overlaps src/marketing_crew.py's blog_writer) ──


def write_content(content_type: str, topic: str, context: str = "", publish: bool = True, *, organization_id: str) -> dict[str, Any]:
    return {"ok": False, "reason": _DEFERRED_REASON}


# ── Agent 7: LinkedIn Content (deferred — overlaps src/marketing_crew.py's social_copywriter) ──


def draft_linkedin_content(post_type: str, topic: str, context: str = "", *, organization_id: str) -> dict[str, Any]:
    return {"ok": False, "reason": _DEFERRED_REASON}


# ── Agent 8: Social Media (deferred — overlaps src/marketing_crew.py's social_copywriter) ──


def draft_social_posts(topic: str, platforms: list[str], context: str = "", *, organization_id: str) -> dict[str, Any]:
    return {"ok": False, "reason": _DEFERRED_REASON}


# ── Agent 9: Video Strategy ───────────────────────────────────────────────────


def plan_video(topic: str, context: str = "", *, organization_id: str) -> dict[str, Any]:
    """Script/hook/B-roll/caption planning — no external channel touched,
    so this just returns the plan and logs it for the record."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service

    script = ai_service.generate_video_script(topic, context)

    db = SessionLocal()
    try:
        _log_insight(db, AGENT_VIDEO_STRATEGY, "video_strategy", topic, script.get("hook", ""), organization_id=organization_id)
        db.commit()
    finally:
        db.close()

    return {"ok": True, "topic": topic, **script}


# ── Agent 10: Creative Design ─────────────────────────────────────────────────


def create_design_brief(asset_type: str, topic: str, context: str = "", *, organization_id: str) -> dict[str, Any]:
    """A brief for a designer or image-gen tool to execute — this agent
    does not generate images itself (no image-gen provider is wired up)."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service

    brief = ai_service.generate_creative_brief(asset_type, topic, context)

    db = SessionLocal()
    try:
        _log_insight(
            db, AGENT_CREATIVE_DESIGN, "creative_brief", f"{asset_type}: {topic}",
            brief.get("concept", ""), organization_id=organization_id,
        )
        db.commit()
    finally:
        db.close()

    return {"ok": True, "asset_type": asset_type, **brief}
