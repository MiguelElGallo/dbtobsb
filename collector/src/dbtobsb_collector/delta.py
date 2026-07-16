"""Native Spark/Delta idempotent evidence publication."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from dbtobsb_contracts import load_support_manifest

from dbtobsb_collector.bootstrap import (
    INVOCATIONS_TABLE,
    NODE_RESULTS_TABLE,
    REGISTRY_TABLE,
    InstallationSeal,
)
from dbtobsb_collector.contracts import AttemptContext, CollectionRecord
from dbtobsb_collector.naming import qualify

SAFE_COLLECTION_ISSUE_CODES = frozenset(
    {
        "DBT_JOBS_DBT_SOURCE_UNSUPPORTED",
        "DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH",
        "DBT_JOBS_DBT_COMMAND_CONTRACT_MISMATCH",
        "DBT_JOBS_DBT_ENVIRONMENT_CONTRACT_MISMATCH",
        "DBT_JOBS_DBT_TARGET_BINDING_INVALID",
        "DBT_JOBS_DBT_TASK_POLICY_MISMATCH",
        "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED",
        "DBT_JOBS_INSTALLED_JOB_BINDING_MISMATCH",
        "DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED",
        "DBT_JOBS_WORKSPACE_BINDING_MISMATCH",
        "DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH",
        "DBT_JOBS_DBT_CONFIGURATION_NOT_READY",
        "DBT_JOBS_PARENT_CORRELATION_MISMATCH",
        "DBT_JOBS_PARENT_PAGINATION_INVALID",
        "DBT_JOBS_TASK_CORRELATION_MISMATCH",
        "DBT_JOBS_TASK_NOT_TERMINAL",
        "DBT_JOBS_TASK_RESULT_UNAVAILABLE",
        "DBT_JOBS_OUTPUT_CORRELATION_MISMATCH",
        "DBTOBSB_ATTEMPT_ROOT_CONFLICT",
        "DBTOBSB_ATTEMPT_ROOT_READBACK_MISMATCH",
        "DBTOBSB_CHILD_READBACK_MISMATCH",
        "DBTOBSB_PUBLISH_SENTINEL_NOT_COMMITTED",
        "DBTOBSB_RECONCILIATION_INTERRUPTED_ATTEMPT",
        "DBTOBSB_RECONCILIATION_COLLECTION_FAILED",
    }
)
_COLLECTION_CLAIM_LEASE = timedelta(minutes=20)
_FIXED_DBT_TASK_KEY = "dbt_build"


class SparkRuntimeSession(Protocol):
    """Small Spark surface required by the runtime DML-only sink."""

    def createDataFrame(self, data: list[dict[str, Any]], schema: str) -> Any: ...

    def sql(self, query: str, *, args: dict[str, Any] | None = None) -> Any: ...


REGISTRY_SOURCE_SCHEMA = """
workspace_id LONG,
dbt_task_run_id LONG,
observed_job_id LONG,
observed_job_run_id LONG,
observed_task_key STRING,
repair_count INT,
execution_count INT,
attempt_number INT,
task_start_time TIMESTAMP,
task_end_time TIMESTAMP,
lakeflow_result_state STRING,
retrieval_state STRING,
capture_state STRING,
pair_state STRING,
dbt_include_deps BOOLEAN,
issue_code STRING,
logs_truncated BOOLEAN,
archive_sha256 STRING,
archive_size_bytes LONG,
raw_archive_locator STRING,
manifest_sha256 STRING,
manifest_size_bytes LONG,
run_results_sha256 STRING,
run_results_size_bytes LONG,
structured_log_state STRING,
structured_log_sha256 STRING,
structured_log_size_bytes LONG,
structured_log_file_count INT,
structured_log_version INT,
deps_structured_log_state STRING,
deps_structured_log_sha256 STRING,
deps_structured_log_size_bytes LONG,
deps_structured_log_file_count INT,
deps_structured_log_version INT,
structured_log_expected_dbt_common_version STRING,
invocation_id STRING,
expected_node_count LONG,
normalized_digest STRING,
collector_state STRING,
collected_at TIMESTAMP,
published_at TIMESTAMP,
first_discovered_at TIMESTAMP,
last_attempted_at TIMESTAMP,
collection_attempt_count INT,
collection_issue_code STRING,
last_reconciliation_run_id LONG
""".strip()

INVOCATION_SOURCE_SCHEMA = """
workspace_id LONG,
dbt_task_run_id LONG,
invocation_id STRING,
generated_at TIMESTAMP,
elapsed_time DOUBLE,
dbt_version STRING,
adapter_type STRING,
command STRING,
result_count LONG,
status_counts_json STRING,
normalized_digest STRING
""".strip()

NODE_SOURCE_SCHEMA = """
workspace_id LONG,
dbt_task_run_id LONG,
invocation_id STRING,
unique_id STRING,
resource_type STRING,
status STRING,
execution_time DOUBLE,
failures LONG,
normalized_digest STRING
""".strip()


def _one_row(result: Any) -> Any | None:
    rows = result.collect()
    if len(rows) > 1:
        raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_DUPLICATE")
    return rows[0] if rows else None


def _value(row: Any, key: str) -> Any:
    try:
        return row[key]
    except (KeyError, TypeError):
        return getattr(row, key)


@dataclass(frozen=True, slots=True)
class CollectionAttemptState:
    """Durable retry state stored in the existing artifact registry root."""

    collector_state: str
    collection_attempt_count: int
    normalized_digest: str | None


def _verify_context_root(row: Any, context: AttemptContext) -> None:
    expected = {
        "workspace_id": context.workspace_id,
        "dbt_task_run_id": context.dbt_task_run_id,
        "observed_job_id": context.observed_job_id,
        "observed_job_run_id": context.observed_job_run_id,
        "observed_task_key": context.observed_task_key,
        "repair_count": context.repair_count,
        "execution_count": context.execution_count,
    }
    if any(_value(row, field) != value for field, value in expected.items()):
        raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_CONFLICT")


def _validate_attempt_binding(
    context: AttemptContext,
    installation_seal: InstallationSeal,
) -> None:
    if (
        context.workspace_id != installation_seal.workspace_id
        or context.observed_job_id != installation_seal.observed_job_id
        or context.observed_task_key != _FIXED_DBT_TASK_KEY
    ):
        raise RuntimeError("DBTOBSB_DELTA_ATTEMPT_BINDING_MISMATCH")


def _attempt_root_select(registry: str) -> str:
    return f"""SELECT
  workspace_id,
  dbt_task_run_id,
  observed_job_id,
  observed_job_run_id,
  observed_task_key,
  repair_count,
  execution_count,
  normalized_digest,
  collector_state,
  first_discovered_at,
  last_attempted_at,
  collection_attempt_count,
  last_reconciliation_run_id
