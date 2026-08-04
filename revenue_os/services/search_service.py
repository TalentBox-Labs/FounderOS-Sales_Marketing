from __future__ import annotations

import uuid
from typing import Any

import chromadb
from chromadb.config import Settings
from sqlalchemy.orm import Session

from revenue_os.config import settings
from revenue_os.models.activity import Activity
from revenue_os.models.contact import Contact
from revenue_os.models.deal import Deal
from revenue_os.models.project import Project

_client: chromadb.ClientAPI | None = None
_COLLECTION_NAME = "revenue_os_search"


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _get_collection():
    client = _get_client()
    try:
        return client.get_collection(_COLLECTION_NAME)
    except (ValueError, chromadb.errors.NotFoundError):
        return client.create_collection(_COLLECTION_NAME)


def index_contact(contact_id: uuid.UUID, first_name: str, last_name: str,
                  email: str | None = None, designation: str | None = None,
                  tags: str | None = None, notes: str | None = None) -> None:
    collection = _get_collection()
    text = f"{first_name} {last_name} {email or ''} {designation or ''} {tags or ''} {notes or ''}"
    collection.upsert(
        ids=[str(contact_id)],
        documents=[text],
        metadatas=[{
            "type": "contact",
            "name": f"{first_name} {last_name}",
            "email": email or "",
        }],
    )


def index_deal(deal_id: uuid.UUID, name: str, description: str | None = None,
               tags: str | None = None) -> None:
    collection = _get_collection()
    text = f"{name} {description or ''} {tags or ''}"
    collection.upsert(
        ids=[str(deal_id)],
        documents=[text],
        metadatas=[{"type": "deal", "name": name}],
    )


def index_activity(activity_id: uuid.UUID, subject: str | None = None,
                   body: str | None = None) -> None:
    collection = _get_collection()
    text = f"{subject or ''} {body or ''}"
    collection.upsert(
        ids=[str(activity_id)],
        documents=[text],
        metadatas=[{"type": "activity", "subject": subject or ""}],
    )


def index_project(project_id: uuid.UUID, name: str, description: str | None = None) -> None:
    collection = _get_collection()
    text = f"{name} {description or ''}"
    collection.upsert(
        ids=[str(project_id)],
        documents=[text],
        metadatas=[{"type": "project", "name": name}],
    )


def index_kb_article(article_id: uuid.UUID, title: str, content: str | None = None,
                     tags: str | None = None) -> None:
    collection = _get_collection()
    text = f"{title} {content or ''} {tags or ''}"
    collection.upsert(
        ids=[str(article_id)],
        documents=[text],
        metadatas=[{"type": "kb_article", "title": title}],
    )


def search(query: str, limit: int = 10, type_filter: str | None = None,
           db: Session | None = None) -> list[dict[str, Any]]:
    collection = _get_collection()
    where = {"type": type_filter} if type_filter else None
    results = collection.query(
        query_texts=[query],
        n_results=limit,
        where=where,
    )

    hits = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            hits.append({
                "id": doc_id,
                "score": float(results["distances"][0][i]) if results["distances"] else 0,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "snippet": (results["documents"][0][i][:200]
                           if results["documents"] else ""),
            })

    if db and hits:
        for hit in hits:
            hit["record"] = _fetch_record(db, hit["id"], hit["metadata"].get("type", ""))

    return hits


def _fetch_record(db: Session, record_id: str, record_type: str) -> dict[str, Any] | None:
    try:
        uid = uuid.UUID(record_id)
    except ValueError:
        return None

    if record_type == "contact":
        c = db.query(Contact).filter(Contact.id == uid).first()
        if c:
            return {"id": str(c.id), "name": c.full_name, "email": c.email,
                    "designation": c.designation, "status": c.status.value}
    elif record_type == "deal":
        d = db.query(Deal).filter(Deal.id == uid).first()
        if d:
            return {"id": str(d.id), "name": d.name, "stage": d.stage.value,
                    "value": d.value}
    elif record_type == "activity":
        a = db.query(Activity).filter(Activity.id == uid).first()
        if a:
            return {"id": str(a.id), "subject": a.subject,
                    "type": a.activity_type.value}
    elif record_type == "project":
        p = db.query(Project).filter(Project.id == uid).first()
        if p:
            return {"id": str(p.id), "name": p.name, "status": p.status.value}
    elif record_type == "kb_article":
        from revenue_os.models.content import KnowledgeBaseArticle

        a = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == uid).first()
        if a:
            return {"id": str(a.id), "title": a.title,
                    "knowledge_base_id": str(a.knowledge_base_id)}

    return None


def delete_index(record_id: uuid.UUID) -> None:
    collection = _get_collection()
    collection.delete(ids=[str(record_id)])
