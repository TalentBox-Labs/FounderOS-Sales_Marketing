from __future__ import annotations

import json
from typing import Any

from revenue_os.config import settings

_SYSTEM_SDR = (
    "You are an SDR writing outreach for a founder. Be concise, specific to "
    "the context you're given, and never generic — no merge-tag-shaped filler."
)


def _chat(system: str, user: str, max_tokens: int = 300) -> str | None:
    """One-shot chat completion. Returns None if unconfigured or the call fails."""
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or None
    except Exception:
        return None


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


def generate_linkedin_opener(
    prospect_name: str,
    company_name: str,
    context: str | None = None,
) -> dict[str, str]:
    """A connection note (LinkedIn caps these at 300 characters) plus a
    follow-up DM to send once the connection is accepted."""
    raw = _chat(
        _SYSTEM_SDR + " Never open with a pitch — sound like a peer, not a vendor.",
        (
            f"Write LinkedIn outreach to {prospect_name} at {company_name}.\n"
            f"Context: {context or 'no additional context'}\n\n"
            "Return strict JSON: {\"connection_note\": \"<=300 chars, no pitch, "
            "references something real about them\", \"follow_up_dm\": \"a short "
            "message to send after they accept, still no hard pitch\"}"
        ),
        max_tokens=350,
    )
    if raw:
        try:
            parsed = json.loads(raw)
            note = str(parsed["connection_note"])[:300]
            dm = str(parsed["follow_up_dm"])
            if note and dm:
                return {"connection_note": note, "follow_up_dm": dm}
        except Exception:
            pass
    return _fallback_linkedin_opener(prospect_name, company_name, context)


def _fallback_linkedin_opener(
    prospect_name: str,
    company_name: str,
    context: str | None = None,
) -> dict[str, str]:
    note = f"Hi {prospect_name} — came across {company_name} and would love to connect."
    dm = (
        f"Thanks for connecting, {prospect_name}. "
        f"{context or f'Curious how things are going at {company_name}.'} "
        "No agenda — just wanted to say hi."
    )
    return {"connection_note": note[:300], "follow_up_dm": dm}


_DEFAULT_SEQUENCE_TEMPLATE = [
    {"delay_days": 0, "action_type": "send_email", "subject": "Quick thought for {company}",
     "body": "Hi {name}, wanted to reach out directly given what {company} is working on."},
    {"delay_days": 2, "action_type": "linkedin_connect", "subject": "LinkedIn connect",
     "body": "Hi {name} — following up from my email, would love to connect here too."},
    {"delay_days": 4, "action_type": "send_email", "subject": "Re: Quick thought for {company}",
     "body": "Following up in case my last note got buried — still think this is relevant to {company}."},
    {"delay_days": 7, "action_type": "linkedin_message", "subject": "LinkedIn follow-up",
     "body": "Hi {name}, sharing a quick resource that might be useful for {company} either way."},
    {"delay_days": 11, "action_type": "send_email", "subject": "One more try",
     "body": "Last note from me on this — happy to pick it back up whenever it's useful for {company}."},
    {"delay_days": 16, "action_type": "send_email", "subject": "Closing the loop",
     "body": "Assuming the timing isn't right — I'll leave this here, feel free to reach out if that changes."},
]


def generate_followup_sequence(
    prospect_name: str,
    company_name: str,
    context: str | None = None,
    num_steps: int = 6,
) -> list[dict]:
    """A 5-7 touch sequence mixing email and LinkedIn. Steps after the first
    carry a plain-English condition (e.g. "only if no reply yet") — this is
    advisory copy for whoever runs the sequence, not an auto-branching engine."""
    num_steps = max(5, min(7, num_steps))
    raw = _chat(
        _SYSTEM_SDR,
        (
            f"Build a {num_steps}-touch follow-up sequence for {prospect_name} at {company_name}, "
            f"alternating email and LinkedIn. Context: {context or 'no additional context'}\n\n"
            "Return strict JSON: a list of objects, each with: delay_days (int, days after the "
            "previous step), action_type (one of send_email, linkedin_message, linkedin_connect), "
            "subject (short), body (the message, personalized, no merge tags), "
            "condition (plain English — when to send this step, e.g. 'only if no reply to step 2')."
        ),
        max_tokens=1200,
    )
    if raw:
        try:
            parsed = json.loads(raw)
            steps = []
            for i, step in enumerate(parsed, start=1):
                steps.append({
                    "step_order": i,
                    "delay_days": int(step.get("delay_days", i * 2)),
                    "action_type": str(step.get("action_type", "send_email")),
                    "subject": str(step.get("subject", ""))[:500],
                    "body": str(step.get("body", "")),
                    "condition": str(step.get("condition", "")) or None,
                })
            if len(steps) >= 5:
                return steps
        except Exception:
            pass
    return _fallback_sequence(prospect_name, company_name, num_steps)


