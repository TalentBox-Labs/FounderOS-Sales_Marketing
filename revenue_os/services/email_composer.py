from __future__ import annotations

import json
import re
from typing import Any

from revenue_os.config import settings

ANGLES = [
    "trigger_event",
    "pain_point",
    "social_proof",
    "warm_intro",
    "competitor_mention",
    "content_gate",
]


def compose(
    profile: dict[str, Any],
    angle: str | None = None,
    product_description: str | None = None,
) -> dict[str, Any]:
    if angle and angle not in ANGLES:
        angle = None

    if settings.OPENAI_API_KEY:
        try:
            return _ai_compose(profile, angle, product_description)
        except Exception:
            return _template_fallback(profile, angle)
    return _template_fallback(profile, angle)


def _ai_compose(
    profile: dict[str, Any],
    angle: str | None,
    product_description: str | None,
) -> dict[str, Any]:
    from openai import OpenAI

    contact = profile.get("contact", {})
    company = profile.get("company") or {}
    signals = profile.get("signals", {})
    deal = profile.get("deal")
    outreach_history = profile.get("outreach_history", {})

    trigger_events = signals.get("trigger_events", [])
    intent_signals = signals.get("intent_signals", [])
    outreach_tips = signals.get("outreach_tips", "")
    icp_fit = signals.get("icp_fit", "medium")

    product = product_description or "Our platform"

    system_prompt = (
        "You are writing a personalized sales email for a human SDR to send "
        "from their own email account. Your goal is a reply or meeting booking.\n\n"
        "RULES:\n"
        "1. Hook MUST reference something real about the prospect or company — "
        "their title, trigger event, tech stack, hiring, funding.\n"
        "2. Keep the body under 150 words — scannable on mobile.\n"
        "3. No fluff, no fake urgency, no jargon.\n"
        "4. End with a specific low-friction CTA (reply with thought, 15-min call).\n"
        "5. Write conversational, not corporate.\n"
        "6. Return ONLY valid JSON with keys: subject, hook, body, cta, angle_used.\n"
    )

    user_prompt = f"Prospect: {contact.get('full_name', 'Unknown')}\n"
    user_prompt += f"Title: {contact.get('title', 'Unknown')}\n"
    user_prompt += f"Company: {company.get('name', 'Unknown')}\n"
    user_prompt += f"Industry: {company.get('industry', 'Unknown')}\n\n"

    if trigger_events:
        user_prompt += "Trigger events:\n" + "\n".join(
            f"- {e}" for e in trigger_events
        ) + "\n\n"
    if intent_signals:
        user_prompt += "Intent signals:\n" + "\n".join(
            f"- {s}" for s in intent_signals
        ) + "\n\n"
    if outreach_tips:
        user_prompt += f"Outreach tips: {outreach_tips}\n\n"
    if deal:
        user_prompt += (
            f"Active deal: {deal.get('name')} ({deal.get('stage')}, "
            f"${deal.get('value', 0):,})\n\n"
        )
    if outreach_history.get("previous_subjects"):
        user_prompt += "Previous email subjects sent:\n" + "\n".join(
            f"- {s}" for s in outreach_history["previous_subjects"][-5:]
        ) + "\n\n"

    user_prompt += f"Product: {product}\n"
    user_prompt += (
        f"Angle preferred: {angle or 'auto-select best'}\n\n"
    )
    user_prompt += (
        "Return JSON: { subject, hook, body, cta, angle_used }"
    )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    content = resp.choices[0].message.content or ""
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return _template_fallback(profile, angle)


def _template_fallback(
    profile: dict[str, Any],
    angle: str | None,
) -> dict[str, Any]:
    contact = profile.get("contact", {})
    company = profile.get("company") or {}
    signals = profile.get("signals", {})
    first_name = contact.get("first_name", "there")
    company_name = company.get("name", "your company")
    trigger_events = signals.get("trigger_events", [])

    if angle == "trigger_event" and trigger_events:
        hook = trigger_events[0]
        body = (
            f"I noticed {hook.lower()}. We help teams like {company_name} "
            f"streamline their sales outreach and close more deals."
        )
    elif company.get("industry"):
        hook = f"Thoughts on {company.get('industry')} sales process?"
        body = (
            f"We specialize in helping {company.get('industry')} companies "
            f"like {company_name} improve their pipeline velocity."
        )
    else:
        hook = f"Quick question for {company_name}"
        body = (
            f"I came across {company_name} and wanted to reach out. "
            f"We help teams improve their outreach and close rates."
        )

    return {
        "subject": hook,
        "hook": hook,
        "body": (
            f"Hi {first_name},\n\n"
            f"{body}\n\n"
            f"Would you be open to a 15-minute call this week?\n\n"
            f"Best,\n{os_get_founder_name()}"
        ),
        "cta": "Open to a 15-minute call this week?",
        "angle_used": angle or "generic",
    }


def os_get_founder_name() -> str:
    import os
    return os.getenv("FOUNDER_NAME", "Founder")
