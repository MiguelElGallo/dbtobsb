"""Deterministic local validation of one dbt manifest/run-results pair."""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from jsonschema.exceptions import ValidationError

from dbtobsb_capture.contracts import (
    ArtifactPairIssue,
    ArtifactPairReport,
    ArtifactPairSummary,
    NativeStatusCount,
    PairState,
)
from dbtobsb_capture.registry import (
    ISSUE_PRECEDENCE,
    MAX_REPORT_ISSUES,
    RUN_STATUSES,
    TEST_STATUSES,
)
from dbtobsb_capture.schemas import (
    MANIFEST_SCHEMA_NAME,
    RUN_RESULTS_SCHEMA_NAME,
    validator_for,
)

SUPPORTED_DBT_VERSION = "1.11.12"
SUPPORTED_ADAPTER_TYPE = "databricks"
SUPPORTED_COMMAND = "build"
SUPPORTED_MANIFEST_SCHEMA = "https://schemas.getdbt.com/dbt/manifest/v12.json"
SUPPORTED_RUN_RESULTS_SCHEMA = "https://schemas.getdbt.com/dbt/run-results/v6.json"
MAX_PRIMARY_ARTIFACT_BYTES = 128 * 1024 * 1024
MAX_JSON_NESTING_DEPTH = 256
MAX_ISSUES = MAX_REPORT_ISSUES

_SUPPORTED_RESULT_COLLECTIONS: dict[str, frozenset[str]] = {
    "nodes": frozenset({"model", "seed", "snapshot", "test"}),
    "unit_tests": frozenset({"unit_test"}),
    "saved_queries": frozenset({"saved_query"}),
    "exposures": frozenset({"exposure"}),
    "functions": frozenset({"function"}),
}
_UNSUPPORTED_RESULT_COLLECTIONS = (
    "sources",
    "macros",
    "metrics",
    "semantic_models",
)
_RUN_STATUSES = frozenset(RUN_STATUSES)
_TEST_STATUSES = frozenset(TEST_STATUSES)
_ISSUE_RANK = {code: rank for rank, code in enumerate(ISSUE_PRECEDENCE)}
_DATABRICKS_FUNCTION_MACRO_ID = "macro.dbt.materialization_function_default"
_DATABRICKS_FUNCTION_LANGUAGES = ["sql", "python", "javascript"]
_SUPPORTED_LANGUAGES_SCHEMA_PATH = (
    "properties",
    "macros",
    "additionalProperties",
    "properties",
    "supported_languages",
    "anyOf",
)


@dataclass(frozen=True, slots=True)
class _IssueTemplate:
    component: str
    field: str
    observed_category: str
    impact: str
    next_action: str


