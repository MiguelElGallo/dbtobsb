"""Bounded inspection of one Databricks dbt task artifact archive."""

from __future__ import annotations

import hashlib
import io
import tarfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from uuid import UUID

from dbtobsb_capture.contracts import ArtifactPairReport
from dbtobsb_capture.inspector import (
    MAX_PRIMARY_ARTIFACT_BYTES,
    SUPPORTED_ADAPTER_TYPE,
    SUPPORTED_DBT_VERSION,
    SUPPORTED_MANIFEST_SCHEMA,
    _is_offset_timestamp,
    _json_nesting_exceeds_limit,
    _manifest_schema_is_accepted,
    _mapping,
    _parse_json,
)
from dbtobsb_capture.projection import (
    ArtifactPairProjection,
    inspect_and_project_artifact_pair,
)

MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_EXPANDED_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 4096
MAX_ARCHIVE_PATH_BYTES = 1024
MANIFEST_PATH = "target/manifest.json"
RUN_RESULTS_PATH = "target/run_results.json"


class CaptureState(StrEnum):
    """Outcome of interpreting the retrieved archive evidence."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    NOT_PRODUCED = "NOT_PRODUCED"
    ARCHIVE_UNAVAILABLE = "ARCHIVE_UNAVAILABLE"
    INVALID_CAPTURE_CONTRACT = "INVALID_CAPTURE_CONTRACT"


@dataclass(frozen=True, slots=True)
class ArchiveCapture:
    """Evidence-safe archive result without raw bytes or signed URLs."""

    capture_state: CaptureState
    issue_code: str | None
    archive_sha256: str | None
    archive_size_bytes: int | None
    member_count: int
    manifest_sha256: str | None
    manifest_size_bytes: int | None
    run_results_sha256: str | None
    run_results_size_bytes: int | None
    pair_report: ArtifactPairReport | None
    projection: ArtifactPairProjection | None


def unavailable_archive_capture(*, issue_code: str) -> ArchiveCapture:
    """Classify a task whose archive could not be retrieved safely."""
    if not issue_code or not issue_code.isascii():
        raise ValueError("issue_code must be a nonempty ASCII code")
    return ArchiveCapture(
        capture_state=CaptureState.ARCHIVE_UNAVAILABLE,
        issue_code=issue_code,
        archive_sha256=None,
        archive_size_bytes=None,
        member_count=0,
        manifest_sha256=None,
        manifest_size_bytes=None,
        run_results_sha256=None,
        run_results_size_bytes=None,
        pair_report=None,
        projection=None,
    )


def _capture(
    *,
    state: CaptureState,
    issue_code: str | None,
    archive: bytes,
    member_count: int,
    manifest: bytes | None = None,
    run_results: bytes | None = None,
    pair_report: ArtifactPairReport | None = None,
    projection: ArtifactPairProjection | None = None,
) -> ArchiveCapture:
    return ArchiveCapture(
        capture_state=state,
        issue_code=issue_code,
        archive_sha256=hashlib.sha256(archive).hexdigest(),
        archive_size_bytes=len(archive),
        member_count=member_count,
        manifest_sha256=hashlib.sha256(manifest).hexdigest() if manifest is not None else None,
        manifest_size_bytes=len(manifest) if manifest is not None else None,
        run_results_sha256=(
            hashlib.sha256(run_results).hexdigest() if run_results is not None else None
        ),
        run_results_size_bytes=len(run_results) if run_results is not None else None,
        pair_report=pair_report,
        projection=projection,
    )


def _safe_member_name(name: str) -> bool:
    if not name or "\\" in name or len(name.encode("utf-8")) > MAX_ARCHIVE_PATH_BYTES:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _manifest_is_standalone_valid(raw: bytes) -> bool:
    if len(raw) > MAX_PRIMARY_ARTIFACT_BYTES or _json_nesting_exceeds_limit(raw):
        return False
    document, error = _parse_json(raw, component="manifest")
    if document is None or error is not None:
        return False
    try:
        if not _manifest_schema_is_accepted(document):
            return False
    except RecursionError:
        return False
    metadata = _mapping(document.get("metadata"))
    invocation = metadata.get("invocation_id")
    try:
        UUID(invocation) if isinstance(invocation, str) else (_ for _ in ()).throw(ValueError)
    except (ValueError, AttributeError):
        return False
    return (
        metadata.get("dbt_schema_version") == SUPPORTED_MANIFEST_SCHEMA
        and metadata.get("dbt_version") == SUPPORTED_DBT_VERSION
        and metadata.get("adapter_type") == SUPPORTED_ADAPTER_TYPE
        and _is_offset_timestamp(metadata.get("generated_at"))
    )


def inspect_dbt_output_archive(*, archive: bytes) -> ArchiveCapture:
    """Inspect a retrieved ``dbt-output.tar.gz`` without extracting to disk."""
    if not isinstance(archive, bytes):
        raise TypeError("archive must be bytes")
    if len(archive) > MAX_ARCHIVE_BYTES:
        return _capture(
            state=CaptureState.INVALID_CAPTURE_CONTRACT,
            issue_code="DBT_ARCHIVE_SIZE_LIMIT_EXCEEDED",
            archive=archive,
            member_count=0,
        )

    manifest: bytes | None = None
    run_results: bytes | None = None
    member_count = 0
    expanded_bytes = 0
    seen_member_names: set[str] = set()

    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r|gz") as stream:
            for member in stream:
                member_count += 1
                if member_count > MAX_ARCHIVE_MEMBERS:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_MEMBER_LIMIT_EXCEEDED",
                        archive=archive,
                        member_count=member_count,
                    )
                if not _safe_member_name(member.name):
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_PATH_UNSAFE",
                        archive=archive,
                        member_count=member_count,
                    )
                normalized_name = str(PurePosixPath(member.name))
                if normalized_name in seen_member_names:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_MEMBER_DUPLICATE",
                        archive=archive,
                        member_count=member_count,
                    )
                seen_member_names.add(normalized_name)
                if member.isdir():
                    continue
                if not member.isreg() or member.size < 0 or member.sparse is not None:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_MEMBER_TYPE_UNSAFE",
                        archive=archive,
                        member_count=member_count,
                    )
                expanded_bytes += member.size
                if expanded_bytes > MAX_ARCHIVE_EXPANDED_BYTES:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_EXPANDED_SIZE_LIMIT_EXCEEDED",
                        archive=archive,
                        member_count=member_count,
                    )

                basename = PurePosixPath(normalized_name).name
                if basename not in {"manifest.json", "run_results.json"}:
                    continue
                if member.name != normalized_name:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED",
                        archive=archive,
                        member_count=member_count,
                    )
                expected_path = MANIFEST_PATH if basename == "manifest.json" else RUN_RESULTS_PATH
                if normalized_name != expected_path:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED",
                        archive=archive,
                        member_count=member_count,
                    )
                if member.size > MAX_PRIMARY_ARTIFACT_BYTES:
                    code = (
                        "DBT_MANIFEST_SIZE_LIMIT_EXCEEDED"
                        if basename == "manifest.json"
                        else "DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED"
                    )
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code=code,
                        archive=archive,
                        member_count=member_count,
                    )
                source = stream.extractfile(member)
                if source is None:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_PRIMARY_UNREADABLE",
                        archive=archive,
                        member_count=member_count,
                    )
                raw = source.read(MAX_PRIMARY_ARTIFACT_BYTES + 1)
                if len(raw) != member.size:
                    return _capture(
                        state=CaptureState.INVALID_CAPTURE_CONTRACT,
                        issue_code="DBT_ARCHIVE_PRIMARY_TRUNCATED",
                        archive=archive,
                        member_count=member_count,
                    )
                if basename == "manifest.json":
                    if manifest is not None:
                        return _capture(
                            state=CaptureState.INVALID_CAPTURE_CONTRACT,
                            issue_code="DBT_ARCHIVE_MANIFEST_DUPLICATE",
                            archive=archive,
                            member_count=member_count,
                        )
                    manifest = raw
                else:
                    if run_results is not None:
                        return _capture(
                            state=CaptureState.INVALID_CAPTURE_CONTRACT,
                            issue_code="DBT_ARCHIVE_RUN_RESULTS_DUPLICATE",
                            archive=archive,
                            member_count=member_count,
                        )
                    run_results = raw
    except (tarfile.TarError, EOFError, OSError):
        return _capture(
            state=CaptureState.INVALID_CAPTURE_CONTRACT,
            issue_code="DBT_ARCHIVE_INVALID",
            archive=archive,
            member_count=member_count,
        )

    if manifest is None and run_results is None:
        return _capture(
            state=CaptureState.NOT_PRODUCED,
            issue_code="DBT_PRIMARY_ARTIFACTS_NOT_PRODUCED",
            archive=archive,
            member_count=member_count,
        )
    if manifest is None:
        return _capture(
            state=CaptureState.INVALID_CAPTURE_CONTRACT,
            issue_code="DBT_RUN_RESULTS_WITHOUT_MANIFEST",
            archive=archive,
            member_count=member_count,
            run_results=run_results,
        )
    if run_results is None:
        manifest_valid = _manifest_is_standalone_valid(manifest)
        return _capture(
            state=(
                CaptureState.PARTIAL if manifest_valid else CaptureState.INVALID_CAPTURE_CONTRACT
            ),
            issue_code=(
                "DBT_RUN_RESULTS_NOT_PRODUCED"
                if manifest_valid
                else "DBT_MANIFEST_STANDALONE_INVALID"
            ),
            archive=archive,
            member_count=member_count,
            manifest=manifest,
        )

    inspection = inspect_and_project_artifact_pair(manifest=manifest, run_results=run_results)
    if inspection.projection is None:
        primary = inspection.report.primary_issue
        return _capture(
            state=CaptureState.INVALID_CAPTURE_CONTRACT,
            issue_code=primary.code if primary is not None else "DBT_ARTIFACT_PAIR_INVALID",
            archive=archive,
            member_count=member_count,
            manifest=manifest,
            run_results=run_results,
            pair_report=inspection.report,
        )
    return _capture(
        state=CaptureState.COMPLETE,
        issue_code=None,
        archive=archive,
        member_count=member_count,
        manifest=manifest,
        run_results=run_results,
        pair_report=inspection.report,
        projection=inspection.projection,
    )
