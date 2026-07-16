"""Native Spark/Delta idempotent evidence publication."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Protocol

from dbtobsb_collector.bootstrap import (
    INVOCATIONS_TABLE,
    NODE_RESULTS_TABLE,
    REGISTRY_TABLE,
)
from dbtobsb_collector.contracts import CollectionRecord
from dbtobsb_collector.naming import qualify


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
issue_code STRING,
logs_truncated BOOLEAN,
archive_sha256 STRING,
archive_size_bytes LONG,
raw_archive_locator STRING,
manifest_sha256 STRING,
manifest_size_bytes LONG,
run_results_sha256 STRING,
run_results_size_bytes LONG,
invocation_id STRING,
expected_node_count LONG,
normalized_digest STRING,
collector_state STRING,
collected_at TIMESTAMP,
published_at TIMESTAMP
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


def _registry_row(record: CollectionRecord) -> dict[str, Any]:
    capture = record.capture
    projection = capture.projection
    pair_state = capture.pair_report.state.value if capture.pair_report is not None else None
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
        "issue_code": capture.issue_code,
        "logs_truncated": record.observed.logs_truncated,
        "archive_sha256": capture.archive_sha256,
        "archive_size_bytes": capture.archive_size_bytes,
        "raw_archive_locator": record.raw_archive_locator,
        "manifest_sha256": capture.manifest_sha256,
        "manifest_size_bytes": capture.manifest_size_bytes,
        "run_results_sha256": capture.run_results_sha256,
        "run_results_size_bytes": capture.run_results_size_bytes,
        "invocation_id": projection.invocation.invocation_id if projection is not None else None,
        "expected_node_count": len(projection.node_results) if projection is not None else 0,
        "normalized_digest": record.normalized_digest,
        "collector_state": "COLLECTING",
        "collected_at": record.collected_at,
        "published_at": None,
    }


def _artifact_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise RuntimeError("DBTOBSB_ACCEPTED_TIMESTAMP_INVALID") from None


class DeltaEvidenceSink:
    """Publish via typed DataFrames, deterministic MERGE, and a root sentinel."""

    def __init__(self, spark: SparkRuntimeSession, *, catalog: str, schema: str) -> None:
        self._spark = spark
        self._registry = qualify(catalog, schema, REGISTRY_TABLE)
        self._invocations = qualify(catalog, schema, INVOCATIONS_TABLE)
        self._nodes = qualify(catalog, schema, NODE_RESULTS_TABLE)

    def publish(self, record: CollectionRecord) -> None:
        key_args = {
            "workspace_id": record.context.workspace_id,
            "task_run_id": record.context.dbt_task_run_id,
        }
        existing = _one_row(
            self._spark.sql(
                f"""SELECT normalized_digest, collector_state
FROM {self._registry}
WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id""",
                args=key_args,
            )
        )
        if existing is not None:
            if _value(existing, "normalized_digest") != record.normalized_digest:
                raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_CONFLICT")
            if _value(existing, "collector_state") == "PUBLISHED":
                return

        self._spark.createDataFrame(
            [_registry_row(record)], schema=REGISTRY_SOURCE_SCHEMA
        ).createOrReplaceTempView("dbtobsb_registry_source")
        self._spark.sql(
            f"""MERGE INTO {self._registry} AS target
USING dbtobsb_registry_source AS source
ON target.workspace_id = source.workspace_id
 AND target.dbt_task_run_id = source.dbt_task_run_id
WHEN NOT MATCHED THEN INSERT *"""
        )
        root = _one_row(
            self._spark.sql(
                f"""SELECT normalized_digest, collector_state
FROM {self._registry}
WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id""",
                args=key_args,
            )
        )
        if root is None or _value(root, "normalized_digest") != record.normalized_digest:
            raise RuntimeError("DBTOBSB_ATTEMPT_ROOT_READBACK_MISMATCH")

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
 AND target.unique_id = source.unique_id
WHEN NOT MATCHED THEN INSERT *"""
            )

        counts = _one_row(
            self._spark.sql(
                f"""SELECT
  (SELECT count(*) FROM {self._invocations}
    WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id
      AND normalized_digest = :digest) AS invocation_count,
  (SELECT count(*) FROM {self._nodes}
    WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id
      AND normalized_digest = :digest) AS node_count""",
                args={**key_args, "digest": record.normalized_digest},
            )
        )
        expected_invocations = 1 if projection is not None else 0
        expected_nodes = len(projection.node_results) if projection is not None else 0
        if (
            counts is None
            or _value(counts, "invocation_count") != expected_invocations
            or _value(counts, "node_count") != expected_nodes
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
                f"""SELECT normalized_digest, collector_state
FROM {self._registry}
WHERE workspace_id = :workspace_id AND dbt_task_run_id = :task_run_id""",
                args=key_args,
            )
        )
        if published is None or _value(published, "collector_state") != "PUBLISHED":
            raise RuntimeError("DBTOBSB_PUBLISH_SENTINEL_NOT_COMMITTED")