_ISSUES: dict[str, _IssueTemplate] = {
    "DBT_MANIFEST_SIZE_LIMIT_EXCEEDED": _IssueTemplate(
        "manifest",
        "document",
        "over_128_mib",
        "The manifest cannot be inspected within the bounded local memory policy.",
        "Collect a complete manifest within 128 MiB; do not split or truncate it.",
    ),
    "DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED": _IssueTemplate(
        "run_results",
        "document",
        "over_128_mib",
        "The run-results file cannot be inspected within the bounded local memory policy.",
        "Collect a complete run_results.json within 128 MiB; do not split or truncate it.",
    ),
    "DBT_MANIFEST_JSON_INVALID": _IssueTemplate(
        "manifest",
        "document",
        "invalid_utf8_or_json",
        "The manifest is not one unambiguous UTF-8 JSON document.",
        "Collect manifest.json again from the pinned dbt build target directory.",
    ),
    "DBT_RUN_RESULTS_JSON_INVALID": _IssueTemplate(
        "run_results",
        "document",
        "invalid_utf8_or_json",
        "The run-results file is not one unambiguous UTF-8 JSON document.",
        "Collect run_results.json again from the pinned dbt build target directory.",
    ),
    "DBT_MANIFEST_JSON_DUPLICATE_KEY": _IssueTemplate(
        "manifest",
        "document",
        "duplicate_object_key",
        "A duplicate JSON key makes the manifest interpretation ambiguous.",
        "Collect a new manifest from the pinned dbt build; do not repair it by hand.",
    ),
    "DBT_RUN_RESULTS_JSON_DUPLICATE_KEY": _IssueTemplate(
        "run_results",
        "document",
        "duplicate_object_key",
        "A duplicate JSON key makes the run-results interpretation ambiguous.",
        "Collect new run results from the pinned dbt build; do not repair them by hand.",
    ),
    "DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED": _IssueTemplate(
        "manifest",
        "document",
        "over_256_levels",
        "The manifest exceeds the bounded JSON nesting policy.",
        "Collect a normal unmodified manifest from the pinned dbt build.",
    ),
    "DBT_RUN_RESULTS_JSON_NESTING_LIMIT_EXCEEDED": _IssueTemplate(
        "run_results",
        "document",
        "over_256_levels",
        "The run-results file exceeds the bounded JSON nesting policy.",
        "Collect normal unmodified run results from the pinned dbt build.",
    ),
    "DBT_MANIFEST_SCHEMA_INVALID": _IssueTemplate(
        "manifest",
        "document",
        "schema_violation",
        "The manifest does not satisfy the vendored dbt manifest v12 schema.",
        "Re-run the pinned dbt build and collect its unmodified manifest.json.",
    ),
    "DBT_RUN_RESULTS_SCHEMA_INVALID": _IssueTemplate(
        "run_results",
        "document",
        "schema_violation",
        "The run-results file does not satisfy the vendored dbt run-results v6 schema.",
        "Re-run the pinned dbt build and collect its unmodified run_results.json.",
    ),
    "DBT_SCHEMA_VERSION_UNSUPPORTED": _IssueTemplate(
        "artifact_pair",
        "metadata.dbt_schema_version",
        "not_exact_v12_v6_pair",
        "The files are not the exact artifact-schema pair qualified by P1.1.",
        "Use manifest v12 and run-results v6, or qualify a new pair before inspection.",
    ),
    "DBT_CORE_VERSION_UNSUPPORTED": _IssueTemplate(
        "artifact_pair",
        "metadata.dbt_version",
        "not_exact_1_11_12_pair",
        "The files were not both produced by the qualified dbt Core version.",
        "Run the supported job with dbt-core 1.11.12 and collect both artifacts again.",
    ),
    "DBT_INVOCATION_ID_INVALID": _IssueTemplate(
        "artifact_pair",
        "metadata.invocation_id",
        "missing_or_invalid_uuid",
        "The files cannot be bound to one parseable dbt invocation.",
        "Collect both closed artifacts from one completed pinned dbt build invocation "
        "before another dbt command runs.",
    ),
    "DBT_INVOCATION_ID_MISMATCH": _IssueTemplate(
        "artifact_pair",
        "metadata.invocation_id",
        "different_valid_values",
        "The files do not have the same dbt invocation identity.",
        "Collect both closed artifacts from one completed pinned dbt build invocation "
        "before another dbt command runs.",
    ),
    "DBT_ADAPTER_TYPE_UNSUPPORTED": _IssueTemplate(
        "manifest",
        "metadata.adapter_type",
        "not_databricks",
        "The manifest is not from the qualified Databricks adapter path.",
        "Use the pinned dbt-databricks job or qualify another adapter separately.",
    ),
    "DBT_COMMAND_UNSUPPORTED": _IssueTemplate(
        "run_results",
        "args.command_and_selector",
        "not_approved_named_selector_build",
        "The result artifact is not evidence from the exact supported named-selector build.",
        "Run the approved named-selector dbt build and collect that run_results.json.",
    ),
    "DBT_EMPTY_EXECUTION": _IssueTemplate(
        "run_results",
        "results",
        "empty",
        "An empty result array does not satisfy the supported execution contract.",
        "Fix the selector or executable-node set, then run the pinned dbt build again.",
    ),
    "DBT_RESULTS_DUPLICATE_ID": _IssueTemplate(
        "run_results",
        "results.unique_id",
        "duplicate",
        "One dbt resource appears more than once in the execution results.",
        "Collect a fresh unmodified artifact pair from the pinned dbt build.",
    ),
    "DBT_RESULT_ID_UNRESOLVED": _IssueTemplate(
        "artifact_pair",
        "results.unique_id",
        "missing_from_supported_manifest_collections",
        "An executed result cannot be resolved to the supported manifest inventory.",
        "Collect manifest.json and run_results.json from the same build invocation.",
    ),
    "DBT_RESULT_ID_UNSUPPORTED_RESOURCE": _IssueTemplate(
        "artifact_pair",
        "results.unique_id",
        "unsupported_manifest_collection",
        "A result resolves only to a resource type that P1.1 does not accept for build results.",
        "Use the supported dbt build contract or qualify this evidence type separately.",
    ),
    "DBT_RESULT_ID_AMBIGUOUS": _IssueTemplate(
        "artifact_pair",
        "results.unique_id",
        "multiple_manifest_matches",
        "A result identifier has more than one possible manifest resource.",
        "Collect a fresh unmodified artifact pair; do not choose a resource manually.",
    ),
    "DBT_MANIFEST_RESOURCE_ID_MISMATCH": _IssueTemplate(
        "manifest",
        "resource.unique_id",
        "mapping_key_and_resource_disagree",
        "A matched manifest resource contradicts its enclosing identifier.",
        "Collect a fresh unmodified manifest from the pinned dbt build.",
    ),
    "DBT_RESULT_RESOURCE_TYPE_UNSUPPORTED": _IssueTemplate(
        "artifact_pair",
        "resource.resource_type",
        "not_allowed_for_buildtask_collection",
        "A matched manifest collection contains a resource type that BuildTask does not accept.",
        "Collect a fresh pair from the pinned build or qualify the resource type separately.",
    ),
    "DBT_RESULT_STATUS_UNSUPPORTED": _IssueTemplate(
        "artifact_pair",
        "results.status",
        "not_allowed_for_resource_type",
        "The native dbt status is not valid for the matched resource type.",
        "Collect a fresh pair from the pinned build; do not reinterpret the status.",
    ),
    "DBT_TIMING_INVALID": _IssueTemplate(
        "run_results",
        "metadata.generated_at_or_elapsed_time_or_results.execution_time",
        "invalid_timestamp_or_duration",
        "The artifact contains a timestamp or duration that cannot be stored as execution time.",
        "Collect a fresh unmodified run_results.json from the pinned dbt build.",
    ),
    "DBT_FAILURE_COUNT_INVALID": _IssueTemplate(
        "run_results",
        "results.failures",
        "negative",
        "The artifact contains a negative dbt failure count.",
        "Collect a fresh unmodified run_results.json from the pinned dbt build.",
    ),
}
if tuple(_ISSUES) != ISSUE_PRECEDENCE:
    raise RuntimeError("issue registry and shared precedence are inconsistent")