def _fallback_sequence(prospect_name: str, company_name: str, num_steps: int) -> list[dict]:
    steps = []
    for i, tmpl in enumerate(_DEFAULT_SEQUENCE_TEMPLATE[:num_steps], start=1):
        steps.append({
            "step_order": i,
            "delay_days": tmpl["delay_days"],
            "action_type": tmpl["action_type"],
            "subject": tmpl["subject"].format(company=company_name),
            "body": tmpl["body"].format(name=prospect_name, company=company_name),
            "condition": "only if no reply to the previous step" if i > 1 else None,
        })
    return steps


_REPLY_CATEGORIES = {"not_interested", "send_more_info", "wrong_person", "interested", "other"}


def classify_and_draft_reply(
    prospect_name: str,
    company_name: str,
    reply_text: str,
    context: str | None = None,
) -> dict[str, str]:
    """Classify an inbound reply and draft a response in the same category.
    The draft is filed for approval — this never sends on its own."""
    raw = _chat(
        _SYSTEM_SDR + " Match the prospect's tone and pace — don't oversell.",
        (
            f"{prospect_name} at {company_name} replied to outreach. Context: {context or 'none'}\n\n"
            f"Their reply:\n\"\"\"\n{reply_text}\n\"\"\"\n\n"
            "Classify it as exactly one of: not_interested, send_more_info, wrong_person, "
            "interested, other. Then draft a short reply matching that category and the "
            "prospect's tone.\n\n"
            "Return strict JSON: {\"category\": \"...\", \"draft_reply\": \"...\"}"
        ),
        max_tokens=350,
    )
    if raw:
        try:
            parsed = json.loads(raw)
            category = str(parsed.get("category", "")).strip()
            draft = str(parsed.get("draft_reply", "")).strip()
            if category in _REPLY_CATEGORIES and draft:
                return {"category": category, "draft_reply": draft}
        except Exception:
            pass
    return _fallback_classify_reply(prospect_name, reply_text)


def _fallback_classify_reply(prospect_name: str, reply_text: str) -> dict[str, str]:
    text = (reply_text or "").lower()
    if "not interested" in text or "no thanks" in text or "remove me" in text:
        category = "not_interested"
        draft = f"Totally understand, {prospect_name} — I'll close this out. Thanks for the reply."
    elif "wrong person" in text or "not the right" in text or "not my area" in text:
        category = "wrong_person"
        draft = f"Appreciate the redirect, {prospect_name} — could you point me to the right person?"
    elif "send" in text and ("more info" in text or "details" in text):
        category = "send_more_info"
        draft = f"Happy to, {prospect_name} — sending over a bit more detail shortly."
    elif "interested" in text or "sounds good" in text or "let's talk" in text:
        category = "interested"
        draft = f"Great to hear, {prospect_name} — do you have 15 minutes this week to talk it through?"
    else:
        category = "other"
        draft = f"Thanks for the reply, {prospect_name} — following up shortly."
    return {"category": category, "draft_reply": draft}


# ═══════════════════════════════════════════════════════════════════════════
# Marketing Agent crew — same pattern throughout: OpenAI if configured, a
# real non-fabricated fallback otherwise, never an exception.
# ═══════════════════════════════════════════════════════════════════════════

_SYSTEM_MARKETER = (
    "You are a sharp B2B marketing strategist for a founder-led company. "
    "Be specific and grounded in the data you're given — never invent facts, "
    "numbers, or sources that weren't provided to you."
)