FROM {registry}
WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id"""


def _ensure_attempt_root(
    spark: SparkRuntimeSession,
    *,
    registry: str,
    context: AttemptContext,
    installation_seal: InstallationSeal,
    initial_state: str,
    first_discovered_at: datetime,
    last_attempted_at: datetime | None,
    collection_attempt_count: int,
    reconciliation_run_id: int | None,
) -> Any:
    _validate_attempt_binding(context, installation_seal)
    key_args = {
        "workspace_id": context.workspace_id,
        "task_run_id": context.dbt_task_run_id,
    }
    existing = _one_row(spark.sql(_attempt_root_select(registry), args=key_args))
    if existing is not None:
        _verify_context_root(existing, context)
        return existing

    merge_statement = f"""MERGE INTO {registry} AS target
USING (
  SELECT
    :workspace_id AS workspace_id,
    :task_run_id AS dbt_task_run_id,
    :observed_job_id AS observed_job_id,
    :observed_job_run_id AS observed_job_run_id,
    :observed_task_key AS observed_task_key,
    :repair_count AS repair_count,
    :execution_count AS execution_count,
    :initial_state AS collector_state,
    :first_discovered_at AS first_discovered_at,
    :last_attempted_at AS last_attempted_at,
    :collection_attempt_count AS collection_attempt_count,
    :reconciliation_run_id AS last_reconciliation_run_id
) AS source
ON target.workspace_id = source.workspace_id
 AND target.dbt_task_run_id = source.dbt_task_run_id