class _DuplicateJsonKey(ValueError):
    """Internal marker; the duplicate key itself is intentionally discarded."""


def _issue(code: str) -> ArtifactPairIssue:
    template = _ISSUES[code]
    return ArtifactPairIssue(
        code=code,
        component=template.component,
        field=template.field,
        observed_category=template.observed_category,
        impact=template.impact,
        next_action=template.next_action,
    )


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey
        result[key] = value
    return result


def _reject_json_constant(_: str) -> None:
    raise ValueError


def _json_nesting_exceeds_limit(raw: bytes) -> bool:
    """Bound structural depth before the recursive standard decoder runs."""
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:  # backslash
                escaped = True
            elif byte == 0x22:  # quote
                in_string = False
        elif byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):  # opening bracket or brace
            depth += 1
            if depth > MAX_JSON_NESTING_DEPTH:
                return True
        elif byte in (0x5D, 0x7D) and depth:
            depth -= 1
    return False


def _parse_json(raw: bytes, *, component: str) -> tuple[dict[str, Any] | None, str | None]:
    duplicate_code = f"DBT_{component.upper()}_JSON_DUPLICATE_KEY"
    invalid_code = f"DBT_{component.upper()}_JSON_INVALID"
    try:
        decoded = raw.decode("utf-8")
        value: Any = json.loads(
            decoded,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_json_constant,
        )
    except _DuplicateJsonKey:
        return None, duplicate_code
    except RecursionError:
        return None, f"DBT_{component.upper()}_JSON_NESTING_LIMIT_EXCEEDED"
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None, invalid_code
    if not isinstance(value, dict):
        return None, invalid_code
    return value, None


