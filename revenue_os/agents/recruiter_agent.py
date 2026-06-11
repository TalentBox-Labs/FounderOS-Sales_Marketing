from __future__ import annotations

from typing import Any

from revenue_os.config import settings


def _has_llm() -> bool:
    return bool(settings.OPENAI_API_KEY) or bool(settings.GEMINI_API_KEY)


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


def match_candidate_to_job(
    candidate_name: str,
    candidate_skills: str,
    candidate_experience: str,
    job_title: str,
    job_requirements: str,
) -> dict[str, Any]:
    if not _has_llm():
        return _fallback_match(
            candidate_skills, candidate_experience, job_requirements
        )

    from crewai import Agent, Crew, Process, Task

    llm = _build_llm()
    agent = Agent(
        role="Recruiter AI Agent",
        goal="Match candidates to job descriptions with precision scoring",
        backstory="You are an expert technical recruiter who has placed "
        "hundreds of candidates. You evaluate skill overlap, experience "
        "relevance, culture fit signals, and career trajectory to determine "
        "match quality.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=(
            f"Evaluate this candidate for the role:\n\n"
            f"Candidate: {candidate_name}\n"
            f"Skills: {candidate_skills}\n"
            f"Experience: {candidate_experience}\n\n"
            f"Job Title: {job_title}\n"
            f"Requirements: {job_requirements}\n\n"
            "Return a JSON object with:\n"
            "- match_score (0-100)\n"
            "- skill_match (percentage)\n"
            "- experience_match (seniority level match: "
            "exceeds/meets/partial/below)\n"
            "- strengths (list of 2-3 key strengths)\n"
            "- gaps (list of any gaps or missing requirements)\n"
            "- recommendation (strong_yes/yes/maybe/no)\n"
            "- interview_questions (2-3 suggested questions)\n\n"
            "Return ONLY the JSON object."
        ),
        expected_output="JSON object with match evaluation",
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

    json_match = re.search(r"\{.*\}", result, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return _fallback_match(
        candidate_skills, candidate_experience, job_requirements
    )


def screen_resume(
    resume_text: str,
    job_requirements: str,
) -> dict[str, Any]:
    if not _has_llm():
        return _fallback_screen()

    from crewai import Agent, Crew, Process, Task

    llm = _build_llm()
    agent = Agent(
        role="Resume Screener",
        goal="Screen resumes against job requirements and extract key insights",
        backstory="You are an AI trained to screen resumes at scale. "
        "You identify relevant experience, key skills, red flags, "
        "and provide a structured screening decision.",
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=(
            f"Screen this resume:\n\n{resume_text[:3000]}\n\n"
            f"Against these requirements:\n{job_requirements}\n\n"
            "Return JSON with:\n"
            "- screening_decision (advance/reject/maybe)\n"
            "- key_skills_found (list)\n"
            "- experience_relevance (high/medium/low)\n"
            "- red_flags (list of concerns)\n"
            "- green_flags (list of positives)\n"
            "- summary (1-2 sentence summary)\n\n"
            "Return ONLY the JSON."
        ),
        expected_output="JSON screening result",
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

    json_match = re.search(r"\{.*\}", result, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return _fallback_screen()


def _fallback_match(
    candidate_skills: str,
    candidate_experience: str,
    job_requirements: str,
) -> dict[str, Any]:
    req_skills = set(
        s.strip().lower()
        for s in job_requirements.replace(",", " ").split()
    )
    cand_skills = set(
        s.strip().lower()
        for s in candidate_skills.replace(",", " ").split()
    )
    overlap = req_skills & cand_skills
    skill_match = round(len(overlap) / max(len(req_skills), 1) * 100)

    return {
        "match_score": skill_match,
        "skill_match": skill_match,
        "experience_match": "partial",
        "strengths": list(overlap)[:3],
        "gaps": list(req_skills - cand_skills)[:3],
        "recommendation": (
            "yes" if skill_match >= 70 else "maybe" if skill_match >= 40 else "no"
        ),
        "interview_questions": [
            "Tell me about your experience with the required tech stack.",
            "Describe a challenging project you worked on.",
        ],
    }


def _fallback_screen() -> dict[str, Any]:
    return {
        "screening_decision": "maybe",
        "key_skills_found": [],
        "experience_relevance": "medium",
        "red_flags": [],
        "green_flags": [],
        "summary": (
            "AI screening requires an API key. "
            "Set OPENAI_API_KEY or GEMINI_API_KEY in .env."
        ),
    }
