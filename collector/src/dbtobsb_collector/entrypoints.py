"""Databricks Python-wheel entrypoints with fixed bootstrap/runtime separation."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

from dbtobsb_collector.bootstrap import bootstrap_objects
from dbtobsb_collector.contracts import AttemptContext
from dbtobsb_collector.custody import VolumeRawArchiveStore
from dbtobsb_collector.delta import DeltaEvidenceSink
from dbtobsb_collector.download import HttpsArchiveDownloader
from dbtobsb_collector.jobs import DatabricksJobsEvidenceReader
from dbtobsb_collector.runtime import collect_task_run


def _active_spark() -> Any:
    spark_module = importlib.import_module("pyspark.sql")
    session_type = spark_module.SparkSession
    session = session_type.getActiveSession()
    if session is None:
        session = session_type.builder.getOrCreate()
    return session


def _positive_integer(value: str, *, field: str, allow_zero: bool = False) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a resolved decimal integer") from None
    minimum = 0 if allow_zero else 1
    if parsed < minimum or str(parsed) != value:
        raise ValueError(f"{field} must be a canonical resolved decimal integer")
    return parsed


def _run_bootstrap(*, catalog: str, schema: str, raw_volume_name: str) -> None:
    result = bootstrap_objects(
        _active_spark(), catalog=catalog, schema=schema, raw_volume_name=raw_volume_name
    )
    print(
        json.dumps(
            {
                "event": "dbtobsb_bootstrap_verified",
                "manifest_version": result.manifest_version,
                "object_count": len(result.verified_objects),
            },
            sort_keys=True,
        )
    )


def _run_collect(
    *,
    workspace_id: str,
    observed_job_id: str,
    observed_job_run_id: str,
    dbt_task_run_id: str,
    observed_task_key: str,
    repair_count: str,
    execution_count: str,
    catalog: str,
    schema: str,
    raw_volume_name: str = "dbtobsb_raw",
) -> None:
    context = AttemptContext(
        workspace_id=_positive_integer(workspace_id, field="workspace_id"),
        observed_job_id=_positive_integer(observed_job_id, field="observed_job_id"),
        observed_job_run_id=_positive_integer(observed_job_run_id, field="observed_job_run_id"),
        dbt_task_run_id=_positive_integer(dbt_task_run_id, field="dbt_task_run_id"),
        observed_task_key=observed_task_key,
        repair_count=_positive_integer(repair_count, field="repair_count", allow_zero=True),
        execution_count=_positive_integer(execution_count, field="execution_count"),
    )
    spark = _active_spark()
    record = collect_task_run(
        context=context,
        jobs=DatabricksJobsEvidenceReader(),
        downloader=HttpsArchiveDownloader(),
        raw_store=VolumeRawArchiveStore(
            f"/Volumes/{catalog}/{schema}/{raw_volume_name}", require_volume=True
        ),
        sink=DeltaEvidenceSink(spark, catalog=catalog, schema=schema),
    )
    print(
        json.dumps(
            {
                "event": "dbtobsb_collection_published",
                "capture_state": record.capture.capture_state.value,
                "retrieval_state": record.retrieval_state.value,
                "pair_state": (
                    record.capture.pair_report.state.value
                    if record.capture.pair_report is not None
                    else None
                ),
                "node_count": (
                    len(record.capture.projection.node_results)
                    if record.capture.projection is not None
                    else 0
                ),
            },
            sort_keys=True,
        )
    )


def bootstrap() -> None:
    """Parse fixed bootstrap arguments passed by the Databricks wheel runner."""
    parser = argparse.ArgumentParser(prog="dbtobsb-bootstrap", allow_abbrev=False)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--raw_volume_name", default="dbtobsb_raw")
    arguments = parser.parse_args()
    _run_bootstrap(
        catalog=arguments.catalog,
        schema=arguments.schema,
        raw_volume_name=arguments.raw_volume_name,
    )


def collect() -> None:
    """Parse fixed runtime arguments passed by the Databricks wheel runner."""
    parser = argparse.ArgumentParser(prog="dbtobsb-collect", allow_abbrev=False)
    for name in (
        "workspace_id",
        "observed_job_id",
        "observed_job_run_id",
        "dbt_task_run_id",
        "observed_task_key",
        "repair_count",
        "execution_count",
        "catalog",
        "schema",
    ):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--raw_volume_name", default="dbtobsb_raw")
    arguments = parser.parse_args()
    _run_collect(
        workspace_id=arguments.workspace_id,
        observed_job_id=arguments.observed_job_id,
        observed_job_run_id=arguments.observed_job_run_id,
        dbt_task_run_id=arguments.dbt_task_run_id,
        observed_task_key=arguments.observed_task_key,
        repair_count=arguments.repair_count,
        execution_count=arguments.execution_count,
        catalog=arguments.catalog,
        schema=arguments.schema,
        raw_volume_name=arguments.raw_volume_name,
    )


def main() -> None:
    """Explain the two fixed entrypoints without exposing a dynamic command surface."""
    print("Use the fixed Databricks wheel entrypoint 'bootstrap' or 'collect'.")
