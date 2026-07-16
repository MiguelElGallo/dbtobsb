"""Archive and restricted-projection contract tests."""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from dbtobsb_capture import CaptureState, inspect_dbt_output_archive

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


def test_valid_manifest_without_run_results_is_partial() -> None:
    capture = inspect_dbt_output_archive(
        archive=_tar([("target/manifest.json", _fixture("manifest.json"))])
    )

    assert capture.capture_state is CaptureState.PARTIAL
    assert capture.issue_code == "DBT_RUN_RESULTS_NOT_PRODUCED"
    assert capture.projection is None


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