WHEN NOT MATCHED THEN INSERT (
  workspace_id,
  dbt_task_run_id,
  observed_job_id,
  observed_job_run_id,
  observed_task_key,
  repair_count,
  execution_count,
  collector_state,
  first_discovered_at,
  last_attempted_at,
  collection_attempt_count,
  last_reconciliation_run_id
) VALUES (
  source.workspace_id,
  source.dbt_task_run_id,
  source.observed_job_id,
  source.observed_job_run_id,
  source.observed_task_key,
  source.repair_count,
  source.execution_count,
  source.collector_state,
  source.first_discovered_at,
  source.last_attempted_at,
  source.collection_attempt_count,
  source.last_reconciliation_run_id
)"""
    merge_args = {
        **key_args,
        "observed_job_id": context.observed_job_id,
        "observed_job_run_id": context.observed_job_run_id,
        "observed_task_key": context.observed_task_key,
        "repair_count": context.repair_count,
        "execution_count": context.execution_count,
        "initial_state": initial_state,
        "first_discovered_at": first_discovered_at,
        "last_attempted_at": last_attempted_at,
        "collection_attempt_count": collection_attempt_count,
        "reconciliation_run_id": reconciliation_run_id,
    }
    merge_failed = False
    try:
        spark.sql(merge_statement, args=merge_args)
    except Exception:
        merge_failed = True
    try:
        root = _one_row(spark.sql(_attempt_root_select(registry), args=key_args))
    except Exception:
        raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_WRITE_INDETERMINATE") from None
    if root is None:
        if merge_failed:
            raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_WRITE_INDETERMINATE")
        raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_READBACK_MISMATCH")
    _verify_context_root(root, context)
    return root


def _registry_row(record: CollectionRecord, *, existing: Any | None = None) -> dict[str, Any]:
    if existing is None:
        raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_READBACK_MISMATCH")
    capture = record.capture
    projection = capture.projection
    pair_state = capture.pair_report.state.value if capture.pair_report is not None else None
    build_log = capture.structured_logs[-1]
    deps_log = capture.structured_logs[0] if capture.include_deps else None
    packages = load_support_manifest().dbt["packages"]
    expected_dbt_common_version = packages["dbt-common"]
    if not isinstance(expected_dbt_common_version, str):
        raise RuntimeError("DBTOBSB_SUPPORT_MANIFEST_DBT_COMMON_VERSION_INVALID")
    return {
        "workspace_id": record.context.workspace_id,
        "dbt_task_run_id": record.context.dbt_task_run_id,
        "observed_job_id": record.context.observed_job_id,
        "observed_job_run_id": record.context.observed_job_run_id,
        "observed_task_key": record.context.observed_task_key,
        "repair_count": record.context.repair_count,
        "execution_count": record.context.execution_count,
        "attempt_number": record.observed.attempt_number,
        "task_start_time": record.observed.task_start_time,
        "task_end_time": record.observed.task_end_time,
        "lakeflow_result_state": record.observed.lakeflow_result_state,
        "retrieval_state": record.retrieval_state.value,
        "capture_state": capture.capture_state.value,
        "pair_state": pair_state,
        "dbt_include_deps": capture.include_deps,
        "issue_code": capture.issue_code,
        "logs_truncated": record.observed.logs_truncated,
        "archive_sha256": capture.archive_sha256,
        "archive_size_bytes": capture.archive_size_bytes,
        "raw_archive_locator": record.raw_archive_locator,
        "manifest_sha256": capture.manifest_sha256,
        "manifest_size_bytes": capture.manifest_size_bytes,
        "run_results_sha256": capture.run_results_sha256,
        "run_results_size_bytes": capture.run_results_size_bytes,
        "structured_log_state": build_log.state.value,
        "structured_log_sha256": build_log.sha256,
        "structured_log_size_bytes": build_log.size_bytes,
        "structured_log_file_count": build_log.file_count,
        "structured_log_version": build_log.log_version,
        "deps_structured_log_state": deps_log.state.value if deps_log is not None else None,
        "deps_structured_log_sha256": deps_log.sha256 if deps_log is not None else None,
        "deps_structured_log_size_bytes": deps_log.size_bytes if deps_log is not None else None,
        "deps_structured_log_file_count": deps_log.file_count if deps_log is not None else None,
        "deps_structured_log_version": deps_log.log_version if deps_log is not None else None,
        "structured_log_expected_dbt_common_version": expected_dbt_common_version,
        "invocation_id": projection.invocation.invocation_id if projection is not None else None,
        "expected_node_count": len(projection.node_results) if projection is not None else 0,
        "normalized_digest": record.normalized_digest,
        "collector_state": "COLLECTING",
        "collected_at": record.collected_at,
        "published_at": None,
        "first_discovered_at": (
            _value(existing, "first_discovered_at") if existing is not None else record.collected_at
        ),
        "last_attempted_at": (
            _value(existing, "last_attempted_at") if existing is not None else record.collected_at
        ),
        "collection_attempt_count": (
            _value(existing, "collection_attempt_count") if existing is not None else 1
        ),
        "collection_issue_code": None,
        "last_reconciliation_run_id": (_value(existing, "last_reconciliation_run_id")),
    }


def _artifact_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise RuntimeError("DBTOBSB_ACCEPTED_TIMESTAMP_INVALID") from None


class DeltaCollectionTracker:
    """Track bounded reconciliation attempts in the existing registry table only."""

    def __init__(
        self,
        spark: SparkRuntimeSession,
        *,
        catalog: str,
        schema: str,
        installation_seal: InstallationSeal,
    ) -> None:
        if (
            installation_seal.evidence_catalog != catalog
            or installation_seal.evidence_schema != schema
        ):
            raise ValueError("DBTOBSB_DELTA_INSTALLATION_BINDING_MISMATCH")
        self._spark = spark
        self._registry = qualify(catalog, schema, REGISTRY_TABLE)
        self._installation_seal = installation_seal

    def discover(
        self,
        context: AttemptContext,
        *,
        reconciliation_run_id: int,
        discovered_at: datetime,
    ) -> CollectionAttemptState:
        existing = _ensure_attempt_root(
            self._spark,
            registry=self._registry,
            context=context,
            installation_seal=self._installation_seal,
            initial_state="DISCOVERED",
            first_discovered_at=discovered_at,
            last_attempted_at=None,
            collection_attempt_count=0,
            reconciliation_run_id=reconciliation_run_id,
        )
        if _value(existing, "collector_state") == "COLLECTING":
            last_attempted_at = _value(existing, "last_attempted_at")
            if (
                not isinstance(last_attempted_at, datetime)
                or last_attempted_at.tzinfo is None
                or discovered_at.tzinfo is None
                or last_attempted_at > discovered_at
            ):
                raise RuntimeError("DBTOBSB_RECONCILIATION_STATE_INVALID")
            if discovered_at - last_attempted_at < _COLLECTION_CLAIM_LEASE:
                return self._state(context)
            self._spark.sql(
                f"""UPDATE {self._registry}
