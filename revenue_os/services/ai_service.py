from __future__ import annotations

from revenue_os.config import settings


def generate_cold_email(
    prospect_name: str,
    company_name: str,
    context: str | None = None,
) -> str:
    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an SDR writing cold outreach emails. "
                        "Be concise, personalized, and value-driven.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Write a cold email to {prospect_name} at {company_name}. "
                            f"Context: {context or 'Introducing our platform'}"
                        ),
                    },
                ],
                temperature=0.7,
                max_tokens=300,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            return _fallback_cold_email(prospect_name, company_name, context)
    return _fallback_cold_email(prospect_name, company_name, context)


def _fallback_cold_email(
    prospect_name: str,
    company_name: str,
    context: str | None = None,
) -> str:
    return (
        f"Subject: Quick thought for {company_name}\n\n"
        f"Hi {prospect_name},\n\n"
        f"I noticed {company_name} is doing interesting work. "
        f"{context or 'I think we could help streamline your operations.'}\n\n"
        f"Would you be open to a 15-minute chat this week?\n\n"
        f"Best,\nFounder"
    )
