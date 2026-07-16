"""Bounded inspection of one Databricks dbt task artifact archive."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any
from uuid import UUID

from dbtobsb_contracts import DbtOutputExpectation, load_support_manifest

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


class StructuredLogState(StrEnum):
    """Bounded structural classification of one command ordinal's closed logs."""

    UNAVAILABLE = "UNAVAILABLE"
    NOT_INITIALIZED = "NOT_INITIALIZED"
    TRUNCATED = "TRUNCATED"
    MALFORMED = "MALFORMED"
    MISSING = "MISSING"
    UNKNOWN_VERSION = "UNKNOWN_VERSION"
    ARTIFACT_INVOCATION_MISMATCH = "ARTIFACT_INVOCATION_MISMATCH"
    VALID = "VALID"


@dataclass(frozen=True, slots=True)
class StructuredLogCapture:
    """Safe deterministic metadata for one reconstructed ordinal log set."""

    ordinal: str
    state: StructuredLogState
    sha256: str | None
    size_bytes: int | None
    file_count: int
    log_version: int | None


@dataclass(frozen=True, slots=True)
class _ClosedLogFile:
    """One bounded closed log member held only during archive inspection."""

    rotation: int
    raw: bytes | None
    declared_size: int


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
    include_deps: bool
    structured_logs: tuple[StructuredLogCapture, ...]
    pair_report: ArtifactPairReport | None
    projection: ArtifactPairProjection | None

    @property
    def structured_log_state(self) -> StructuredLogState:
        """Return the primary build log state for compatibility with v0 callers."""
        return self.structured_logs[-1].state

    @property
    def structured_log_sha256(self) -> str | None:
        """Return the reconstructed primary build log hash."""
        return self.structured_logs[-1].sha256

    @property
    def structured_log_size_bytes(self) -> int | None:
        """Return the reconstructed primary build log byte count."""
        return self.structured_logs[-1].size_bytes

    @property
    def structured_log_file_count(self) -> int:
        """Return the primary build log member count."""
        return self.structured_logs[-1].file_count

    @property
    def structured_log_version(self) -> int | None:
        """Return the primary build log version when exactly one was parsed."""
        return self.structured_logs[-1].log_version


def _reject_duplicate_log_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _reject_log_constant(_: str) -> None:
    raise ValueError


def _expected_log_bases(
    expectation: DbtOutputExpectation | None,
) -> tuple[tuple[str, str | None], ...]:
    if expectation is not None:
        return expectation.ordinal_log_members
    manifest = load_support_manifest()
    return ((str(manifest.dbt["build_ordinal"]), None),)


def _unavailable_log_captures(
    expectation: DbtOutputExpectation | None,
) -> tuple[StructuredLogCapture, ...]:
    return tuple(
        StructuredLogCapture(
            ordinal=ordinal,
            state=StructuredLogState.UNAVAILABLE,
            sha256=None,
            size_bytes=None,
            file_count=0,
            log_version=None,
        )
        for ordinal, _ in _expected_log_bases(expectation)
    )


def _normalized_invocation_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        return None


def _jsonl_lines(raw: bytes) -> tuple[bytes, ...] | None:
    if not raw:
        return ()
    lines = raw.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    if not lines or any(not line for line in lines):
        return None
    return tuple(lines)