SET collector_state = CASE
      WHEN normalized_digest IS NULL AND collection_attempt_count >= 3
        THEN 'TERMINAL_FAILURE'
      ELSE 'RETRYABLE'
    END,
    collection_issue_code = 'DBTOBSB_RECONCILIATION_INTERRUPTED_ATTEMPT'
WHERE workspace_id = :workspace_id
  AND dbt_task_run_id = :task_run_id
  AND collector_state = 'COLLECTING'""",
                args={
                    "workspace_id": context.workspace_id,
                    "task_run_id": context.dbt_task_run_id,
                },
            )
        self._spark.sql(
            f"""UPDATE {self._registry}
SET last_reconciliation_run_id = :reconciliation_run_id
WHERE workspace_id = :workspace_id
  AND dbt_task_run_id = :task_run_id
  AND collector_state <> 'PUBLISHED'""",
            args={
                "workspace_id": context.workspace_id,
                "task_run_id": context.dbt_task_run_id,
                "reconciliation_run_id": reconciliation_run_id,
            },
        )
        return self._state(context)

    def begin_attempt(
        self,
        context: AttemptContext,
        *,
        attempted_at: datetime,
    ) -> CollectionAttemptState:
        _validate_attempt_binding(context, self._installation_seal)
        self._spark.sql(
            f"""UPDATE {self._registry}
SET collector_state = 'COLLECTING',
    last_attempted_at = :attempted_at,
    collection_attempt_count = CASE
      WHEN normalized_digest IS NULL THEN collection_attempt_count + 1
      ELSE collection_attempt_count
    END,
    collection_issue_code = NULL
WHERE workspace_id = :workspace_id
  AND dbt_task_run_id = :task_run_id
  AND collector_state IN ('DISCOVERED', 'RETRYABLE')
  AND (normalized_digest IS NOT NULL OR collection_attempt_count < 3)""",
            args={
                "workspace_id": context.workspace_id,
                "task_run_id": context.dbt_task_run_id,
                "attempted_at": attempted_at,
            },
        )
        state = self._state(context)
        if state.collector_state == "PUBLISHED":
            return state
        if state.collector_state != "COLLECTING":
            raise RuntimeError("DBTOBSB_RECONCILIATION_ATTEMPT_NOT_CLAIMED")
        return state

    def record_failure(self, context: AttemptContext, *, issue_code: str) -> CollectionAttemptState:
        _validate_attempt_binding(context, self._installation_seal)
        if issue_code not in SAFE_COLLECTION_ISSUE_CODES:
            issue_code = "DBTOBSB_RECONCILIATION_COLLECTION_FAILED"
        self._spark.sql(
            f"""UPDATE {self._registry}
