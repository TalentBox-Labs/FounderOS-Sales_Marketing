from __future__ import annotations

import json

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


def generate_follow_up_email(
    prospect_name: str,
    company_name: str,
    *,
    step: int,
    context: str | None = None,
    prior_subject: str | None = None,
) -> dict[str, str]:
    """Draft a single follow-up email (proposal-only — never sends)."""
    subject_hint = prior_subject or f"Re: Quick thought for {company_name}"
    raw = _chat(
        _SYSTEM_SDR,
        (
            f"Write follow-up #{step} for {prospect_name} at {company_name}. "
            f"Prior subject: {subject_hint}. Context: {context or 'prior cold outreach sent'}\n\n"
            "Return strict JSON: {\"subject\": \"...\", \"body\": \"...\", \"rationale\": \"...\"}"
        ),
        max_tokens=400,
    )
    if raw:
        try:
            parsed = json.loads(raw)
            subject = str(parsed.get("subject", "")).strip()
            body = str(parsed.get("body", "")).strip()
            rationale = str(parsed.get("rationale", "")).strip()
            if subject and body:
                return {"subject": subject[:500], "body": body, "rationale": rationale}
        except Exception:
            pass
    return _fallback_follow_up_email(prospect_name, company_name, step=step, prior_subject=subject_hint)


def _fallback_follow_up_email(
    prospect_name: str,
    company_name: str,
    *,
    step: int,
    prior_subject: str,
) -> dict[str, str]:
    if step == 1:
        body = (
            f"Hi {prospect_name},\n\n"
            f"Circling back on my note about {company_name} — still think there could be a fit.\n\n"
            f"Open to a quick chat this week?\n\nBest"
        )
        rationale = "First bounded follow-up after initial outreach"
    else:
        body = (
            f"Hi {prospect_name},\n\n"
            f"Last quick bump in case my earlier note got buried — happy to reconnect whenever "
            f"timing works for {company_name}.\n\nBest"
        )
        rationale = "Second bounded follow-up; cadence limit applies"
    return {
        "subject": prior_subject,
        "body": body,
        "rationale": rationale,
    }


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
