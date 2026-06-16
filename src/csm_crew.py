"""Customer Success Manager (CSM) Crew for account management and retention."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.base_crew import BaseCrew

logger = logging.getLogger(__name__)


class CSMCrew(BaseCrew):
    """Customer Success Manager Crew for account health, retention, and expansion."""

    def __init__(self):
        """Initialize CSM crew."""
        super().__init__(crew_name="csm")

    def build_agents_and_tasks(self):
        """Build CSM team: Account Manager, Health Monitor, Expansion Specialist."""
        from crewai import Agent, Task

        # Account Manager Agent
        account_manager = Agent(
            role="Account Manager",
            goal="Manage customer relationships, ensure satisfaction, and drive adoption",
            backstory=(
                "Experienced account manager who builds strong customer relationships, "
                "understands customer needs deeply, and ensures successful product adoption."
            ),
            llm=self.llm,
            verbose=True,
        )

        # Health Monitor Agent
        health_monitor = Agent(
            role="Customer Health Monitor",
            goal="Identify at-risk accounts early and recommend interventions",
            backstory=(
                "Data-driven analyst who monitors customer health signals, "
                "identifies churn risks early, and recommends proactive interventions."
            ),
            llm=self.llm,
            verbose=True,
        )

        # Expansion Specialist Agent
        expansion_specialist = Agent(
            role="Expansion Specialist",
            goal="Identify and execute expansion and upsell opportunities",
            backstory=(
                "Growth-focused specialist who identifies expansion opportunities, "
                "understands customer use cases, and drives revenue growth."
            ),
            llm=self.llm,
            verbose=True,
        )

        # Tasks
        health_assessment_task = Task(
            description=(
                "Assess the health of the customer account:\n"
                "- Review recent engagement and interactions\n"
                "- Analyze product usage and adoption metrics\n"
                "- Identify any concerning signals or trends\n"
                "- Rate overall account health\n"
                "\nAccount Information:\n{account_info}"
            ),
            agent=health_monitor,
            expected_output="Health assessment with signals and risk indicators",
        )

        retention_strategy_task = Task(
            description=(
                "Develop retention strategy for the account:\n"
                "- If at-risk: Create intervention plan with specific actions\n"
                "- If healthy: Identify engagement opportunities\n"
                "- Schedule check-ins and business reviews\n"
                "- Recommend success milestones\n"
                "\nHealth Assessment:\n{health_assessment}"
            ),
            agent=account_manager,
            expected_output="Retention strategy with specific actions and timeline",
        )

        expansion_plan_task = Task(
            description=(
                "Identify expansion opportunities:\n"
                "- Analyze current usage patterns\n"
                "- Identify adjacent use cases\n"
                "- Calculate expansion value potential\n"
                "- Develop expansion approach (education, trial, proposal)\n"
                "\nAccount Information:\n{account_info}\n"
                "Health Assessment:\n{health_assessment}"
            ),
            agent=expansion_specialist,
            expected_output="Expansion plan with opportunities and go-to-market approach",
        )

        self.agents = [health_monitor, account_manager, expansion_specialist]
        self.tasks = [health_assessment_task, retention_strategy_task, expansion_plan_task]

    def run_account_review(
        self,
        account_name: str,
        company_size: str,
        industry: str,
        adoption_stage: str,
        usage_level: str,
    ) -> dict:
        """
        Execute comprehensive account review.

        Args:
            account_name: Customer company name
            company_size: Small, Mid, Enterprise
            industry: Customer industry
            adoption_stage: Early, Growing, Mature
            usage_level: Low, Medium, High

        Returns: Health assessment, retention strategy, expansion plan.
        """
        logger.info(
            "Starting CSM account review",
            extra={
                "account": account_name,
                "stage": adoption_stage,
                "usage": usage_level,
            },
        )

        account_info = f"""
Account: {account_name}
Company Size: {company_size}
Industry: {industry}
Adoption Stage: {adoption_stage}
Usage Level: {usage_level}
Review Date: {datetime.now(timezone.utc).isoformat()}
"""

        try:
            result = self.crew.kickoff(inputs={"account_info": account_info})

            logger.info(
                "Account review completed",
                extra={"account": account_name, "status": "success"},
            )

            return {
                "ok": True,
                "account": account_name,
                "status": "completed",
                "output": str(result),
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(
                "Account review failed",
                extra={"account": account_name, "error": str(e)},
            )

            return {
                "ok": False,
                "account": account_name,
                "status": "failed",
                "error": str(e),
            }

    def validate_output(self, output: str) -> bool:
        """Validate CSM crew output contains required elements."""
        required = ["health", "assessment", "retention", "expansion"]
        output_lower = output.lower()
        return all(req in output_lower for req in required)