SET collector_state = CASE
      WHEN collection_attempt_count >= 3 THEN 'TERMINAL_FAILURE'
      ELSE 'RETRYABLE'
    END,
    collection_issue_code = :issue_code
WHERE workspace_id = :workspace_id
  AND dbt_task_run_id = :task_run_id
  AND collector_state = 'COLLECTING'""",
            args={
                "workspace_id": context.workspace_id,
                "task_run_id": context.dbt_task_run_id,
                "issue_code": issue_code,
            },
        )
        state = self._state(context)
        if state.collector_state not in {"RETRYABLE", "TERMINAL_FAILURE"}:
            raise RuntimeError("DBTOBSB_RECONCILIATION_FAILURE_NOT_RECORDED")
        return state

    def _state(self, context: AttemptContext) -> CollectionAttemptState:
        row = _one_row(
            self._spark.sql(
                _attempt_root_select(self._registry),
                args={
                    "workspace_id": context.workspace_id,
                    "task_run_id": context.dbt_task_run_id,
                },
            )
        )
        if row is None:
            raise RuntimeError("DBTOBSB_RECONCILIATION_STATE_UNAVAILABLE")
        _verify_context_root(row, context)
        state = _value(row, "collector_state")
        count = _value(row, "collection_attempt_count")
        digest = _value(row, "normalized_digest")
        if (
            not isinstance(state, str)
            or type(count) is not int
            or count < 0
            or count > 3
            or (digest is not None and not isinstance(digest, str))
        ):
            raise RuntimeError("DBTOBSB_RECONCILIATION_STATE_INVALID")
        return CollectionAttemptState(state, count, digest)


class DeltaEvidenceSink:
    """Publish via typed DataFrames, deterministic MERGE, and a root sentinel."""

    def __init__(
        self,
        spark: SparkRuntimeSession,
        *,
        catalog: str,
        schema: str,
        installation_seal: InstallationSeal,
    ) -> None:
        if (
            installation_seal.evidence_catalog != catalog
            or installation_seal.evidence_schema != schema
        ):
            raise ValueError("DBTOBSB_DELTA_INSTALLATION_BINDING_MISMATCH")
        self._spark = spark
        self._registry = qualify(catalog, schema, REGISTRY_TABLE)
        self._invocations = qualify(catalog, schema, INVOCATIONS_TABLE)
        self._nodes = qualify(catalog, schema, NODE_RESULTS_TABLE)
        self._installation_seal = installation_seal

    def publish(self, record: CollectionRecord) -> None:
        key_args = {
            "workspace_id": record.context.workspace_id,
            "task_run_id": record.context.dbt_task_run_id,
        }
        existing = _ensure_attempt_root(
            self._spark,
            registry=self._registry,
            context=record.context,
            installation_seal=self._installation_seal,
            initial_state="COLLECTING",
            first_discovered_at=record.collected_at,
            last_attempted_at=record.collected_at,
            collection_attempt_count=1,
            reconciliation_run_id=None,
        )
        existing_digest = _value(existing, "normalized_digest")
        if existing_digest is not None and existing_digest != record.normalized_digest:
            raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_CONFLICT")
        if _value(existing, "collector_state") == "PUBLISHED":
            return

        self._spark.createDataFrame(
            [_registry_row(record, existing=existing)], schema=REGISTRY_SOURCE_SCHEMA
        ).createOrReplaceTempView("dbtobsb_registry_source")
        self._spark.sql(
            f"""MERGE INTO {self._registry} AS target
USING dbtobsb_registry_source AS source
ON target.workspace_id = source.workspace_id
 AND target.dbt_task_run_id = source.dbt_task_run_id
