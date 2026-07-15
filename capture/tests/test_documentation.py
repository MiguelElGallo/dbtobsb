"""Executable contracts for the P1.1 developer documentation."""

from __future__ import annotations

import inspect
import re
import subprocess
import sys
import types
import unicodedata
from dataclasses import fields
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints
from urllib.parse import unquote

from dbtobsb_capture import (
    ArtifactPairIssue,
    ArtifactPairReport,
    ArtifactPairSummary,
    NativeStatusCount,
    inspect_artifact_pair,
)
from dbtobsb_capture import inspector as inspector_module
from dbtobsb_capture.registry import ISSUE_PRECEDENCE, MAX_REPORT_ISSUES, NATIVE_STATUSES

REPOSITORY_ROOT = Path(__file__).parents[2]
PYTHON_REFERENCE = REPOSITORY_ROOT / "docs/developers/reference/python-api.md"
CLI_REFERENCE = REPOSITORY_ROOT / "docs/developers/reference/cli-report-and-exit-codes.md"
DIAGNOSIS_HOW_TO = REPOSITORY_ROOT / "docs/developers/how-to/diagnose-an-invalid-artifact-pair.md"
RAW_HANDLING_HOW_TO = REPOSITORY_ROOT / "docs/developers/how-to/handle-raw-dbt-artifacts-safely.md"
RAW_CUSTODY_EXPLANATION = REPOSITORY_ROOT / "docs/developers/explanation/raw-artifact-custody.md"

ISSUE_DOCUMENTATION = {
    "DBT_MANIFEST_SIZE_LIMIT_EXCEEDED": (
        "Correct input or recollect",
        "recover-file-json-or-schema-inputs",
    ),
    "DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED": (
        "Correct input or recollect",
        "recover-file-json-or-schema-inputs",
    ),
    "DBT_MANIFEST_JSON_INVALID": ("Recollect", "recover-file-json-or-schema-inputs"),
    "DBT_RUN_RESULTS_JSON_INVALID": ("Recollect", "recover-file-json-or-schema-inputs"),
    "DBT_MANIFEST_JSON_DUPLICATE_KEY": ("Recollect", "recover-file-json-or-schema-inputs"),
    "DBT_RUN_RESULTS_JSON_DUPLICATE_KEY": ("Recollect", "recover-file-json-or-schema-inputs"),
    "DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED": ("Recollect", "recover-file-json-or-schema-inputs"),
    "DBT_RUN_RESULTS_JSON_NESTING_LIMIT_EXCEEDED": (
        "Recollect",
        "recover-file-json-or-schema-inputs",
    ),
    "DBT_MANIFEST_SCHEMA_INVALID": (
        "Recollect or compatibility review",
        "recover-file-json-or-schema-inputs",
    ),
    "DBT_RUN_RESULTS_SCHEMA_INVALID": (
        "Recollect or compatibility review",
        "recover-file-json-or-schema-inputs",
    ),
    "DBT_SCHEMA_VERSION_UNSUPPORTED": (
        "Unsupported compatibility",
        "recover-file-json-or-schema-inputs",
    ),
    "DBT_CORE_VERSION_UNSUPPORTED": (
        "Unsupported compatibility",
        "recover-file-json-or-schema-inputs",
    ),
    "DBT_INVOCATION_ID_INVALID": ("Recollect pair", "recover-pair-metadata"),
    "DBT_INVOCATION_ID_MISMATCH": ("Recollect pair", "recover-pair-metadata"),
    "DBT_ADAPTER_TYPE_UNSUPPORTED": ("Unsupported compatibility", "recover-pair-metadata"),
    "DBT_COMMAND_UNSUPPORTED": ("Unsupported compatibility", "recover-pair-metadata"),
    "DBT_EMPTY_EXECUTION": ("Correct and rerun", "recover-result-evidence"),
    "DBT_RESULTS_DUPLICATE_ID": ("Recollect pair", "recover-result-evidence"),
    "DBT_RESULT_ID_UNRESOLVED": ("Recollect pair", "recover-result-evidence"),
    "DBT_RESULT_ID_UNSUPPORTED_RESOURCE": ("Unsupported compatibility", "recover-result-evidence"),
    "DBT_RESULT_ID_AMBIGUOUS": ("Recollect pair", "recover-result-evidence"),
    "DBT_MANIFEST_RESOURCE_ID_MISMATCH": ("Recollect pair", "recover-result-evidence"),
    "DBT_RESULT_RESOURCE_TYPE_UNSUPPORTED": (
        "Unsupported compatibility",
        "recover-result-evidence",
    ),
    "DBT_RESULT_STATUS_UNSUPPORTED": ("Unsupported compatibility", "recover-result-evidence"),
    "DBT_TIMING_INVALID": ("Recollect", "recover-numeric-evidence"),
    "DBT_FAILURE_COUNT_INVALID": ("Recollect", "recover-numeric-evidence"),
}


def _marked_section(path: Path, marker: str) -> str:
    text = path.read_text(encoding="utf-8")
    begin = f"<!-- BEGIN: {marker} -->"
    end = f"<!-- END: {marker} -->"
    assert text.count(begin) == 1
    assert text.count(end) == 1
    return text.split(begin, 1)[1].split(end, 1)[0]


def _fenced_content(path: Path, marker: str, language: str) -> str:
    section = _marked_section(path, marker)
    pattern = rf"\s*```{language}\n(?P<content>.*?)```\s*"
    match = re.fullmatch(pattern, section, flags=re.DOTALL)
    assert match is not None
    return match.group("content")


