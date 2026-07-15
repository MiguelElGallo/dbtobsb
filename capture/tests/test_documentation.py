"""Executable contracts for the P1.1 developer documentation."""

from __future__ import annotations

import re
from pathlib import Path

from dbtobsb_capture import inspector
from dbtobsb_capture.registry import ISSUE_PRECEDENCE, MAX_REPORT_ISSUES, NATIVE_STATUSES

REPOSITORY_ROOT = Path(__file__).parents[2]
PYTHON_REFERENCE = REPOSITORY_ROOT / "docs/developers/reference/python-api.md"
CLI_REFERENCE = REPOSITORY_ROOT / "docs/developers/reference/cli-report-and-exit-codes.md"
HOW_TO = REPOSITORY_ROOT / "docs/developers/how-to/diagnose-an-invalid-artifact-pair.md"
RAW_CUSTODY = REPOSITORY_ROOT / "docs/developers/explanation/raw-artifact-custody.md"


def _marked_section(path: Path, marker: str) -> str:
    text = path.read_text(encoding="utf-8")
    begin = f"<!-- BEGIN: {marker} -->"
    end = f"<!-- END: {marker} -->"
    assert text.count(begin) == 1
    assert text.count(end) == 1
    return text.split(begin, 1)[1].split(end, 1)[0]


def test_displayed_python_example_matches_checked_in_program() -> None:
    section = _marked_section(PYTHON_REFERENCE, "inspect-valid-fixture.py")
    match = re.fullmatch(r"\s*```python\n(?P<source>.*?)```\s*", section, flags=re.DOTALL)
    assert match is not None

    example = REPOSITORY_ROOT / "capture/examples/inspect_valid_fixture.py"
    assert match.group("source") == example.read_text(encoding="utf-8")


def test_python_reference_binds_closed_public_contract() -> None:
    contract = _marked_section(PYTHON_REFERENCE, "python-public-contract")

    assert "128 MiB" in contract
    assert "256" in contract
    assert f"One to {MAX_REPORT_ISSUES}" in contract
    for status in NATIVE_STATUSES:
        assert f"`{status}`" in contract


def test_issue_registry_binds_precedence_and_recovery_routes() -> None:
    registry = _marked_section(CLI_REFERENCE, "issue-registry")
    documented_codes = tuple(re.findall(r"`(DBT_[A-Z0-9_]+)`", registry))
    assert documented_codes == ISSUE_PRECEDENCE

    data_rows = [line for line in registry.splitlines() if line.startswith("| `DBT_")]
    assert data_rows
    for row in data_rows:
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert len(columns) == 5
        code = columns[0].strip("`")
        template = inspector._ISSUES[code]
        assert columns[1] == template.impact
        assert columns[2]
        assert columns[3] == template.next_action
        assert "](../how-to/diagnose-an-invalid-artifact-pair.md#" in columns[4]


def test_real_artifact_routes_preserve_sensitive_input_boundary() -> None:
    custody_route = "raw-artifact-custody.md"
    for path in (PYTHON_REFERENCE, CLI_REFERENCE, HOW_TO):
        text = path.read_text(encoding="utf-8")
        assert "Personal Data" in text
        assert custody_route in text

    custody = RAW_CUSTODY.read_text(encoding="utf-8").casefold()
    for required_boundary in (
        "least-privilege",
        "do not commit",
        "ordinary support ticket",
        "retention",
        "legal-hold",
        "does not persist, copy, upload, or transmit",
        "customer's Databricks environment",
    ):
        assert required_boundary.casefold() in custody
