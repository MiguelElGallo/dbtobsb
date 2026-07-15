"""Contract tests for the deterministic P1.1 artifact-pair inspector."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

from dbtobsb_capture import (
    ArtifactPairIssue,
    ArtifactPairReport,
    ArtifactPairSummary,
    NativeStatusCount,
    PairState,
    inspect_artifact_pair,
)
from dbtobsb_capture import inspector as inspector_module
from dbtobsb_capture import schemas as schemas_module
from dbtobsb_capture.inspector import _ISSUES, MAX_ISSUES
from dbtobsb_capture.registry import ISSUE_PRECEDENCE, MAX_REPORT_ISSUES, NATIVE_STATUSES
from dbtobsb_capture.schemas import (
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_SHA256,
    RUN_RESULTS_SCHEMA_NAME,
    RUN_RESULTS_SCHEMA_SHA256,
    validator_for,
)

FIXTURES = Path(__file__).parent / "fixtures" / "artifact_pair"
REPORT_SCHEMA = (
    Path(__file__).parents[1]
    / "src"
    / "dbtobsb_capture"
    / "schemas"
    / "artifact-pair-report-v1.json"
)
MODEL_ID = "model.dbtobsb_capture_fixture.observed_model"
SEED_ID = "seed.dbtobsb_capture_fixture.observed_seed"
SNAPSHOT_ID = "snapshot.dbtobsb_capture_fixture.observed_snapshot"
DATA_TEST_ID = "test.dbtobsb_capture_fixture.not_null_observed_model_fixture_id.397be03b66"
UNIT_TEST_ID = "unit_test.dbtobsb_capture_fixture.observed_model.observed_model_returns_one"
SAVED_QUERY_ID = "saved_query.dbtobsb_capture_fixture.fixture_saved_query"
EXPOSURE_ID = "exposure.dbtobsb_capture_fixture.fixture_dashboard"
FUNCTION_ID = "function.dbtobsb_capture_fixture.fixture_double"
SOURCE_ID = "source.dbtobsb_capture_fixture.fixture_source.fixture_table"
MACRO_ID = "macro.dbtobsb_capture_fixture.fixture_macro"
METRIC_ID = "metric.dbtobsb_capture_fixture.fixture_row_count"
SEMANTIC_MODEL_ID = "semantic_model.dbtobsb_capture_fixture.fixture_semantic"
CANARY_PREFIX = "CANARY_"


def _bytes(fixture: str, name: str) -> bytes:
    return (FIXTURES / fixture / name).read_bytes()


def _json(fixture: str, name: str) -> dict[str, Any]:
    value: Any = json.loads(_bytes(fixture, name))
    assert isinstance(value, dict)
    return value


def _dump(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n").encode()


def _inspect_documents(
    manifest: dict[str, Any], run_results: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    report = inspect_artifact_pair(manifest=_dump(manifest), run_results=_dump(run_results))
    return report.state.value, report.to_dict()


def _primary_code(report: dict[str, Any]) -> str:
    primary = report["issues"][0]
    assert isinstance(primary, dict)
    code = primary["code"]
    assert isinstance(code, str)
    return code


def _closed_issue(code: str) -> ArtifactPairIssue:
    template = _ISSUES[code]
    return ArtifactPairIssue(
        code=code,
        component=template.component,
        field=template.field,
        observed_category=template.observed_category,
        impact=template.impact,
        next_action=template.next_action,
    )


@pytest.mark.parametrize("fixture", ["valid_success", "valid_dbt_failure"])
def test_golden_valid_reports_match_reviewed_snapshots(fixture: str) -> None:
    report = inspect_artifact_pair(
        manifest=_bytes(fixture, "manifest.json"),
        run_results=_bytes(fixture, "run_results.json"),
    )

    assert report.state is PairState.VALID
    assert report.to_dict() == _json(fixture, "expected-report.json")
    Draft202012Validator(json.loads(REPORT_SCHEMA.read_bytes())).validate(report.to_dict())


def test_dbt_failure_is_valid_evidence_but_not_relabelled_success() -> None:
    report = inspect_artifact_pair(
        manifest=_bytes("valid_dbt_failure", "manifest.json"),
        run_results=_bytes("valid_dbt_failure", "run_results.json"),
    )

    assert report.state is PairState.VALID
    assert report.summary is not None
    assert [(item.status, item.count) for item in report.summary.status_counts] == [("error", 1)]


def test_invalid_fixture_matches_reviewed_snapshot() -> None:
    report = inspect_artifact_pair(
        manifest=_bytes("invalid_invocation_mismatch", "manifest.json"),
        run_results=_bytes("invalid_invocation_mismatch", "run_results.json"),
    )

    assert report.state is PairState.INVALID
    assert report.to_dict() == _json("invalid_invocation_mismatch", "expected-report.json")
    Draft202012Validator(json.loads(REPORT_SCHEMA.read_bytes())).validate(report.to_dict())


def test_report_and_repr_exclude_every_sensitive_canary_and_raw_identifier() -> None:
    report = inspect_artifact_pair(
        manifest=_bytes("valid_success", "manifest.json"),
        run_results=_bytes("valid_success", "run_results.json"),
    )
    rendered = json.dumps(report.to_dict(), sort_keys=True) + repr(report) + str(report)

    assert CANARY_PREFIX not in rendered
    assert MODEL_ID not in rendered
    assert "11111111-1111-4111-8111-111111111111" not in rendered


def test_repeated_runs_produce_byte_identical_machine_reports() -> None:
    manifest = _bytes("valid_success", "manifest.json")
    run_results = _bytes("valid_success", "run_results.json")

    reports = [
        json.dumps(
            inspect_artifact_pair(manifest=manifest, run_results=run_results).to_dict(),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        for _ in range(5)
    ]

    assert len(set(reports)) == 1


def test_vendored_schema_digests_and_drafts_are_frozen() -> None:
    schema_root = Path(__file__).parents[1] / "src" / "dbtobsb_capture" / "schemas"
    manifest_bytes = (schema_root / MANIFEST_SCHEMA_NAME).read_bytes()
    run_results_bytes = (schema_root / RUN_RESULTS_SCHEMA_NAME).read_bytes()

    assert hashlib.sha256(manifest_bytes).hexdigest() == MANIFEST_SCHEMA_SHA256
    assert hashlib.sha256(run_results_bytes).hexdigest() == RUN_RESULTS_SCHEMA_SHA256
    assert json.loads(manifest_bytes)["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert (
        json.loads(run_results_bytes)["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    )


def test_fresh_inspection_reads_only_installed_checksum_pinned_schema_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    real_files = schemas_module.files

    def audited_files(anchor: Any) -> Any:
        calls.append(str(anchor))
        return real_files(anchor)

    validator_for.cache_clear()
    monkeypatch.setattr(schemas_module, "files", audited_files)
    report = inspect_artifact_pair(
        manifest=_bytes("valid_success", "manifest.json"),
        run_results=_bytes("valid_success", "run_results.json"),
    )
    validator_for.cache_clear()

    assert report.state is PairState.VALID
    assert calls == ["dbtobsb_capture", "dbtobsb_capture"]


def test_golden_artifacts_satisfy_the_exact_vendored_schemas() -> None:
    for fixture in ("valid_success", "valid_dbt_failure", "invalid_invocation_mismatch"):
        validator_for(MANIFEST_SCHEMA_NAME).validate(_json(fixture, "manifest.json"))
        validator_for(RUN_RESULTS_SCHEMA_NAME).validate(_json(fixture, "run_results.json"))


def test_fixture_provenance_never_claims_live_runtime_evidence() -> None:
    for fixture in ("valid_success", "valid_dbt_failure", "invalid_invocation_mismatch"):
        provenance = _json(fixture, "provenance.json")
        assert provenance["runtime_evidence"] is False
        assert provenance["candidate_context"]["runtime_attestation"] is False
        assert "does not attest" in provenance["candidate_context"]["note"]
        assert (
            provenance["source_manifest_sha256"]
            == "14d1b3c6f54831fcc004bfad548578c0b955e03f41db786bba7f484391be419c"
        )
        assert "validates without an overlay" in provenance["schema_compatibility_note"]
        assert (
            provenance["artifact_sha256"]["manifest"]
            == hashlib.sha256(_bytes(fixture, "manifest.json")).hexdigest()
        )
        assert (
            provenance["artifact_sha256"]["run_results"]
            == hashlib.sha256(_bytes(fixture, "run_results.json")).hexdigest()
        )


@pytest.mark.parametrize(
    ("manifest", "run_results", "expected"),
    [
        (b"not-json", b"{}", "DBT_MANIFEST_JSON_INVALID"),
        (b"{}", b"\xff", "DBT_RUN_RESULTS_JSON_INVALID"),
        (b'{"metadata":{},"metadata":{}}', b"{}", "DBT_MANIFEST_JSON_DUPLICATE_KEY"),
        (b"{}", b'{"results":[],"results":[]}', "DBT_RUN_RESULTS_JSON_DUPLICATE_KEY"),
        (b'{"value":NaN}', b"{}", "DBT_MANIFEST_JSON_INVALID"),
    ],
)
def test_strict_json_failures_are_safe_and_stable(
    manifest: bytes, run_results: bytes, expected: str
) -> None:
    report = inspect_artifact_pair(manifest=manifest, run_results=run_results)

    assert report.state is PairState.INVALID
    assert report.primary_issue is not None
    assert report.primary_issue.code == expected
    assert CANARY_PREFIX not in repr(report)


def test_size_limit_rejects_before_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(inspector_module, "MAX_PRIMARY_ARTIFACT_BYTES", 3)

    report = inspect_artifact_pair(manifest=b"four", run_results=b"also-four")

    assert [issue.code for issue in report.issues] == [
        "DBT_MANIFEST_SIZE_LIMIT_EXCEEDED",
        "DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED",
    ]


def test_nesting_limit_returns_stable_invalid_report_without_recursion_error() -> None:
    deeply_nested = (b"[" * 300) + b"0" + (b"]" * 300)

    report = inspect_artifact_pair(manifest=deeply_nested, run_results=deeply_nested)

    assert [issue.code for issue in report.issues] == [
        "DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED",
        "DBT_RUN_RESULTS_JSON_NESTING_LIMIT_EXCEEDED",
    ]


def test_schema_failures_stop_before_semantic_interpretation() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    del manifest["nodes"]
    del run_results["elapsed_time"]

    _, report = _inspect_documents(manifest, run_results)

    assert [issue["code"] for issue in report["issues"]] == [
        "DBT_MANIFEST_SCHEMA_INVALID",
        "DBT_RUN_RESULTS_SCHEMA_INVALID",
    ]


@pytest.mark.parametrize(
    ("mutator", "expected"),
    [
        (
            lambda manifest, run: manifest["metadata"].update(
                dbt_schema_version="https://schemas.getdbt.com/dbt/manifest/v11.json"
            ),
            "DBT_SCHEMA_VERSION_UNSUPPORTED",
        ),
        (
            lambda manifest, run: run["metadata"].update(dbt_version="1.11.11"),
            "DBT_CORE_VERSION_UNSUPPORTED",
        ),
        (
            lambda manifest, run: manifest["metadata"].update(invocation_id=None),
            "DBT_INVOCATION_ID_INVALID",
        ),
        (
            lambda manifest, run: manifest["metadata"].update(adapter_type="spark"),
            "DBT_ADAPTER_TYPE_UNSUPPORTED",
        ),
        (
            lambda manifest, run: run["args"].update(which="run"),
            "DBT_COMMAND_UNSUPPORTED",
        ),
        (
            lambda manifest, run: run.update(results=[]),
            "DBT_EMPTY_EXECUTION",
        ),
    ],
)
def test_standalone_and_pair_semantic_mutations_have_stable_codes(
    mutator: Any, expected: str
) -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    mutator(manifest, run_results)

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == expected


def test_duplicate_result_identifier_is_invalid() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"].append(copy.deepcopy(run_results["results"][0]))

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == "DBT_RESULTS_DUPLICATE_ID"


@pytest.mark.parametrize(
    ("unique_id", "expected"),
    [
        ("model.dbtobsb_capture_fixture.missing", "DBT_RESULT_ID_UNRESOLVED"),
        (SOURCE_ID, "DBT_RESULT_ID_UNSUPPORTED_RESOURCE"),
    ],
)
def test_result_resolution_rejects_missing_and_prohibited_collections(
    unique_id: str, expected: str
) -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"][0]["unique_id"] = unique_id

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == expected


def test_result_resolution_rejects_ambiguous_supported_collections() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    duplicate = copy.deepcopy(manifest["exposures"][EXPOSURE_ID])
    duplicate["unique_id"] = MODEL_ID
    duplicate["name"] = "observed_model"
    manifest["exposures"][MODEL_ID] = duplicate

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == "DBT_RESULT_ID_AMBIGUOUS"


def test_result_resolution_rejects_inner_id_mismatch() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    manifest["nodes"][MODEL_ID]["unique_id"] = "model.dbtobsb_capture_fixture.other"

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == "DBT_MANIFEST_RESOURCE_ID_MISMATCH"


def test_resource_aware_status_rejects_test_status_for_model() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"][0]["status"] = "pass"

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == "DBT_RESULT_STATUS_UNSUPPORTED"


@pytest.mark.parametrize(
    "status",
    ["success", "error", "skipped", "partial success", "no-op"],
)
def test_every_supported_run_status_remains_native(status: str) -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"][0]["status"] = status

    state, report = _inspect_documents(manifest, run_results)

    assert state == "PAIR_VALID"
    assert report["summary"]["status_counts"] == {status: 1}


@pytest.mark.parametrize(
    "status",
    ["pass", "error", "fail", "warn", "skipped"],
)
def test_every_supported_test_status_remains_native(status: str) -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"][0]["unique_id"] = UNIT_TEST_ID
    run_results["results"][0]["status"] = status

    state, report = _inspect_documents(manifest, run_results)

    assert state == "PAIR_VALID"
    assert report["summary"]["status_counts"] == {status: 1}


def test_freshness_only_runtime_error_status_is_not_accepted_for_build_result() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"][0]["status"] = "runtime error"

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == "DBT_RESULT_STATUS_UNSUPPORTED"


@pytest.mark.parametrize(
    ("unique_id", "status"),
    [
        (MODEL_ID, "success"),
        (SEED_ID, "success"),
        (SNAPSHOT_ID, "success"),
        (DATA_TEST_ID, "pass"),
        (UNIT_TEST_ID, "pass"),
        (SAVED_QUERY_ID, "success"),
        (EXPOSURE_ID, "success"),
        (FUNCTION_ID, "success"),
    ],
)
def test_supported_buildtask_collections_use_resource_aware_statuses(
    unique_id: str, status: str
) -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"][0]["unique_id"] = unique_id
    run_results["results"][0]["status"] = status

    state, report = _inspect_documents(manifest, run_results)

    assert state == "PAIR_VALID"
    assert report["summary"]["status_counts"] == {status: 1}


@pytest.mark.parametrize(
    "unique_id",
    [SOURCE_ID, MACRO_ID, METRIC_ID, SEMANTIC_MODEL_ID],
)
def test_every_unsupported_manifest_collection_is_rejected(unique_id: str) -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"][0]["unique_id"] = unique_id

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == "DBT_RESULT_ID_UNSUPPORTED_RESOURCE"


def test_supported_and_unsupported_collection_collision_is_ambiguous() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    source = copy.deepcopy(manifest["sources"][SOURCE_ID])
    source["unique_id"] = MODEL_ID
    manifest["sources"][MODEL_ID] = source

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == "DBT_RESULT_ID_AMBIGUOUS"


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("elapsed", "DBT_TIMING_INVALID"),
        ("execution", "DBT_TIMING_INVALID"),
        ("failures", "DBT_FAILURE_COUNT_INVALID"),
    ],
)
def test_numeric_semantics_reject_impossible_values(mutation: str, expected: str) -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    if mutation == "elapsed":
        run_results["elapsed_time"] = -1
    elif mutation == "execution":
        run_results["results"][0]["execution_time"] = -1
    else:
        run_results["results"][0]["failures"] = -1

    _, report = _inspect_documents(manifest, run_results)

    assert _primary_code(report) == expected


def test_issue_list_is_deduplicated_and_bounded() -> None:
    manifest = _json("valid_success", "manifest.json")
    run_results = _json("valid_success", "run_results.json")
    run_results["results"] = [
        {**copy.deepcopy(run_results["results"][0]), "unique_id": f"model.fixture.missing_{i}"}
        for i in range(MAX_ISSUES + 10)
    ]

    _, report = _inspect_documents(manifest, run_results)

    assert len(report["issues"]) == 1
    assert _primary_code(report) == "DBT_RESULT_ID_UNRESOLVED"


def test_programmer_misuse_exception_is_static_and_evidence_safe() -> None:
    with pytest.raises(TypeError, match="manifest and run_results must be bytes") as error:
        inspect_artifact_pair(manifest=cast(bytes, "CANARY_SECRET"), run_results=b"{}")

    assert CANARY_PREFIX not in str(error.value)


def test_closed_python_contract_rejects_invented_status_and_issue_text() -> None:
    with pytest.raises(ValueError, match="native vocabulary"):
        NativeStatusCount(status="invented", count=1)
    template = _ISSUES["DBT_EMPTY_EXECUTION"]
    with pytest.raises(ValueError, match="closed v1 issue"):
        ArtifactPairIssue(
            code="DBT_EMPTY_EXECUTION",
            component=template.component,
            field=template.field,
            observed_category=template.observed_category,
            impact="invented evidence-bearing text",
            next_action=template.next_action,
        )


def test_top_level_python_contract_rejects_values_outside_the_json_protocol() -> None:
    first_issue = _closed_issue(ISSUE_PRECEDENCE[0])
    second_issue = _closed_issue(ISSUE_PRECEDENCE[1])

    with pytest.raises(ValueError, match="PairState"):
        ArtifactPairReport(cast(PairState, "INVENTED"), None, ())
    with pytest.raises(ValueError, match="ArtifactPairSummary"):
        ArtifactPairReport(PairState.VALID, cast(ArtifactPairSummary, object()), ())
    with pytest.raises(ValueError, match="tuple"):
        ArtifactPairReport(
            PairState.INVALID,
            None,
            cast(tuple[ArtifactPairIssue, ...], [first_issue]),
        )
    with pytest.raises(ValueError, match="ArtifactPairIssue"):
        ArtifactPairReport(
            PairState.INVALID,
            None,
            (cast(ArtifactPairIssue, object()),),
        )
    with pytest.raises(ValueError, match="maximum"):
        ArtifactPairReport(
            PairState.INVALID,
            None,
            tuple(_closed_issue(code) for code in ISSUE_PRECEDENCE[: MAX_REPORT_ISSUES + 1]),
        )
    with pytest.raises(ValueError, match="unique"):
        ArtifactPairReport(PairState.INVALID, None, (first_issue, first_issue))
    with pytest.raises(ValueError, match="precedence"):
        ArtifactPairReport(PairState.INVALID, None, (second_issue, first_issue))


def test_summary_python_contract_rejects_wrong_status_count_container_and_object() -> None:
    base = {
        "manifest_schema": "https://schemas.getdbt.com/dbt/manifest/v12.json",
        "run_results_schema": "https://schemas.getdbt.com/dbt/run-results/v6.json",
        "dbt_version": "1.11.12",
        "adapter_type": "databricks",
        "command": "build",
    }
    status = NativeStatusCount(status="success", count=1)

    with pytest.raises(ValueError, match="tuple"):
        ArtifactPairSummary(
            **base,
            status_counts=cast(tuple[NativeStatusCount, ...], [status]),
        )
    with pytest.raises(ValueError, match="NativeStatusCount"):
        ArtifactPairSummary(
            **base,
            status_counts=(cast(NativeStatusCount, object()),),
        )


def test_every_constructible_top_level_shape_validates_against_report_schema() -> None:
    validator = Draft202012Validator(json.loads(REPORT_SCHEMA.read_bytes()))
    issues = tuple(_closed_issue(code) for code in ISSUE_PRECEDENCE[:MAX_REPORT_ISSUES])

    report = ArtifactPairReport(PairState.INVALID, None, issues)

    validator.validate(report.to_dict())


def test_every_closed_status_and_issue_variant_validates_against_report_schema() -> None:
    validator = Draft202012Validator(json.loads(REPORT_SCHEMA.read_bytes()))
    for status in NATIVE_STATUSES:
        summary = ArtifactPairSummary(
            manifest_schema="https://schemas.getdbt.com/dbt/manifest/v12.json",
            run_results_schema="https://schemas.getdbt.com/dbt/run-results/v6.json",
            dbt_version="1.11.12",
            adapter_type="databricks",
            command="build",
            status_counts=(NativeStatusCount(status=status, count=1),),
        )
        validator.validate(ArtifactPairReport(PairState.VALID, summary, ()).to_dict())
    for code, template in _ISSUES.items():
        issue = ArtifactPairIssue(
            code=code,
            component=template.component,
            field=template.field,
            observed_category=template.observed_category,
            impact=template.impact,
            next_action=template.next_action,
        )
        validator.validate(ArtifactPairReport(PairState.INVALID, None, (issue,)).to_dict())


def test_report_schema_rejects_reversed_primary_precedence() -> None:
    validator = Draft202012Validator(json.loads(REPORT_SCHEMA.read_bytes()))
    earlier = _closed_issue(ISSUE_PRECEDENCE[0]).to_dict()
    later = _closed_issue(ISSUE_PRECEDENCE[1]).to_dict()
    report = {
        "schema_version": "dbtobsb.artifact-pair-report.v1",
        "pair_state": "PAIR_INVALID",
        "summary": None,
        "issues": [later, earlier],
    }

    assert not validator.is_valid(report)


@pytest.mark.parametrize(
    "mutation",
    [
        "invented_status",
        "invented_code",
        "changed_text",
        "extra_status",
        "legacy_primary",
        "legacy_result_count",
    ],
)
def test_report_schema_rejects_loose_protocol_mutants(mutation: str) -> None:
    validator = Draft202012Validator(json.loads(REPORT_SCHEMA.read_bytes()))
    if mutation in {"invented_code", "changed_text"}:
        report = _json("invalid_invocation_mismatch", "expected-report.json")
        if mutation == "invented_code":
            report["issues"][0]["code"] = "DBT_INVENTED"
        else:
            report["issues"][0]["impact"] = "invented"
    else:
        report = _json("valid_success", "expected-report.json")
        if mutation == "invented_status":
            report["summary"]["status_counts"] = {"invented": 1}
        elif mutation == "extra_status":
            report["summary"]["status_counts"]["invented"] = 2
        elif mutation == "legacy_primary":
            report["primary_issue"] = None
        else:
            report["summary"]["result_count"] = 1

    assert not validator.is_valid(report)


@settings(max_examples=100, deadline=500)
@given(manifest=st.binary(max_size=512), run_results=st.binary(max_size=512))
def test_arbitrary_bounded_bytes_never_crash_or_escape_input(
    manifest: bytes, run_results: bytes
) -> None:
    first = inspect_artifact_pair(manifest=manifest, run_results=run_results)
    second = inspect_artifact_pair(manifest=manifest, run_results=run_results)

    assert first.state is PairState.INVALID
    assert len(first.issues) <= MAX_ISSUES
    assert first == second
    assert all(issue.code.startswith("DBT_") for issue in first.issues)
