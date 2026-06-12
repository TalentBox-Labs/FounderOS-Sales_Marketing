from __future__ import annotations

import os
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from revenue_os.models.contact import Contact, ContactSource, ContactStatus


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name, "") or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
        return max(0, value)
    except ValueError:
        return default


def prospecting_limits() -> dict[str, int]:
    free_limit = _env_int("PROSPECT_FREE_LIMIT", 25)
    scraper_limit = _env_int("PROSPECT_SCRAPER_LIMIT", 100)
    mcp_limit = _env_int("PROSPECT_MCP_LIMIT", 300)
    global_max = _env_int("PROSPECT_GLOBAL_MAX", 1000)
    scale_step = _env_int("PROSPECT_SCALE_STEP", 25)
    return {
        "free_limit": free_limit,
        "scraper_limit": scraper_limit,
        "mcp_limit": mcp_limit,
        "global_max": global_max,
        "scale_step": scale_step,
    }


def provider_status() -> dict[str, bool]:
    scraper = bool((os.getenv("SCRAPER_PROVIDER_URL", "") or "").strip())
    apollo = bool((os.getenv("APOLLO_MCP_API_KEY", "") or "").strip())
    sales_nav = bool((os.getenv("LINKEDIN_SALES_NAVIGATOR_MCP_TOKEN", "") or "").strip())
    return {
        "scraper": scraper,
        "apollo_mcp": apollo,
        "linkedin_sales_navigator_mcp": sales_nav,
    }


def _existing_linkedin_pool(
    db: Session,
    min_score: int,
    statuses: list[ContactStatus],
    limit: int,
) -> list[Contact]:
    query = (
        db.query(Contact)
        .filter(Contact.status.in_(statuses))
        .filter(Contact.lead_score >= min_score)
        .filter(
            or_(
                Contact.source == ContactSource.LINKEDIN,
                Contact.linkedin_url.isnot(None),
            )
        )
        .order_by(Contact.lead_score.desc(), Contact.created_at.desc())
    )
    return query.limit(limit).all()


def build_prospecting_plan(
    db: Session,
    *,
    target_count: int,
    min_score: int,
    statuses: list[ContactStatus],
    allow_scraper: bool,
    allow_mcp: bool,
) -> dict[str, Any]:
    limits = prospecting_limits()
    providers = provider_status()

    target = max(1, min(target_count, limits["global_max"]))

    free_cap = min(target, limits["free_limit"])
    free_pool = _existing_linkedin_pool(
        db,
        min_score=min_score,
        statuses=statuses,
        limit=free_cap,
    )
    free_used = len(free_pool)
    remaining = max(0, target - free_used)

    scraper_used = 0
    scraper_cap = min(remaining, limits["scraper_limit"])
    if allow_scraper and providers["scraper"]:
        scraper_used = scraper_cap
    remaining = max(0, remaining - scraper_used)

    mcp_used = 0
    mcp_cap = min(remaining, limits["mcp_limit"])
    if allow_mcp and (providers["apollo_mcp"] or providers["linkedin_sales_navigator_mcp"]):
        mcp_used = mcp_cap
    remaining = max(0, remaining - mcp_used)

    selected_contacts = [
        {
            "id": str(c.id),
            "name": c.full_name,
            "designation": c.designation,
            "linkedin_url": c.linkedin_url,
            "lead_score": c.lead_score,
            "status": c.status.value,
            "source": c.source.value,
        }
        for c in free_pool
    ]

    return {
        "target_count": target,
        "thresholds": limits,
        "providers": providers,
        "stages": [
            {
                "stage": "free_linkedin_existing_data",
                "cap": free_cap,
                "used": free_used,
                "note": "Use existing LinkedIn contacts first (zero-cost).",
            },
            {
                "stage": "scraper_platforms",
                "cap": scraper_cap,
                "used": scraper_used,
                "enabled": allow_scraper,
                "provider_configured": providers["scraper"],
                "note": "Scale to scraper platforms after free pool limit.",
            },
            {
                "stage": "mcp_providers",
                "cap": mcp_cap,
                "used": mcp_used,
                "enabled": allow_mcp,
                "provider_configured": bool(providers["apollo_mcp"] or providers["linkedin_sales_navigator_mcp"]),
                "note": "Scale to MCP providers like Apollo/Sales Navigator after scraper limits.",
            },
        ],
        "selected_existing_linkedin_contacts": selected_contacts,
        "unfilled_after_limits": remaining,
        "scale_recommendation": {
            "next_increment": limits["scale_step"],
            "message": "Increase in small increments only after current stage conversion and response rates are healthy.",
        },
    }
