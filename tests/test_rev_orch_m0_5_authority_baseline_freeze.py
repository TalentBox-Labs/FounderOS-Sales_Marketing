"""REV-ORCH M0.5 — specialized worker / authority baseline freeze attestation.

Documentation freeze only. Does not change runtime behavior.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M05 = ROOT / "docs" / "revenue" / "orchestration" / "m0_5"

REQUIRED = (
    "M0_5_SPECIALIZED_AGENT_INVENTORY.md",
    "M0_5_AGENT_TAXONOMY_v1.md",
    "M0_5_REVENUE_CAPABILITY_ASSIGNMENT.md",
    "M0_5_M1_WORKER_CONTRACTS.md",
    "M0_5_FUTURE_WORKER_MAP.md",
    "M0_5_AGENT_CAPABILITY_MATRIX_v1.md",
    "M0_5_AGENT_AUTHORITY_DENYLIST_v1.md",
    "M0_5_AGENT_OUTPUT_CONTRACT.md",
    "M0_5_AGENT_HANDOFF_CONTRACT.md",
    "M0_5_AGENT_CONTEXT_BOUNDARIES.md",
    "M0_5_AGENT_FAILURE_CONTRACT.md",
    "M0_5_AGENT_AUDIT_CONTRACT.md",
    "M0_5_MODEL_ROUTING_BOUNDARY.md",
    "M0_5_EXISTING_AGENT_DISPOSITION.md",
    "M0_5_M1_IMPLEMENTATION_MAP.md",
    "M0_5_M0_GAP_RECONCILIATION.md",
    "REVENUE_AGENT_RESPONSIBILITY_AUTHORITY_BASELINE_v1.0.md",
    "M0_5_BASELINE_MANIFEST.md",
)


def test_m0_5_required_artifacts_present() -> None:
    missing = [n for n in REQUIRED if not (M05 / n).exists()]
    assert missing == [], f"Missing M0.5 artifacts: {missing}"


def test_m0_5_taxonomy_one_orchestrator_zero_autonomous() -> None:
    tax = (M05 / "M0_5_AGENT_TAXONOMY_v1.md").read_text()
    assert "zero autonomous revenue agents" in tax.lower()
    assert "WorkflowOrchestrator" in tax
    base = (M05 / "REVENUE_AGENT_RESPONSIBILITY_AUTHORITY_BASELINE_v1.0.md").read_text()
    assert "Autonomous revenue agents" in base


def test_m0_5_handoff_and_denylist_frozen() -> None:
    handoff = (M05 / "M0_5_AGENT_HANDOFF_CONTRACT.md").read_text()
    assert "PEER_TO_PEER_AGENT_AUTHORITY: PROHIBITED" in handoff
    assert "AGENT_HANDOFFS: ORCHESTRATOR_MEDIATED" in handoff
    deny = (M05 / "M0_5_AGENT_AUTHORITY_DENYLIST_v1.md").read_text()
    assert "Directly send email" in deny
    assert "Directly mutate `Contact.status`" in deny


def test_m0_5_m1_workers_are_two() -> None:
    contracts = (M05 / "M0_5_M1_WORKER_CONTRACTS.md").read_text()
    assert "ResearchWorker" in contracts
    assert "PersonalizationWorker" in contracts
    assert "Explicitly not M1 workers" in contracts


def test_m0_5_capability_matrix_workers_deny_send_and_mutate() -> None:
    matrix = (M05 / "M0_5_AGENT_CAPABILITY_MATRIX_v1.md").read_text()
    assert "ResearchWorker" in matrix
    assert "PersonalizationWorker" in matrix
    assert "No worker cell is ALLOW for APPROVE, SEND_EXTERNAL" in matrix


def test_m0_5_no_new_sot() -> None:
    base = (M05 / "REVENUE_AGENT_RESPONSIBILITY_AUTHORITY_BASELINE_v1.0.md").read_text()
    assert "No new SoT" in base
    manifest = (M05 / "M0_5_BASELINE_MANIFEST.md").read_text()
    assert "Feature code changes" in manifest


def test_m0_5_tool_calling_and_canonical_api() -> None:
    base = (M05 / "REVENUE_AGENT_RESPONSIBILITY_AUTHORITY_BASELINE_v1.0.md").read_text()
    assert "PROHIBITED_FOR_M1" in base
    assert "runner_api:app" in base


def test_m0_5_gaps_classified() -> None:
    recon = (M05 / "M0_5_M0_GAP_RECONCILIATION.md").read_text()
    assert "MUST_FIX_IN_M1" in recon
    assert "SAFE_TO_DEFER" in recon
    assert "ALREADY_MITIGATED" in recon
    assert "MUST_FIX_BEFORE_M1" in recon
