from __future__ import annotations

from typing import Any

from revenue_os.config import settings


def _has_llm() -> bool:
    return bool(settings.OPENAI_API_KEY) or bool(settings.GEMINI_API_KEY)


def score_and_enrich_lead(
    company_name: str,
    company_domain: str | None = None,
    industry: str | None = None,
) -> dict[str, Any]:
    if not _has_llm():
        return _fallback_score(company_name, industry)

    from crewai import Agent, Task

    llm = _build_llm()
    agent = Agent(
        role="SDR Intelligence Agent",
        goal="Research leads and score them based on ICP fit and intent signals",
        backstory="You are an expert SDR who evaluates leads by analyzing "
        "company size, industry, tech stack, funding, and hiring signals. "
        "You provide structured scoring and enrichment data.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=(
            f"Research and score this lead:\n"
            f"Company: {company_name}\n"
            f"Domain: {company_domain or 'unknown'}\n"
            f"Industry: {industry or 'unknown'}\n\n"
            "Provide a JSON object with:\n"
            "- lead_score (0-100)\n"
            "- icp_fit (high/medium/low)\n"
            "- intent_signals (list of signals found)\n"
            "- enrichment (company_size estimate, likely_tech_stack, "
            "hiring_activity)\n"
            "- outreach_tips (2-3 sentence personalized tip)\n\n"
            "Return ONLY the JSON object, no markdown."
        ),
        expected_output="JSON object with lead_score, icp_fit, "
        "intent_signals, enrichment, outreach_tips",
        agent=agent,
    )

    return _run_crewai(agent, task)


def generate_outreach_sequence(
    prospect_name: str,
    company_name: str,
    industry: str | None = None,
) -> list[dict[str, Any]]:
    if not _has_llm():
        return _fallback_sequence(prospect_name, company_name)

    from crewai import Agent, Crew, LLM, Process, Task

    llm = _build_llm()
    agent = Agent(
        role="SDR Outreach Strategist",
        goal="Design multi-step outreach sequences that maximize reply rates",
        backstory="You are a senior SDR who has run thousands of outreach "
        "campaigns. You know what messaging works for each industry, "
        "and you design sequences that gradually build value and trust.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=(
            f"Design a 3-step outreach sequence for:\n"
            f"Prospect: {prospect_name}\n"
            f"Company: {company_name}\n"
            f"Industry: {industry or 'unknown'}\n\n"
            "Return a JSON array with 3 steps, each with:\n"
            "- step (1, 2, 3)\n"
            "- delay_days (days after previous step)\n"
            "- channel (email or linkedin)\n"
            "- subject (email subject line)\n"
            "- body (full message body)\n"
            "- goal (what this step aims to achieve)\n\n"
            "Make messages personalized, concise, and value-driven. "
            "Return ONLY the JSON array."
        ),
        expected_output="JSON array of 3 outreach steps",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = str(crew.kickoff())
    import json
    import re

    json_match = re.search(r"\[.*\]", result, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return _fallback_sequence(prospect_name, company_name)


def _run_crewai(agent, task) -> dict[str, Any]:
    from crewai import Crew, Process

    try:
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )

        result = str(crew.kickoff())
        import json
        import re

        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"[crewai] Agent execution failed: {e}", flush=True)

    return {"lead_score": 50, "icp_fit": "medium", "intent_signals": []}


def _build_llm():
    from crewai import LLM

    if settings.OPENAI_API_KEY:
        return LLM(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.2,
        )
    return LLM(
        model="gemini/gemini-2.0-flash",
        api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )


def _fallback_score(
    company_name: str,
    industry: str | None = None,
) -> dict[str, Any]:
    score = 50
    if industry in ("technology", "saas", "software"):
        score = 60
    elif industry in ("staffing", "recruitment", "agency"):
        score = 70
    return {
        "lead_score": score,
        "icp_fit": "medium",
        "intent_signals": ["company in target industry"],
        "enrichment": {
            "company_size": "unknown (API key required for enrichment)",
            "likely_tech_stack": "unknown",
            "hiring_activity": "unknown",
        },
        "outreach_tips": (
            f"Set OPENAI_API_KEY or GEMINI_API_KEY in .env "
            f"for AI-powered lead scoring."
        ),
    }


def _fallback_sequence(
    prospect_name: str,
    company_name: str,
) -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "delay_days": 0,
            "channel": "email",
            "subject": f"Quick thought for {company_name}",
            "body": (
                f"Hi {prospect_name},\n\n"
                f"I noticed {company_name}'s recent work. "
                f"Would you be open to a brief chat?\n\n"
                f"Best,\nFounder"
            ),
            "goal": "Start conversation",
        },
        {
            "step": 2,
            "delay_days": 3,
            "channel": "email",
            "subject": f"Re: {company_name}",
            "body": (
                f"Hi {prospect_name},\n\n"
                f"Following up on my previous message. "
                f"Would love to connect!\n\n"
                f"Best,\nFounder"
            ),
            "goal": "Follow up",
        },
        {
            "step": 3,
            "delay_days": 5,
            "channel": "linkedin",
            "subject": "",
            "body": (
                f"Hi {prospect_name}, I sent an email earlier this week. "
                f"Would be great to connect here as well!"
            ),
            "goal": "Multi-channel touch",
        },
    ]
