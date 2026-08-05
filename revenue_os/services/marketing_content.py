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


def _get_or_create_marketing_kb(db: Any) -> Any:
    from revenue_os.models.content import KnowledgeBase

    kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == "Marketing Content").first()
    if kb is None:
        kb = KnowledgeBase(name="Marketing Content", description="AI-drafted marketing content", kb_type="content")
        db.add(kb)
        db.flush()
    return kb


def _log_insight(db: Any, agent_name: str, category: str, title: str, summary: str) -> None:
    from revenue_os.models.marketing import MarketingInsight

    db.add(MarketingInsight(agent_name=agent_name, category=category, title=title[:500], summary=summary))


# ── Agent 6: Content Writer ──────────────────────────────────────────────────


def write_content(content_type: str, topic: str, context: str = "", publish: bool = True) -> dict[str, Any]:
    """Drafts long-form content. Publishes as a real Knowledge Base article
    by default (same model/search-indexing as manually-written articles)."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service

    draft = ai_service.generate_long_form_content(content_type, topic, context)
    result: dict[str, Any] = {"ok": True, "content_type": content_type, **draft}
    if not publish:
        return result

    from revenue_os.models.content import KnowledgeBaseArticle

    db = SessionLocal()
    try:
        kb = _get_or_create_marketing_kb(db)
        article = KnowledgeBaseArticle(
            knowledge_base_id=kb.id, title=draft["title"], content=draft["content"],
            tags=",".join(draft.get("tags", [])),
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        article.embedding_id = str(article.id)
        db.commit()
        result["article_id"] = str(article.id)
        result["knowledge_base_id"] = str(kb.id)
    finally:
        db.close()

    try:
        from revenue_os.services.search_service import index_kb_article

        index_kb_article(result["article_id"], draft["title"], content=draft["content"], tags=result.get("tags"))
    except Exception as e:
        logger.warning(f"Marketing content search-index failed: {e}")

    return result


# ── Agent 7: LinkedIn Content ────────────────────────────────────────────────


def draft_linkedin_content(post_type: str, topic: str, context: str = "") -> dict[str, Any]:
    """Founder-voice LinkedIn post, filed for approval — no compliant
    automated posting API is configured, so approval marks it ready to
    post by hand rather than pretending to publish it."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service
    from revenue_os.services.approvals import request_approval

    body = ai_service.generate_linkedin_post(post_type, topic, context)

    db = SessionLocal()
    try:
        _log_insight(db, AGENT_LINKEDIN_CONTENT, "linkedin_content", f"{post_type}: {topic}", body[:500])
        db.commit()
    finally:
        db.close()

    approval = request_approval(
        requested_by=AGENT_LINKEDIN_CONTENT, action_type="publish_linkedin_post",
        title=f"LinkedIn {post_type} post: {topic}",
        description="AI-drafted LinkedIn content, ready for founder review before posting.",
        payload={"post_type": post_type, "topic": topic, "body": body},
    )
    return {"ok": True, "post_type": post_type, "body": body, "approval_id": approval["id"]}


# ── Agent 8: Social Media ────────────────────────────────────────────────────


def draft_social_posts(topic: str, platforms: list[str], context: str = "") -> dict[str, Any]:
    """One platform-native variant per platform, filed for approval as a
    single batch — same manual-posting caveat as LinkedIn Content."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service
    from revenue_os.services.approvals import request_approval

    variants = ai_service.generate_social_variants(topic, context, platforms)

    db = SessionLocal()
    try:
        _log_insight(db, AGENT_SOCIAL_MEDIA, "social_media", topic, f"Platforms: {', '.join(platforms)}")
        db.commit()
    finally:
        db.close()

    approval = request_approval(
        requested_by=AGENT_SOCIAL_MEDIA, action_type="publish_social_post",
        title=f"Social posts: {topic}",
        description=f"AI-drafted variants for {', '.join(platforms)}, ready for review before posting.",
        payload={"topic": topic, "platforms": platforms, "variants": variants},
    )
    return {"ok": True, "topic": topic, "variants": variants, "approval_id": approval["id"]}


# ── Agent 9: Video Strategy ───────────────────────────────────────────────────


def plan_video(topic: str, context: str = "") -> dict[str, Any]:
    """Script/hook/B-roll/caption planning — no external channel touched,
    so this just returns the plan and logs it for the record."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service

    script = ai_service.generate_video_script(topic, context)

    db = SessionLocal()
    try:
        _log_insight(db, AGENT_VIDEO_STRATEGY, "video_strategy", topic, script.get("hook", ""))
        db.commit()
    finally:
        db.close()

    return {"ok": True, "topic": topic, **script}


# ── Agent 10: Creative Design ─────────────────────────────────────────────────


def create_design_brief(asset_type: str, topic: str, context: str = "") -> dict[str, Any]:
    """A brief for a designer or image-gen tool to execute — this agent
    does not generate images itself (no image-gen provider is wired up)."""
    from revenue_os.database import SessionLocal
    from revenue_os.services import ai_service

    brief = ai_service.generate_creative_brief(asset_type, topic, context)

    db = SessionLocal()
    try:
        _log_insight(db, AGENT_CREATIVE_DESIGN, "creative_brief", f"{asset_type}: {topic}", brief.get("concept", ""))
        db.commit()
    finally:
        db.close()

    return {"ok": True, "asset_type": asset_type, **brief}
