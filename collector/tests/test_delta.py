"""Native Delta publish-sentinel and replay tests."""

from __future__ import annotations

import io
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from dbtobsb_capture import inspect_dbt_output_archive

from dbtobsb_collector.contracts import (
    AttemptContext,
    CollectionRecord,
    ObservedTaskEvidence,
    RetrievalState,
)
from dbtobsb_collector.delta import DeltaEvidenceSink

FIXTURES = Path(__file__).parents[2] / "capture" / "tests" / "fixtures" / "artifact_pair"


def _capture() -> Any:
    destination = io.BytesIO()
    with tarfile.open(fileobj=destination, mode="w:gz") as archive:
        for name in ("manifest.json", "run_results.json"):
            value = (FIXTURES / "valid_success" / name).read_bytes()
            member = tarfile.TarInfo(f"target/{name}")
            member.size = len(value)
            archive.addfile(member, io.BytesIO(value))
    return inspect_dbt_output_archive(archive=destination.getvalue())


def _record(*, digest: str = "digest-a") -> CollectionRecord:
    return CollectionRecord(
        context=AttemptContext(101, 201, 301, 401, "dbt_build", 0, 1),
        observed=ObservedTaskEvidence(
            task_start_time=datetime(2026, 7, 16, 8, tzinfo=UTC),
            task_end_time=datetime(2026, 7, 16, 8, 1, tzinfo=UTC),
            lakeflow_result_state="SUCCESS",
            attempt_number=0,
            logs_truncated=False,
            artifact_reference=None,
        ),
        retrieval_state=RetrievalState.RETRIEVED,
        capture=_capture(),
        raw_archive_locator="/Volumes/c/s/v/raw/101/401/hash.tar.gz",
        collected_at=datetime(2026, 7, 16, 9, tzinfo=UTC),
        normalized_digest=digest,
    )


class _Result:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def collect(self) -> list[dict[str, Any]]:
        return self._rows


class _DataFrame:
    def __init__(self, spark: _Spark, rows: list[dict[str, Any]]) -> None:
        self._spark = spark
        self._rows = rows

    def createOrReplaceTempView(self, name: str) -> None:
        self._spark.sources[name] = self._rows


class _Spark:
    def __init__(self) -> None:
        self.sources: dict[str, list[dict[str, Any]]] = {}
        self.root: dict[str, Any] | None = None
        self.invocation: dict[str, Any] | None = None
        self.nodes: dict[str, dict[str, Any]] = {}
        self.statements: list[str] = []

    def createDataFrame(self, data: list[dict[str, Any]], schema: str) -> _DataFrame:
        assert schema
        return _DataFrame(self, data)

    def sql(self, query: str, *, args: dict[str, Any] | None = None) -> _Result:
        self.statements.append(query)
        normalized = " ".join(query.split()).upper()
        if normalized.startswith("SELECT NORMALIZED_DIGEST, COLLECTOR_STATE"):
            return _Result([self.root] if self.root is not None else [])
        if normalized.startswith("MERGE INTO") and "DBT_ARTIFACT_REGISTRY" in normalized:
            if self.root is None:
                self.root = dict(self.sources["dbtobsb_registry_source"][0])
            return _Result([])
        if normalized.startswith("MERGE INTO") and "DBT_INVOCATIONS" in normalized:
            if self.invocation is None:
                self.invocation = dict(self.sources["dbtobsb_invocation_source"][0])
            return _Result([])
        if normalized.startswith("MERGE INTO") and "DBT_NODE_RESULTS" in normalized:
            for row in self.sources["dbtobsb_node_source"]:
                self.nodes.setdefault(row["unique_id"], dict(row))
            return _Result([])
        if normalized.startswith("SELECT (SELECT COUNT(*)"):
            digest = args["digest"] if args is not None else None
            invocation_count = int(
                self.invocation is not None and self.invocation["normalized_digest"] == digest
            )
            node_count = sum(row["normalized_digest"] == digest for row in self.nodes.values())
            return _Result([{"invocation_count": invocation_count, "node_count": node_count}])
        if normalized.startswith("UPDATE"):
            assert self.root is not None
            if args is not None and self.root["normalized_digest"] == args["digest"]:
                self.root["collector_state"] = "PUBLISHED"
            return _Result([])
        raise AssertionError(f"unexpected SQL shape: {normalized[:100]}")


def test_delta_sink_publishes_once_and_replay_is_a_noop() -> None:
    spark = _Spark()
    sink = DeltaEvidenceSink(spark, catalog="c", schema="s")
    record = _record()

    sink.publish(record)
    first_statement_count = len(spark.statements)
    assert spark.root is not None
    assert spark.root["collector_state"] == "PUBLISHED"
    assert spark.invocation is not None
    assert record.capture.projection is not None
    assert len(spark.nodes) == record.capture.projection.invocation.result_count

    sink.publish(record)
    assert len(spark.statements) == first_statement_count + 1
    assert all(
        keyword not in "\n".join(spark.statements).upper()
        for keyword in ("CREATE ", "REPLACE ", "ALTER ", "DROP ")
    )


def test_delta_sink_rejects_conflicting_replay() -> None:
    spark = _Spark()
    sink = DeltaEvidenceSink(spark, catalog="c", schema="s")
    sink.publish(_record())

    with pytest.raises(RuntimeError, match="DBTOBSB_ATTEMPT_ROOT_CONFLICT"):
        sink.publish(_record(digest="digest-b"))