def _chat_json(system: str, user: str, max_tokens: int, fallback: dict) -> dict:
    """_chat() that expects JSON back; returns fallback untouched on any
    missing config, malformed output, or provider failure."""
    raw = _chat(system, user, max_tokens=max_tokens)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return fallback


def synthesize_market_research(signals: dict[str, Any], context: str = "") -> dict[str, Any]:
    """Agent 1 (Market Research) — turns raw external signals (Reddit/HN
    threads, competitor data) into insights and opportunities. Signals
    that came back empty are named as gaps, never quietly papered over."""
    reddit = signals.get("reddit", [])
    hn = signals.get("hackernews", [])
    competitors = signals.get("competitors", [])
    unavailable = signals.get("unavailable_channels", [])

    fallback_insights = []
    if reddit:
        fallback_insights.append(f"{len(reddit)} relevant Reddit discussions found — top: \"{reddit[0]['title']}\"")
    if hn:
        fallback_insights.append(f"{len(hn)} relevant Hacker News stories found — top: \"{hn[0]['title']}\"")
    if competitors:
        fallback_insights.append(f"Tracked {len(competitors)} competitor(s): {', '.join(c.get('name', '?') for c in competitors)}")
    if not fallback_insights:
        fallback_insights.append("No external signals returned this pass — check that Reddit/HN are reachable and competitors are configured.")
    fallback = {
        "insights": fallback_insights,
        "opportunities": ["Review raw signals manually — no LLM configured to synthesize deeper opportunities."],
        "gaps": [f"No data available for: {', '.join(unavailable)}"] if unavailable else [],
    }
    if not settings.OPENAI_API_KEY:
        return fallback

    signal_text = json.dumps({"reddit": reddit[:5], "hackernews": hn[:5], "competitors": competitors}, default=str)[:4000]
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Company context: {context or 'none provided'}\n\n"
            f"Raw signals gathered today:\n{signal_text}\n\n"
            f"Channels with no data this pass: {', '.join(unavailable) or 'none'}\n\n"
            "Return strict JSON: {\"insights\": [3-5 short specific findings], "
            "\"opportunities\": [2-4 concrete marketing opportunities these findings suggest], "
            "\"gaps\": [channels/topics worth investigating manually]}"
        ),
        max_tokens=600, fallback=fallback,
    )


def generate_customer_persona(crm_summary: str) -> dict[str, str]:
    """Agent 2 (Customer Persona) — built from real CRM aggregates, not
    invented demographics."""
    fallback = {
        "name": "Primary Buyer",
        "summary": f"Derived from CRM data: {crm_summary}",
        "pain_points": "Not enough closed-won data yet to infer specific pain points.",
        "motivations": "Not enough data yet.",
        "objections": "Not enough data yet.",
        "messaging": "Lead with concrete outcomes once more deals close — persona will sharpen automatically.",
    }
    raw = _chat(
        _SYSTEM_MARKETER,
        (
            f"Build a buyer persona from this real CRM data (no invented demographics): {crm_summary}\n\n"
            "Return strict JSON: {\"name\": \"short persona name\", \"summary\": \"2-3 sentences\", "
            "\"pain_points\": \"...\", \"motivations\": \"...\", \"objections\": \"...\", "
            "\"messaging\": \"how to talk to this persona\"}"
        ),
        max_tokens=500,
    )
    if raw:
        try:
            parsed = json.loads(raw)
            if all(k in parsed for k in ("name", "summary")):
                return {**fallback, **parsed}
        except Exception:
            pass
    return fallback


def generate_content_calendar(context: str, num_weeks: int = 4) -> dict[str, Any]:
    """Agent 3 (Content Strategy) — a monthly theme + weekly topics."""
    fallback = {
        "monthly_theme": "Product education and customer proof",
        "weeks": [
            {"week": i + 1, "topic": f"Week {i + 1} focus (set OPENAI_API_KEY for tailored topics)",
             "channels": ["blog", "linkedin"], "content_ideas": ["Customer story", "How-to guide"]}
            for i in range(num_weeks)
        ],
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Build a {num_weeks}-week content calendar. Context: {context or 'none provided'}\n\n"
            "Return strict JSON: {\"monthly_theme\": \"...\", \"weeks\": [{\"week\": 1, \"topic\": \"...\", "
            "\"channels\": [\"blog\",\"linkedin\",...], \"content_ideas\": [\"...\", \"...\"]}]}"
        ),
        max_tokens=800, fallback=fallback,
    )


