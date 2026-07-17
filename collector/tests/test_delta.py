"""Native Delta publish-sentinel and replay tests."""

from __future__ import annotations

import io
import json
import tarfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from dbtobsb_capture import inspect_dbt_output_archive
from dbtobsb_contracts import (
    AttemptIdentity,
    demo_installed_policy,
    expected_dbt_output,
    fixed_demo_configuration_snapshot,
)

from dbtobsb_collector.bootstrap import (
    BASE_OBSERVABILITY_CONTRACT_SHA256,
    OBJECT_CONTRACT_SHA256,
    OBJECT_MANIFEST_VERSION,
    InstallationSeal,
)
from dbtobsb_collector.contracts import (
    AttemptContext,
    CollectionRecord,
    ObservedTaskEvidence,
    RetrievalState,
)
from dbtobsb_collector.delta import DeltaCollectionTracker, DeltaEvidenceSink

FIXTURES = Path(__file__).parents[2] / "capture" / "tests" / "fixtures" / "artifact_pair"


def _seal() -> InstallationSeal:
    configuration = fixed_demo_configuration_snapshot()
    return InstallationSeal(
        manifest_version=OBJECT_MANIFEST_VERSION,
        object_contract_sha256=OBJECT_CONTRACT_SHA256,
        source_contract_sha256=configuration.source_contract_sha256,
        expected_runtime_policy_sha256=configuration.expected_runtime_policy_sha256,
        base_observability_contract_sha256=BASE_OBSERVABILITY_CONTRACT_SHA256,
        installation_id="a" * 64,
        workspace_id=101,
        evidence_catalog="c",
        evidence_schema="s",
        warehouse_id="0123456789abcdef",
        observed_job_id=201,
        collector_job_id=202,
        reconciler_job_id=203,
        observed_service_principal_name="observed-sp",
        collector_service_principal_name="collector-sp",
        job_manager_group_name="job-managers",
        collector_environment_sha256="b" * 64,
    )


def _sink(spark: _Spark) -> DeltaEvidenceSink:
    return DeltaEvidenceSink(
        spark,
        catalog="c",
        schema="s",
        installation_seal=_seal(),
    )


def _tracker(spark: _Spark) -> DeltaCollectionTracker:
    return DeltaCollectionTracker(
        spark,
        catalog="c",
        schema="s",
        installation_seal=_seal(),
    )


def _capture() -> Any:
    destination = io.BytesIO()
    with tarfile.open(fileobj=destination, mode="w:gz") as archive:
        for name in ("manifest.json", "run_results.json"):
            value = (FIXTURES / "valid_success" / name).read_bytes()
            member = tarfile.TarInfo(f"target/{name}")
            member.size = len(value)
            archive.addfile(member, io.BytesIO(value))
    return inspect_dbt_output_archive(archive=destination.getvalue())


