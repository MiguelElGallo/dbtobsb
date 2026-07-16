"""Fixed one-shot Unity Catalog bootstrap for the engineering preview."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from dbtobsb_collector.naming import qualify, quote_identifier

REGISTRY_TABLE = "dbt_artifact_registry"
INVOCATIONS_TABLE = "dbt_invocations"
NODE_RESULTS_TABLE = "dbt_node_results"
RUN_HEALTH_VIEW = "dbt_run_health"
NODE_HEALTH_VIEW = "dbt_node_health"
OBJECT_MANIFEST_VERSION = "dbtobsb.evidence.v0.2.0-alpha.1"


class SparkBootstrapSession(Protocol):
    """Small Spark surface used by the fixed bootstrap entrypoint."""

    def sql(self, query: str) -> Any: ...

    def table(self, table_name: str) -> Any: ...


@dataclass(frozen=True, slots=True)
class ObjectSpec:
    """Expected visible schema for one table or view."""

    name: str
    fields: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Verified object-manifest result."""

    manifest_version: str
    verified_objects: tuple[str, ...]
    raw_volume: str


REGISTRY_FIELDS: tuple[tuple[str, str], ...] = (
    ("workspace_id", "bigint"),
    ("dbt_task_run_id", "bigint"),
    ("observed_job_id", "bigint"),
    ("observed_job_run_id", "bigint"),
    ("observed_task_key", "string"),
    ("repair_count", "int"),
    ("execution_count", "int"),
    ("attempt_number", "int"),
    ("task_start_time", "timestamp"),
    ("task_end_time", "timestamp"),
    ("lakeflow_result_state", "string"),
    ("retrieval_state", "string"),
    ("capture_state", "string"),
    ("pair_state", "string"),
    ("issue_code", "string"),
    ("logs_truncated", "boolean"),
    ("archive_sha256", "string"),
    ("archive_size_bytes", "bigint"),
    ("raw_archive_locator", "string"),
    ("manifest_sha256", "string"),
    ("manifest_size_bytes", "bigint"),
    ("run_results_sha256", "string"),
    ("run_results_size_bytes", "bigint"),
    ("invocation_id", "string"),
    ("expected_node_count", "bigint"),
    ("normalized_digest", "string"),
    ("collector_state", "string"),
    ("collected_at", "timestamp"),
    ("published_at", "timestamp"),
)

INVOCATION_FIELDS: tuple[tuple[str, str], ...] = (
    ("workspace_id", "bigint"),
    ("dbt_task_run_id", "bigint"),
    ("invocation_id", "string"),
    ("generated_at", "timestamp"),
    ("elapsed_time", "double"),
    ("dbt_version", "string"),
    ("adapter_type", "string"),
    ("command", "string"),
    ("result_count", "bigint"),
    ("status_counts_json", "string"),
    ("normalized_digest", "string"),
)

NODE_FIELDS: tuple[tuple[str, str], ...] = (
    ("workspace_id", "bigint"),
    ("dbt_task_run_id", "bigint"),
    ("invocation_id", "string"),
    ("unique_id", "string"),
    ("resource_type", "string"),
    ("status", "string"),
    ("execution_time", "double"),
    ("failures", "bigint"),
    ("normalized_digest", "string"),
)

RUN_VIEW_FIELDS: tuple[tuple[str, str], ...] = tuple(
    field for field in REGISTRY_FIELDS if field[0] not in {"raw_archive_locator", "collector_state"}
) + tuple(field for field in INVOCATION_FIELDS[3:-1])

NODE_VIEW_FIELDS: tuple[tuple[str, str], ...] = (
    ("workspace_id", "bigint"),
    ("dbt_task_run_id", "bigint"),
    ("observed_job_id", "bigint"),
    ("observed_job_run_id", "bigint"),
    ("observed_task_key", "string"),
    ("capture_state", "string"),
    ("lakeflow_result_state", "string"),
    ("invocation_id", "string"),
    ("unique_id", "string"),
    ("resource_type", "string"),
    ("status", "string"),
    ("execution_time", "double"),
    ("failures", "bigint"),
)


def _column_sql(fields: tuple[tuple[str, str], ...]) -> str:
    return ",\n  ".join(
        f"{quote_identifier(name)} {data_type.upper()}" for name, data_type in fields
    )


def _actual_fields(spark: SparkBootstrapSession, name: str) -> tuple[tuple[str, str], ...]:
    schema = spark.table(name).schema
    return tuple((field.name, field.dataType.simpleString().lower()) for field in schema.fields)


def _verify_fields(
    spark: SparkBootstrapSession,
    *,
    fully_qualified_name: str,
    expected: tuple[tuple[str, str], ...],
) -> None:
    if _actual_fields(spark, fully_qualified_name) != expected:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_SCHEMA_MISMATCH")


def bootstrap_objects(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
    raw_volume_name: str = "dbtobsb_raw",
) -> BootstrapResult:
    """Create missing fixed objects and fail if any visible schema is incompatible."""
    schema_name = f"{quote_identifier(catalog)}.{quote_identifier(schema)}"
    registry = qualify(catalog, schema, REGISTRY_TABLE)
    invocations = qualify(catalog, schema, INVOCATIONS_TABLE)
    nodes = qualify(catalog, schema, NODE_RESULTS_TABLE)
    run_view = qualify(catalog, schema, RUN_HEALTH_VIEW)
    node_view = qualify(catalog, schema, NODE_HEALTH_VIEW)
    volume = qualify(catalog, schema, raw_volume_name)

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    for name, fields in (
        (registry, REGISTRY_FIELDS),
        (invocations, INVOCATION_FIELDS),
        (nodes, NODE_FIELDS),
    ):
        spark.sql(f"CREATE TABLE IF NOT EXISTS {name} (\n  {_column_sql(fields)}\n) USING DELTA")
        _verify_fields(spark, fully_qualified_name=name, expected=fields)

    spark.sql(f"CREATE VOLUME IF NOT EXISTS {volume}")
    spark.sql(
        f"""CREATE VIEW IF NOT EXISTS {run_view} AS
SELECT
  r.* EXCEPT (raw_archive_locator, collector_state),
  i.generated_at,
  i.elapsed_time,
  i.dbt_version,
  i.adapter_type,
  i.command,
  i.result_count,
  i.status_counts_json
FROM {registry} AS r
LEFT JOIN {invocations} AS i
  USING (workspace_id, dbt_task_run_id)
WHERE r.collector_state = 'PUBLISHED'"""
    )
    spark.sql(
        f"""CREATE VIEW IF NOT EXISTS {node_view} AS
SELECT
  r.workspace_id,
  r.dbt_task_run_id,
  r.observed_job_id,
  r.observed_job_run_id,
  r.observed_task_key,
  r.capture_state,
  r.lakeflow_result_state,
  n.invocation_id,
  n.unique_id,
  n.resource_type,
  n.status,
  n.execution_time,
  n.failures
FROM {registry} AS r
INNER JOIN {nodes} AS n
  USING (workspace_id, dbt_task_run_id)
WHERE r.collector_state = 'PUBLISHED'"""
    )
    _verify_fields(spark, fully_qualified_name=run_view, expected=RUN_VIEW_FIELDS)
    _verify_fields(spark, fully_qualified_name=node_view, expected=NODE_VIEW_FIELDS)
    return BootstrapResult(
        manifest_version=OBJECT_MANIFEST_VERSION,
        verified_objects=(registry, invocations, nodes, run_view, node_view),
        raw_volume=volume,
    )
