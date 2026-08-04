"""Founder Copilot API — chat with, and command, the platform."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from revenue_os.services.copilot import chat
from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


@router.post("/chat")
def copilot_chat(
    req: ChatRequest,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """One founder message in, one grounded answer (and any actions) out."""
    result = chat(req.message)
    return {"ok": True, **result}
