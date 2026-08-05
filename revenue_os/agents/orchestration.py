"""Multi-agent orchestration and coordination."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
import uuid

logger = logging.getLogger(__name__)


class OrchestrationStrategy(Enum):
    """Agent orchestration strategies."""

    SEQUENTIAL = "sequential"  # Execute agents in order
    PARALLEL = "parallel"  # Execute all agents simultaneously
    HIERARCHICAL = "hierarchical"  # Manager agent delegates to team
    CONSENSUS = "consensus"  # Multiple agents vote on decision


@dataclass
class AgentWorkflow:
    """Multi-agent workflow."""

    id: str
    name: str
    description: str
    strategy: OrchestrationStrategy
    agents: list[str]  # agent type names
    trigger_condition: str  # when to start
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "strategy": self.strategy.value,
            "agents": self.agents,
            "trigger_condition": self.trigger_condition,
            "enabled": self.enabled,
        }


@dataclass
class WorkflowExecution:
    """Execution of a multi-agent workflow."""

    id: str
    workflow_id: str
    status: str  # pending, running, completed, failed
    started_at: datetime | None = None
    completed_at: datetime | None = None
    agent_results: dict[str, Any] = field(default_factory=dict)
    final_decision: str | None = None
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "final_decision": self.final_decision,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }


def seed_platform_agents() -> None:
    """Register the platform's built-in autonomous subsystems.

    register_agent() upserts, so this is safe (and cheap) to call on every
    startup — it gives the agent registry real content reflecting what the
    platform actually runs, instead of an empty shell nobody ever fills in.
    """
    AgentCoordinator.register_agent(
        "heartbeat", "operations",
        capabilities=["score_new_leads", "check_deals_at_risk", "snapshot_pipeline_metrics", "hermes_goal_check", "sync_gmail_inbox", "run_marketing_cycle"],
        description="Autonomous scheduler — runs the platform's background jobs on a fixed interval.",
    )
    AgentCoordinator.register_agent(
        "hermes", "sales_manager",
        capabilities=["goal_planning", "propose_outreach"],
        description="Goal-based planner — turns a target metric into a plan and executes it every heartbeat.",
    )
    AgentCoordinator.register_agent(
        "copilot", "custom",
        capabilities=["chat", "run_scoring", "create_goal", "run_goal_check"],
        description="Founder-facing chat interface — reads live data and runs platform actions on request.",
    )
    AgentCoordinator.register_agent(
        "workflow_engine", "operations",
        capabilities=["event_automation"],
        description="Event-driven automation — runs conditions/actions when platform events fire.",
    )
    AgentCoordinator.register_agent(
        "n8n_bridge", "custom",
        capabilities=["external_automation"],
        description="Bridges platform events to n8n and receives results back via inbound webhooks.",
    )
    AgentCoordinator.register_agent(
        "icp_research_agent", "sdr",
        capabilities=["research_contact"],
        description="Pulls buying signals — funding rounds, recent job changes, company fit — from real LinkedIn data in one pass.",
    )
    AgentCoordinator.register_agent(
        "cold_email_agent", "sdr",
        capabilities=["draft_cold_email"],
        description="Drafts first-touch cold emails from a contact's real CRM context, not merge tags.",
    )
    AgentCoordinator.register_agent(
        "linkedin_opener_agent", "sdr",
        capabilities=["draft_linkedin_opener"],
        description="Drafts LinkedIn connection requests and follow-up DMs that don't read like a pitch.",
    )
    AgentCoordinator.register_agent(
        "followup_sequence_agent", "sdr",
        capabilities=["build_followup_sequence"],
        description="Builds 5-7 touch nurture sequences across email and LinkedIn.",
    )
    AgentCoordinator.register_agent(
        "objection_handler_agent", "sdr",
        capabilities=["handle_latest_reply"],
        description="Classifies inbound replies (not interested / send more info / wrong person) and drafts a matching response for approval.",
    )
    AgentCoordinator.register_agent(
        "marketing_orchestrator", "marketing_manager",
        capabilities=["run_marketing_cycle"],
        description="The AI CMO — runs the full research -> persona -> strategy -> content -> campaign -> analytics pipeline and coordinates the marketing agent crew.",
    )
    AgentCoordinator.register_agent(
        "market_research_agent", "marketing",
        capabilities=["run_market_research"],
        description="Tracks competitors, industry trends, and buyer pain points via real Reddit/Hacker News signals and competitor LinkedIn data.",
    )
    AgentCoordinator.register_agent(
        "customer_persona_agent", "marketing",
        capabilities=["update_customer_persona"],
        description="Builds and continuously refreshes buyer personas from real CRM data.",
    )
    AgentCoordinator.register_agent(
        "content_strategy_agent", "marketing",
        capabilities=["build_content_strategy"],
        description="Plans a content calendar grounded in tracked SEO keywords and active goals.",
    )
    AgentCoordinator.register_agent(
        "seo_strategy_agent", "marketing",
        capabilities=["build_seo_strategy"],
        description="Finds keyword gaps, topic clusters, and internal-linking opportunities from real tracked keywords.",
    )
    AgentCoordinator.register_agent(
        "geo_agent", "marketing",
        capabilities=["analyze_geo_readiness"],
        description="Optimizes content for AI answer engines (ChatGPT/Claude/Gemini/Perplexity) — entity coverage, FAQs, citations.",
    )
    AgentCoordinator.register_agent(
        "content_writer_agent", "marketing",
        capabilities=["write_content"],
        description="Writes blogs, landing pages, and case studies, publishing them as real Knowledge Base articles.",
    )
    AgentCoordinator.register_agent(
        "linkedin_content_agent", "marketing",
        capabilities=["draft_linkedin_content"],
        description="Drafts founder-led LinkedIn posts and announcements, filed for approval before posting.",
    )
    AgentCoordinator.register_agent(
        "social_media_agent", "marketing",
        capabilities=["draft_social_posts"],
        description="Drafts platform-specific variants for LinkedIn, X, Instagram, and more, filed for approval.",
    )
    AgentCoordinator.register_agent(
        "video_strategy_agent", "marketing",
        capabilities=["plan_video"],
        description="Plans video hooks, talking points, B-roll, and captions.",
    )
    AgentCoordinator.register_agent(
        "creative_design_agent", "marketing",
        capabilities=["create_design_brief"],
        description="Generates creative briefs for graphics, carousels, and ad creatives for a designer or image-gen tool to execute.",
    )
    AgentCoordinator.register_agent(
        "email_marketing_agent", "marketing",
        capabilities=["draft_email_campaign"],
        description="Drafts newsletters and campaign emails, filed for approval before sending to a real audience segment.",
    )
    AgentCoordinator.register_agent(
        "whatsapp_marketing_agent", "marketing",
        capabilities=["draft_whatsapp_campaign"],
        description="Drafts WhatsApp campaigns, filed for approval before sending via the real Meta Cloud API.",
    )
    AgentCoordinator.register_agent(
        "campaign_manager_agent", "marketing",
        capabilities=["plan_campaign"],
        description="Plans and coordinates multi-channel campaigns with clear goals, timelines, and KPIs.",
    )
    AgentCoordinator.register_agent(
        "marketing_automation_agent", "marketing",
        capabilities=["trigger_marketing_automation"],
        description="Fires n8n marketing workflows — publishing, CRM sync, scheduled posts — with real payload data.",
    )
    AgentCoordinator.register_agent(
        "analytics_attribution_agent", "marketing",
        capabilities=["generate_analytics_report"],
        description="Tracks attribution, LTV, CAC, and campaign performance from real platform data; produces executive summaries.",
    )
    AgentCoordinator.register_agent(
        "community_engagement_agent", "marketing",
        capabilities=["monitor_communities"],
        description="Monitors Reddit discussions and drafts thoughtful (non-pitchy) replies for approval.",
    )
    AgentCoordinator.register_agent(
        "brand_monitoring_agent", "marketing",
        capabilities=["monitor_brand_mentions"],
        description="Tracks brand mentions on Reddit and classifies sentiment, flagging negative mentions.",
    )
    AgentCoordinator.register_agent(
        "cro_agent", "marketing",
        capabilities=["analyze_conversion_funnel"],
        description="Analyzes the real deal-stage funnel and recommends conversion improvements.",
    )
    AgentCoordinator.register_agent(
        "partnership_influencer_agent", "marketing",
        capabilities=["discover_partnership_leads"],
        description="Discovers potential partners, podcasts, and communities via Reddit/HN, and drafts outreach pitches.",
    )
    AgentCoordinator.register_agent(
        "product_marketing_agent", "marketing",
        capabilities=["build_product_marketing_kit"],
        description="Coordinates launch announcements, positioning, and sales enablement materials for new features.",
    )


class WorkflowOrchestrator:
    """Orchestrate multi-agent workflows."""

    _workflows: dict[str, AgentWorkflow] = {}
    _executions: dict[str, WorkflowExecution] = {}

    @classmethod
    def create_workflow(
        cls,
        name: str,
        description: str,
        strategy: OrchestrationStrategy,
        agents: list[str],
        trigger_condition: str,
    ) -> AgentWorkflow:
        """Create a multi-agent workflow."""
        workflow = AgentWorkflow(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            strategy=strategy,
            agents=agents,
            trigger_condition=trigger_condition,
        )
        cls._workflows[workflow.id] = workflow
        logger.info(f"Workflow created: {workflow.id} ({strategy.value})")
        return workflow

    @classmethod
    def get_workflow(cls, workflow_id: str) -> AgentWorkflow | None:
        """Get workflow by ID."""
        return cls._workflows.get(workflow_id)

    @classmethod
    def list_workflows(cls) -> list[AgentWorkflow]:
        """List all workflows."""
        return list(cls._workflows.values())

    @classmethod
    def execute_workflow(
        cls, workflow_id: str, context: dict[str, Any]
    ) -> WorkflowExecution | None:
        """Execute a workflow."""
        workflow = cls.get_workflow(workflow_id)
        if not workflow or not workflow.enabled:
            logger.error(f"Workflow not found or disabled: {workflow_id}")
            return None

        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        cls._executions[execution.id] = execution

        try:
            if workflow.strategy == OrchestrationStrategy.SEQUENTIAL:
                cls._execute_sequential(execution, workflow, context)
            elif workflow.strategy == OrchestrationStrategy.PARALLEL:
                cls._execute_parallel(execution, workflow, context)
            elif workflow.strategy == OrchestrationStrategy.HIERARCHICAL:
                cls._execute_hierarchical(execution, workflow, context)
            elif workflow.strategy == OrchestrationStrategy.CONSENSUS:
                cls._execute_consensus(execution, workflow, context)

            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)
            logger.info(f"Workflow executed: {execution.id}")

        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.now(timezone.utc)
            logger.error(f"Workflow execution failed: {str(e)}")

        return execution

    @classmethod
    def _execute_sequential(
        cls, execution: WorkflowExecution, workflow: AgentWorkflow, context: dict[str, Any]
    ) -> None:
        """Execute agents sequentially."""
        for agent_name in workflow.agents:
            result = cls._execute_agent(agent_name, context)
            execution.agent_results[agent_name] = result
            # Pass result to next agent
            context[f"{agent_name}_result"] = result

        # Take first agent's decision as final
        execution.final_decision = execution.agent_results.get(workflow.agents[0], {}).get(
            "decision"
        )
        execution.confidence = execution.agent_results.get(workflow.agents[0], {}).get(
            "confidence", 0.0
        )

    @classmethod
    def _execute_parallel(
        cls, execution: WorkflowExecution, workflow: AgentWorkflow, context: dict[str, Any]
    ) -> None:
        """Execute agents in parallel."""
        import concurrent.futures

        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(workflow.agents)) as executor:
            futures = {
                executor.submit(cls._execute_agent, agent, context): agent
                for agent in workflow.agents
            }
            for future in concurrent.futures.as_completed(futures):
                agent = futures[future]
                results[agent] = future.result()

        execution.agent_results = results

        # Average confidence from all agents
        confidences = [
            r.get("confidence", 0.0) for r in results.values() if isinstance(r, dict)
        ]
        execution.confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Use majority decision
        decisions = [r.get("decision") for r in results.values() if isinstance(r, dict)]
        execution.final_decision = max(set(decisions), key=decisions.count) if decisions else None

    @classmethod
    def _execute_hierarchical(
        cls, execution: WorkflowExecution, workflow: AgentWorkflow, context: dict[str, Any]
    ) -> None:
        """Execute with manager agent delegating to team."""
        manager = workflow.agents[0]
        team = workflow.agents[1:]

        manager_result = cls._execute_agent(manager, context)
        execution.agent_results[manager] = manager_result

        # Manager delegates to team
        for agent in team:
            agent_context = context.copy()
            agent_context["manager_guidance"] = manager_result.get("guidance", "")
            result = cls._execute_agent(agent, agent_context)
            execution.agent_results[agent] = result

        execution.final_decision = manager_result.get("decision")
        execution.confidence = manager_result.get("confidence", 0.0)

    @classmethod
    def _execute_consensus(
        cls, execution: WorkflowExecution, workflow: AgentWorkflow, context: dict[str, Any]
    ) -> None:
        """Execute and reach consensus."""
        # All agents evaluate independently
        results = {}
        for agent in workflow.agents:
            result = cls._execute_agent(agent, context)
            results[agent] = result

        execution.agent_results = results

        # Count votes for each decision
        votes = {}
        for result in results.values():
            if isinstance(result, dict):
                decision = result.get("decision")
                if decision:
                    votes[decision] = votes.get(decision, 0) + 1

        # Consensus: decision with most votes
        if votes:
            execution.final_decision = max(votes, key=votes.get)
            execution.confidence = votes[execution.final_decision] / len(workflow.agents)
        else:
            execution.confidence = 0.0

    @classmethod
    def _execute_agent(cls, agent_name: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single agent."""
        # Placeholder for actual agent execution
        # In production, this would call the actual agent/crew
        return {
            "decision": f"action_by_{agent_name}",
            "confidence": 0.75,
            "reasoning": f"Agent {agent_name} evaluated context",
        }

    @classmethod
    def get_execution(cls, execution_id: str) -> WorkflowExecution | None:
        """Get execution by ID."""
        return cls._executions.get(execution_id)

    @classmethod
    def list_executions(cls, workflow_id: str | None = None) -> list[WorkflowExecution]:
        """List executions with optional filter."""
        executions = cls._executions.values()
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        return list(executions)


