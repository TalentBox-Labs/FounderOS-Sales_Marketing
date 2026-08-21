"""ACP-3 — Durable Autonomous Operations Runtime contract (no new SoT).

Persistent facts: AgentActionLog (append-only) + ApprovalRequest + domain state.
WorkItem remains in-memory. Reconciliation reconstructs operational state from
facts; it never fabricates success, approval, or tenant ownership.

Semantics:
  at-least-once discovery + idempotent effect execution
  (not distributed exactly-once unless the repository proves it)
"""

from __future__ import annotations

from enum import Enum

# Recovery classification for founder oversight
class RecoveryClass(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE = "RETRYABLE"
    EXHAUSTED = "EXHAUSTED"
    WAITING_HUMAN = "WAITING_HUMAN"
    BLOCKED = "BLOCKED"
    PROHIBITED = "PROHIBITED"
    AMBIGUOUS_EFFECT = "AMBIGUOUS_EFFECT"
    CANCELLED = "CANCELLED"
    IN_FLIGHT = "IN_FLIGHT"


# Provenance action types (append-only)
LOG_ACP3_RECONCILED = "acp3_work_reconciled"
LOG_ACP3_RECOVERY_ATTEMPTED = "acp3_recovery_attempted"
LOG_ACP3_AMBIGUOUS = "acp3_ambiguous_effect"
LOG_ACP3_RESUME_PASS = "acp3_resume_pass"
LOG_ACP3_PAUSE_GATE = "acp3_pause_gate"
LOG_ACP3_KILL_GATE = "acp3_kill_gate"
LOG_ACP3_DISCOVERED = "acp3_work_discovered"

# Bounds per reconciliation / resume pass
DEFAULT_RECONCILE_SCAN_LIMIT = 200
DEFAULT_RECOVERY_EXEC_LIMIT = 25
DEFAULT_SCHEDULER_UNIT_LIMIT = 25

# Env (reuse ACP-2; ACP-3 documents semantics)
# HEARTBEAT_ENABLED=0 → PAUSE (no new scheduler-driven mutating work)
# ACP2_AUTONOMOUS_EXECUTION_ENABLED=0 → KILL (fail closed for autonomous execution)
ENV_RESUME_ENABLED = "ACP3_RESUME_ENABLED"  # default 1; 0 blocks recovery execution only
