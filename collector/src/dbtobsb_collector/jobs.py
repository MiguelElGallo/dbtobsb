"""Databricks Jobs API adapter for one observed dbt task run."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from databricks.sdk import WorkspaceClient

from dbtobsb_collector.contracts import (
    ArtifactReference,
    AttemptContext,
    ObservedTaskEvidence,
)


class JobsEvidenceError(RuntimeError):
    """Static Jobs evidence error that excludes native response content."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _datetime_from_millis(value: int | None) -> datetime | None:
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value / 1000, tz=UTC)


def _enum_value(value: Any, *, fallback: str) -> str:
    native = getattr(value, "value", None)
    return native if isinstance(native, str) else fallback


def _allow_internal_artifact_http(value: str, *, workspace_host: str) -> bool:
    """Recognize a Databricks-issued internal URL in an authenticated Azure workspace."""
    parts = urlsplit(value)
    if parts.scheme.lower() != "http":
        return False
    try:
        port = parts.port
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    trusted_host = host.endswith(".azuredatabricks.net") or host.endswith(".databricks.com")
    if (
        not trusted_host
        or parts.username is not None
        or parts.password is not None
        or port is not None
    ):
        return False
    workspace = urlsplit(workspace_host)
    try:
        workspace_port = workspace.port
    except ValueError:
        return False
    workspace_name = (workspace.hostname or "").lower()
    return not (
        workspace.scheme.lower() != "https"
        or not workspace_name.endswith(".azuredatabricks.net")
        or workspace.username is not None
        or workspace.password is not None
        or workspace_port is not None
        or workspace.path not in {"", "/"}
        or workspace.query
        or workspace.fragment
    )


class DatabricksJobsEvidenceReader:
    """Use a pinned SDK client to fetch and cross-check task output and metadata."""

    def __init__(self, client: WorkspaceClient | None = None) -> None:
        self._client = client or WorkspaceClient()

    def read(self, context: AttemptContext) -> ObservedTaskEvidence:
        parent = self._client.jobs.get_run(context.observed_job_run_id)
        if parent.run_id != context.observed_job_run_id or parent.job_id != context.observed_job_id:
            raise JobsEvidenceError("DBT_JOBS_PARENT_CORRELATION_MISMATCH")

        tasks = list(parent.tasks or [])
        page_token = parent.next_page_token
        seen_tokens: set[str] = set()
        while page_token:
            if page_token in seen_tokens or len(seen_tokens) >= 100:
                raise JobsEvidenceError("DBT_JOBS_PARENT_PAGINATION_INVALID")
            seen_tokens.add(page_token)
            page = self._client.jobs.get_run(
                context.observed_job_run_id,
                page_token=page_token,
            )
            if (page.run_id is not None and page.run_id != context.observed_job_run_id) or (
                page.job_id is not None and page.job_id != context.observed_job_id
            ):
                raise JobsEvidenceError("DBT_JOBS_PARENT_CORRELATION_MISMATCH")
            tasks.extend(page.tasks or [])
            page_token = page.next_page_token

        matches = [
            task
            for task in tasks
            if task.task_key == context.observed_task_key
            and task.run_id == context.dbt_task_run_id
            and task.dbt_task is not None
        ]
        if len(matches) != 1:
            raise JobsEvidenceError("DBT_JOBS_TASK_CORRELATION_MISMATCH")
        task = matches[0]

        status = getattr(task, "status", None)
        current_state = getattr(status, "state", None)
        if current_state is not None:
            if _enum_value(current_state, fallback="UNKNOWN") != "TERMINATED":
                raise JobsEvidenceError("DBT_JOBS_TASK_NOT_TERMINAL")
            termination = getattr(status, "termination_details", None)
            result_state = getattr(termination, "code", None)
        else:
            legacy = getattr(task, "state", None)
            life_cycle_state = getattr(legacy, "life_cycle_state", None)
            if _enum_value(life_cycle_state, fallback="UNKNOWN") not in {
                "TERMINATED",
                "SKIPPED",
                "INTERNAL_ERROR",
            }:
                raise JobsEvidenceError("DBT_JOBS_TASK_NOT_TERMINAL")
            result_state = getattr(legacy, "result_state", None)
        if result_state is None:
            raise JobsEvidenceError("DBT_JOBS_TASK_RESULT_UNAVAILABLE")

        output = self._client.jobs.get_run_output(context.dbt_task_run_id)
        metadata = output.metadata
        if metadata is not None:
            comparisons = (
                (metadata.run_id, context.dbt_task_run_id),
                (metadata.job_id, context.observed_job_id),
                (metadata.job_run_id, context.observed_job_run_id),
            )
            if any(actual is not None and actual != expected for actual, expected in comparisons):
                raise JobsEvidenceError("DBT_JOBS_OUTPUT_CORRELATION_MISMATCH")

        dbt_output = output.dbt_output
        reference = None
        if dbt_output is not None and dbt_output.artifacts_link:
            reference = ArtifactReference(
                url=dbt_output.artifacts_link,
                headers=dict(dbt_output.artifacts_headers or {}),
                allow_internal_databricks_http=_allow_internal_artifact_http(
                    dbt_output.artifacts_link, workspace_host=self._client.config.host
                ),
            )

        return ObservedTaskEvidence(
            task_start_time=_datetime_from_millis(task.start_time),
            task_end_time=_datetime_from_millis(task.end_time),
            lakeflow_result_state=_enum_value(result_state, fallback="UNKNOWN"),
            attempt_number=task.attempt_number or 0,
            logs_truncated=output.logs_truncated,
            artifact_reference=reference,
        )
