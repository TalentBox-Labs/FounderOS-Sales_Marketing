"""OpenAPI/Swagger documentation schemas and examples."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Pipeline Router Schemas ──────────────────────────────────────────────────


class PipelineRunRequest(BaseModel):
    """Request model for pipeline run endpoints."""

    week: str | None = Field(None, description="Content week ID (e.g., W99)")
    topic: str | None = Field(None, description="Content topic (optional)")
    url: str | None = Field(None, description="URL context (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "week": "W99",
                "topic": "AI Recruiting",
                "url": "https://example.com",
            }
        }


class PipelineStepResult(BaseModel):
    """Result of a single pipeline step."""

    status: str = Field(..., description="Step status (ok, failed, skipped)")
    step: str | None = Field(None, description="Step name")
    message: str | None = Field(None, description="Step output or error message")
    duration_ms: int | None = Field(None, description="Execution duration in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "step": "validators",
                "message": "All validators passed",
                "duration_ms": 2500,
            }
        }


class PipelineResponse(BaseModel):
    """Response from pipeline endpoints."""

    ok: bool = Field(..., description="Whether operation succeeded")
    week: str | None = Field(None, description="Week that was processed")
    stdout: str = Field(default="", description="Standard output (last 5000 chars)")
    stderr: str = Field(default="", description="Standard error (last 5000 chars)")
    steps: list[PipelineStepResult] = Field(default_factory=list, description="Individual step results")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "week": "W99",
                "stdout": "Pipeline executed successfully",
                "stderr": "",
                "steps": [
                    {"status": "ok", "step": "validators", "message": "Passed", "duration_ms": 2500}
                ],
            }
        }


# ── Marketing Router Schemas ─────────────────────────────────────────────────


class MarketingGenerateRequest(BaseModel):
    """Request model for marketing content generation."""

    brand: str = Field(..., description="Brand name (workcrew, hirestack, founder)")
    topic: str = Field(..., description="Content topic/angle")
    keyword: str = Field(..., description="Primary SEO keyword")
    geo: str = Field(default="", description="Geographic target (e.g., 'United States')")
    funnel: str = Field(default="consideration", description="Funnel stage (awareness, consideration, decision)")
    output_root: str | None = Field(None, description="Custom output directory path (repo-relative)")
    channel: str = Field(default="all", description="Channel filter (all, blog, social, email)")

    class Config:
        json_schema_extra = {
            "example": {
                "brand": "workcrew",
                "topic": "AI-Powered Recruiting",
                "keyword": "ai recruiting tools",
                "geo": "United States",
                "funnel": "consideration",
                "output_root": None,
                "channel": "all",
            }
        }


class MarketingGenerateResponse(BaseModel):
    """Response from marketing generation endpoint."""

    ok: bool = Field(..., description="Whether generation succeeded")
    stdout: str = Field(default="", description="Generation output (last 5000 chars)")
    stderr: str = Field(default="", description="Errors or warnings (last 5000 chars)")
    output_path: str = Field(default="", description="Path to generated artifacts")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "stdout": "Marketing content generated successfully",
                "stderr": "",
                "output_path": "output/marketing/workcrew/ai-recruiting-tools",
            }
        }


class MarketingDryRunRequest(BaseModel):
    """Request for marketing dry-run preview."""

    status_path: str = Field(..., description="Path to 08_Publish_Status.json manifest")
    brand: str = Field(default="workcrew", description="Brand context for preview")

    class Config:
        json_schema_extra = {
            "example": {
                "status_path": "output/marketing/workcrew/ai-recruiting-tools/08_Publish_Status.json",
                "brand": "workcrew",
            }
        }


class MarketingPublishRequest(BaseModel):
    """Request for marketing content publication."""

    status_path: str = Field(..., description="Path to publish status manifest")
    confirmed: bool = Field(..., description="Must be true to publish (safety confirmation)")
    instagram_image_url: str = Field(default="", description="Instagram image URL override")
    brand: str = Field(default="workcrew", description="Brand context")

    class Config:
        json_schema_extra = {
            "example": {
                "status_path": "output/marketing/workcrew/ai-recruiting-tools/08_Publish_Status.json",
                "confirmed": True,
                "instagram_image_url": "https://example.com/image.jpg",
                "brand": "workcrew",
            }
        }


# ── Orchestration Router Schemas ─────────────────────────────────────────────


class OrchestrationPlanRequest(BaseModel):
    """Request for orchestration strategy planning."""

    backend: str = Field(default="hermes", description="Orchestration backend (hermes, etc.)")
    brand: str = Field(..., description="Brand target")
    topic: str = Field(..., description="Content topic")
    keyword: str = Field(..., description="Primary keyword")
    geo_target: str = Field(default="global", description="Geographic target")
    funnel_stage: str = Field(default="consideration", description="Funnel stage")
    audience: str = Field(default="", description="Target audience segment")
    channels: list[str] = Field(default_factory=list, description="Distribution channels")

    class Config:
        json_schema_extra = {
            "example": {
                "backend": "hermes",
                "brand": "workcrew",
                "topic": "AI Recruiting",
                "keyword": "ai recruiting automation",
                "geo_target": "United States",
                "funnel_stage": "consideration",
                "audience": "recruiters",
                "channels": ["blog", "linkedin", "email"],
            }
        }


class OrchestrationRunRequest(BaseModel):
    """Request to execute orchestration workflow."""

    backend: str = Field(default="hermes", description="Orchestration backend")
    brand: str = Field(..., description="Brand")
    topic: str = Field(..., description="Topic")
    keyword: str = Field(..., description="Primary keyword")
    geo_target: str = Field(default="global", description="Geographic target")
    funnel_stage: str = Field(default="consideration", description="Funnel stage")
    audience: str = Field(default="", description="Target audience")
    channels: list[str] = Field(default_factory=list, description="Channels")
    run_content: bool = Field(default=False, description="Run content generation")
    run_seo: bool = Field(default=False, description="Run SEO backend")
    run_email: bool = Field(default=False, description="Run email backend")
    run_prospecting: bool = Field(default=False, description="Run prospecting")
    run_voice_qualification: bool = Field(default=False, description="Run voice qualification")
    run_meeting_booking: bool = Field(default=False, description="Run meeting booking")

    class Config:
        json_schema_extra = {
            "example": {
                "backend": "hermes",
                "brand": "workcrew",
                "topic": "Source Engineering Talent",
                "keyword": "technical recruiter outreach",
                "geo_target": "India",
                "funnel_stage": "decision",
                "audience": "talent leads",
                "channels": ["blog", "linkedin"],
                "run_content": True,
                "run_seo": True,
                "run_email": True,
            }
        }


class OrchestrationResponse(BaseModel):
    """Response from orchestration endpoints."""

    ok: bool = Field(..., description="Operation success status")
    result: dict[str, Any] = Field(default_factory=dict, description="Orchestration result")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "result": {
                    "backend": "hermes",
                    "status": "queued",
                    "run_id": "orch_20240615_w99_abc123",
                },
            }
        }


# ── Outreach Router Schemas ──────────────────────────────────────────────────


class OutreachSequence(BaseModel):
    """Outreach sequence metadata."""

    id: str = Field(..., description="Sequence ID")
    name: str = Field(..., description="Sequence name")
    channel: str = Field(..., description="Communication channel (email, sms, etc.)")
    steps_count: int = Field(..., description="Number of steps in sequence")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "seq_001",
                "name": "Welcome Series",
                "channel": "email",
                "steps_count": 5,
            }
        }


class OutreachSequencesResponse(BaseModel):
    """Response listing outreach sequences."""

    ok: bool = Field(..., description="Operation success")
    sequences: list[OutreachSequence] = Field(..., description="Active sequences")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "sequences": [
                    {"id": "seq_001", "name": "Welcome", "channel": "email", "steps_count": 5},
                    {"id": "seq_002", "name": "Follow-up", "channel": "sms", "steps_count": 3},
                ],
            }
        }


# ── Error Response Schemas ───────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")
    error_code: str | None = Field(None, description="Machine-readable error code")
    request_id: str | None = Field(None, description="Request tracing ID")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid API key provided",
                "error_code": "AUTH_INVALID_KEY",
                "request_id": "req_abc123",
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    detail: str = Field(..., description="Error summary")
    errors: list[dict[str, Any]] = Field(default_factory=list, description="Field-level errors")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Request validation failed",
                "errors": [
                    {"field": "brand", "message": "Brand is required"},
                    {"field": "keyword", "message": "Keyword must be at least 3 characters"},
                ],
            }
        }


# ── Health Check Schemas ─────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status (ok, degraded, down)")
    service: str = Field(..., description="Service name")
    timestamp: str | None = Field(None, description="Health check timestamp")
    uptime_seconds: int | None = Field(None, description="Service uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "service": "WorkCrew CMS OS",
                "timestamp": "2024-06-15T10:30:00Z",
                "uptime_seconds": 86400,
            }
        }


# ── Common Response Wrappers ─────────────────────────────────────────────────


class SuccessResponse(BaseModel):
    """Generic success response wrapper."""

    ok: bool = True
    message: str = Field(..., description="Success message")
    data: dict[str, Any] = Field(default_factory=dict, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "message": "Operation completed successfully",
                "data": {"count": 42, "items": []},
            }
        }


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    ok: bool = True
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Pagination offset")
    items: list[dict[str, Any]] = Field(..., description="Page items")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "total": 150,
                "limit": 20,
                "offset": 0,
                "items": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"},
                ],
            }
        }