def _capture_with_deps() -> Any:
    expectation = expected_dbt_output(
        attempt=AttemptIdentity(101, 201, 301, 401, 0, 1),
        policy=replace(demo_installed_policy(), include_deps=True),
    )
    assert expectation.deps_log_member is not None
    destination = io.BytesIO()
    with tarfile.open(fileobj=destination, mode="w:gz") as archive:
        entries = [
            (
                expectation.manifest_member,
                (FIXTURES / "valid_success" / "manifest.json").read_bytes(),
            ),
            (
                expectation.run_results_member,
                (FIXTURES / "valid_success" / "run_results.json").read_bytes(),
            ),
            (
                expectation.deps_log_member,
                (
                    json.dumps(
                        {
                            "data": {"log_version": 3},
                            "info": {
                                "invocation_id": "22222222-2222-4222-8222-222222222222",
                                "name": "MainReportVersion",
                            },
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                ).encode(),
            ),
            (
                expectation.log_member,
                (
                    json.dumps(
                        {
                            "data": {"log_version": 3},
                            "info": {
                                "invocation_id": "11111111-1111-4111-8111-111111111111",
                                "name": "MainReportVersion",
                            },
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                ).encode(),
            ),
        ]
        for name, value in entries:
            member = tarfile.TarInfo(name)
            member.size = len(value)
            archive.addfile(member, io.BytesIO(value))
    return inspect_dbt_output_archive(archive=destination.getvalue(), expectation=expectation)


def _record(*, digest: str = "digest-a", capture: Any | None = None) -> CollectionRecord:
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
        capture=capture if capture is not None else _capture(),
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
    def __init__(
        self,
        *,
        root_merge_failure: str | None = None,
    ) -> None:
        self.sources: dict[str, list[dict[str, Any]]] = {}
        self.root: dict[str, Any] | None = None
        self.invocations: list[dict[str, Any]] = []
        self.nodes: dict[tuple[str, str], dict[str, Any]] = {}
        self.statements: list[str] = []
        self.root_merge_failure = root_merge_failure

    def createDataFrame(self, data: list[dict[str, Any]], schema: str) -> _DataFrame:
        assert schema
        return _DataFrame(self, data)

    def sql(self, query: str, *, args: dict[str, Any] | None = None) -> _Result:
        self.statements.append(query)
        normalized = " ".join(query.split()).upper()
        if normalized.startswith("SELECT WORKSPACE_ID, DBT_TASK_RUN_ID"):
            return _Result([self.root] if self.root is not None else [])
        if normalized.startswith("SELECT NORMALIZED_DIGEST, COLLECTOR_STATE"):
            return _Result([self.root] if self.root is not None else [])
        if normalized.startswith("SELECT COLLECTOR_STATE, COLLECTION_ATTEMPT_COUNT"):
            return _Result([self.root] if self.root is not None else [])
        if (
            normalized.startswith("MERGE INTO")
            and "DBT_ARTIFACT_REGISTRY" in normalized
            and "DBTOBSB_REGISTRY_SOURCE" not in normalized
        ):
            assert args is not None
            if self.root_merge_failure == "absent_then_raise":
                raise OSError("commit outcome unavailable")
            if self.root is None:
                self.root = {
                    "workspace_id": args["workspace_id"],
                    "dbt_task_run_id": args["task_run_id"],
                    "observed_job_id": args["observed_job_id"],
                    "observed_job_run_id": args["observed_job_run_id"],
                    "observed_task_key": args["observed_task_key"],
                    "repair_count": args["repair_count"],
                    "execution_count": args["execution_count"],
                    "normalized_digest": None,
                    "collector_state": args["initial_state"],
                    "first_discovered_at": args["first_discovered_at"],
                    "last_attempted_at": args["last_attempted_at"],
                    "collection_attempt_count": args["collection_attempt_count"],
                    "collection_issue_code": None,
                    "last_reconciliation_run_id": args["reconciliation_run_id"],
                }
            if self.root_merge_failure in {"commit_then_raise", "winner_then_raise"}:
                raise OSError("commit outcome unavailable")
            return _Result([])
        if normalized.startswith("MERGE INTO") and "DBT_ARTIFACT_REGISTRY" in normalized:
            if self.root is None or self.root["normalized_digest"] is None:
                self.root = dict(self.sources["dbtobsb_registry_source"][0])
            return _Result([])
        if normalized.startswith("MERGE INTO") and "DBT_INVOCATIONS" in normalized:
            row = self.sources["dbtobsb_invocation_source"][0]
            if not any(
                existing["normalized_digest"] == row["normalized_digest"]
                for existing in self.invocations
            ):
                self.invocations.append(dict(row))
            return _Result([])
        if normalized.startswith("MERGE INTO") and "DBT_NODE_RESULTS" in normalized:
            for row in self.sources["dbtobsb_node_source"]:
                key = (row["normalized_digest"], row["unique_id"])
                self.nodes.setdefault(key, dict(row))
            return _Result([])
        if normalized.startswith("SELECT (SELECT COUNT(*)"):
            digest = args["digest"] if args is not None else None
            invocation_matching_count = sum(
                row["normalized_digest"] == digest for row in self.invocations
            )
            node_matching_count = sum(
                row["normalized_digest"] == digest for row in self.nodes.values()
            )
            return _Result(
                [
                    {
                        "invocation_total_count": len(self.invocations),
                        "invocation_matching_count": invocation_matching_count,
                        "node_total_count": len(self.nodes),
                        "node_matching_count": node_matching_count,
                    }
                ]
            )
        if normalized.startswith("UPDATE") and "SET COLLECTOR_STATE = 'COLLECTING'" in normalized:
            assert self.root is not None and args is not None
            if self.root["collector_state"] in {"DISCOVERED", "RETRYABLE"} and (
                self.root["normalized_digest"] is not None
                or self.root["collection_attempt_count"] < 3
            ):
                self.root["collector_state"] = "COLLECTING"
                self.root["last_attempted_at"] = args["attempted_at"]
                if self.root["normalized_digest"] is None:
                    self.root["collection_attempt_count"] += 1
                self.root["collection_issue_code"] = None
            return _Result([])
        if normalized.startswith("UPDATE") and "SET COLLECTOR_STATE = CASE" in normalized:
            assert self.root is not None
            if self.root["collector_state"] == "COLLECTING":
                if "DBTOBSB_RECONCILIATION_INTERRUPTED_ATTEMPT" in normalized:
                    self.root["collector_state"] = (
                        "TERMINAL_FAILURE"
                        if self.root["normalized_digest"] is None
                        and self.root["collection_attempt_count"] >= 3
                        else "RETRYABLE"
                    )
                    self.root["collection_issue_code"] = (
                        "DBTOBSB_RECONCILIATION_INTERRUPTED_ATTEMPT"
                    )
                else:
                    assert args is not None
                    self.root["collector_state"] = (
                        "TERMINAL_FAILURE"
                        if self.root["collection_attempt_count"] >= 3
                        else "RETRYABLE"
                    )
                    self.root["collection_issue_code"] = args["issue_code"]
            return _Result([])
        if normalized.startswith("UPDATE") and "SET LAST_RECONCILIATION_RUN_ID" in normalized:
            assert self.root is not None and args is not None
            if self.root["collector_state"] != "PUBLISHED":
                self.root["last_reconciliation_run_id"] = args["reconciliation_run_id"]
            return _Result([])
        if normalized.startswith("UPDATE"):
            assert self.root is not None
            if args is not None and self.root["normalized_digest"] == args["digest"]:
                self.root["collector_state"] = "PUBLISHED"
            return _Result([])
        raise AssertionError(f"unexpected SQL shape: {normalized[:100]}")


def test_supported_collector_never_reads_a_runtime_trust_view() -> None:
    spark = _Spark()
    record = _record()

    _sink(spark).publish(record)
    assert spark.root is not None
    assert spark.root["normalized_digest"] == record.normalized_digest
    _sink(spark).publish(record)
    _tracker(spark).discover(
        record.context,
        reconciliation_run_id=501,
        discovered_at=datetime(2026, 7, 16, 9, tzinfo=UTC),
    )
    assert all("runtime_trust" not in statement.lower() for statement in spark.statements)


def test_first_root_commit_then_transport_error_is_reconciled_by_exact_readback() -> None:
    spark = _Spark(root_merge_failure="commit_then_raise")

    _sink(spark).publish(_record())

    assert spark.root is not None
    assert spark.root["collector_state"] == "PUBLISHED"


def test_first_root_error_with_proven_absence_is_indeterminate_and_never_retried() -> None:
    spark = _Spark(root_merge_failure="absent_then_raise")

    with pytest.raises(RuntimeError, match="DBTOBSB_ATTEMPT_ROOT_WRITE_INDETERMINATE"):
        _sink(spark).publish(_record())

    assert spark.root is None
    assert (
        sum(statement.lstrip().upper().startswith("MERGE INTO") for statement in spark.statements)
        == 1
    )


@pytest.mark.parametrize(
    "context",
    [
        replace(_record().context, workspace_id=999),
        replace(_record().context, observed_job_id=999),
        replace(_record().context, observed_task_key="other_task"),
    ],
    ids=("workspace", "observed-job", "task-key"),
)
@pytest.mark.parametrize("consumer", ["sink", "discover", "begin", "record_failure"])
def test_attempt_context_must_match_the_installation_seal_before_any_read(
    context: AttemptContext,
    consumer: str,
) -> None:
    spark = _Spark()

    with pytest.raises(RuntimeError, match="DBTOBSB_DELTA_ATTEMPT_BINDING_MISMATCH"):
        if consumer == "sink":
            _sink(spark).publish(replace(_record(), context=context))
        elif consumer == "discover":
            _tracker(spark).discover(
                context,
                reconciliation_run_id=501,
                discovered_at=datetime(2026, 7, 16, 9, tzinfo=UTC),
            )
        elif consumer == "begin":
            _tracker(spark).begin_attempt(
                context,
                attempted_at=datetime(2026, 7, 16, 9, tzinfo=UTC),
            )
        else:
            _tracker(spark).record_failure(
                context,
                issue_code="DBT_JOBS_TASK_RESULT_UNAVAILABLE",
            )

    assert spark.statements == []
    assert spark.root is None


def test_delta_sink_publishes_once_and_replay_is_a_noop() -> None:
    spark = _Spark()
    sink = _sink(spark)
    record = _record()

    sink.publish(record)
    first_statement_count = len(spark.statements)
    assert spark.root is not None
    assert spark.root["collector_state"] == "PUBLISHED"
    assert spark.root["structured_log_state"] == "MISSING"
    assert spark.root["structured_log_sha256"] is None
    assert spark.root["structured_log_size_bytes"] is None
    assert spark.root["structured_log_file_count"] == 0
    assert spark.root["structured_log_version"] is None
    assert spark.root["dbt_include_deps"] is False
    assert spark.root["deps_structured_log_state"] is None
    assert spark.root["deps_structured_log_sha256"] is None
    assert spark.root["deps_structured_log_size_bytes"] is None
    assert spark.root["deps_structured_log_file_count"] is None
    assert spark.root["deps_structured_log_version"] is None
    assert spark.root["structured_log_expected_dbt_common_version"] == "1.37.5"
    assert len(spark.invocations) == 1
    assert record.capture.projection is not None
    assert len(spark.nodes) == record.capture.projection.invocation.result_count

    sink.publish(record)
    assert len(spark.statements) == first_statement_count + 1
    assert all(
        keyword not in "\n".join(spark.statements).upper()
        for keyword in ("CREATE ", "REPLACE ", "ALTER ", "DROP ")
    )
    child_merges = [
        statement
        for statement in spark.statements
        if statement.lstrip().upper().startswith("MERGE INTO")
        and "DBT_ARTIFACT_REGISTRY" not in statement.upper()
    ]
    assert len(child_merges) == 2
    assert all("target.normalized_digest = source.normalized_digest" in sql for sql in child_merges)


def test_delta_sink_rejects_conflicting_replay() -> None:
    spark = _Spark()
    sink = _sink(spark)
    sink.publish(_record())

    with pytest.raises(RuntimeError, match="DBTOBSB_ATTEMPT_ROOT_CONFLICT"):
        sink.publish(_record(digest="digest-b"))


@pytest.mark.parametrize("foreign_table", ["invocations", "nodes"])
def test_delta_sink_rejects_foreign_digest_child_rows(foreign_table: str) -> None:
    spark = _Spark()
    sink = _sink(spark)
    record = _record()
    sink.publish(record)
    assert spark.root is not None
    spark.root["collector_state"] = "COLLECTING"

    if foreign_table == "invocations":
        foreign = dict(spark.invocations[0])
        foreign["normalized_digest"] = "foreign-digest"
        spark.invocations.append(foreign)
    else:
        foreign = dict(next(iter(spark.nodes.values())))
        foreign["normalized_digest"] = "foreign-digest"
        spark.nodes[(foreign["normalized_digest"], foreign["unique_id"])] = foreign

    with pytest.raises(RuntimeError, match="DBTOBSB_CHILD_READBACK_MISMATCH"):
        sink.publish(record)


def test_delta_sink_persists_each_expected_ordinal_without_raw_log_data() -> None:
    spark = _Spark()
    capture = _capture_with_deps()
    assert capture.projection is not None

    _sink(spark).publish(_record(capture=capture))

    assert spark.root is not None
    assert spark.root["dbt_include_deps"] is True
    assert spark.root["structured_log_state"] == "VALID"
    assert spark.root["structured_log_version"] == 3
    assert spark.root["structured_log_file_count"] == 1
    assert spark.root["deps_structured_log_state"] == "VALID"
    assert spark.root["deps_structured_log_version"] == 3
    assert spark.root["deps_structured_log_file_count"] == 1
    assert all("raw_log" not in key for key in spark.root)
    assert all(not isinstance(value, bytes) for value in spark.root.values())


def test_reconciliation_tracker_caps_retries_in_the_existing_registry() -> None:
    spark = _Spark()
    tracker = _tracker(spark)
    context = _record().context
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)

    state = tracker.discover(context, reconciliation_run_id=501, discovered_at=now)
    assert state.collector_state == "DISCOVERED"
    for expected_count in (1, 2, 3):
        claimed = tracker.begin_attempt(context, attempted_at=now)
        assert claimed.collection_attempt_count == expected_count
        failed = tracker.record_failure(context, issue_code="DBT_JOBS_TASK_RESULT_UNAVAILABLE")
        expected_state = "TERMINAL_FAILURE" if expected_count == 3 else "RETRYABLE"
        assert failed.collector_state == expected_state

    with pytest.raises(RuntimeError, match="DBTOBSB_RECONCILIATION_ATTEMPT_NOT_CLAIMED"):
        tracker.begin_attempt(context, attempted_at=now)


def test_reconciliation_tracker_replaces_unapproved_issue_text() -> None:
    spark = _Spark()
    context = _record().context
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)
    tracker = _tracker(spark)
    tracker.discover(context, reconciliation_run_id=501, discovered_at=now)
    tracker.begin_attempt(context, attempted_at=now)

    tracker.record_failure(context, issue_code="DBTOBSB_RECONCILIATION_native response text")

    assert spark.root is not None
    assert spark.root["collection_issue_code"] == "DBTOBSB_RECONCILIATION_COLLECTION_FAILED"


@pytest.mark.parametrize(
    "changed",
    [
        replace(_record().context, observed_job_id=999),
        replace(_record().context, observed_job_run_id=999),
        replace(_record().context, observed_task_key="different"),
        replace(_record().context, repair_count=2),
        replace(_record().context, execution_count=2),
    ],
)
def test_reconciliation_tracker_rejects_attempt_lineage_conflict(
    changed: AttemptContext,
) -> None:
    spark = _Spark()
    tracker = _tracker(spark)
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)
    tracker.discover(_record().context, reconciliation_run_id=501, discovered_at=now)

    with pytest.raises(
        RuntimeError,
        match=r"DBTOBSB_(ATTEMPT_ROOT_CONFLICT|DELTA_ATTEMPT_BINDING_MISMATCH)",
    ):
        tracker.discover(changed, reconciliation_run_id=502, discovered_at=now)


def test_stale_null_digest_claim_consumes_an_attempt_and_requeues() -> None:
    spark = _Spark()
    context = _record().context
    tracker = _tracker(spark)
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)
    tracker.discover(context, reconciliation_run_id=501, discovered_at=now)
    tracker.begin_attempt(context, attempted_at=now)

    state = tracker.discover(
        context,
        reconciliation_run_id=502,
        discovered_at=now + timedelta(minutes=21),
    )

    assert state.collector_state == "RETRYABLE"
    assert state.collection_attempt_count == 1
    reclaimed = tracker.begin_attempt(context, attempted_at=now + timedelta(minutes=21))
    assert reclaimed.collector_state == "COLLECTING"
    assert reclaimed.collection_attempt_count == 2