def generate_seo_strategy(keywords_summary: str, context: str = "") -> dict[str, Any]:
    """Agent 4 (SEO Strategy) — gaps and clusters from real tracked keywords."""
    fallback = {
        "topic_clusters": ["Group your tracked keywords by buyer intent to form clusters — no LLM configured to do this automatically."],
        "gaps": [], "internal_linking": [], "recommendations": ["Add more tracked keywords for a stronger baseline."],
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Tracked keywords: {keywords_summary}\nContext: {context or 'none provided'}\n\n"
            "Return strict JSON: {\"topic_clusters\": [\"cluster name: keywords\"], "
            "\"gaps\": [\"likely competitor keyword gaps\"], "
            "\"internal_linking\": [\"linking opportunities between tracked pages\"], "
            "\"recommendations\": [\"concrete next actions\"]}"
        ),
        max_tokens=600, fallback=fallback,
    )


def generate_geo_recommendations(title: str, content_excerpt: str) -> dict[str, Any]:
    """Agent 5 (GEO) — makes existing content more citable by AI answer
    engines: entity coverage, FAQ structure, semantic clarity."""
    fallback = {
        "entity_coverage": "Not evaluated — no LLM configured.",
        "faqs": ["Add 3-5 FAQ-style Q&As directly answering what buyers ask ChatGPT/Perplexity about this topic."],
        "structured_content_tips": ["Use clear H2/H3 headers with direct-answer opening sentences under each."],
        "citations_needed": ["Cite at least one primary source or original data point."],
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Title: {title}\nContent excerpt: {content_excerpt[:1500]}\n\n"
            "Evaluate this for Generative Engine Optimization (visibility in ChatGPT/Claude/Gemini/Perplexity/"
            "Google AI Overviews). Return strict JSON: {\"entity_coverage\": \"what's missing\", "
            "\"faqs\": [\"suggested FAQ questions this content should answer\"], "
            "\"structured_content_tips\": [\"...\"], \"citations_needed\": [\"...\"]}"
        ),
        max_tokens=500, fallback=fallback,
    )


def generate_long_form_content(content_type: str, topic: str, context: str = "") -> dict[str, str]:
    """Agent 6 (Content Writer) — blog/landing/case-study/comparison copy."""
    fallback = {
        "title": f"{topic} — {content_type}",
        "content": f"[Draft placeholder — configure OPENAI_API_KEY for a real draft]\n\nTopic: {topic}\nType: {content_type}\nContext: {context}",
        "tags": [content_type],
    }
    return _chat_json(
        _SYSTEM_MARKETER + " Write in a clear, confident, non-hypey brand voice.",
        (
            f"Write a {content_type} about: {topic}\nContext: {context or 'none provided'}\n\n"
            "Return strict JSON: {\"title\": \"...\", \"content\": \"full markdown content, 400-800 words\", "
            "\"tags\": [\"2-4 relevant tags\"]}"
        ),
        max_tokens=1500, fallback=fallback,
    )


def generate_linkedin_post(post_type: str, topic: str, context: str = "") -> str:
    """Agent 7 (LinkedIn Content) — founder-voice posts, not corporate-speak."""
    raw = _chat(
        _SYSTEM_MARKETER + " Write like a founder posting to their own network — first person, no corporate voice, no hashtag spam.",
        f"Write a LinkedIn {post_type} post about: {topic}\nContext: {context or 'none provided'}",
        max_tokens=400,
    )
    return raw or (
        f"[{post_type}] {topic}\n\n{context or 'Configure OPENAI_API_KEY for a real founder-voice draft.'}"
    )


def generate_social_variants(topic: str, context: str, platforms: list[str]) -> dict[str, str]:
    """Agent 8 (Social Media) — one variant per platform, same core message."""
    fallback = {p: f"[{p}] {topic} — {context or 'configure OPENAI_API_KEY for tailored copy'}" for p in platforms}
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Topic: {topic}\nContext: {context or 'none provided'}\nPlatforms: {', '.join(platforms)}\n\n"
            "Write one platform-native variant per platform (tone/length/hashtag conventions differ per platform). "
            f"Return strict JSON: an object keyed by platform name, values are the post text. Keys must be exactly: {platforms}"
        ),
        max_tokens=700, fallback=fallback,
    )


