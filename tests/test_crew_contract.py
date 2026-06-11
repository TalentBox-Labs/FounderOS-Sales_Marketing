"""QA markdown contract (Phase 2 agent output gate)."""

from __future__ import annotations

from src.crew_contract import qa_report_contract_errors, qa_report_meets_contract


def test_valid_qa_report_passes():
    md = """
## Passed Checks
ok

## Failed Checks
none

## Observable Issues
none

## Final Verdict
PASS
"""
    assert qa_report_meets_contract(md)
    assert qa_report_contract_errors(md) == []


def test_heading_case_insensitive():
    md = """
## passed checks
x

## failed checks
x

## observable issues
x

## final verdict
FAIL
"""
    assert qa_report_meets_contract(md)


def test_missing_section():
    md = "## Passed Checks\n\n## Failed Checks\n\n## Final Verdict\nPASS\n"
    errs = qa_report_contract_errors(md)
    assert any("Observable Issues" in e for e in errs)


def test_final_verdict_requires_standalone_pass_fail():
    md = """
## Passed Checks
a
## Failed Checks
b
## Observable Issues
c
## Final Verdict
Probably PASS
"""
    errs = qa_report_contract_errors(md)
    assert any("PASS or FAIL" in e for e in errs)


def test_final_verdict_accepts_markdown_list_item():
    md = """
## Passed Checks
a
## Failed Checks
b
## Observable Issues
c
## Final Verdict

- FAIL
"""
    assert qa_report_meets_contract(md)
    assert qa_report_contract_errors(md) == []


def test_empty_report():
    assert qa_report_contract_errors("") == ["Report is empty"]
