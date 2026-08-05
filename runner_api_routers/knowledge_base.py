"""Knowledge base — playbooks and notes with semantic search and RAG answers.

Articles are indexed into the same chromadb collection search_service.py
already uses for contacts/deals/activities, so "search" and "ask" work
across the whole platform, not just the knowledge base.
"""

from __future__ import annotations

import logging
import uuid as uuid_lib
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from revenue_os.database import SessionLocal
from revenue_os.models.content import KnowledgeBase, KnowledgeBaseArticle
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])

DEFAULT_KB_NAME = "Playbooks & Notes"


def _kb_dict(kb: KnowledgeBase, article_count: int | None = None) -> dict[str, Any]:
    return {
        "id": str(kb.id),
        "name": kb.name,
        "description": kb.description,
        "kb_type": kb.kb_type,
        "article_count": article_count,
        "created_at": kb.created_at.isoformat() if kb.created_at else None,
    }


def _article_dict(a: KnowledgeBaseArticle) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "knowledge_base_id": str(a.knowledge_base_id),
        "title": a.title,
        "content": a.content,
        "tags": a.tags,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _get_or_create_default_kb(db) -> KnowledgeBase:
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == DEFAULT_KB_NAME).first()
    if not kb:
        kb = KnowledgeBase(name=DEFAULT_KB_NAME, description="Default playbooks and notes.", kb_type="playbook")
        db.add(kb)
        db.commit()
        db.refresh(kb)
    return kb


class KBCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    kb_type: str = Field(default="playbook")


class ArticleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(default="")
    tags: str | None = None


class ArticleUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str | None = None
    tags: str | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)
    type_filter: str | None = None


@router.get("/bases")
def list_knowledge_bases(_: str | None = Depends(_verify_api_key)) -> dict[str, Any]:
    db = SessionLocal()
    try:
        bases = db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).all()
        result = []
        for kb in bases:
            count = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.knowledge_base_id == kb.id).count()
            result.append(_kb_dict(kb, article_count=count))
        return {"ok": True, "count": len(result), "knowledge_bases": result}
    finally:
        db.close()


@router.post("/bases")
def create_knowledge_base(
    req: KBCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        kb = KnowledgeBase(name=req.name, description=req.description, kb_type=req.kb_type)
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return {"ok": True, "knowledge_base": _kb_dict(kb, article_count=0)}
    finally:
        db.close()


@router.get("/bases/{kb_id}")
def get_knowledge_base(
    kb_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            kid = uuid_lib.UUID(kb_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid knowledge_base id")
        kb = db.get(KnowledgeBase, kid)
        if kb is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        articles = (
            db.query(KnowledgeBaseArticle)
            .filter(KnowledgeBaseArticle.knowledge_base_id == kid)
            .order_by(KnowledgeBaseArticle.updated_at.desc())
            .all()
        )
        result = _kb_dict(kb, article_count=len(articles))
        result["articles"] = [_article_dict(a) for a in articles]
        return {"ok": True, "knowledge_base": result}
    finally:
        db.close()


@router.post("/bases/{kb_id}/articles")
def create_article(
    kb_id: str,
    req: ArticleCreateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        if kb_id == "default":
            kb = _get_or_create_default_kb(db)
        else:
            try:
                kid = uuid_lib.UUID(kb_id)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid knowledge_base id")
            kb = db.get(KnowledgeBase, kid)
            if kb is None:
                raise HTTPException(status_code=404, detail="Knowledge base not found")

        article = KnowledgeBaseArticle(
            knowledge_base_id=kb.id, title=req.title, content=req.content, tags=req.tags,
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        article.embedding_id = str(article.id)
        db.commit()
        result = _article_dict(article)
    finally:
        db.close()

    try:
        from revenue_os.services.search_service import index_kb_article

        index_kb_article(article.id, req.title, content=req.content, tags=req.tags)
    except Exception as e:
        logger.warning(f"KB article search-index failed: {e}")

    return {"ok": True, "article": result}


@router.get("/articles/{article_id}")
def get_article(
    article_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            aid = uuid_lib.UUID(article_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid article id")
        article = db.get(KnowledgeBaseArticle, aid)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        return {"ok": True, "article": _article_dict(article)}
    finally:
        db.close()


@router.put("/articles/{article_id}")
def update_article(
    article_id: str,
    req: ArticleUpdateRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            aid = uuid_lib.UUID(article_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid article id")
        article = db.get(KnowledgeBaseArticle, aid)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")

        if req.title is not None:
            article.title = req.title
        if req.content is not None:
            article.content = req.content
        if req.tags is not None:
            article.tags = req.tags
        db.commit()
        db.refresh(article)
        result = _article_dict(article)
    finally:
        db.close()

    try:
        from revenue_os.services.search_service import index_kb_article

        index_kb_article(article.id, result["title"], content=result["content"], tags=result["tags"])
    except Exception as e:
        logger.warning(f"KB article re-index failed: {e}")

    return {"ok": True, "article": result}


@router.delete("/articles/{article_id}")
def delete_article(
    article_id: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        try:
            aid = uuid_lib.UUID(article_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid article id")
        article = db.get(KnowledgeBaseArticle, aid)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        db.delete(article)
        db.commit()
    finally:
        db.close()

    try:
        from revenue_os.services.search_service import delete_index

        delete_index(aid)
    except Exception as e:
        logger.warning(f"KB article de-index failed: {e}")

    return {"ok": True}


@router.get("/search")
def semantic_search(
    q: str = Query(..., min_length=1),
    type_filter: str | None = Query(default=None, alias="type"),
    limit: int = Query(default=10, ge=1, le=50),
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Semantic search across the knowledge base and CRM (contacts, deals, activities)."""
    from revenue_os.services.search_service import search

    db = SessionLocal()
    try:
        hits = search(q, limit=limit, type_filter=type_filter, db=db)
    finally:
        db.close()
    return {"ok": True, "count": len(hits), "results": hits}


@router.post("/ask")
def ask(
    req: AskRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Ask a question — retrieves relevant context and synthesizes an answer."""
    from revenue_os.services.rag_service import answer_question

    result = answer_question(req.question, limit=req.limit, type_filter=req.type_filter)
    return {"ok": True, **result}
