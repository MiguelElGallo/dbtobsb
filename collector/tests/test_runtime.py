"""Collector orchestration and raw-custody tests."""

from __future__ import annotations

import io
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from dbtobsb_capture import CaptureState

from dbtobsb_collector import (
    ArtifactReference,
    AttemptContext,
    CollectionRecord,
    ObservedTaskEvidence,
    RetrievalState,
    collect_task_run,
)
from dbtobsb_collector.custody import VolumeRawArchiveStore
from dbtobsb_collector.download import ArtifactDownloadError

FIXTURES = Path(__file__).parents[2] / "capture" / "tests" / "fixtures" / "artifact_pair"


def _archive() -> bytes:
    destination = io.BytesIO()
    with tarfile.open(fileobj=destination, mode="w:gz") as archive:
        for name in ("manifest.json", "run_results.json"):
            value = (FIXTURES / "valid_success" / name).read_bytes()
            member = tarfile.TarInfo(f"target/{name}")
            member.size = len(value)
            archive.addfile(member, io.BytesIO(value))
    return destination.getvalue()


def _context() -> AttemptContext:
    return AttemptContext(
        workspace_id=101,
        observed_job_id=201,
        observed_job_run_id=301,
        dbt_task_run_id=401,
        observed_task_key="dbt_build",
        repair_count=0,
        execution_count=1,
    )


def _observed(reference: ArtifactReference | None) -> ObservedTaskEvidence:
    return ObservedTaskEvidence(
        task_start_time=datetime(2026, 7, 16, 8, tzinfo=UTC),
        task_end_time=datetime(2026, 7, 16, 8, 1, tzinfo=UTC),
        lakeflow_result_state="SUCCESS",
        attempt_number=0,
        logs_truncated=False,
        artifact_reference=reference,
    )


@dataclass
class _Jobs:
    evidence: ObservedTaskEvidence

    def read(self, context: AttemptContext) -> ObservedTaskEvidence:
        assert context == _context()
        return self.evidence


@dataclass
class _Downloader:
    archive: bytes

    def download(self, reference: ArtifactReference) -> bytes:
        assert reference.headers == {"x-required": "present"}
        return self.archive


class _UnavailableDownloader:
    def download(self, reference: ArtifactReference) -> bytes:
        raise ArtifactDownloadError("DBT_ARCHIVE_LINK_EXPIRED_OR_DENIED")


@dataclass
class _Sink:
    records: list[CollectionRecord]

    def publish(self, record: CollectionRecord) -> None:
        self.records.append(record)


def test_complete_archive_is_preserved_classified_and_published(tmp_path: Path) -> None:
    sink = _Sink([])
    value = _archive()
    record = collect_task_run(
        context=_context(),
        jobs=_Jobs(
            _observed(ArtifactReference("https://signed.invalid/a", {"x-required": "present"}))
        ),
        downloader=_Downloader(value),
        raw_store=VolumeRawArchiveStore(str(tmp_path), require_volume=False),
        sink=sink,
        now=datetime(2026, 7, 16, 9, tzinfo=UTC),
    )

    assert record.retrieval_state is RetrievalState.RETRIEVED
    assert record.capture.capture_state is CaptureState.COMPLETE
    assert record.capture.projection is not None
    assert record.normalized_digest
    assert record.raw_archive_locator is not None
    assert Path(record.raw_archive_locator).read_bytes() == value
    assert sink.records == [record]

    replay = collect_task_run(
        context=_context(),
        jobs=_Jobs(
            _observed(ArtifactReference("https://signed.invalid/b", {"x-required": "present"}))
        ),
        downloader=_Downloader(value),
        raw_store=VolumeRawArchiveStore(str(tmp_path), require_volume=False),
        sink=sink,
        now=datetime(2026, 7, 16, 10, tzinfo=UTC),
    )
    assert replay.normalized_digest == record.normalized_digest
    assert replay.raw_archive_locator == record.raw_archive_locator


@pytest.mark.parametrize(
    ("reference", "downloader", "issue_code"),
    [
        (None, _Downloader(b"unused"), "DBT_ARCHIVE_LINK_UNAVAILABLE"),
        (
            ArtifactReference("https://signed.invalid/expired", {}),
            _UnavailableDownloader(),
            "DBT_ARCHIVE_LINK_EXPIRED_OR_DENIED",
        ),
    ],
)
def test_missing_or_failed_download_is_archive_unavailable(
    tmp_path: Path,
    reference: ArtifactReference | None,
    downloader: _Downloader | _UnavailableDownloader,
    issue_code: str,
) -> None:
    sink = _Sink([])
    record = collect_task_run(
        context=_context(),
        jobs=_Jobs(_observed(reference)),
        downloader=downloader,
        raw_store=VolumeRawArchiveStore(str(tmp_path), require_volume=False),
        sink=sink,
    )

    assert record.retrieval_state is RetrievalState.UNAVAILABLE
    assert record.capture.capture_state is CaptureState.ARCHIVE_UNAVAILABLE
    assert record.capture.issue_code == issue_code
    assert record.raw_archive_locator is None
    assert record.capture.projection is None
    assert sink.records == [record]


@pytest.mark.parametrize(
    "change",
    [
        {"workspace_id": 0},
        {"repair_count": -1},
        {"observed_task_key": "{{tasks.bad.run_id}}"},
    ],
)
def test_attempt_context_rejects_unresolved_or_invalid_dynamic_values(
    change: dict[str, object],
) -> None:
    values: dict[str, object] = {
        "workspace_id": 101,
        "observed_job_id": 201,
        "observed_job_run_id": 301,
        "dbt_task_run_id": 401,
        "observed_task_key": "dbt_build",
        "repair_count": 0,
        "execution_count": 1,
    }
    values.update(change)
    with pytest.raises(ValueError):
        AttemptContext(**values)  # type: ignore[arg-type]


def test_signed_reference_repr_never_exposes_url_or_headers() -> None:
    reference = ArtifactReference(
        "https://example.invalid/path?signature=TOP_SECRET",
        {"Authorization": "TOP_SECRET"},
    )

    assert "TOP_SECRET" not in repr(reference)
    assert "example.invalid" not in repr(reference)
