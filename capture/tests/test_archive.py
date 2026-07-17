"""Archive and restricted-projection contract tests."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from dataclasses import replace
from pathlib import Path

import pytest
from dbtobsb_contracts import (
    AttemptIdentity,
    demo_installed_policy,
    expected_dbt_output,
    load_support_manifest,
)

from dbtobsb_capture import (
    CaptureState,
    StructuredLogState,
    inspect_dbt_output_archive,
    unavailable_archive_capture,
)
from dbtobsb_capture import inspector as inspector_module

FIXTURES = Path(__file__).parent / "fixtures" / "artifact_pair"
FIXTURE_MACRO_ID = "macro.dbtobsb_capture_fixture.fixture_macro"
DBT_FUNCTION_MACRO_ID = "macro.dbt.materialization_function_default"


def _fixture(name: str) -> bytes:
    return (FIXTURES / "valid_success" / name).read_bytes()


def _databricks_manifest() -> bytes:
    manifest = json.loads(_fixture("manifest.json"))
    macro = manifest["macros"].pop(FIXTURE_MACRO_ID)
    macro["unique_id"] = DBT_FUNCTION_MACRO_ID
    macro["package_name"] = "dbt"
    macro["name"] = "materialization_function_default"
    macro["supported_languages"] = ["sql", "python", "javascript"]
    manifest["macros"][DBT_FUNCTION_MACRO_ID] = macro
    return (json.dumps(manifest, ensure_ascii=True, sort_keys=True) + "\n").encode()


def _tar(entries: list[tuple[str, bytes]], *, symlink: str | None = None) -> bytes:
    destination = io.BytesIO()
    with tarfile.open(fileobj=destination, mode="w:gz") as archive:
        for name, value in entries:
            member = tarfile.TarInfo(name)
            member.size = len(value)
            archive.addfile(member, io.BytesIO(value))
        if symlink is not None:
            member = tarfile.TarInfo(symlink)
            member.type = tarfile.SYMTYPE
            member.linkname = "manifest.json"
            archive.addfile(member)
    return destination.getvalue()


ARTIFACT_INVOCATION_ID = "11111111-1111-4111-8111-111111111111"


def _expectation(*, include_deps: bool = False):
    return expected_dbt_output(
        attempt=AttemptIdentity(101, 201, 301, 401, 0, 1),
        policy=replace(demo_installed_policy(), include_deps=include_deps),
    )


def _structured_event(
    *,
    name: str,
    invocation_id: str = ARTIFACT_INVOCATION_ID,
    data: dict[str, object] | None = None,
) -> bytes:
    event = {
        "data": data or {},
        "info": {"invocation_id": invocation_id, "name": name},
    }
    return (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _structured_log(version: int = 3, *, invocation_id: str = ARTIFACT_INVOCATION_ID) -> bytes:
    return _structured_event(
        name="MainReportVersion",
        invocation_id=invocation_id,
        data={"log_version": version},
    )


def _ordinal_log(capture, ordinal: str):
    return next(item for item in capture.structured_logs if item.ordinal == ordinal)


def test_valid_archive_is_complete_and_projects_only_allowlisted_fields() -> None:
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                ("target/manifest.json", _fixture("manifest.json")),
                ("target/run_results.json", _fixture("run_results.json")),
                ("target/compiled/private.sql", b"select 'do not project'"),
            ]
        )
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.issue_code is None
    assert capture.archive_sha256 is not None
    assert capture.manifest_sha256 is not None
    assert capture.run_results_sha256 is not None
    assert capture.pair_report is not None
    assert capture.projection is not None
    assert capture.projection.invocation.command == "build"
    assert capture.projection.invocation.result_count > 0
    assert capture.projection.node_results
    assert all(node.unique_id for node in capture.projection.node_results)
    assert "do not project" not in repr(capture)


def test_resolved_v1_nested_paths_are_accepted_only_for_the_exact_attempt() -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.structured_log_state is StructuredLogState.MISSING
    assert capture.structured_log_file_count == 0

    wrong_attempt = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member.replace("-e1/", "-e2/"), _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
            ]
        ),
        expectation=expectation,
    )
    assert wrong_attempt.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert wrong_attempt.issue_code == "DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED"


def test_exact_structured_log_is_classified_without_changing_artifact_success() -> None:
    expectation = _expectation()
    raw_log = _structured_log() + _structured_event(
        name="NodeStart", data={"message": "TOP_SECRET_LOG_CANARY"}
    )
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                (expectation.log_member, raw_log),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.structured_log_state is StructuredLogState.VALID
    assert capture.structured_log_sha256 == hashlib.sha256(raw_log).hexdigest()
    assert capture.structured_log_size_bytes == len(raw_log)
    assert capture.structured_log_file_count == 1
    assert capture.structured_log_version == 3
    assert "TOP_SECRET_LOG_CANARY" not in repr(capture)


@pytest.mark.parametrize(
    ("raw_log", "state"),
    [
        (b"", StructuredLogState.NOT_INITIALIZED),
        (b"not-json\n", StructuredLogState.MALFORMED),
        (_structured_event(name="NodeStart"), StructuredLogState.MISSING),
        (_structured_log(version=2), StructuredLogState.UNKNOWN_VERSION),
    ],
)
def test_structured_log_failures_are_separate_from_artifact_pair(
    raw_log: bytes, state: StructuredLogState
) -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                (expectation.log_member, raw_log),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.structured_log_state is state


def test_structured_log_wrong_attempt_path_fails_closed() -> None:
    expectation = _expectation()
    wrong_path = expectation.log_member.replace("-e1/", "-e2/")
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                (wrong_path, _structured_log()),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert capture.issue_code == "DBT_ARCHIVE_LOG_PATH_UNEXPECTED"


def test_structured_log_duplicate_fails_closed() -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.log_member, _structured_log()),
                (expectation.log_member, _structured_log()),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert capture.issue_code == "DBT_ARCHIVE_MEMBER_DUPLICATE"


def test_archive_unavailable_is_not_reported_as_confirmed_log_missing() -> None:
    expectation = _expectation(include_deps=True)
    capture = unavailable_archive_capture(
        issue_code="DBT_ARCHIVE_LINK_UNAVAILABLE",
        expectation=expectation,
    )

    assert capture.include_deps is True
    assert [item.state for item in capture.structured_logs] == [
        StructuredLogState.UNAVAILABLE,
        StructuredLogState.UNAVAILABLE,
    ]
    assert capture.structured_log_state is StructuredLogState.UNAVAILABLE


def test_deps_and_build_logs_are_classified_independently() -> None:
    expectation = _expectation(include_deps=True)
    assert expectation.deps_log_member is not None
    deps_invocation = "22222222-2222-4222-8222-222222222222"
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                (
                    f"{expectation.deps_log_member}.1",
                    _structured_log(invocation_id=deps_invocation),
                ),
                (
                    expectation.deps_log_member,
                    _structured_event(name="CommandCompleted", invocation_id=deps_invocation),
                ),
                (expectation.log_member, b"not-json\n"),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert _ordinal_log(capture, "000-deps").state is StructuredLogState.VALID
    assert _ordinal_log(capture, "000-deps").file_count == 2
    assert _ordinal_log(capture, "001-build").state is StructuredLogState.MALFORMED


def test_rotations_are_reconstructed_oldest_to_newest() -> None:
    expectation = _expectation()
    oldest = _structured_log()
    middle = _structured_event(name="NodeStart")
    newest = _structured_event(name="CommandCompleted")
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                (expectation.log_member, newest),
                (f"{expectation.log_member}.2", oldest),
                (f"{expectation.log_member}.1", middle),
            ]
        ),
        expectation=expectation,
    )

    build_log = _ordinal_log(capture, "001-build")
    assert build_log.state is StructuredLogState.VALID
    assert build_log.file_count == 3
    assert build_log.size_bytes == len(oldest) + len(middle) + len(newest)
    assert build_log.sha256 == hashlib.sha256(oldest + middle + newest).hexdigest()


def test_active_log_plus_all_five_rotations_is_the_exact_file_count_limit() -> None:
    expectation = _expectation()
    entries = [
        (expectation.manifest_member, _fixture("manifest.json")),
        (expectation.run_results_member, _fixture("run_results.json")),
        (f"{expectation.log_member}.5", _structured_log()),
    ]
    entries.extend(
        (
            expectation.log_member if rotation == 0 else f"{expectation.log_member}.{rotation}",
            _structured_event(name=f"Event{rotation}"),
        )
        for rotation in range(4, -1, -1)
    )
    capture = inspect_dbt_output_archive(
        archive=_tar(entries),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.structured_log_state is StructuredLogState.VALID
    assert capture.structured_log_file_count == 6


@pytest.mark.parametrize(
    "members",
    [
        (".1",),
        ("", ".2"),
        ("", ".1", ".3"),
    ],
)
def test_missing_active_log_or_rotation_gap_is_truncated(
    members: tuple[str, ...],
) -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                *[
                    (
                        f"{expectation.log_member}{suffix}",
                        _structured_event(name=f"Event{suffix or 'active'}"),
                    )
                    for suffix in members
                ],
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.structured_log_state is StructuredLogState.TRUNCATED


def test_full_rotation_set_without_main_report_is_truncated_even_when_files_are_small() -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                *[
                    (
                        expectation.log_member
                        if rotation == 0
                        else f"{expectation.log_member}.{rotation}",
                        _structured_event(name=f"Event{rotation}"),
                    )
                    for rotation in range(5, -1, -1)
                ],
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.structured_log_state is StructuredLogState.TRUNCATED
    assert capture.structured_log_file_count == 6


@pytest.mark.parametrize("suffix", [".6", ".bak", ".1.extra"])
def test_only_the_active_log_and_five_exact_rotations_are_allowed(suffix: str) -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar([(f"{expectation.log_member}{suffix}", _structured_log())]),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert capture.issue_code == "DBT_ARCHIVE_LOG_PATH_UNEXPECTED"
    assert capture.structured_log_state is StructuredLogState.UNAVAILABLE


def test_a_log_file_above_the_manifest_limit_is_truncated_not_parsed() -> None:
    expectation = _expectation()
    file_limit = int(load_support_manifest().governed_output["file_log_max_bytes"])
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                (expectation.log_member, b"x" * (file_limit + 1)),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.structured_log_state is StructuredLogState.TRUNCATED
    assert capture.structured_log_sha256 is None
    assert capture.structured_log_size_bytes == file_limit + 1
    assert capture.structured_log_file_count == 1


def test_build_log_invocation_mismatch_is_distinct_and_does_not_invalidate_pair() -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (expectation.run_results_member, _fixture("run_results.json")),
                (
                    expectation.log_member,
                    _structured_log(invocation_id="33333333-3333-4333-8333-333333333333"),
                ),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.COMPLETE
    assert capture.projection is not None
    assert capture.structured_log_state is StructuredLogState.ARTIFACT_INVOCATION_MISMATCH


@pytest.mark.parametrize(
    "raw_log",
    [
        _structured_log() + _structured_log(),
        _structured_log()
        + _structured_event(
            name="NodeStart",
            invocation_id="44444444-4444-4444-8444-444444444444",
        ),
        (
            b'{"data":{"nested":'
            + (b"[" * 300)
            + b"0"
            + (b"]" * 300)
            + b'},"info":{"invocation_id":"11111111-1111-4111-8111-111111111111",'
            + b'"name":"MainReportVersion"}}\n'
        ),
    ],
)
def test_duplicate_conflicting_or_deep_json_is_malformed_without_raising(
    raw_log: bytes,
) -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar([(expectation.log_member, raw_log)]),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.NOT_PRODUCED
    assert capture.structured_log_state is StructuredLogState.MALFORMED


def test_support_manifest_schema_digests_match_packaged_schema_bytes() -> None:
    manifest = load_support_manifest()
    schema_root = Path(inspector_module.__file__).parent / "schemas"

    assert (
        hashlib.sha256((schema_root / "manifest-v12.json").read_bytes()).hexdigest()
        == (manifest.dbt["manifest_schema_sha256"])
    )
    assert (
        hashlib.sha256((schema_root / "run-results-v6.json").read_bytes()).hexdigest()
        == (manifest.dbt["run_results_schema_sha256"])
    )


def test_valid_manifest_without_run_results_is_partial() -> None:
    capture = inspect_dbt_output_archive(
        archive=_tar([("target/manifest.json", _fixture("manifest.json"))])
    )

    assert capture.capture_state is CaptureState.PARTIAL
    assert capture.issue_code == "DBT_RUN_RESULTS_NOT_PRODUCED"
    assert capture.projection is None


def test_manifest_only_build_log_is_bound_to_manifest_invocation() -> None:
    expectation = _expectation()
    capture = inspect_dbt_output_archive(
        archive=_tar(
            [
                (expectation.manifest_member, _fixture("manifest.json")),
                (
                    expectation.log_member,
                    _structured_log(invocation_id="33333333-3333-4333-8333-333333333333"),
                ),
            ]
        ),
        expectation=expectation,
    )

    assert capture.capture_state is CaptureState.PARTIAL
    assert capture.issue_code == "DBT_RUN_RESULTS_NOT_PRODUCED"
    assert capture.structured_log_state is StructuredLogState.ARTIFACT_INVOCATION_MISMATCH


def test_qualified_databricks_manifest_without_run_results_is_partial() -> None:
    capture = inspect_dbt_output_archive(
        archive=_tar([("target/manifest.json", _databricks_manifest())])
    )

    assert capture.capture_state is CaptureState.PARTIAL
    assert capture.issue_code == "DBT_RUN_RESULTS_NOT_PRODUCED"
    assert capture.projection is None


def test_manifest_only_capture_rejects_an_invalid_generated_timestamp() -> None:
    manifest = json.loads(_fixture("manifest.json"))
    manifest["metadata"]["generated_at"] = "not-a-timestamp"
    raw = (json.dumps(manifest, ensure_ascii=True, sort_keys=True) + "\n").encode()

    capture = inspect_dbt_output_archive(archive=_tar([("target/manifest.json", raw)]))

    assert capture.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert capture.issue_code == "DBT_MANIFEST_STANDALONE_INVALID"


def test_run_results_without_manifest_is_invalid() -> None:
    capture = inspect_dbt_output_archive(
        archive=_tar([("target/run_results.json", _fixture("run_results.json"))])
    )

    assert capture.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert capture.issue_code == "DBT_RUN_RESULTS_WITHOUT_MANIFEST"
    assert capture.projection is None


def test_archive_without_primary_artifacts_is_not_produced() -> None:
    capture = inspect_dbt_output_archive(archive=_tar([("target/catalog.json", b"{}")]))

    assert capture.capture_state is CaptureState.NOT_PRODUCED
    assert capture.issue_code == "DBT_PRIMARY_ARTIFACTS_NOT_PRODUCED"


@pytest.mark.parametrize(
    ("entries", "symlink", "issue_code"),
    [
        (
            [
                ("target/manifest.json", _fixture("manifest.json")),
                ("copy/manifest.json", _fixture("manifest.json")),
            ],
            None,
            "DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED",
        ),
        (
            [("target/./manifest.json", _fixture("manifest.json"))],
            None,
            "DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED",
        ),
        (
            [("target//manifest.json", _fixture("manifest.json"))],
            None,
            "DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED",
        ),
        ([("../manifest.json", _fixture("manifest.json"))], None, "DBT_ARCHIVE_PATH_UNSAFE"),
        (
            [("target/catalog.json", b"{}"), ("target/./catalog.json", b"{}")],
            None,
            "DBT_ARCHIVE_MEMBER_DUPLICATE",
        ),
        ([], "target/manifest-link.json", "DBT_ARCHIVE_MEMBER_TYPE_UNSAFE"),
    ],
)
def test_unsafe_or_ambiguous_archive_fails_closed(
    entries: list[tuple[str, bytes]], symlink: str | None, issue_code: str
) -> None:
    capture = inspect_dbt_output_archive(archive=_tar(entries, symlink=symlink))

    assert capture.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert capture.issue_code == issue_code
    assert capture.projection is None


def test_malformed_archive_fails_closed_without_evidence_text() -> None:
    capture = inspect_dbt_output_archive(archive=b"not a tar archive")

    assert capture.capture_state is CaptureState.INVALID_CAPTURE_CONTRACT
    assert capture.issue_code == "DBT_ARCHIVE_INVALID"
    assert "not a tar archive" not in repr(capture)