def _is_qualified_databricks_manifest_exception(error: ValidationError) -> bool:
    """Accept the one reviewed dbt-databricks 1.12.2 manifest-v12 schema mismatch."""
    return (
        error.validator == "anyOf"
        and tuple(error.absolute_path)
        == ("macros", _DATABRICKS_FUNCTION_MACRO_ID, "supported_languages")
        and tuple(error.absolute_schema_path) == _SUPPORTED_LANGUAGES_SCHEMA_PATH
        and error.instance == _DATABRICKS_FUNCTION_LANGUAGES
    )


def _manifest_schema_is_accepted(document: dict[str, Any]) -> bool:
    """Apply the same strict manifest schema contract for pair and partial capture."""
    errors = validator_for(MANIFEST_SCHEMA_NAME).iter_errors(document)
    return all(_is_qualified_databricks_manifest_exception(error) for error in errors)


def _uuid(value: Any) -> UUID | None:
    if not isinstance(value, str):
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resource_match(
    manifest: dict[str, Any], unique_id: str
) -> tuple[int, int, bool, bool, str | None]:
    supported_count = 0
    unsupported_count = 0
    matched_resource_consistent = True
    matched_resource_type_allowed = True
    matched_resource_type: str | None = None

    for collection_name, allowed_types in _SUPPORTED_RESULT_COLLECTIONS.items():
        collection = _mapping(manifest.get(collection_name))
        if unique_id in collection:
            supported_count += 1
            resource = collection[unique_id]
            if not isinstance(resource, dict) or resource.get("unique_id") != unique_id:
                matched_resource_consistent = False
            if isinstance(resource, dict):
                resource_type = resource.get("resource_type")
                if isinstance(resource_type, str):
                    matched_resource_type = resource_type
                if resource_type not in allowed_types:
                    matched_resource_type_allowed = False
            else:
                matched_resource_type_allowed = False

    for collection_name in _UNSUPPORTED_RESULT_COLLECTIONS:
        collection = _mapping(manifest.get(collection_name))
        if unique_id in collection:
            unsupported_count += 1

    return (
        supported_count,
        unsupported_count,
        matched_resource_consistent,
        matched_resource_type_allowed,
        matched_resource_type,
    )


def _is_nonnegative_finite_number(value: Any) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _is_offset_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or "T" not in value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _invalid(codes: list[str]) -> ArtifactPairReport:
    unique_codes = tuple(sorted(dict.fromkeys(codes), key=_ISSUE_RANK.__getitem__)[:MAX_ISSUES])
    return ArtifactPairReport(
        state=PairState.INVALID,
        summary=None,
        issues=tuple(_issue(code) for code in unique_codes),
    )


