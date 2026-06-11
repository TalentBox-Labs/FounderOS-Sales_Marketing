from __future__ import annotations

from revenue_os.agents.sdr_agent import score_and_enrich_lead

from . import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def score_lead_background(
    self, company_name: str, company_domain: str | None = None, industry: str | None = None
) -> dict:
    try:
        result = score_and_enrich_lead(
            company_name=company_name,
            company_domain=company_domain,
            industry=industry,
        )
        return result
    except Exception as exc:
        raise self.retry(exc=exc)