def _agents_db():
    """Open a DB session for agent-registry persistence. Returns None if unavailable."""
    try:
        from revenue_os.database import SessionLocal
        return SessionLocal()
    except Exception:
        return None


class AgentCoordinator:
    """Coordinate multiple autonomous agents.

    Runs from in-memory dicts for speed, but every mutation writes through
    to AgentRegistryRecord/AgentMessageRecord and both are hydrated from
    those tables once per process — otherwise the registry (and every
    inter-agent handoff) evaporates on restart, same issue WorkflowEngine
    had before M4.
    """

    _agent_registry: dict[str, dict[str, Any]] = {}
    _inter_agent_messages: dict[str, list[dict[str, Any]]] = {}
    _hydrated: bool = False

    @classmethod
    def _hydrate_from_db(cls) -> None:
        if cls._hydrated:
            return
        cls._hydrated = True
        db = _agents_db()
        if db is None:
            return
        try:
            from revenue_os.models.agents import AgentMessageRecord, AgentRegistryRecord

            for row in db.query(AgentRegistryRecord).all():
                if row.name in cls._agent_registry:
                    continue
                cls._agent_registry[row.name] = {
                    "type": row.agent_type,
                    "capabilities": row.capabilities or [],
                    "status": row.status,
                    "description": row.description or "",
                    "registered_at": row.registered_at,
                }
                cls._inter_agent_messages.setdefault(row.name, [])

            for row in db.query(AgentMessageRecord).order_by(AgentMessageRecord.created_at).all():
                cls._inter_agent_messages.setdefault(row.to_agent, [])
                cls._inter_agent_messages[row.to_agent].append({
                    "id": row.id,
                    "from": row.from_agent,
                    "timestamp": row.created_at.isoformat() if row.created_at else None,
                    "message": row.message,
                    "data": row.data or {},
                    "read": bool(row.is_read),
                })
        except Exception as e:
            logger.warning(f"Agent registry hydration skipped: {e}")
        finally:
            db.close()

    @classmethod
    def register_agent(
        cls, agent_name: str, agent_type: str, capabilities: list[str], description: str = "",
    ) -> None:
        """Register an autonomous agent (persisted)."""
        cls._hydrate_from_db()
        cls._agent_registry[agent_name] = {
            "type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "description": description,
            "registered_at": datetime.now(timezone.utc),
        }
        cls._inter_agent_messages.setdefault(agent_name, [])

        db = _agents_db()
        if db is not None:
            try:
                from revenue_os.models.agents import AgentRegistryRecord

                row = db.get(AgentRegistryRecord, agent_name)
                if row is None:
                    row = AgentRegistryRecord(name=agent_name)
                    db.add(row)
                row.agent_type = agent_type
                row.capabilities = capabilities
                row.description = description
                row.status = "active"
                db.commit()
            except Exception as e:
                logger.warning(f"Agent registration not persisted ({agent_name}): {e}")
            finally:
                db.close()
        logger.info(f"Agent registered: {agent_name} ({agent_type})")

    @classmethod
    def touch_agent(cls, agent_name: str) -> None:
        """Record that an agent just acted — updates last_active_at."""
        db = _agents_db()
        if db is None:
            return
        try:
            from revenue_os.models.agents import AgentRegistryRecord

            row = db.get(AgentRegistryRecord, agent_name)
            if row is not None:
                row.last_active_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            logger.warning(f"Agent activity not recorded ({agent_name}): {e}")
        finally:
            db.close()

    @classmethod
    def get_agent_info(cls, agent_name: str) -> dict[str, Any] | None:
        """Get agent information."""
        cls._hydrate_from_db()
        return cls._agent_registry.get(agent_name)

    @classmethod
    def list_agents(cls, agent_type: str | None = None) -> list[dict[str, Any]]:
        """List registered agents."""
        cls._hydrate_from_db()
        agents = [{"name": name, **info} for name, info in cls._agent_registry.items()]
        if agent_type:
            agents = [a for a in agents if a.get("type") == agent_type]
        return agents

    @classmethod
    def send_message(
        cls, from_agent: str, to_agent: str, message: str, data: dict[str, Any] | None = None
    ) -> bool:
        """Send message between agents (persisted)."""
        cls._hydrate_from_db()
        if to_agent not in cls._agent_registry:
            logger.error(f"Agent not found: {to_agent}")
            return False

        now = datetime.now(timezone.utc)
        msg = {
            "from": from_agent,
            "timestamp": now.isoformat(),
            "message": message,
            "data": data or {},
            "read": False,
        }
        cls._inter_agent_messages.setdefault(to_agent, []).append(msg)

        db = _agents_db()
        if db is not None:
            try:
                from revenue_os.models.agents import AgentMessageRecord

                row = AgentMessageRecord(
                    from_agent=from_agent, to_agent=to_agent, message=message, data=data or {},
                )
                db.add(row)
                db.commit()
                msg["id"] = row.id
            except Exception as e:
                logger.warning(f"Message not persisted ({from_agent} -> {to_agent}): {e}")
            finally:
                db.close()

        logger.info(f"Message sent from {from_agent} to {to_agent}")
        return True

    @classmethod
    def get_messages(cls, agent_name: str, unread_only: bool = True) -> list[dict[str, Any]]:
        """Get messages for agent."""
        cls._hydrate_from_db()
        messages = cls._inter_agent_messages.get(agent_name, [])
        if unread_only:
            messages = [m for m in messages if not m.get("read", False)]
        return messages

    @classmethod
    def mark_message_read(cls, agent_name: str, message_index: int) -> bool:
        """Mark message as read (persisted)."""
        cls._hydrate_from_db()
        messages = cls._inter_agent_messages.get(agent_name, [])
        if not (0 <= message_index < len(messages)):
            return False
        messages[message_index]["read"] = True

        msg_id = messages[message_index].get("id")
        if msg_id:
            db = _agents_db()
            if db is not None:
                try:
                    from revenue_os.models.agents import AgentMessageRecord

                    row = db.get(AgentMessageRecord, msg_id)
                    if row is not None:
                        row.is_read = 1
                        db.commit()
                except Exception as e:
                    logger.warning(f"Message read-state not persisted ({msg_id}): {e}")
                finally:
                    db.close()
        return True
