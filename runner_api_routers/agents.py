"""Autonomous AI agents API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from revenue_os.database import SessionLocal
from revenue_os.agents.execution import (
    AgentType,
    TaskQueue,
    DecisionManager,
    PerformanceTracker,
)
from revenue_os.agents.orchestration import (
    WorkflowOrchestrator,
    AgentCoordinator,
    OrchestrationStrategy,
)
from revenue_os.agents.safeguards import (
    SafeguardEngine,
    AgentMonitor,
    AuditLog,
)

from runner_api_routers.utils import _verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/tasks", tags=["agents"])
def create_agent_task(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a task for an autonomous agent."""
    logger.info(f"Creating task for {payload.get('agent_type')}")

    try:
        agent_type = AgentType(payload["agent_type"])
        task = TaskQueue.create_task(
            agent_type=agent_type,
            title=payload["title"],
            description=payload["description"],
            priority=payload.get("priority", 3),
            requires_approval=payload.get("requires_approval", False),
            metadata=payload.get("metadata", {}),
        )
        return {"ok": True, "task": task.to_dict()}
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/tasks/{agent_type}", tags=["agents"])
def get_pending_tasks(
    agent_type: str,
    limit: int = 10,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get pending tasks for an agent type."""
    logger.info(f"Getting pending tasks for {agent_type}")

    try:
        agent_enum = AgentType(agent_type)
        tasks = TaskQueue.get_pending_tasks(agent_enum, limit=limit)
        return {
            "ok": True,
            "agent_type": agent_type,
            "count": len(tasks),
            "tasks": [t.to_dict() for t in tasks],
        }
    except Exception as e:
        logger.error(f"Failed to get tasks: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/tasks/{task_id}/complete", tags=["agents"])
def complete_task(
    task_id: str,
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Mark task as completed."""
    logger.info(f"Completing task: {task_id}")

    try:
        success = TaskQueue.complete_task(task_id, result=payload.get("result", {}))
        return {
            "ok": success,
            "message": "Task completed" if success else "Task not found",
        }
    except Exception as e:
        logger.error(f"Failed to complete task: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/decisions", tags=["agents"])
def propose_decision(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Propose an autonomous decision."""
    logger.info(f"Proposing decision for {payload.get('entity_type')}")

    try:
        agent_type = AgentType(payload["agent_type"])
        decision = DecisionManager.propose_decision(
            agent_type=agent_type,
            entity_id=payload["entity_id"],
            entity_type=payload["entity_type"],
            decision=payload["decision"],
            confidence=payload.get("confidence", 0.5),
            reasoning=payload.get("reasoning", ""),
            alternative_actions=payload.get("alternative_actions", []),
        )
        return {"ok": True, "decision": decision.to_dict()}
    except Exception as e:
        logger.error(f"Failed to propose decision: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/decisions/pending", tags=["agents"])
def get_pending_decisions(
    limit: int = 20,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get decisions pending approval."""
    logger.info("Getting pending decisions")

    try:
        decisions = DecisionManager.list_pending_decisions(limit=limit)
        return {
            "ok": True,
            "count": len(decisions),
            "decisions": [d.to_dict() for d in decisions],
        }
    except Exception as e:
        logger.error(f"Failed to get pending decisions: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/decisions/{decision_id}/approve", tags=["agents"])
def approve_decision(
    decision_id: str,
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Approve an autonomous decision."""
    logger.info(f"Approving decision: {decision_id}")

    try:
        success = DecisionManager.approve_decision(
            decision_id, approved_by=payload.get("approved_by", "system")
        )
        return {"ok": success, "message": "Decision approved" if success else "Decision not found"}
    except Exception as e:
        logger.error(f"Failed to approve decision: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/workflows", tags=["agents"])
def create_workflow(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Create a multi-agent workflow."""
    logger.info(f"Creating workflow: {payload.get('name')}")

    try:
        strategy = OrchestrationStrategy(payload["strategy"])
        workflow = WorkflowOrchestrator.create_workflow(
            name=payload["name"],
            description=payload["description"],
            strategy=strategy,
            agents=payload["agents"],
            trigger_condition=payload["trigger_condition"],
        )
        return {"ok": True, "workflow": workflow.to_dict()}
    except Exception as e:
        logger.error(f"Failed to create workflow: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/workflows", tags=["agents"])
def list_workflows(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all workflows."""
    logger.info("Listing workflows")

    try:
        workflows = WorkflowOrchestrator.list_workflows()
        return {
            "ok": True,
            "count": len(workflows),
            "workflows": [w.to_dict() for w in workflows],
        }
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/workflows/{workflow_id}/execute", tags=["agents"])
def execute_workflow(
    workflow_id: str,
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Execute a workflow."""
    logger.info(f"Executing workflow: {workflow_id}")

    try:
        execution = WorkflowOrchestrator.execute_workflow(
            workflow_id, context=payload.get("context", {})
        )
        return {
            "ok": execution is not None,
            "execution": execution.to_dict() if execution else None,
        }
    except Exception as e:
        logger.error(f"Failed to execute workflow: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/safeguards/rules", tags=["agents"])
def add_safeguard_rule(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Add a safeguard rule."""
    logger.info(f"Adding safeguard rule: {payload.get('name')}")

    try:
        rule = SafeguardEngine.add_rule(
            name=payload["name"],
            description=payload["description"],
            rule_type=payload["rule_type"],
            condition=payload["condition"],
            action=payload["action"],
        )
        return {"ok": True, "rule": rule.to_dict()}
    except Exception as e:
        logger.error(f"Failed to add safeguard rule: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/safeguards/rules", tags=["agents"])
def list_safeguard_rules(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """List all safeguard rules."""
    logger.info("Listing safeguard rules")

    try:
        rules = SafeguardEngine.list_rules()
        return {
            "ok": True,
            "count": len(rules),
            "rules": [r.to_dict() for r in rules],
        }
    except Exception as e:
        logger.error(f"Failed to list rules: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.post("/safeguards/check", tags=["agents"])
def check_safeguards(
    payload: dict[str, Any],
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Check if action passes safeguards."""
    logger.info(f"Checking safeguards for {payload.get('agent_name')}")

    try:
        allowed, violations = SafeguardEngine.check_safeguards(
            agent_name=payload["agent_name"],
            task_id=payload["task_id"],
            action=payload["action"],
            context=payload.get("context", {}),
        )
        return {
            "ok": True,
            "allowed": allowed,
            "violations": [v.to_dict() for v in violations],
        }
    except Exception as e:
        logger.error(f"Failed to check safeguards: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/monitor/{agent_name}/health", tags=["agents"])
def get_agent_health(
    agent_name: str,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get health status of an agent."""
    logger.info(f"Getting health for {agent_name}")

    try:
        health = AgentMonitor.get_health_status(agent_name)
        return {"ok": True, "health": health}
    except Exception as e:
        logger.error(f"Failed to get health: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/monitor/health", tags=["agents"])
def get_all_agent_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get health status of all agents."""
    logger.info("Getting health for all agents")

    try:
        health = AgentMonitor.get_all_health()
        return {
            "ok": True,
            "count": len(health),
            "agents": health,
        }
    except Exception as e:
        logger.error(f"Failed to get all health: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/audit/{agent_name}", tags=["agents"])
def get_agent_audit_trail(
    agent_name: str,
    limit: int = 100,
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get audit trail for an agent."""
    logger.info(f"Getting audit trail for {agent_name}")

    try:
        logs = AuditLog.get_agent_audit_trail(agent_name, limit=limit)
        return {
            "ok": True,
            "agent_name": agent_name,
            "count": len(logs),
            "logs": logs,
        }
    except Exception as e:
        logger.error(f"Failed to get audit trail: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/performance", tags=["agents"])
def get_agent_performance(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get performance metrics for all agents."""
    logger.info("Getting performance metrics")

    try:
        performance = PerformanceTracker.list_all_performance()
        return {
            "ok": True,
            "count": len(performance),
            "agents": [p.to_dict() for p in performance],
        }
    except Exception as e:
        logger.error(f"Failed to get performance: {str(e)}")
        return {"ok": False, "error": str(e)}


@router.get("/health", tags=["agents"])
def agents_system_health(
    _: str | None = Depends(_verify_api_key),
) -> dict[str, Any]:
    """Get agents system health."""
    logger.info("Checking agents system health")

    all_health = AgentMonitor.get_all_health()
    status = "healthy"
    if any(h["status"] == "critical" for h in all_health.values()):
        status = "critical"
    elif any(h["status"] == "degraded" for h in all_health.values()):
        status = "degraded"

    return {
        "ok": True,
        "status": status,
        "agents_active": len(all_health),
        "workflows_available": len(WorkflowOrchestrator.list_workflows()),
        "safeguard_rules": len(SafeguardEngine.list_rules()),
    }
