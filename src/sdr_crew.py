"""SDR (Sales Development Representative) Crew for autonomous lead outreach."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from src.base_crew import BaseCrew

logger = logging.getLogger(__name__)


class SDRCrew(BaseCrew):
    """Sales Development Representative Crew for autonomous lead engagement."""

    def __init__(self):
        """Initialize SDR crew."""
        super().__init__(crew_name="sdr")

    def build_agents_and_tasks(self):
        """Build SDR team: Researcher, Personalizer, Scheduler."""
        from crewai import Agent, Task

        # Researcher Agent
        researcher = Agent(
            role="Lead Researcher",
            goal="Research prospects to understand their company, role, and pain points",
            backstory=(
                "Expert researcher who digs deep into company information, "
                "recent news, and LinkedIn profiles to find relevant context for outreach."
            ),
            llm=self.llm,
            verbose=True,
        )

        # Personalizer Agent
        personalizer = Agent(
            role="Outreach Copywriter",
            goal="Create personalized, compelling outreach messages that get responses",
            backstory=(
                "Award-winning copywriter who crafts highly personalized messages "
                "that speak directly to prospect pain points and drive engagement."
            ),
            llm=self.llm,
            verbose=True,
        )

        # Scheduler Agent
        scheduler = Agent(
            role="Outreach Coordinator",
            goal="Schedule and track outreach activities across email and LinkedIn",
            backstory=(
                "Strategic coordinator who ensures consistent outreach timing, "
                "tracks engagement, and schedules follow-ups."
            ),
            llm=self.llm,
            verbose=True,
        )

        # Tasks
        research_task = Task(
            description=(
                "Research the following prospect and provide a brief profile:\n"
                "- Company overview and industry\n"
                "- Prospect's role and responsibilities\n"
                "- Recent company news or initiatives\n"
                "- Potential pain points\n"
                "\nProspect Information:\n{prospect_info}"
            ),
            agent=researcher,
            expected_output=(
                "Structured prospect profile with company context, role details, and identified pain points"
            ),
        )

        personalize_task = Task(
            description=(
                "Create a personalized outreach message based on the research:\n"
                "- Open with specific, relevant context about their company or role\n"
                "- Highlight specific value proposition\n"
                "- Include clear call-to-action (meeting, call, demo)\n"
                "- Keep to 150-200 words\n"
                "\nResearch Profile:\n{research_output}"
            ),
            agent=personalizer,
            expected_output="Personalized outreach message with compelling hook and clear CTA",
        )

        schedule_task = Task(
            description=(
                "Create an outreach schedule for the prospect:\n"
                "- Initial email outreach timing\n"
                "- LinkedIn connection message (if applicable)\n"
                "- Follow-up sequence (3 touches over 2 weeks)\n"
                "- Track engagement and adjust as needed\n"
                "\nPersonalized Message:\n{personalize_output}"
            ),
            agent=scheduler,
            expected_output="Outreach schedule with specific times and follow-up plan",
        )

        self.agents = [researcher, personalizer, scheduler]
        self.tasks = [research_task, personalize_task, schedule_task]

    def run_sdr_outreach(
        self,
        contact_name: str,
        company_name: str,
        role: str,
        email: str,
        linkedin_url: str | None = None,
    ) -> dict:
        """
        Execute SDR outreach workflow for a prospect.

        Args:
            contact_name: Prospect name
            company_name: Company name
            role: Job title/role
            email: Email address
            linkedin_url: LinkedIn profile URL (optional)

        Returns: Outreach plan and personalized messages.
        """
        logger.info(
            "Starting SDR outreach",
            extra={
                "contact": contact_name,
                "company": company_name,
                "email": email,
            },
        )

        prospect_info = f"""
Name: {contact_name}
Company: {company_name}
Role: {role}
Email: {email}
LinkedIn: {linkedin_url or 'Not provided'}
"""

        try:
            result = self.crew.kickoff(inputs={"prospect_info": prospect_info})

            logger.info(
                "SDR outreach completed",
                extra={"contact": contact_name, "status": "success"},
            )

            return {
                "ok": True,
                "contact": contact_name,
                "company": company_name,
                "status": "completed",
                "output": str(result),
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(
                "SDR outreach failed",
                extra={"contact": contact_name, "error": str(e)},
            )

            return {
                "ok": False,
                "contact": contact_name,
                "company": company_name,
                "status": "failed",
                "error": str(e),
            }

    def validate_output(self, output: str) -> bool:
        """Validate SDR crew output contains required elements."""
        required = ["personalized", "outreach", "schedule", "follow-up"]
        output_lower = output.lower()
        return all(req in output_lower for req in required)