def generate_video_script(topic: str, context: str = "") -> dict[str, Any]:
    """Agent 9 (Video Strategy) — hook, talking points, B-roll, caption."""
    fallback = {
        "hook": f"Ever wondered about {topic}?",
        "talking_points": [f"Configure OPENAI_API_KEY for a real script on: {topic}"],
        "b_roll": ["Product UI screen recording", "Team working shot"],
        "caption": f"{topic} — {context}",
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Plan a short video on: {topic}\nContext: {context or 'none provided'}\n\n"
            "Return strict JSON: {\"hook\": \"first 3 seconds\", \"talking_points\": [\"3-5 beats\"], "
            "\"b_roll\": [\"2-4 visual suggestions\"], \"caption\": \"social caption with a CTA\"}"
        ),
        max_tokens=500, fallback=fallback,
    )


def generate_creative_brief(asset_type: str, topic: str, context: str = "") -> dict[str, str]:
    """Agent 10 (Creative Design) — a brief for a designer or image-gen
    tool, not a generated image (no image-gen provider is wired up here)."""
    fallback = {
        "concept": f"{asset_type} concept for: {topic}",
        "headline": topic,
        "visual_direction": "Configure OPENAI_API_KEY for a specific visual direction.",
        "copy": context or "",
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Write a creative brief for a {asset_type} about: {topic}\nContext: {context or 'none provided'}\n\n"
            "Return strict JSON: {\"concept\": \"one-line creative concept\", \"headline\": \"headline text\", "
            "\"visual_direction\": \"colors/imagery/layout guidance for a designer\", \"copy\": \"any on-asset copy\"}"
        ),
        max_tokens=400, fallback=fallback,
    )


def generate_email_campaign(campaign_type: str, context: str = "") -> dict[str, str]:
    """Agent 11 (Email Marketing) — newsletter/nurture/announcement copy."""
    fallback = {
        "subject": f"{campaign_type.replace('_', ' ').title()}",
        "preview_text": "",
        "body": f"[Configure OPENAI_API_KEY for a real draft]\n\n{context}",
        "cta": "Learn more",
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Write a {campaign_type} marketing email. Context: {context or 'none provided'}\n\n"
            "Return strict JSON: {\"subject\": \"...\", \"preview_text\": \"...\", \"body\": \"full email body\", \"cta\": \"button text\"}"
        ),
        max_tokens=600, fallback=fallback,
    )


def generate_whatsapp_campaign(campaign_type: str, context: str = "") -> dict[str, str]:
    """Agent 12 (WhatsApp Marketing) — short, personal, WhatsApp-native copy."""
    raw = _chat(
        _SYSTEM_MARKETER + " WhatsApp copy is short, personal, and conversational — not an email crammed into a text.",
        f"Write a {campaign_type} WhatsApp message. Context: {context or 'none provided'}",
        max_tokens=200,
    )
    return {"message": raw or f"[{campaign_type}] {context or 'Configure OPENAI_API_KEY for a real draft.'}"}


def generate_campaign_plan(goal: str, channels: list[str], context: str = "") -> dict[str, Any]:
    """Agent 13 (Campaign Manager) — timeline + KPIs tying channels to one goal."""
    fallback = {
        "timeline": [{"phase": "Launch", "channels": channels, "notes": "Configure OPENAI_API_KEY for a detailed timeline."}],
        "kpis": ["Define specific KPIs per channel."],
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"Plan a multi-channel campaign. Goal: {goal}\nChannels: {', '.join(channels)}\nContext: {context or 'none'}\n\n"
            "Return strict JSON: {\"timeline\": [{\"phase\": \"...\", \"channels\": [...], \"notes\": \"...\"}], "
            "\"kpis\": [\"3-5 measurable KPIs\"]}"
        ),
        max_tokens=700, fallback=fallback,
    )


