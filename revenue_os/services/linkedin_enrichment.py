"""LinkedIn enrichment via Proxycurl — a licensed third-party data provider.

Direct scraping of linkedin.com violates LinkedIn's Terms of Service, so
this calls Proxycurl's Person/Company Profile API instead. Without a
configured API key it returns a clear "not configured" result — it never
asks an LLM to guess company data from a name, which would look like
enrichment but actually be fabricated.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_PERSON_URL = "https://nubela.co/proxycurl/api/v2/linkedin"
_COMPANY_URL = "https://nubela.co/proxycurl/api/v2/linkedin/company"
_TIMEOUT = 15


def _api_key(organization_id: str | None = None) -> str | None:
    from revenue_os.services.credentials_vault import load_credentials

    if organization_id is not None:
        config = load_credentials(
            "linkedin_enrichment",
            organization_id=organization_id,
            allow_global_fallback=False,
        )
    else:
        config = load_credentials("linkedin_enrichment", organization_id=None)
    return config.get("api_key") if config else None


def _fetch(url: str, linkedin_url: str, organization_id: str | None = None) -> dict[str, Any]:
    api_key = _api_key(organization_id)
    if not api_key:
        return {
            "ok": False, "configured": False,
            "reason": "LinkedIn enrichment is not configured — add a Proxycurl API key on the Integrations page.",
        }
    try:
        import requests

        resp = requests.get(
            url,
            params={"url": linkedin_url, "use_cache": "if-present"},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=_TIMEOUT,
        )
        if resp.status_code == 404:
            return {"ok": False, "configured": True, "reason": "Not found on LinkedIn"}
        resp.raise_for_status()
        return {"ok": True, "configured": True, "profile": resp.json()}
    except Exception as e:
        logger.warning(f"LinkedIn enrichment request failed: {e}")
        return {"ok": False, "configured": True, "reason": str(e)}


def enrich_person(linkedin_url: str, *, organization_id: str | None = None) -> dict[str, Any]:
    """Fetch a person's LinkedIn profile. Never raises."""
    return _fetch(_PERSON_URL, linkedin_url, organization_id)


def enrich_company(linkedin_url: str, *, organization_id: str | None = None) -> dict[str, Any]:
    """Fetch a company's LinkedIn profile. Never raises."""
    return _fetch(_COMPANY_URL, linkedin_url, organization_id)


_INDUSTRY_MAP = {
    "computer software": "technology", "information technology and services": "technology",
    "internet": "technology", "computer & network security": "technology",
    "financial services": "finance", "banking": "finance", "investment management": "finance",
    "hospital & health care": "healthcare", "health, wellness and fitness": "healthcare",
    "medical practice": "healthcare", "education management": "education",
    "higher education": "education", "e-learning": "education",
    "manufacturing": "manufacturing", "industrial automation": "manufacturing",
    "retail": "retail", "consumer goods": "retail", "real estate": "real_estate",
    "staffing and recruiting": "staffing", "human resources": "recruitment",
    "marketing and advertising": "agency", "management consulting": "agency",
}


def map_industry(raw: str | None) -> str:
    """Map Proxycurl's free-text industry into this platform's Industry enum values."""
    if not raw:
        return "other"
    return _INDUSTRY_MAP.get(raw.strip().lower(), "other")


# Transparent, editable ICP thresholds — not a black-box model. A founder
# can see exactly why a contact scored the way it did.
ICP_TARGET_INDUSTRIES = {"technology", "staffing", "recruitment", "agency"}
ICP_EMPLOYEE_RANGE = (10, 2000)


def score_icp_fit(industry: str, employee_count: int | None) -> dict[str, Any]:
    """A simple, explainable ICP score from real enriched fields."""
    reasons = []
    score = 0

    if industry in ICP_TARGET_INDUSTRIES:
        score += 50
        reasons.append(f"industry '{industry}' is a target vertical")
    else:
        reasons.append(f"industry '{industry}' is outside target verticals")

    if employee_count is not None:
        lo, hi = ICP_EMPLOYEE_RANGE
        if lo <= employee_count <= hi:
            score += 50
            reasons.append(f"company size {employee_count} is in target range ({lo}-{hi})")
        else:
            reasons.append(f"company size {employee_count} is outside target range ({lo}-{hi})")
    else:
        reasons.append("company size unknown")

    fit = "high" if score >= 75 else "medium" if score >= 50 else "low"
    return {"score": score, "fit": fit, "reasons": reasons}