def _classify_structured_log(
    *,
    ordinal: str,
    files: tuple[_ClosedLogFile, ...],
    artifact_invocation_id: str | None,
) -> StructuredLogCapture:
    manifest = load_support_manifest()
    max_file_bytes = int(manifest.governed_output["file_log_max_bytes"])
    max_files = int(manifest.governed_output["file_log_max_files"])
    max_total_bytes = int(manifest.governed_output["file_log_total_max_bytes"])
    expected_version = manifest.dbt["structured_log_version"]
    if not isinstance(expected_version, int) or isinstance(expected_version, bool):
        raise RuntimeError("DBTOBSB_SUPPORT_MANIFEST_LOG_VERSION_INVALID")

    if not files:
        return StructuredLogCapture(
            ordinal=ordinal,
            state=StructuredLogState.MISSING,
            sha256=None,
            size_bytes=None,
            file_count=0,
            log_version=None,
        )

    ordered = tuple(sorted(files, key=lambda item: item.rotation, reverse=True))
    file_count = len(ordered)
    size_bytes = sum(item.declared_size for item in ordered)
    complete = all(item.raw is not None and len(item.raw) == item.declared_size for item in ordered)
    reconstructed = b"".join(item.raw for item in ordered if item.raw is not None)
    digest = hashlib.sha256(reconstructed).hexdigest() if complete else None
    if (
        file_count > max_files
        or size_bytes > max_total_bytes
        or any(item.declared_size > max_file_bytes for item in ordered)
        or not complete
    ):
        return StructuredLogCapture(
            ordinal=ordinal,
            state=StructuredLogState.TRUNCATED,
            sha256=digest,
            size_bytes=size_bytes,
            file_count=file_count,
            log_version=None,
        )
    rotations = {item.rotation for item in ordered}
    max_rotation = max(rotations)
    if 0 not in rotations or rotations != set(range(max_rotation + 1)):
        return StructuredLogCapture(
            ordinal=ordinal,
            state=StructuredLogState.TRUNCATED,
            sha256=digest,
            size_bytes=size_bytes,
            file_count=file_count,
            log_version=None,
        )
    if not reconstructed:
        return StructuredLogCapture(
            ordinal=ordinal,
            state=StructuredLogState.NOT_INITIALIZED,
            sha256=digest,
            size_bytes=0,
            file_count=file_count,
            log_version=None,
        )

    invocation_ids: set[str] = set()
    main_report_count = 0
    main_report_version: int | None = None
    malformed = False
    for item in ordered:
        if item.raw is None:
            malformed = True
            break
        lines = _jsonl_lines(item.raw)
        if lines is None:
            malformed = True
            break
        for line in lines:
            if _json_nesting_exceeds_limit(line):
                malformed = True
                break
            try:
                event: Any = json.loads(
                    line,
                    object_pairs_hook=_reject_duplicate_log_keys,
                    parse_constant=_reject_log_constant,
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
                RecursionError,
                ValueError,
            ):
                malformed = True
                break
            if not isinstance(event, dict):
                malformed = True
                break
            info = event.get("info")
            data = event.get("data")
            if not isinstance(info, dict) or not isinstance(data, dict):
                malformed = True
                break
            name = info.get("name")
            invocation_id = _normalized_invocation_id(info.get("invocation_id"))
            if not isinstance(name, str) or not name or invocation_id is None:
                malformed = True
                break
            invocation_ids.add(invocation_id)
            if name == "MainReportVersion":
                main_report_count += 1
                version = data.get("log_version")
                if not isinstance(version, int) or isinstance(version, bool):
                    malformed = True
                    break
                main_report_version = version
        if malformed:
            break

    if malformed or len(invocation_ids) != 1 or main_report_count > 1:
        state = StructuredLogState.MALFORMED
        main_report_version = None
    elif main_report_count == 0:
        saturated_rotation = file_count == max_files and max_rotation == max_files - 1
        state = StructuredLogState.TRUNCATED if saturated_rotation else StructuredLogState.MISSING
    elif main_report_version != expected_version:
        state = StructuredLogState.UNKNOWN_VERSION
    else:
        parsed_invocation_id = next(iter(invocation_ids))
        state = (
            StructuredLogState.ARTIFACT_INVOCATION_MISMATCH
            if artifact_invocation_id is not None
            and parsed_invocation_id != _normalized_invocation_id(artifact_invocation_id)
            else StructuredLogState.VALID
        )
    return StructuredLogCapture(
        ordinal=ordinal,
        state=state,
        sha256=digest,
        size_bytes=size_bytes,
        file_count=file_count,
        log_version=main_report_version,
    )


def unavailable_archive_capture(
    *, issue_code: str, expectation: DbtOutputExpectation | None = None
) -> ArchiveCapture:
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
        include_deps=expectation.include_deps if expectation is not None else False,
        structured_logs=_unavailable_log_captures(expectation),
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
    expectation: DbtOutputExpectation | None = None,
    structured_logs: tuple[StructuredLogCapture, ...] | None = None,
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
        include_deps=expectation.include_deps if expectation is not None else False,
        structured_logs=(
            structured_logs
            if structured_logs is not None
            else _unavailable_log_captures(expectation)
        ),
        pair_report=pair_report,
        projection=projection,
    )


