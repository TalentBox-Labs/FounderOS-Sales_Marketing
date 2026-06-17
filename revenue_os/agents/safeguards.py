"""Safeguards and monitoring for autonomous agents."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SafeguardRule:
    """Rule for autonomous agent safeguard."""

    id: str
    name: str
    description: str
    rule_type: str  # max_value, budget, approval_required, etc.
    condition: str  # the condition to check
    action: str  # what to do if violated (block, alert, require_approval)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type,
            "condition": self.condition,
            "action": self.action,
            "enabled": self.enabled,
        }


@dataclass
class SafeguardViolation:
    """Record of safeguard violation."""

    id: str
    rule_id: str
    agent_name: str
    task_id: str
    violation_type: str
    severity: AlertSeverity
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_by: str | None = None
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "agent_name": self.agent_name,
            "violation_type": self.violation_type,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
        }


class SafeguardEngine:
    """Enforce safeguards on autonomous agents."""

    _rules: dict[str, SafeguardRule] = {}
    _violations: dict[str, SafeguardViolation] = {}
    _action_limits: dict[str, dict[str, Any]] = {}

    @classmethod
    def add_rule(
        cls,
        name: str,
        description: str,
        rule_type: str,
        condition: str,
        action: str,
    ) -> SafeguardRule:
        """Add a safeguard rule."""
        rule = SafeguardRule(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            rule_type=rule_type,
            condition=condition,
            action=action,
        )
        cls._rules[rule.id] = rule
        logger.info(f"Safeguard rule added: {rule.name}")
        return rule

    @classmethod
    def get_rule(cls, rule_id: str) -> SafeguardRule | None:
        """Get rule by ID."""
        return cls._rules.get(rule_id)

    @classmethod
    def list_rules(cls) -> list[SafeguardRule]:
        """List all rules."""
        return list(cls._rules.values())

    @classmethod
    def check_safeguards(
        cls, agent_name: str, task_id: str, action: str, context: dict[str, Any]
    ) -> tuple[bool, list[SafeguardViolation]]:
        """Check if action violates any safeguards."""
        violations = []

        for rule in cls._rules.values():
            if not rule.enabled:
                continue

            if cls._evaluate_condition(rule.condition, context):
                violation = SafeguardViolation(
                    id=str(uuid.uuid4()),
                    rule_id=rule.id,
                    agent_name=agent_name,
                    task_id=task_id,
                    violation_type=rule.rule_type,
                    severity=AlertSeverity.CRITICAL if rule.action == "block" else AlertSeverity.WARNING,
                    message=f"Safeguard violation: {rule.name}",
                    metadata={"action": action, "rule": rule.name},
                )
                cls._violations[violation.id] = violation
                violations.append(violation)

                logger.warning(f"Safeguard violated by {agent_name}: {rule.name}")

        # Block if any critical violations
        blocked = any(v.severity == AlertSeverity.CRITICAL for v in violations)
        return not blocked, violations

    @classmethod
    def _evaluate_condition(cls, condition: str, context: dict[str, Any]) -> bool:
        """Evaluate a condition against context."""
        # Simplified condition evaluation
        # In production, use proper expression evaluation
        try:
            # Example conditions:
            # "context['amount'] > 50000"
            # "context['customer_type'] == 'new'"
            return eval(condition, {"context": context})
        except Exception as e:
            logger.error(f"Failed to evaluate condition: {str(e)}")
            return False

    @classmethod
    def get_violations(cls, agent_name: str | None = None) -> list[SafeguardViolation]:
        """Get violations with optional agent filter."""
        violations = cls._violations.values()
        if agent_name:
            violations = [v for v in violations if v.agent_name == agent_name]
        return list(violations)

    @classmethod
    def resolve_violation(cls, violation_id: str, resolved_by: str) -> bool:
        """Resolve a violation."""
        violation = cls._violations.get(violation_id)
        if violation:
            violation.resolved = True
            violation.resolved_by = resolved_by
            violation.resolved_at = datetime.now(timezone.utc)
            logger.info(f"Violation resolved: {violation_id}")
            return True
        return False


class AgentMonitor:
    """Monitor autonomous agent health and performance."""

    _agent_metrics: dict[str, dict[str, Any]] = {}
    _anomalies: dict[str, list[dict[str, Any]]] = {}

    @classmethod
    def record_metric(
        cls, agent_name: str, metric_name: str, value: float, context: dict[str, Any] | None = None
    ) -> None:
        """Record a metric for an agent."""
        if agent_name not in cls._agent_metrics:
            cls._agent_metrics[agent_name] = {
                "metrics": {},
                "last_updated": datetime.now(timezone.utc),
            }

        cls._agent_metrics[agent_name]["metrics"][metric_name] = {
            "value": value,
            "timestamp": datetime.now(timezone.utc),
            "context": context or {},
        }

        # Check for anomalies
        if cls._is_anomalous(agent_name, metric_name, value):
            cls._record_anomaly(agent_name, metric_name, value)

    @classmethod
    def _is_anomalous(cls, agent_name: str, metric_name: str, value: float) -> bool:
        """Detect anomalies in metrics."""
        # Get historical values for this metric
        metrics = cls._agent_metrics.get(agent_name, {}).get("metrics", {})
        metric_history = [m["value"] for m in metrics.get(metric_name, [])]

        if len(metric_history) < 5:
            return False

        # Simple anomaly detection: 3 std dev from mean
        import statistics

        try:
            mean = statistics.mean(metric_history[-10:])
            stdev = statistics.stdev(metric_history[-10:])
            threshold = mean + (3 * stdev)
            return value > threshold
        except:
            return False

    @classmethod
    def _record_anomaly(cls, agent_name: str, metric_name: str, value: float) -> None:
        """Record an anomaly."""
        if agent_name not in cls._anomalies:
            cls._anomalies[agent_name] = []

        anomaly = {
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.now(timezone.utc),
        }
        cls._anomalies[agent_name].append(anomaly)
        logger.warning(f"Anomaly detected for {agent_name}: {metric_name}={value}")

    @classmethod
    def get_health_status(cls, agent_name: str) -> dict[str, Any]:
        """Get health status of an agent."""
        metrics = cls._agent_metrics.get(agent_name, {})
        anomalies = cls._anomalies.get(agent_name, [])

        recent_anomalies = [
            a for a in anomalies
            if (datetime.now(timezone.utc) - a["timestamp"]) < timedelta(hours=1)
        ]

        health_status = "healthy"
        if len(recent_anomalies) > 3:
            health_status = "degraded"
        if len(recent_anomalies) > 5:
            health_status = "critical"

        return {
            "agent_name": agent_name,
            "status": health_status,
            "metrics_count": len(metrics.get("metrics", {})),
            "anomalies_1h": len(recent_anomalies),
            "last_updated": metrics.get("last_updated", "").isoformat()
            if metrics.get("last_updated")
            else None,
        }

    @classmethod
    def get_all_health(cls) -> dict[str, dict[str, Any]]:
        """Get health status of all agents."""
        return {agent: cls.get_health_status(agent) for agent in cls._agent_metrics.keys()}


class AuditLog:
    """Audit log for autonomous agent actions."""

    _logs: list[dict[str, Any]] = []

    @classmethod
    def log_action(
        cls,
        agent_name: str,
        action: str,
        entity_id: str,
        entity_type: str,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Log an autonomous agent action."""
        log_entry = {
            "id": str(uuid.uuid4()),
            "agent_name": agent_name,
            "action": action,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "result": result,
            "timestamp": datetime.now(timezone.utc),
            "metadata": metadata or {},
        }
        cls._logs.append(log_entry)
        logger.info(f"Action logged: {agent_name} {action} on {entity_type} {entity_id}")
        return log_entry["id"]

    @classmethod
    def get_logs(
        cls,
        agent_name: str | None = None,
        entity_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get audit logs with filters."""
        logs = cls._logs

        if agent_name:
            logs = [l for l in logs if l["agent_name"] == agent_name]

        if entity_id:
            logs = [l for l in logs if l["entity_id"] == entity_id]

        if start_time:
            logs = [l for l in logs if l["timestamp"] >= start_time]

        if end_time:
            logs = [l for l in logs if l["timestamp"] <= end_time]

        return logs

    @classmethod
    def get_agent_audit_trail(cls, agent_name: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get complete audit trail for an agent."""
        logs = cls.get_logs(agent_name=agent_name)
        return logs[-limit:]
