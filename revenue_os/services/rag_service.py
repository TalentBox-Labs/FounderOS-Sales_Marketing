"""Retrieval-augmented answers over the platform's knowledge base and CRM data.

Retrieval always runs (chromadb, local embeddings, no API key required).
Synthesis uses OpenAI when configured; without a key it degrades to a plain
listing of the top matches — same fallback shape as ai_service.py.
"""

from __future__ import annotations

from typing import Any

from revenue_os.config import settings


def answer_question(
    question: str, limit: int = 5, type_filter: str | None = None,
) -> dict[str, Any]:
    """Retrieve relevant snippets and synthesize a grounded answer. Never raises."""
    from revenue_os.database import SessionLocal
    from revenue_os.services.search_service import search

    db = SessionLocal()
    try:
        hits = search(question, limit=limit, type_filter=type_filter, db=db)
    finally:
        db.close()

    if not hits:
        return {
            "answer": "I couldn't find anything relevant in the knowledge base or CRM yet.",
            "sources": [],
        }

    sources = [_source_summary(h) for h in hits]

    if settings.OPENAI_API_KEY:
        try:
            return {"answer": _synthesize(question, hits), "sources": sources}
        except Exception:
            pass

    return {"answer": _fallback_answer(hits), "sources": sources}


def _source_summary(hit: dict[str, Any]) -> dict[str, Any]:
    meta = hit.get("metadata") or {}
    return {
        "id": hit["id"],
        "type": meta.get("type"),
        "title": meta.get("title") or meta.get("name") or meta.get("subject") or hit["id"],
        "snippet": hit.get("snippet", ""),
    }


def _synthesize(question: str, hits: list[dict[str, Any]]) -> str:
    from openai import OpenAI

    context = "\n\n".join(
        f"[{i + 1}] ({(h.get('metadata') or {}).get('type', 'unknown')}) "
        f"{(h.get('metadata') or {}).get('title') or (h.get('metadata') or {}).get('name') or ''}: "
        f"{h.get('snippet', '')}"
        for i, h in enumerate(hits)
    )
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer the founder's question using ONLY the numbered context "
                    "snippets below. Cite sources inline like [1]. If the context "
                    "doesn't answer the question, say so plainly rather than guessing."
                ),
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
        max_tokens=400,
    )
    return resp.choices[0].message.content or _fallback_answer(hits)


def _fallback_answer(hits: list[dict[str, Any]]) -> str:
    lines = ["Here's what I found (set OPENAI_API_KEY for a synthesized answer):"]
    for i, h in enumerate(hits, 1):
        meta = h.get("metadata") or {}
        title = meta.get("title") or meta.get("name") or meta.get("subject") or h["id"]
        lines.append(f"{i}. [{meta.get('type', 'unknown')}] {title} — {h.get('snippet', '')[:120]}")
    return "\n".join(lines)
