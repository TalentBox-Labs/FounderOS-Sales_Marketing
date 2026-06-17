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


class AgentCoordinator:
    """Coordinate multiple autonomous agents."""

    _agent_registry: dict[str, dict[str, Any]] = {}
    _inter_agent_messages: dict[str, list[dict[str, Any]]] = {}

    @classmethod
    def register_agent(
        cls, agent_name: str, agent_type: str, capabilities: list[str]
    ) -> None:
        """Register an autonomous agent."""
        cls._agent_registry[agent_name] = {
            "type": agent_type,
            "capabilities": capabilities,
            "status": "active",
            "registered_at": datetime.now(timezone.utc),
        }
        cls._inter_agent_messages[agent_name] = []
        logger.info(f"Agent registered: {agent_name} ({agent_type})")

    @classmethod
    def get_agent_info(cls, agent_name: str) -> dict[str, Any] | None:
        """Get agent information."""
        return cls._agent_registry.get(agent_name)

    @classmethod
    def list_agents(cls, agent_type: str | None = None) -> list[dict[str, Any]]:
        """List registered agents."""
        agents = cls._agent_registry.values()
        if agent_type:
            agents = [a for a in agents if a.get("type") == agent_type]
        return list(agents)

    @classmethod
    def send_message(
        cls, from_agent: str, to_agent: str, message: str, data: dict[str, Any] | None = None
    ) -> bool:
        """Send message between agents."""
        if to_agent not in cls._inter_agent_messages:
            logger.error(f"Agent not found: {to_agent}")
            return False

        msg = {
            "from": from_agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "data": data or {},
        }
        cls._inter_agent_messages[to_agent].append(msg)
        logger.info(f"Message sent from {from_agent} to {to_agent}")
        return True

    @classmethod
    def get_messages(cls, agent_name: str, unread_only: bool = True) -> list[dict[str, Any]]:
        """Get messages for agent."""
        messages = cls._inter_agent_messages.get(agent_name, [])
        if unread_only:
            messages = [m for m in messages if not m.get("read", False)]
        return messages

    @classmethod
    def mark_message_read(cls, agent_name: str, message_index: int) -> bool:
        """Mark message as read."""
        messages = cls._inter_agent_messages.get(agent_name, [])
        if 0 <= message_index < len(messages):
            messages[message_index]["read"] = True
            return True
        return False