def generate_marketing_exec_summary(metrics_summary: str) -> str:
    """Agent 15 (Analytics & Attribution) — a founder-readable summary of
    real metrics, not a fabricated report."""
    raw = _chat(
        _SYSTEM_MARKETER,
        f"Write a 3-5 sentence executive summary of these real marketing metrics, with one clear optimization recommendation:\n{metrics_summary}",
        max_tokens=300,
    )
    return raw or f"Metrics summary (configure OPENAI_API_KEY for a narrative summary):\n{metrics_summary}"


def generate_cro_recommendations(funnel_summary: str) -> list[dict[str, str]]:
    """Agent 18 (CRO) — recommendations grounded in the real funnel numbers passed in."""
    fallback = [{"issue": "No LLM configured", "recommendation": f"Review this funnel data manually: {funnel_summary}", "impact": "unknown"}]
    raw = _chat(
        _SYSTEM_MARKETER,
        (
            f"Real funnel/conversion data: {funnel_summary}\n\n"
            "Identify the weakest stage(s) and suggest concrete fixes. Return strict JSON: a list of objects "
            "with keys: issue, recommendation, impact (low/medium/high)."
        ),
        max_tokens=500,
    )
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                return parsed
        except Exception:
            pass
    return fallback


def generate_product_marketing_kit(feature: str, context: str = "") -> dict[str, str]:
    """Agent 20 (Product Marketing) — launch announcement + enablement angle."""
    fallback = {
        "announcement": f"Introducing: {feature}",
        "one_pager_summary": context or "Configure OPENAI_API_KEY for a real summary.",
        "demo_talking_points": "Configure OPENAI_API_KEY for real talking points.",
        "comparison_angle": "Configure OPENAI_API_KEY for a competitive angle.",
    }
    return _chat_json(
        _SYSTEM_MARKETER,
        (
            f"New feature/launch: {feature}\nContext: {context or 'none provided'}\n\n"
            "Return strict JSON: {\"announcement\": \"1-sentence announcement\", \"one_pager_summary\": \"3-4 sentences\", "
            "\"demo_talking_points\": \"key points for a sales demo\", \"comparison_angle\": \"how this compares to alternatives\"}"
        ),
        max_tokens=500, fallback=fallback,
    )


def draft_community_reply(thread_title: str, thread_body: str, context: str = "") -> str:
    """Agent 16 (Community Engagement) — a genuinely helpful reply, not a
    disguised pitch. Filed for approval before it's ever posted."""
    raw = _chat(
        _SYSTEM_MARKETER + " Reply like a knowledgeable community member, not a marketer. Only mention your "
        "product if it's genuinely the most helpful answer — otherwise just help.",
        f"Thread: \"{thread_title}\"\n{thread_body[:800]}\n\nCompany context: {context or 'none provided'}\n\nDraft a reply.",
        max_tokens=300,
    )
    return raw or f"[Configure OPENAI_API_KEY for a drafted reply to: {thread_title}]"


def generate_partnership_pitch(partner_name: str, partner_context: str, our_context: str = "") -> str:
    """Agent 19 (Partnership & Influencer) — a genuine collaboration pitch,
    not a form-letter affiliate ask."""
    raw = _chat(
        _SYSTEM_MARKETER + " Write a short, specific outreach note — reference something real about them, propose a concrete collaboration, no generic flattery.",
        f"Partner: {partner_name}\nWhat we know about them: {partner_context}\nOur context: {our_context or 'none provided'}",
        max_tokens=250,
    )
    return raw or f"[Configure OPENAI_API_KEY for a drafted pitch to {partner_name}]"


def classify_sentiment(text: str) -> str:
    """Agent 17 (Brand Monitoring) — positive/neutral/negative, LLM if
    configured, a plain keyword heuristic otherwise (never fabricated)."""
    raw = _chat(
        "Classify sentiment. Reply with exactly one word: positive, neutral, or negative.",
        text[:1000], max_tokens=5,
    )
    if raw:
        word = raw.strip().lower().split()[0] if raw.strip() else ""
        if word in ("positive", "neutral", "negative"):
            return word
    lowered = text.lower()
    positive_words = ("love", "great", "amazing", "excellent", "recommend", "awesome")
    negative_words = ("hate", "terrible", "awful", "worst", "broken", "disappointed", "bug")
    if any(w in lowered for w in negative_words):
        return "negative"
    if any(w in lowered for w in positive_words):
        return "positive"
    return "neutral"