def _display_type(annotation: Any) -> str:
    origin = get_origin(annotation)
    arguments = get_args(annotation)
    if origin is tuple:
        item_type, ellipsis = arguments
        assert ellipsis is Ellipsis
        return f"tuple[{_display_type(item_type)}, ...]"
    if origin is types.UnionType:
        return " | ".join(_display_type(argument) for argument in arguments)
    if annotation is type(None):
        return "None"
    assert isinstance(annotation, type)
    return annotation.__name__


def _markdown_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+[^>]*id=["\']([^"\']+)["\']', text, re.IGNORECASE))
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        normalized = unicodedata.normalize("NFC", heading.strip().lower())
        normalized = "".join(
            character for character in normalized if character.isalnum() or character in " -_"
        )
        anchors.add(re.sub(r"\s+", "-", normalized))
    return anchors


def test_displayed_python_example_and_output_match_execution() -> None:
    displayed_source = _fenced_content(PYTHON_REFERENCE, "inspect-valid-fixture.py", "python")
    expected_output = _fenced_content(PYTHON_REFERENCE, "inspect-valid-fixture-output", "text")
    example = REPOSITORY_ROOT / "capture/examples/inspect_valid_fixture.py"
    assert displayed_source == example.read_text(encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, example],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    assert completed.stdout == expected_output


def test_python_reference_binds_closed_public_contract() -> None:
    contract = _marked_section(PYTHON_REFERENCE, "python-public-contract")
    public_types = _marked_section(PYTHON_REFERENCE, "python-public-types")

    artifact_limit = inspector_module.MAX_PRIMARY_ARTIFACT_BYTES
    limit_text = f"{artifact_limit:,} bytes ({artifact_limit // (1024 * 1024)} MiB)"
    assert contract.count(limit_text) == 2
    assert (
        contract.count(f"at most {inspector_module.MAX_JSON_NESTING_DEPTH} structural levels") == 2
    )
    assert f"One to {MAX_REPORT_ISSUES}" in contract
    for status in NATIVE_STATUSES:
        assert f"`{status}`" in contract

    signature = inspect.signature(inspect_artifact_pair)
    hints = get_type_hints(inspect_artifact_pair)
    rendered_parameters = []
    for parameter in signature.parameters.values():
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        rendered_parameters.append(f"{parameter.name}: {_display_type(hints[parameter.name])}")
    rendered_signature = (
        f"{inspect_artifact_pair.__name__}(*, {', '.join(rendered_parameters)})"
        f" -> {_display_type(hints['return'])}"
    )
    assert rendered_signature in PYTHON_REFERENCE.read_text(encoding="utf-8")

    for public_type in (
        ArtifactPairReport,
        ArtifactPairSummary,
        NativeStatusCount,
        ArtifactPairIssue,
    ):
        type_hints = get_type_hints(public_type)
        for field in fields(public_type):
            assert f"`{field.name}: {_display_type(type_hints[field.name])}`" in public_types


def test_issue_registry_binds_precedence_classification_and_recovery() -> None:
    registry = _marked_section(CLI_REFERENCE, "issue-registry")
    documented_codes = tuple(re.findall(r"`(DBT_[A-Z0-9_]+)`", registry))
    assert documented_codes == ISSUE_PRECEDENCE
    assert tuple(ISSUE_DOCUMENTATION) == ISSUE_PRECEDENCE

    data_rows = [line for line in registry.splitlines() if line.startswith("| `DBT_")]
    assert len(data_rows) == len(ISSUE_PRECEDENCE)
    for row in data_rows:
        columns = [column.strip() for column in row.strip("|").split("|")]
        assert len(columns) == 5
        code = columns[0].strip("`")
        template = inspector_module._ISSUES[code]
        expected_classification, expected_fragment = ISSUE_DOCUMENTATION[code]
        assert columns[1] == template.impact
        assert columns[2] == expected_classification
        assert columns[3] == template.next_action

        link = re.fullmatch(r"\[[^\]]+\]\((?P<target>[^)]+)\)", columns[4])
        assert link is not None
        target = unquote(link.group("target"))
        relative_path, separator, fragment = target.partition("#")
        assert separator == "#"
        assert fragment == expected_fragment
        destination = (CLI_REFERENCE.parent / relative_path).resolve()
        assert destination.is_relative_to(REPOSITORY_ROOT)
        assert destination == DIAGNOSIS_HOW_TO.resolve()
        assert fragment in _markdown_anchors(destination)


def test_real_artifact_routes_preserve_sensitive_input_boundary() -> None:
    handling_route = "handle-raw-dbt-artifacts-safely.md"
    for path in (PYTHON_REFERENCE, CLI_REFERENCE, DIAGNOSIS_HOW_TO):
        text = path.read_text(encoding="utf-8")
        assert "Personal Data" in text
        assert handling_route in text

    handling = RAW_HANDLING_HOW_TO.read_text(encoding="utf-8").casefold()
    for required_control in (
        "least-privilege",
        "do not commit",
        "ordinary support ticket",
        "retention",
        "legal-hold",
        "approved restricted-evidence process",
        "does not perform or attest that deletion",
    ):
        assert required_control.casefold() in handling

    explanation = RAW_CUSTODY_EXPLANATION.read_text(encoding="utf-8").casefold()
    for required_boundary in (
        "personal data",
        "transient in-process parsing",
        "declassification decision",
        "customer's databricks environment",
        "workstation-side candidate is not proof",
    ):
        assert required_boundary.casefold() in explanation