WHEN MATCHED
 AND target.normalized_digest IS NULL
 AND target.collector_state <> 'PUBLISHED'
 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *"""
        )
        root = _one_row(
            self._spark.sql(
                _attempt_root_select(self._registry),
                args=key_args,
            )
        )
        if root is None or _value(root, "normalized_digest") != record.normalized_digest:
            raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_READBACK_MISMATCH")
        _verify_context_root(root, record.context)

        projection = record.capture.projection
        if projection is not None:
            invocation = projection.invocation
            invocation_row = {
                "workspace_id": record.context.workspace_id,
                "dbt_task_run_id": record.context.dbt_task_run_id,
                "invocation_id": invocation.invocation_id,
                "generated_at": _artifact_timestamp(invocation.generated_at),
                "elapsed_time": invocation.elapsed_time,
                "dbt_version": invocation.dbt_version,
                "adapter_type": invocation.adapter_type,
                "command": invocation.command,
                "result_count": invocation.result_count,
                "status_counts_json": json.dumps(
                    dict(invocation.status_counts), sort_keys=True, separators=(",", ":")
                ),
                "normalized_digest": record.normalized_digest,
            }
            self._spark.createDataFrame(
                [invocation_row], schema=INVOCATION_SOURCE_SCHEMA
            ).createOrReplaceTempView("dbtobsb_invocation_source")
            self._spark.sql(
                f"""MERGE INTO {self._invocations} AS target
USING dbtobsb_invocation_source AS source
ON target.workspace_id = source.workspace_id
 AND target.dbt_task_run_id = source.dbt_task_run_id
 AND target.normalized_digest = source.normalized_digest
WHEN NOT MATCHED THEN INSERT *"""
            )

            node_rows = [
                {
                    "workspace_id": record.context.workspace_id,
                    "dbt_task_run_id": record.context.dbt_task_run_id,
                    "invocation_id": invocation.invocation_id,
                    "unique_id": node.unique_id,
                    "resource_type": node.resource_type,
                    "status": node.status,
                    "execution_time": node.execution_time,
                    "failures": node.failures,
                    "normalized_digest": record.normalized_digest,
                }
                for node in projection.node_results
            ]
            self._spark.createDataFrame(
                node_rows, schema=NODE_SOURCE_SCHEMA
            ).createOrReplaceTempView("dbtobsb_node_source")
            self._spark.sql(
                f"""MERGE INTO {self._nodes} AS target
USING dbtobsb_node_source AS source
ON target.workspace_id = source.workspace_id
 AND target.dbt_task_run_id = source.dbt_task_run_id
 AND target.normalized_digest = source.normalized_digest
 AND target.unique_id = source.unique_id
WHEN NOT MATCHED THEN INSERT *"""
            )

        counts = _one_row(
            self._spark.sql(
                f"""SELECT
  (SELECT count(*) FROM {self._invocations}
    WHERE workspace_id = :workspace_id
      AND dbt_task_run_id = :task_run_id) AS invocation_total_count,
  (SELECT count(*) FROM {self._invocations}
    WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id
      AND normalized_digest = :digest) AS invocation_matching_count,
  (SELECT count(*) FROM {self._nodes}
    WHERE workspace_id = :workspace_id
      AND dbt_task_run_id = :task_run_id) AS node_total_count,
  (SELECT count(*) FROM {self._nodes}
    WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id
      AND normalized_digest = :digest) AS node_matching_count""",
                args={**key_args, "digest": record.normalized_digest},
            )
        )
        expected_invocations = 1 if projection is not None else 0
        expected_nodes = len(projection.node_results) if projection is not None else 0
        if (
            counts is None
            or _value(counts, "invocation_total_count") != expected_invocations
            or _value(counts, "invocation_matching_count") != expected_invocations
            or _value(counts, "node_total_count") != expected_nodes
            or _value(counts, "node_matching_count") != expected_nodes
        ):
            raise RuntimeError("DBTOBSB_CHILD_READBACK_MISMATCH")

        self._spark.sql(
            f"""UPDATE {self._registry}
SET collector_state = 'PUBLISHED', published_at = current_timestamp()
WHERE workspace_id = :workspace_id
  AND dbt_task_run_id = :task_run_id
  AND normalized_digest = :digest
  AND collector_state = 'COLLECTING'""",
            args={**key_args, "digest": record.normalized_digest},
        )
        published = _one_row(
            self._spark.sql(
                _attempt_root_select(self._registry),
                args=key_args,
            )
        )
        if published is None or _value(published, "collector_state") != "PUBLISHED":
            raise RuntimeError("DBTOBSB_PUBLISH_SENTINEL_NOT_COMMITTED")
        _verify_context_root(published, record.context)
