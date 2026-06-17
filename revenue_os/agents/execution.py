"""Autonomous AI agent execution system."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
import uuid

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of autonomous agents."""

    SDR = "sdr"  # Sales development representative
    CSM = "csm"  # Customer success manager
    SALES_MANAGER = "sales_manager"
    FINANCE = "finance"
    PRODUCT = "product"
    OPERATIONS = "operations"
    CUSTOM = "custom"


class ExecutionStatus(Enum):
    """Agent execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    APPROVED = "approved"


@dataclass
class AgentTask:
    """Task for an autonomous agent."""

    id: str
    agent_type: AgentType
    title: str
    description: str
    priority: int  # 1-5, 5 = highest
    status: ExecutionStatus = ExecutionStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    requires_approval: bool = False
    approved_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "agent_type": self.agent_type.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "requires_approval": self.requires_approval,
            "approved_by": self.approved_by,
        }


@dataclass
class AgentDecision:
    """Decision made by an autonomous agent."""

    id: str
    agent_type: AgentType
    entity_id: str  # deal_id, contact_id, account_id, etc.
    entity_type: str  # deal, contact, account, etc.
    decision: str  # action to take
    confidence: float  # 0-1
    reasoning: str  # why this decision
    alternative_actions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed: bool = False
    executed_by: str | None = None  # user or system
    executed_at: datetime | None = None
    result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "agent_type": self.agent_type.value,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "decision": self.decision,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "alternative_actions": self.alternative_actions,
            "created_at": self.created_at.isoformat(),
            "executed": self.executed,
            "executed_by": self.executed_by,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


@dataclass
class AgentPerformance:
    """Track autonomous agent performance."""

    agent_type: AgentType
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    approved_decisions: int = 0
    rejected_decisions: int = 0
    avg_confidence: float = 0.0
    total_value_generated: float = 0.0  # revenue impacted
    last_execution: datetime | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_type": self.agent_type.value,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.completed_tasks / max(self.total_tasks, 1),
            "approved_decisions": self.approved_decisions,
            "rejected_decisions": self.rejected_decisions,
            "approval_rate": self.approved_decisions / max(
                self.approved_decisions + self.rejected_decisions, 1
            ),
            "avg_confidence": self.avg_confidence,
            "total_value_generated": self.total_value_generated,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
        }


class TaskQueue:
    """Queue for autonomous agent tasks."""

    _tasks: dict[str, AgentTask] = {}
    _pending_by_type: dict[AgentType, list[str]] = {}

    @classmethod
    def create_task(
        cls,
        agent_type: AgentType,
        title: str,
        description: str,
        priority: int = 3,
        requires_approval: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> AgentTask:
        """Create a new task for an agent."""
        task = AgentTask(
            id=str(uuid.uuid4()),
            agent_type=agent_type,
            title=title,
            description=description,
            priority=priority,
            requires_approval=requires_approval,
            metadata=metadata or {},
        )
        cls._tasks[task.id] = task

        if agent_type not in cls._pending_by_type:
            cls._pending_by_type[agent_type] = []
        cls._pending_by_type[agent_type].append(task.id)

        logger.info(f"Task created: {task.id} for {agent_type.value}")
        return task

    @classmethod
    def get_task(cls, task_id: str) -> AgentTask | None:
        """Get task by ID."""
        return cls._tasks.get(task_id)

    @classmethod
    def get_pending_tasks(cls, agent_type: AgentType, limit: int = 10) -> list[AgentTask]:
        """Get pending tasks for agent type, sorted by priority."""
        task_ids = cls._pending_by_type.get(agent_type, [])
        pending = [
            cls._tasks[tid]
            for tid in task_ids
            if tid in cls._tasks and cls._tasks[tid].status == ExecutionStatus.PENDING
        ]
        pending.sort(key=lambda t: t.priority, reverse=True)
        return pending[:limit]

    @classmethod
    def start_task(cls, task_id: str) -> bool:
        """Mark task as started."""
        task = cls.get_task(task_id)
        if task:
            task.status = ExecutionStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            logger.info(f"Task started: {task_id}")
            return True
        return False

    @classmethod
    def complete_task(cls, task_id: str, result: dict[str, Any]) -> bool:
        """Mark task as completed."""
        task = cls.get_task(task_id)
        if task:
            task.status = ExecutionStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result
            logger.info(f"Task completed: {task_id}")
            return True
        return False

    @classmethod
    def fail_task(cls, task_id: str, error: str) -> bool:
        """Mark task as failed."""
        task = cls.get_task(task_id)
        if task:
            task.status = ExecutionStatus.FAILED
            task.error = error
            task.completed_at = datetime.now(timezone.utc)
            logger.error(f"Task failed: {task_id} - {error}")
            return True
        return False

    @classmethod
    def block_task(cls, task_id: str, reason: str) -> bool:
        """Block task pending approval."""
        task = cls.get_task(task_id)
        if task:
            task.status = ExecutionStatus.BLOCKED
            task.metadata["blocked_reason"] = reason
            logger.info(f"Task blocked: {task_id} - {reason}")
            return True
        return False

    @classmethod
    def approve_task(cls, task_id: str, approved_by: str) -> bool:
        """Approve a blocked task."""
        task = cls.get_task(task_id)
        if task:
            task.status = ExecutionStatus.APPROVED
            task.approved_by = approved_by
            logger.info(f"Task approved: {task_id}")
            return True
        return False


class DecisionManager:
    """Manage autonomous agent decisions."""

    _decisions: dict[str, AgentDecision] = {}
    _pending_approval: list[str] = []

    @classmethod
    def propose_decision(
        cls,
        agent_type: AgentType,
        entity_id: str,
        entity_type: str,
        decision: str,
        confidence: float,
        reasoning: str,
        alternative_actions: list[str] | None = None,
    ) -> AgentDecision:
        """Propose a decision for execution."""
        decision_obj = AgentDecision(
            id=str(uuid.uuid4()),
            agent_type=agent_type,
            entity_id=entity_id,
            entity_type=entity_type,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            alternative_actions=alternative_actions or [],
        )
        cls._decisions[decision_obj.id] = decision_obj

        if confidence < 0.8:
            cls._pending_approval.append(decision_obj.id)
            logger.info(f"Decision pending approval: {decision_obj.id} (confidence: {confidence})")
        else:
            logger.info(f"Decision auto-approved: {decision_obj.id} (confidence: {confidence})")

        return decision_obj

    @classmethod
    def get_decision(cls, decision_id: str) -> AgentDecision | None:
        """Get decision by ID."""
        return cls._decisions.get(decision_id)

    @classmethod
    def list_pending_decisions(cls, limit: int = 20) -> list[AgentDecision]:
        """Get pending decisions awaiting approval."""
        pending = [
            cls._decisions[did]
            for did in cls._pending_approval
            if did in cls._decisions and not cls._decisions[did].executed
        ]
        return pending[:limit]

    @classmethod
    def approve_decision(cls, decision_id: str, approved_by: str) -> bool:
        """Approve a pending decision."""
        decision = cls.get_decision(decision_id)
        if decision:
            decision.executed = True
            decision.executed_by = approved_by
            decision.executed_at = datetime.now(timezone.utc)
            if decision_id in cls._pending_approval:
                cls._pending_approval.remove(decision_id)
            logger.info(f"Decision approved: {decision_id}")
            return True
        return False

    @classmethod
    def reject_decision(cls, decision_id: str, rejected_by: str, reason: str) -> bool:
        """Reject a pending decision."""
        decision = cls.get_decision(decision_id)
        if decision:
            decision.metadata["rejected"] = True
            decision.metadata["rejected_by"] = rejected_by
            decision.metadata["rejection_reason"] = reason
            if decision_id in cls._pending_approval:
                cls._pending_approval.remove(decision_id)
            logger.info(f"Decision rejected: {decision_id} - {reason}")
            return True
        return False

    @classmethod
    def auto_execute_decision(cls, decision_id: str, executor: str = "system") -> bool:
        """Auto-execute a high-confidence decision."""
        decision = cls.get_decision(decision_id)
        if decision and decision.confidence >= 0.85 and not decision.executed:
            decision.executed = True
            decision.executed_by = executor
            decision.executed_at = datetime.now(timezone.utc)
            logger.info(f"Decision auto-executed: {decision_id}")
            return True
        return False


class PerformanceTracker:
    """Track autonomous agent performance metrics."""

    _performance: dict[AgentType, AgentPerformance] = {}

    @classmethod
    def get_performance(cls, agent_type: AgentType) -> AgentPerformance:
        """Get performance metrics for agent type."""
        if agent_type not in cls._performance:
            cls._performance[agent_type] = AgentPerformance(agent_type=agent_type)
        return cls._performance[agent_type]

    @classmethod
    def record_task_completion(
        cls, agent_type: AgentType, success: bool, value_generated: float = 0.0
    ) -> None:
        """Record task completion."""
        perf = cls.get_performance(agent_type)
        perf.total_tasks += 1
        if success:
            perf.completed_tasks += 1
            perf.total_value_generated += value_generated
        else:
            perf.failed_tasks += 1
        perf.last_execution = datetime.now(timezone.utc)

    @classmethod
    def record_decision(
        cls, agent_type: AgentType, confidence: float, approved: bool
    ) -> None:
        """Record decision outcome."""
        perf = cls.get_performance(agent_type)
        if approved:
            perf.approved_decisions += 1
        else:
            perf.rejected_decisions += 1

        # Update rolling average confidence
        total_decisions = perf.approved_decisions + perf.rejected_decisions
        perf.avg_confidence = (
            (perf.avg_confidence * (total_decisions - 1) + confidence) / total_decisions
        )

    @classmethod
    def list_all_performance(cls) -> list[AgentPerformance]:
        """Get performance metrics for all agents."""
        return list(cls._performance.values())