def _inspect_artifact_pair_for_selector(
    *, manifest: bytes, run_results: bytes, expected_selector: str
) -> ArtifactPairReport:
    """Inspect one in-memory pair without opening caller paths or external services.

    Expected evidence failures return ``PAIR_INVALID`` with static issue text. The
    returned object never retains raw bytes, SQL, messages, paths, environment values,
    node identifiers, project names, relation names, or invocation identifiers. Validation
    reads only the installed checksum-pinned schema resources; it performs no network,
    environment, clock, subprocess, dbt, or Databricks access.
    """
    if not isinstance(manifest, bytes) or not isinstance(run_results, bytes):
        raise TypeError("manifest and run_results must be bytes")

    size_codes: list[str] = []
    if len(manifest) > MAX_PRIMARY_ARTIFACT_BYTES:
        size_codes.append("DBT_MANIFEST_SIZE_LIMIT_EXCEEDED")
    if len(run_results) > MAX_PRIMARY_ARTIFACT_BYTES:
        size_codes.append("DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED")
    if size_codes:
        return _invalid(size_codes)

    nesting_codes: list[str] = []
    if _json_nesting_exceeds_limit(manifest):
        nesting_codes.append("DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED")
    if _json_nesting_exceeds_limit(run_results):
        nesting_codes.append("DBT_RUN_RESULTS_JSON_NESTING_LIMIT_EXCEEDED")
    if nesting_codes:
        return _invalid(nesting_codes)

    manifest_document, manifest_error = _parse_json(manifest, component="manifest")
    run_document, run_error = _parse_json(run_results, component="run_results")
    parse_codes = [code for code in (manifest_error, run_error) if code is not None]
    if parse_codes:
        return _invalid(parse_codes)
    if manifest_document is None or run_document is None:
        raise RuntimeError("artifact parsing invariant failed")

    schema_codes: list[str] = []
    try:
        if not _manifest_schema_is_accepted(manifest_document):
            schema_codes.append("DBT_MANIFEST_SCHEMA_INVALID")
    except RecursionError:
        schema_codes.append("DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED")
    try:
        run_errors = iter(validator_for(RUN_RESULTS_SCHEMA_NAME).iter_errors(run_document))
        if next(run_errors, None) is not None:
            schema_codes.append("DBT_RUN_RESULTS_SCHEMA_INVALID")
    except RecursionError:
        schema_codes.append("DBT_RUN_RESULTS_JSON_NESTING_LIMIT_EXCEEDED")
    if schema_codes:
        return _invalid(schema_codes)

    manifest_metadata = _mapping(manifest_document.get("metadata"))
    run_metadata = _mapping(run_document.get("metadata"))
    run_args = _mapping(run_document.get("args"))
    results = run_document.get("results")
    if not isinstance(results, list):
        raise RuntimeError("validated run-results invariant failed")

    codes: list[str] = []
    manifest_schema = manifest_metadata.get("dbt_schema_version")
    run_schema = run_metadata.get("dbt_schema_version")
    if manifest_schema != SUPPORTED_MANIFEST_SCHEMA or run_schema != SUPPORTED_RUN_RESULTS_SCHEMA:
        codes.append("DBT_SCHEMA_VERSION_UNSUPPORTED")

    manifest_version = manifest_metadata.get("dbt_version")
    run_version = run_metadata.get("dbt_version")
    if manifest_version != SUPPORTED_DBT_VERSION or run_version != SUPPORTED_DBT_VERSION:
        codes.append("DBT_CORE_VERSION_UNSUPPORTED")

    manifest_invocation = _uuid(manifest_metadata.get("invocation_id"))
    run_invocation = _uuid(run_metadata.get("invocation_id"))
    if manifest_invocation is None or run_invocation is None:
        codes.append("DBT_INVOCATION_ID_INVALID")
    elif manifest_invocation != run_invocation:
        codes.append("DBT_INVOCATION_ID_MISMATCH")

    if manifest_metadata.get("adapter_type") != SUPPORTED_ADAPTER_TYPE:
        codes.append("DBT_ADAPTER_TYPE_UNSUPPORTED")
    if (
        run_args.get("which") != SUPPORTED_COMMAND
        or run_args.get("selector") != expected_selector
        or run_args.get("select") != []
        or run_args.get("exclude") != []
        or run_args.get("indirect_selection") != "eager"
        or run_args.get("full_refresh") is not None
    ):
        codes.append("DBT_COMMAND_UNSUPPORTED")
    if not results:
        codes.append("DBT_EMPTY_EXECUTION")

    if (
        not _is_offset_timestamp(manifest_metadata.get("generated_at"))
        or not _is_offset_timestamp(run_metadata.get("generated_at"))
        or not _is_nonnegative_finite_number(run_document.get("elapsed_time"))
    ):
        codes.append("DBT_TIMING_INVALID")

    result_ids = [result.get("unique_id") for result in results if isinstance(result, dict)]
    string_result_ids = [item for item in result_ids if isinstance(item, str)]
    if len(set(string_result_ids)) != len(string_result_ids):
        codes.append("DBT_RESULTS_DUPLICATE_ID")

    results_by_id = {
        result["unique_id"]: result
        for result in results
        if isinstance(result, dict) and isinstance(result.get("unique_id"), str)
    }
    for unique_id in dict.fromkeys(string_result_ids):
        (
            supported_count,
            unsupported_count,
            consistent,
            resource_type_allowed,
            resource_type,
        ) = _resource_match(manifest_document, unique_id)
        if supported_count > 1 or (supported_count > 0 and unsupported_count > 0):
            codes.append("DBT_RESULT_ID_AMBIGUOUS")
        elif supported_count == 0 and unsupported_count > 0:
            codes.append("DBT_RESULT_ID_UNSUPPORTED_RESOURCE")
        elif supported_count == 0:
            codes.append("DBT_RESULT_ID_UNRESOLVED")
        elif not consistent:
            codes.append("DBT_MANIFEST_RESOURCE_ID_MISMATCH")
        elif not resource_type_allowed or resource_type is None:
            codes.append("DBT_RESULT_RESOURCE_TYPE_UNSUPPORTED")
        else:
            result = results_by_id[unique_id]
            status = result.get("status")
            allowed_statuses = (
                _TEST_STATUSES if resource_type in {"test", "unit_test"} else _RUN_STATUSES
            )
            if status not in allowed_statuses:
                codes.append("DBT_RESULT_STATUS_UNSUPPORTED")

    for result in results:
        if not isinstance(result, dict):
            continue
        if not _is_nonnegative_finite_number(result.get("execution_time")):
            codes.append("DBT_TIMING_INVALID")
        failures = result.get("failures")
        if isinstance(failures, int) and not isinstance(failures, bool) and failures < 0:
            codes.append("DBT_FAILURE_COUNT_INVALID")

    if codes:
        return _invalid(codes)

    statuses = Counter(
        result["status"]
        for result in results
        if isinstance(result, dict) and isinstance(result.get("status"), str)
    )
    summary = ArtifactPairSummary(
        manifest_schema=SUPPORTED_MANIFEST_SCHEMA,
        run_results_schema=SUPPORTED_RUN_RESULTS_SCHEMA,
        dbt_version=SUPPORTED_DBT_VERSION,
        adapter_type=SUPPORTED_ADAPTER_TYPE,
        command=SUPPORTED_COMMAND,
        status_counts=tuple(
            NativeStatusCount(status=status, count=count)
            for status, count in sorted(statuses.items())
        ),
    )
    return ArtifactPairReport(state=PairState.VALID, summary=summary, issues=())


def inspect_artifact_pair(*, manifest: bytes, run_results: bytes) -> ArtifactPairReport:
    """Inspect one pair against the fixed engineering-preview selector.

    The v1 collector uses the internal selector-aware inspector with a selector
    obtained from installed configuration. This wrapper preserves the P1.1 public API.
    """
    return _inspect_artifact_pair_for_selector(
        manifest=manifest,
        run_results=run_results,
        expected_selector="observability_demo",
    )