def _safe_member_name(name: str) -> bool:
    if not name or "\\" in name or len(name.encode("utf-8")) > MAX_ARCHIVE_PATH_BYTES:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _manifest_standalone_invocation_id(raw: bytes) -> str | None:
    if len(raw) > MAX_PRIMARY_ARTIFACT_BYTES or _json_nesting_exceeds_limit(raw):
        return None
    document, error = _parse_json(raw, component="manifest")
    if document is None or error is not None:
        return None
    try:
        if not _manifest_schema_is_accepted(document):
            return None
    except RecursionError:
        return None
    metadata = _mapping(document.get("metadata"))
    invocation = metadata.get("invocation_id")
    try:
        UUID(invocation) if isinstance(invocation, str) else (_ for _ in ()).throw(ValueError)
    except (ValueError, AttributeError):
        return None
    valid = (
        metadata.get("dbt_schema_version") == SUPPORTED_MANIFEST_SCHEMA
        and metadata.get("dbt_version") == SUPPORTED_DBT_VERSION
        and metadata.get("adapter_type") == SUPPORTED_ADAPTER_TYPE
        and _is_offset_timestamp(metadata.get("generated_at"))
    )
    return _normalized_invocation_id(invocation) if valid else None


def inspect_dbt_output_archive(
    *, archive: bytes, expectation: DbtOutputExpectation | None = None
) -> ArchiveCapture:
    """Inspect a retrieved ``dbt-output.tar.gz`` without extracting to disk."""
    if not isinstance(archive, bytes):
        raise TypeError("archive must be bytes")
    if len(archive) > MAX_ARCHIVE_BYTES:
        return _capture(
            state=CaptureState.INVALID_CAPTURE_CONTRACT,
            issue_code="DBT_ARCHIVE_SIZE_LIMIT_EXCEEDED",
            archive=archive,
            member_count=0,
            expectation=expectation,
        )

    manifest: bytes | None = None
    run_results: bytes | None = None
    log_files: dict[str, list[_ClosedLogFile]] = {
        ordinal: [] for ordinal, _ in _expected_log_bases(expectation)
    }
    allowed_log_paths: dict[str, tuple[str, int]] = {}
    if expectation is not None:
        max_files = int(load_support_manifest().governed_output["file_log_max_files"])
        for ordinal, base in expectation.ordinal_log_members:
            allowed_log_paths[base] = (ordinal, 0)
            for rotation in range(1, max_files):
                allowed_log_paths[f"{base}.{rotation}"] = (ordinal, rotation)
    member_count = 0
    expanded_bytes = 0
    seen_member_names: set[str] = set()

    def invalid(code: str) -> ArchiveCapture:
        return _capture(
            state=CaptureState.INVALID_CAPTURE_CONTRACT,
            issue_code=code,
            archive=archive,
            member_count=member_count,
            expectation=expectation,
        )

    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r|gz") as stream:
            for member in stream:
                member_count += 1
                if member_count > MAX_ARCHIVE_MEMBERS:
                    return invalid("DBT_ARCHIVE_MEMBER_LIMIT_EXCEEDED")
                if not _safe_member_name(member.name):
                    return invalid("DBT_ARCHIVE_PATH_UNSAFE")
                normalized_name = str(PurePosixPath(member.name))
                if normalized_name in seen_member_names:
                    return invalid("DBT_ARCHIVE_MEMBER_DUPLICATE")
                seen_member_names.add(normalized_name)
                basename = PurePosixPath(normalized_name).name
                log_spec = allowed_log_paths.get(normalized_name)
                if expectation is not None and basename.startswith("dbt.log") and log_spec is None:
                    return invalid("DBT_ARCHIVE_LOG_PATH_UNEXPECTED")
                if member.isdir():
                    if log_spec is not None:
                        return invalid("DBT_ARCHIVE_MEMBER_TYPE_UNSAFE")
                    continue
                if not member.isreg() or member.size < 0 or member.sparse is not None:
                    return invalid("DBT_ARCHIVE_MEMBER_TYPE_UNSAFE")
                expanded_bytes += member.size
                if expanded_bytes > MAX_ARCHIVE_EXPANDED_BYTES:
                    return invalid("DBT_ARCHIVE_EXPANDED_SIZE_LIMIT_EXCEEDED")

                if log_spec is not None:
                    ordinal, rotation = log_spec
                    max_file_bytes = int(
                        load_support_manifest().governed_output["file_log_max_bytes"]
                    )
                    raw_log: bytes | None = None
                    if member.size <= max_file_bytes:
                        source = stream.extractfile(member)
                        if source is not None:
                            candidate = source.read(max_file_bytes + 1)
                            if len(candidate) == member.size:
                                raw_log = candidate
                    log_files[ordinal].append(
                        _ClosedLogFile(
                            rotation=rotation,
                            raw=raw_log,
                            declared_size=member.size,
                        )
                    )
                    continue
                if basename not in {"manifest.json", "run_results.json"}:
                    continue
                if member.name != normalized_name:
                    return invalid("DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED")
                expected_path = (
                    expectation.manifest_member
                    if expectation is not None and basename == "manifest.json"
                    else expectation.run_results_member
                    if expectation is not None
                    else MANIFEST_PATH
                    if basename == "manifest.json"
                    else RUN_RESULTS_PATH
                )
                if normalized_name != expected_path:
                    return invalid("DBT_ARCHIVE_PRIMARY_PATH_UNEXPECTED")
                if member.size > MAX_PRIMARY_ARTIFACT_BYTES:
                    code = (
                        "DBT_MANIFEST_SIZE_LIMIT_EXCEEDED"
                        if basename == "manifest.json"
                        else "DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED"
                    )
                    return invalid(code)
                source = stream.extractfile(member)
                if source is None:
                    return invalid("DBT_ARCHIVE_PRIMARY_UNREADABLE")
                raw = source.read(MAX_PRIMARY_ARTIFACT_BYTES + 1)
                if len(raw) != member.size:
                    return invalid("DBT_ARCHIVE_PRIMARY_TRUNCATED")
                if basename == "manifest.json":
                    if manifest is not None:
                        return invalid("DBT_ARCHIVE_MANIFEST_DUPLICATE")
                    manifest = raw
                else:
                    if run_results is not None:
                        return invalid("DBT_ARCHIVE_RUN_RESULTS_DUPLICATE")
                    run_results = raw
    except (tarfile.TarError, EOFError, OSError):
        return invalid("DBT_ARCHIVE_INVALID")

    def classified_logs(
        artifact_invocation_id: str | None = None,
    ) -> tuple[StructuredLogCapture, ...]:
        build_ordinal = str(load_support_manifest().dbt["build_ordinal"])
        return tuple(
            _classify_structured_log(
                ordinal=ordinal,
                files=tuple(log_files[ordinal]),
                artifact_invocation_id=(
                    artifact_invocation_id if ordinal == build_ordinal else None
                ),
            )
            for ordinal, _ in _expected_log_bases(expectation)
        )

    if manifest is None and run_results is None:
        return _capture(
            state=CaptureState.NOT_PRODUCED,
            issue_code="DBT_PRIMARY_ARTIFACTS_NOT_PRODUCED",
            archive=archive,
            member_count=member_count,
            expectation=expectation,
            structured_logs=classified_logs(),
        )
    if manifest is None:
        return _capture(
            state=CaptureState.INVALID_CAPTURE_CONTRACT,
            issue_code="DBT_RUN_RESULTS_WITHOUT_MANIFEST",
            archive=archive,
            member_count=member_count,
            run_results=run_results,
            expectation=expectation,
            structured_logs=classified_logs(),
        )
    if run_results is None:
        manifest_invocation_id = _manifest_standalone_invocation_id(manifest)
        manifest_valid = manifest_invocation_id is not None
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
            expectation=expectation,
            structured_logs=classified_logs(manifest_invocation_id),
        )

    inspection = inspect_and_project_artifact_pair(
        manifest=manifest,
        run_results=run_results,
        expected_selector=(
            expectation.approved_selector if expectation is not None else "observability_demo"
        ),
    )
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
            expectation=expectation,
            structured_logs=classified_logs(),
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
        expectation=expectation,
        structured_logs=classified_logs(inspection.projection.invocation.invocation_id),
    )