def test_stale_third_null_digest_claim_becomes_terminal() -> None:
    spark = _Spark()
    context = _record().context
    tracker = _tracker(spark)
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)
    tracker.discover(context, reconciliation_run_id=501, discovered_at=now)
    for _ in range(2):
        tracker.begin_attempt(context, attempted_at=now)
        tracker.record_failure(context, issue_code="DBT_JOBS_TASK_RESULT_UNAVAILABLE")
    tracker.begin_attempt(context, attempted_at=now)

    state = tracker.discover(
        context,
        reconciliation_run_id=502,
        discovered_at=now + timedelta(minutes=21),
    )

    assert state.collector_state == "TERMINAL_FAILURE"
    assert state.collection_attempt_count == 3


def test_stale_same_digest_partial_root_resumes_without_consuming_attempt() -> None:
    spark = _Spark()
    record = _record()
    tracker = _tracker(spark)
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)
    tracker.discover(record.context, reconciliation_run_id=501, discovered_at=now)
    tracker.begin_attempt(record.context, attempted_at=now)
    assert spark.root is not None
    spark.root["normalized_digest"] = record.normalized_digest

    state = tracker.discover(
        record.context,
        reconciliation_run_id=502,
        discovered_at=now + timedelta(minutes=21),
    )
    assert state.collector_state == "RETRYABLE"
    tracker.begin_attempt(record.context, attempted_at=now + timedelta(minutes=21))
    assert spark.root["collection_attempt_count"] == 1

    _sink(spark).publish(record)

    assert spark.root["collector_state"] == "PUBLISHED"


def test_published_race_is_a_benign_claim_result() -> None:
    spark = _Spark()
    record = _record()
    tracker = _tracker(spark)
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)
    tracker.discover(record.context, reconciliation_run_id=501, discovered_at=now)
    _sink(spark).publish(record)

    state = tracker.begin_attempt(record.context, attempted_at=now)

    assert state.collector_state == "PUBLISHED"


def test_successful_publish_replaces_a_discovered_registry_root() -> None:
    spark = _Spark()
    context = _record().context
    now = datetime(2026, 7, 16, 9, tzinfo=UTC)
    tracker = _tracker(spark)
    tracker.discover(context, reconciliation_run_id=501, discovered_at=now)
    tracker.begin_attempt(context, attempted_at=now)

    _sink(spark).publish(_record())

    assert spark.root is not None
    assert spark.root["collector_state"] == "PUBLISHED"
    assert spark.root["normalized_digest"] == "digest-a"
    assert spark.root["collection_attempt_count"] == 1
    assert spark.root["last_reconciliation_run_id"] == 501
