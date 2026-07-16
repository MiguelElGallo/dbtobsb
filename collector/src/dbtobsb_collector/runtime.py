"""Collector orchestration with conservative archive classification."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from dbtobsb_capture import inspect_dbt_output_archive, unavailable_archive_capture

from dbtobsb_collector.contracts import (
    ArchiveDownloader,
    AttemptContext,
    CollectionRecord,
    EvidenceSink,
    JobsEvidenceReader,
    RawArchiveStore,
    RetrievalState,
)
from dbtobsb_collector.download import ArtifactDownloadError


def _digest(record: CollectionRecord) -> str:
    capture = record.capture
    projection = capture.projection
    normalized = {
        "attempt": {
            "workspace_id": record.context.workspace_id,
            "observed_job_id": record.context.observed_job_id,
            "observed_job_run_id": record.context.observed_job_run_id,
            "dbt_task_run_id": record.context.dbt_task_run_id,
            "observed_task_key": record.context.observed_task_key,
            "repair_count": record.context.repair_count,
            "execution_count": record.context.execution_count,
        },
        "capture": {
            "retrieval_state": record.retrieval_state.value,
            "capture_state": capture.capture_state.value,
            "issue_code": capture.issue_code,
            "archive_sha256": capture.archive_sha256,
            "manifest_sha256": capture.manifest_sha256,
            "run_results_sha256": capture.run_results_sha256,
        },
        "outer": {
            "task_start_time": (
                record.observed.task_start_time.isoformat()
                if record.observed.task_start_time is not None
                else None
            ),
            "task_end_time": (
                record.observed.task_end_time.isoformat()
                if record.observed.task_end_time is not None
                else None
            ),
            "lakeflow_result_state": record.observed.lakeflow_result_state,
            "attempt_number": record.observed.attempt_number,
            "logs_truncated": record.observed.logs_truncated,
        },
        "invocation": (
            {
                "invocation_id": projection.invocation.invocation_id,
                "elapsed_time": projection.invocation.elapsed_time,
                "result_count": projection.invocation.result_count,
                "status_counts": projection.invocation.status_counts,
            }
            if projection is not None
            else None
        ),
        "nodes": (
            sorted(
                [
                    {
                        "unique_id": node.unique_id,
                        "resource_type": node.resource_type,
                        "status": node.status,
                        "execution_time": node.execution_time,
                        "failures": node.failures,
                    }
                    for node in projection.node_results
                ],
                key=lambda node: node["unique_id"],
            )
            if projection is not None
            else []
        ),
    }
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def collect_task_run(
    *,
    context: AttemptContext,
    jobs: JobsEvidenceReader,
    downloader: ArchiveDownloader,
    raw_store: RawArchiveStore,
    sink: EvidenceSink,
    now: datetime | None = None,
) -> CollectionRecord:
    """Retrieve, preserve, classify, and idempotently publish one task attempt."""
    observed = jobs.read(context)
    raw_locator: str | None = None
    reference = observed.artifact_reference
    if reference is None:
        retrieval_state = RetrievalState.UNAVAILABLE
        capture = unavailable_archive_capture(issue_code="DBT_ARCHIVE_LINK_UNAVAILABLE")
    else:
        try:
            archive = downloader.download(reference)
        except ArtifactDownloadError as exc:
            retrieval_state = RetrievalState.UNAVAILABLE
            capture = unavailable_archive_capture(issue_code=exc.code)
        else:
            retrieval_state = RetrievalState.RETRIEVED
            raw_locator = raw_store.preserve(context=context, archive=archive)
            capture = inspect_dbt_output_archive(archive=archive)

    provisional = CollectionRecord(
        context=context,
        observed=observed,
        retrieval_state=retrieval_state,
        capture=capture,
        raw_archive_locator=raw_locator,
        collected_at=now or datetime.now(UTC),
        normalized_digest="",
    )
    record = CollectionRecord(
        context=context,
        observed=observed,
        retrieval_state=retrieval_state,
        capture=capture,
        raw_archive_locator=raw_locator,
        collected_at=provisional.collected_at,
        normalized_digest=_digest(provisional),
    )
    sink.publish(record)
    return record
