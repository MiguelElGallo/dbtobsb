"""Bounded installed-policy reconciliation using Jobs APIs and evidence tables."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from itertools import islice
from typing import Any, Protocol

from databricks.sdk import WorkspaceClient
from dbtobsb_contracts import DbtRuntimePolicySnapshot

from dbtobsb_collector.bootstrap import (
    RAW_VOLUME_NAME,
    InstallationSeal,
    SparkBootstrapSession,
    read_installation_seal,
)
from dbtobsb_collector.contracts import AttemptContext, JobsEvidenceReader
from dbtobsb_collector.custody import VolumeRawArchiveStore
from dbtobsb_collector.delta import (
    SAFE_COLLECTION_ISSUE_CODES,
    DeltaCollectionTracker,
    DeltaEvidenceSink,
    SparkRuntimeSession,
)
from dbtobsb_collector.jobs import (
    DatabricksJobsEvidenceReader,
    JobsEvidenceError,
    _collector_environment_matches,
    _task_has_no_retries,
    attempt_context_from_resolved_task,
)
from dbtobsb_collector.runtime import collect_task_run
from dbtobsb_collector.volume_archive import DatabricksArtifactDownloader

_MAX_PARENT_RUNS = 100
_MAX_TASK_RUN_IDS = 500
_MAX_PARENT_PAGES = 10
_MAX_REPLAYS = 20
_LOOKBACK = timedelta(hours=24)
RECONCILIATION_OPERATOR_CODES = frozenset(
    {
        "DBTOBSB_RECONCILIATION_BINDING_MISMATCH",
        "DBTOBSB_RECONCILIATION_PARENT_INVALID",
        "DBTOBSB_RECONCILIATION_PARENT_PAGINATION_INVALID",
        "DBTOBSB_RECONCILIATION_PARENT_LIMIT_EXCEEDED",
        "DBTOBSB_RECONCILIATION_TASK_CONTEXT_INVALID",
        "DBTOBSB_RECONCILIATION_TASK_LIMIT_EXCEEDED",
        "DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH",
    }
)


class ReconciliationSparkSession(SparkRuntimeSession, SparkBootstrapSession, Protocol):
    """Combined Spark surface used by seal readback and runtime DML."""


class ReconciliationError(RuntimeError):
    """Static reconciliation error with no native response content."""


def _enum_value(value: Any, *, fallback: str) -> str:
    if isinstance(value, str):
        return value
    native = getattr(value, "value", None)
    return native if isinstance(native, str) else fallback


def _empty_override(value: Any) -> bool:
    if value is None:
        return True
    as_dict = getattr(value, "as_dict", None)
    observed = as_dict() if as_dict is not None else value
    return observed in ({}, [], ())


class InstalledPolicyReconciliationController:
    """Attest one reconciler run and discover a bounded 24-hour attempt set."""

    def __init__(
        self,
        *,
        installation_seal: InstallationSeal,
        policy: DbtRuntimePolicySnapshot,
        client: WorkspaceClient | None = None,
        sleep: Any = time.sleep,
    ) -> None:
        if (
            installation_seal.source_contract_sha256 != policy.source_contract_sha256
            or installation_seal.expected_runtime_policy_sha256
            != policy.expected_runtime_policy_sha256
        ):
            raise ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH")
        self.installation_seal = installation_seal
        self.policy = policy
        self.client = client or WorkspaceClient()
        self._sleep = sleep

    def _task_parameters(self) -> tuple[str, ...]:
        return (
            "--workspace_id",
            "{{workspace.id}}",
            "--reconciler_job_id",
            "{{job.id}}",
            "--reconciliation_run_id",
            "{{job.run_id}}",
        )

    def _task_matches(self, task: Any, *, run_projection: bool = False) -> bool:
        wheel = getattr(task, "python_wheel_task", None)
        timeout_seconds = getattr(task, "timeout_seconds", None)
        return not (
            getattr(task, "task_key", None) != "reconcile"
            or getattr(task, "environment_key", None) != "collector"
            or (timeout_seconds not in {None, 900} if run_projection else timeout_seconds != 900)
            or not _task_has_no_retries(task)
            or getattr(wheel, "package_name", None) != "dbtobsb-collector"
            or getattr(wheel, "entry_point", None) != "reconcile"
            or tuple(getattr(wheel, "parameters", None) or ()) != self._task_parameters()
        )

    def preflight(
        self,
        *,
        workspace_id: int,
        reconciler_job_id: int,
        reconciliation_run_id: int,
    ) -> None:
        seal = self.installation_seal
        if reconciler_job_id != seal.reconciler_job_id or workspace_id != seal.workspace_id:
            raise ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH")
        try:
            if self.client.get_workspace_id() != seal.workspace_id:
                raise ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH")
            authenticated = self.client.current_user.me()
            job = self.client.jobs.get(seal.reconciler_job_id)
            active = tuple(
                islice(
                    self.client.jobs.list_runs(
                        job_id=seal.reconciler_job_id,
                        active_only=True,
                        limit=2,
                    ),
                    2,
                )
            )
        except ReconciliationError:
            raise
        except Exception as error:
            raise ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH") from error
        settings = getattr(job, "settings", None)
        tasks = list(getattr(settings, "tasks", None) or ())
        parameters = list(getattr(settings, "parameters", None) or ())
        schedule = getattr(settings, "schedule", None)
        if (
            getattr(job, "job_id", None) != seal.reconciler_job_id
            or getattr(job, "run_as_user_name", None) != seal.collector_service_principal_name
            or getattr(authenticated, "user_name", None) != seal.collector_service_principal_name
            or getattr(settings, "max_concurrent_runs", None) != 1
            or getattr(settings, "timeout_seconds", None) != 900
            or _enum_value(getattr(settings, "performance_target", None), fallback="UNKNOWN")
            != "STANDARD"
            or getattr(getattr(settings, "run_as", None), "service_principal_name", None)
            != seal.collector_service_principal_name
            or not _collector_environment_matches(
                settings,
                expected_sha256=seal.collector_environment_sha256,
            )
            or parameters
            or len(tasks) != 1
            or not self._task_matches(tasks[0])
            or getattr(schedule, "quartz_cron_expression", None) != "0 0/15 * * * ?"
            or getattr(schedule, "timezone_id", None) != "UTC"
            or _enum_value(getattr(schedule, "pause_status", None), fallback="UNKNOWN")
            not in {"PAUSED", "UNPAUSED"}
            or len(active) != 1
        ):
            raise ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH")
        try:
            current = self.client.jobs.get_run(
                reconciliation_run_id,
                include_resolved_values=True,
            )
        except Exception as error:
            raise ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH") from error
        run_tasks = list(getattr(current, "tasks", None) or ())
        actual_parameters = list(getattr(current, "job_parameters", None) or ())
        if (
            len(active) != 1
            or getattr(active[0], "run_id", None) != reconciliation_run_id
            or getattr(current, "run_id", None) != reconciliation_run_id
            or getattr(current, "job_id", None) != seal.reconciler_job_id
            or _enum_value(getattr(current, "run_type", None), fallback="UNKNOWN") != "JOB_RUN"
            or _enum_value(getattr(current, "trigger", None), fallback="UNKNOWN")
            not in {"PERIODIC", "ONE_TIME"}
            or _enum_value(
                getattr(current, "effective_performance_target", None), fallback="UNKNOWN"
            )
            != "STANDARD"
            or actual_parameters
            or not _empty_override(getattr(current, "overriding_parameters", None))
            or len(run_tasks) != 1
            or not self._task_matches(run_tasks[0], run_projection=True)
        ):
            raise ReconciliationError("DBTOBSB_RECONCILIATION_BINDING_MISMATCH")

    def _get_run(self, run_id: int, **kwargs: Any) -> Any:
        result = self.client.jobs.get_run(run_id, **kwargs)
        self._sleep(0.055)
        return result

    def _parent_pages(self, parent_run_id: int) -> tuple[Any, ...]:
        pages: list[Any] = []
        page_token: str | None = None
        seen_tokens: set[str] = set()
        while True:
            options: dict[str, Any] = {
                "include_history": True,
                "include_resolved_values": True,
            }
            if page_token is not None:
                options["page_token"] = page_token
            page = self._get_run(parent_run_id, **options)
            if getattr(page, "run_id", parent_run_id) not in {None, parent_run_id} or getattr(
                page, "job_id", self.installation_seal.observed_job_id
            ) not in {None, self.installation_seal.observed_job_id}:
                raise ReconciliationError("DBTOBSB_RECONCILIATION_PARENT_INVALID")
            pages.append(page)
            if len(pages) > _MAX_PARENT_PAGES:
                raise ReconciliationError("DBTOBSB_RECONCILIATION_PARENT_PAGINATION_INVALID")
            next_token = getattr(page, "next_page_token", None)
            if next_token is None:
                return tuple(pages)
            if not isinstance(next_token, str) or not next_token or next_token in seen_tokens:
                raise ReconciliationError("DBTOBSB_RECONCILIATION_PARENT_PAGINATION_INVALID")
            seen_tokens.add(next_token)
            page_token = next_token

    def discover_attempts(self, *, now: datetime) -> tuple[AttemptContext, ...]:
        seal = self.installation_seal
        start_ms = int((now - _LOOKBACK).timestamp() * 1000)
        end_ms = int(now.timestamp() * 1000)
        parents = tuple(
            islice(
                self.client.jobs.list_runs(
                    job_id=seal.observed_job_id,
                    completed_only=True,
                    start_time_from=start_ms,
                    start_time_to=end_ms,
                    expand_tasks=True,
                    limit=20,
                ),
                _MAX_PARENT_RUNS + 1,
            )
        )
        if len(parents) > _MAX_PARENT_RUNS:
            raise ReconciliationError("DBTOBSB_RECONCILIATION_PARENT_LIMIT_EXCEEDED")

        contexts: dict[int, AttemptContext] = {}
        task_run_ids: set[tuple[int, int]] = set()
        task_snapshots: dict[int, Any] = {}
        for summary in parents:
            parent_run_id = getattr(summary, "run_id", None)
            if (
                type(parent_run_id) is not int
                or parent_run_id <= 0
                or getattr(summary, "job_id", None) != seal.observed_job_id
            ):
                raise ReconciliationError("DBTOBSB_RECONCILIATION_PARENT_INVALID")
            for parent in self._parent_pages(parent_run_id):
                for task in getattr(parent, "tasks", None) or ():
                    task_run_id = getattr(task, "run_id", None)
                    if type(task_run_id) is int and task_run_id > 0:
                        if task_run_id in task_snapshots:
                            raise ReconciliationError("DBTOBSB_RECONCILIATION_TASK_CONTEXT_INVALID")
                        task_run_ids.add((parent_run_id, task_run_id))
                        task_snapshots[task_run_id] = task
                for history in getattr(parent, "repair_history", None) or ():
                    for task_run_id in getattr(history, "task_run_ids", None) or ():
                        if type(task_run_id) is not int or task_run_id <= 0:
                            raise ReconciliationError("DBTOBSB_RECONCILIATION_TASK_LIMIT_EXCEEDED")
                        task_run_ids.add((parent_run_id, task_run_id))
            if len(task_run_ids) > _MAX_TASK_RUN_IDS:
                raise ReconciliationError("DBTOBSB_RECONCILIATION_TASK_LIMIT_EXCEEDED")

        for parent_run_id, task_run_id in sorted(task_run_ids):
            task = task_snapshots.get(task_run_id)
            if task is None or getattr(task, "resolved_values", None) is None:
                run = self._get_run(task_run_id, include_resolved_values=True)
                if getattr(run, "task_key", None) is not None:
                    task = run
                else:
                    matching = [
                        candidate
                        for candidate in (getattr(run, "tasks", None) or ())
                        if getattr(candidate, "run_id", None) == task_run_id
                    ]
                    if len(matching) != 1:
                        raise ReconciliationError("DBTOBSB_RECONCILIATION_TASK_CONTEXT_INVALID")
                    task = matching[0]
            if getattr(task, "task_key", None) != self.policy.task_key:
                continue
            try:
                context = attempt_context_from_resolved_task(task, policy=self.policy)
            except JobsEvidenceError as error:
                raise ReconciliationError("DBTOBSB_RECONCILIATION_TASK_CONTEXT_INVALID") from error
            if (
                context.workspace_id != seal.workspace_id
                or context.observed_job_id != seal.observed_job_id
                or context.observed_job_run_id != parent_run_id
            ):
                raise ReconciliationError("DBTOBSB_RECONCILIATION_TASK_CONTEXT_INVALID")
            existing = contexts.get(context.dbt_task_run_id)
            if existing is not None and existing != context:
                raise ReconciliationError("DBTOBSB_RECONCILIATION_TASK_CONTEXT_INVALID")
            contexts[context.dbt_task_run_id] = context
        return tuple(contexts[key] for key in sorted(contexts))


class _ReconciledReader(JobsEvidenceReader):
    def __init__(self, reader: DatabricksJobsEvidenceReader) -> None:
        self._reader = reader

    def read(self, context: AttemptContext) -> Any:
        return self._reader.read_reconciled(context)


def _safe_issue_code(error: Exception) -> str:
    observed = error.code if isinstance(error, JobsEvidenceError) else str(error)
    return (
        observed
        if observed in SAFE_COLLECTION_ISSUE_CODES
        else "DBTOBSB_RECONCILIATION_COLLECTION_FAILED"
    )


def reconcile_installed_policy(
    *,
    controller: InstalledPolicyReconciliationController,
    spark: ReconciliationSparkSession,
    reconciliation_run_id: int,
    now: datetime | None = None,
) -> dict[str, int | bool]:
    """Discover and replay up to twenty missing attempts inside one serverless run."""
    observed_at = now or datetime.now(UTC)
    seal = controller.installation_seal
    installed = read_installation_seal(
        spark,
        catalog=seal.evidence_catalog,
        schema=seal.evidence_schema,
    )
    if installed != seal:
        raise ReconciliationError("DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH")
    contexts = controller.discover_attempts(now=observed_at)
    tracker = DeltaCollectionTracker(
        spark,
        catalog=seal.evidence_catalog,
        schema=seal.evidence_schema,
        installation_seal=seal,
    )
    reader = _ReconciledReader(
        DatabricksJobsEvidenceReader.for_installed_policy(
            controller.client,
            installation_seal=seal,
            policy=controller.policy,
        )
    )
    sink = DeltaEvidenceSink(
        spark,
        catalog=seal.evidence_catalog,
        schema=seal.evidence_schema,
        installation_seal=seal,
    )
    published = 0
    attempted = 0
    terminal = 0
    retryable = 0
    backlog = False
    for context in contexts:
        state = tracker.discover(
            context,
            reconciliation_run_id=reconciliation_run_id,
            discovered_at=observed_at,
        )
        if state.collector_state in {"PUBLISHED", "TERMINAL_FAILURE", "COLLECTING"}:
            terminal += state.collector_state == "TERMINAL_FAILURE"
            continue
        if attempted >= _MAX_REPLAYS:
            backlog = True
            continue
        claimed = tracker.begin_attempt(context, attempted_at=observed_at)
        if claimed.collector_state == "PUBLISHED":
            continue
        attempted += 1
        try:
            collect_task_run(
                context=context,
                jobs=reader,
                downloader=DatabricksArtifactDownloader(),
                raw_store=VolumeRawArchiveStore(
                    f"/Volumes/{seal.evidence_catalog}/{seal.evidence_schema}/{RAW_VOLUME_NAME}",
                    require_volume=True,
                ),
                sink=sink,
                now=observed_at,
                installed_policy=controller.policy.installed_policy,
            )
        except Exception as error:
            updated = tracker.record_failure(context, issue_code=_safe_issue_code(error))
            terminal += updated.collector_state == "TERMINAL_FAILURE"
            retryable += updated.collector_state == "RETRYABLE"
        else:
            published += 1
    return {
        "discovered": len(contexts),
        "attempted": attempted,
        "published": published,
        "retryable": retryable,
        "terminal_failure": terminal,
        "backlog": backlog,
    }
