"""Fixed SQL and unified-auth repository tests."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

import pytest

from dbtobsb_app.configuration import resolve_bindings
from dbtobsb_app.repository import (
    COLLECTION_COLUMNS,
    NODE_COLUMNS,
    RUN_COLUMNS,
    TREND_COLUMNS,
    AppDataAccessError,
    DatabricksSqlRepository,
    databricks_repository,
)


def _bindings():
    return resolve_bindings(
        {
            "DBTOBSB_WAREHOUSE_ID": "0123456789abcdef",
            "DBTOBSB_RUN_HEALTH_VIEW": "customer-catalog.obs.dbt_run_health",
            "DBTOBSB_NODE_HEALTH_VIEW": "customer-catalog.obs.dbt_node_health",
            "DBTOBSB_COLLECTION_HEALTH_VIEW": ("customer-catalog.obs.dbt_collection_health"),
        }
    )


def _run_values(*, logs_truncated: bool | None = False) -> tuple[Any, ...]:
    now = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    return (
        1234567890123456,
        20,
        30,
        40,
        "dbt_build",
        0,
        1,
        1,
        now,
        now,
        "SUCCESS",
        "RETRIEVED",
        "COMPLETE",
        "PAIR_VALID",
        False,
        None,
        logs_truncated,
        "VALID",
        None,
        "1.37.5",
        "invocation-id",
        3,
        now,
        now,
        now,
        1.25,
        "1.11.12",
        "databricks",
        3,
    )


def _node_values() -> tuple[Any, ...]:
    return (
        1234567890123456,
        20,
        30,
        40,
        "dbt_build",
        "COMPLETE",
        "SUCCESS",
        "invocation-id",
        "model.weather.daily",
        "model",
        "success",
        0.2,
        None,
    )


def _collection_values() -> tuple[Any, ...]:
    now = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    return (
        1234567890123456,
        20,
        30,
        40,
        "dbt_build",
        0,
        1,
        1,
        now,
        now,
        "SUCCESS",
        "PUBLISHED",
        None,
        now,
        now,
        1,
        now,
        50,
    )


def _trend_values() -> tuple[Any, ...]:
    return (
        40,
        datetime(2026, 7, 16, 10, 0, tzinfo=UTC),
        2,
        7,
    )


class FakeCursor:
    def __init__(self, rows: list[tuple[Any, ...]], calls: list[tuple[str, dict[str, int]]]):
        self._rows = rows
        self._calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, operation: str, parameters: dict[str, int]) -> None:
        self._calls.append((operation, parameters))

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self._rows


class FakeConnection:
    def __init__(self, rows: list[tuple[Any, ...]], calls: list[tuple[str, dict[str, int]]]):
        self._rows = rows
        self._calls = calls

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._rows, self._calls)


def test_run_query_is_fixed_quoted_parameterized_and_allowlisted() -> None:
    calls: list[tuple[str, dict[str, int]]] = []
    repository = DatabricksSqlRepository(
        _bindings(), lambda: FakeConnection([_run_values()], calls)
    )

    rows = repository.recent_runs(17)

    assert rows[0].observed_job_run_id == 40
    query, parameters = calls[0]
    assert "FROM `customer-catalog`.`obs`.`dbt_run_health`" in query
    assert query.endswith("LIMIT :limit")
    assert parameters == {"limit": 17}
    assert all(f"`{column}`" in query for column in RUN_COLUMNS)
    assert "runtime_trust" not in query
    for forbidden in (
        "raw_archive_locator",
        "archive_sha256",
        "manifest_sha256",
        "run_results_sha256",
        "command",
        "status_counts_json",
        "message",
        "compiled_code",
    ):
        assert forbidden not in query


def test_node_query_is_fixed_quoted_parameterized_and_allowlisted() -> None:
    calls: list[tuple[str, dict[str, int]]] = []
    repository = DatabricksSqlRepository(
        _bindings(), lambda: FakeConnection([_node_values()], calls)
    )

    rows = repository.recent_nodes(9)

    assert rows[0].unique_id == "model.weather.daily"
    query, parameters = calls[0]
    assert "FROM `customer-catalog`.`obs`.`dbt_node_health`" in query
    assert parameters == {"limit": 9}
    assert all(f"`{column}`" in query for column in NODE_COLUMNS)
    assert "raw" not in query.lower()
    assert "message" not in query.lower()


def test_collection_query_is_fixed_quoted_parameterized_and_allowlisted() -> None:
    calls: list[tuple[str, dict[str, int]]] = []
    repository = DatabricksSqlRepository(
        _bindings(), lambda: FakeConnection([_collection_values()], calls)
    )

    rows = repository.recent_collection(11)

    assert rows[0].collector_state == "PUBLISHED"
    query, parameters = calls[0]
    assert "FROM `customer-catalog`.`obs`.`dbt_collection_health`" in query
    assert parameters == {"limit": 11}
    assert all(f"`{column}`" in query for column in COLLECTION_COLUMNS)
    assert "runtime_trust" not in query
    for forbidden in ("raw_archive_locator", "archive_sha256", "message", "compiled_code"):
        assert forbidden not in query


def test_trend_query_is_fixed_parameterized_and_uses_only_sanitized_views() -> None:
    calls: list[tuple[str, dict[str, int]]] = []
    repository = DatabricksSqlRepository(
        _bindings(), lambda: FakeConnection([_trend_values()], calls)
    )

    rows = repository.recent_trends(12)

    assert rows[0].failed_node_results == 2
    assert rows[0].model_results == 7
    query, parameters = calls[0]
    assert "FROM `customer-catalog`.`obs`.`dbt_run_health`" in query
    assert "LEFT JOIN `customer-catalog`.`obs`.`dbt_node_health`" in query
    assert "`pair_state` = 'PAIR_VALID'" in query
    for column in (
        "workspace_id",
        "observed_job_id",
        "observed_job_run_id",
        "dbt_task_run_id",
        "observed_task_key",
    ):
        assert f"n.`{column}` = r.`{column}`" in query
    assert "n.`status` IN ('error', 'fail')" in query
    assert "n.`resource_type` = 'model'" in query
    assert "GROUP BY r.`workspace_id`, r.`observed_job_id`, r.`observed_job_run_id`" in query
    assert "LIMIT :limit" in query
    assert parameters == {"limit": 12}
    assert all(f"`{column}`" in query for column in TREND_COLUMNS)
    for forbidden in (
        "raw_archive_locator",
        "archive_sha256",
        "manifest_sha256",
        "run_results_sha256",
        "compiled_code",
        "message",
    ):
        assert forbidden not in query


class _SqliteCursor:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._cursor = connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        self._cursor.close()

    def execute(self, operation: str, parameters: dict[str, int]) -> None:
        translated = operation.replace(
            "`customer-catalog`.`obs`.`dbt_run_health`", "run_health"
        ).replace("`customer-catalog`.`obs`.`dbt_node_health`", "node_health")
        self._cursor.execute(translated, parameters)

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self._cursor.fetchall()


class _SqliteConnection:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(self) -> _SqliteCursor:
        return _SqliteCursor(self._connection)


def _trend_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
    connection.execute(
        """CREATE TABLE run_health (
          workspace_id INTEGER, observed_job_id INTEGER, observed_job_run_id INTEGER,
          dbt_task_run_id INTEGER, observed_task_key TEXT, generated_at TIMESTAMP, pair_state TEXT
        )"""
    )
    connection.execute(
        """CREATE TABLE node_health (
          workspace_id INTEGER, observed_job_id INTEGER, observed_job_run_id INTEGER,
          dbt_task_run_id INTEGER, observed_task_key TEXT, resource_type TEXT, status TEXT
        )"""
    )
    connection.executemany(
        "INSERT INTO run_health VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            (1, 30, 100, 10, "dbt_build", datetime(2026, 7, 16, 8, 0), "PAIR_VALID"),
            (1, 30, 200, 20, "dbt_build", datetime(2026, 7, 16, 9, 0), "PAIR_VALID"),
            (1, 30, 200, 21, "dbt_build", datetime(2026, 7, 16, 9, 0), "PAIR_VALID"),
            (1, 30, 300, 30, "dbt_build", datetime(2026, 7, 16, 10, 0), "PAIR_VALID"),
            (1, 30, 400, 40, "dbt_build", datetime(2026, 7, 16, 11, 0), "PAIR_REJECTED"),
        ),
    )
    nodes = [
        (1, 30, 100, 10, "dbt_build", "model", "success"),
        (1, 30, 200, 20, "dbt_build", "model", "success"),
        (1, 30, 200, 20, "dbt_build", "model", "error"),
        (1, 30, 200, 20, "dbt_build", "test", "fail"),
        (1, 30, 200, 20, "dbt_build", "test", "warn"),
        (1, 30, 200, 20, "dbt_build", "seed", "error"),
        (1, 30, 400, 40, "dbt_build", "model", "error"),
    ]
    base = (1, 30, 200, 20, "dbt_build", "model", "error")
    for index, replacement in enumerate((2, 31, 201, 99, "other")):
        candidate = list(base)
        candidate[index] = replacement
        nodes.append(tuple(candidate))
    connection.executemany("INSERT INTO node_health VALUES (?, ?, ?, ?, ?, ?, ?)", nodes)
    return connection


def _execute_trend_sql(
    connection: sqlite3.Connection, query: str, *, limit: int = 3
) -> tuple[tuple[Any, ...], ...]:
    translated = query.replace("`customer-catalog`.`obs`.`dbt_run_health`", "run_health").replace(
        "`customer-catalog`.`obs`.`dbt_node_health`", "node_health"
    )
    return tuple(connection.execute(translated, {"limit": limit}).fetchall())


def test_complete_production_trend_path_is_bounded_and_semantically_exact() -> None:
    connection = _trend_database()
    repository = DatabricksSqlRepository(_bindings(), lambda: _SqliteConnection(connection))

    rows = repository.recent_trends(3)

    assert [
        (row.observed_job_run_id, row.failed_node_results, row.model_results) for row in rows
    ] == [
        (200, 3, 2),
        (200, 0, 0),
        (300, 0, 0),
    ]
    assert len(rows) == 3


@pytest.mark.parametrize(
    "mutate",
    [
        lambda query: query.replace("  WHERE `pair_state` = 'PAIR_VALID'\n", ""),
        lambda query: query.replace("LIMIT :limit", "LIMIT :limit + 1"),
        lambda query: query.replace("`generated_at` DESC", "`generated_at` ASC"),
        lambda query: query.replace("n.`workspace_id` = r.`workspace_id`", "1 = 1"),
        lambda query: query.replace("n.`observed_job_id` = r.`observed_job_id`", "1 = 1"),
        lambda query: query.replace("n.`observed_job_run_id` = r.`observed_job_run_id`", "1 = 1"),
        lambda query: query.replace("n.`dbt_task_run_id` = r.`dbt_task_run_id`", "1 = 1"),
        lambda query: query.replace("n.`observed_task_key` = r.`observed_task_key`", "1 = 1"),
        lambda query: query.replace("('error', 'fail')", "('fail')"),
        lambda query: query.replace("n.`resource_type` = 'model'", "n.`resource_type` = 'seed'"),
        lambda query: query.replace(
            "  r.`dbt_task_run_id`, r.`observed_task_key`", "  r.`observed_task_key`"
        ),
    ],
)
def test_trend_sql_contract_is_mutation_sensitive(mutate: Any) -> None:
    connection = _trend_database()
    repository = DatabricksSqlRepository(_bindings(), lambda: _SqliteConnection(connection))
    expected = _execute_trend_sql(connection, repository._trends_query)

    assert _execute_trend_sql(connection, mutate(repository._trends_query)) != expected


def test_each_read_uses_and_closes_a_fresh_connection() -> None:
    counts = {"opened": 0, "closed": 0}
    calls: list[tuple[str, dict[str, int]]] = []

    class CountedConnection(FakeConnection):
        def __enter__(self):
            counts["opened"] += 1
            return self

        def __exit__(self, *args: object) -> None:
            counts["closed"] += 1

    repository = DatabricksSqlRepository(_bindings(), lambda: CountedConnection([], calls))
    repository.recent_runs(1)
    repository.recent_runs(1)

    assert counts == {"opened": 2, "closed": 2}


def test_unexpected_view_shape_is_rejected() -> None:
    repository = DatabricksSqlRepository(
        _bindings(), lambda: FakeConnection([_run_values()[:-1]], [])
    )

    with pytest.raises(AppDataAccessError, match="DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH"):
        repository.recent_runs(1)


def test_unexpected_trend_shape_is_rejected() -> None:
    repository = DatabricksSqlRepository(
        _bindings(), lambda: FakeConnection([_trend_values()[:-1]], [])
    )

    with pytest.raises(AppDataAccessError, match="DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH"):
        repository.recent_trends(1)


def test_connector_failure_is_reclassified_without_response_text() -> None:
    canary = "jdbc secret warehouse permission response"

    def fail() -> FakeConnection:
        raise RuntimeError(canary)

    repository = DatabricksSqlRepository(_bindings(), fail)

    with pytest.raises(AppDataAccessError) as exc_info:
        repository.recent_runs(1)

    assert str(exc_info.value) == "DBTOBSB_APP_QUERY_FAILED"
    assert canary not in repr(exc_info.value)


def test_run_view_model_drift_has_run_specific_category() -> None:
    values = list(_run_values())
    values[26] = "unexpected-dbt-version"
    repository = DatabricksSqlRepository(_bindings(), lambda: FakeConnection([tuple(values)], []))

    with pytest.raises(AppDataAccessError, match="DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH"):
        repository.recent_runs(1)


def test_nullable_jobs_log_truncation_is_a_supported_view_value() -> None:
    repository = DatabricksSqlRepository(
        _bindings(), lambda: FakeConnection([_run_values(logs_truncated=None)], [])
    )

    assert repository.recent_runs(1)[0].logs_truncated is None


@pytest.mark.parametrize("limit", [0, 101, True])
def test_repository_defensively_rejects_unbounded_limits(limit: int) -> None:
    connection_opened = False

    def connection() -> FakeConnection:
        nonlocal connection_opened
        connection_opened = True
        return FakeConnection([], [])

    repository = DatabricksSqlRepository(_bindings(), connection)

    with pytest.raises(ValueError, match="DBTOBSB_QUERY_LIMIT_INVALID"):
        repository.recent_runs(limit)
    assert connection_opened is False


def test_repository_refuses_unresolved_bindings() -> None:
    with pytest.raises(ValueError, match="DBTOBSB_APP_BINDINGS_NOT_READY"):
        DatabricksSqlRepository(resolve_bindings({}), lambda: FakeConnection([], []))


def test_default_factory_uses_config_and_service_principal_credential_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    marker = object()

    class FakeConfig:
        host = "https://workspace.azuredatabricks.net"
        authenticate = marker
        auth_type = "oauth-m2m"
        client_id = "app-service-principal"
        client_secret = "injected-secret"
        token = None

    monkeypatch.setattr("dbtobsb_app.repository.Config", FakeConfig)

    def connect(**kwargs: Any) -> FakeConnection:
        calls.append(kwargs)
        return FakeConnection([], [])

    monkeypatch.setattr("dbtobsb_app.repository.sql.connect", connect)
    repository = databricks_repository(_bindings())
    repository.recent_runs(1)

    assert calls[0]["server_hostname"] == "https://workspace.azuredatabricks.net"
    assert calls[0]["http_path"] == "/sql/1.0/warehouses/0123456789abcdef"
    assert calls[0]["credentials_provider"]() is marker
    assert calls[0]["enable_telemetry"] == 0
    assert type(calls[0]["enable_telemetry"]) is int
    assert "access_token" not in calls[0]
    assert "token" not in calls[0]


@pytest.mark.parametrize(
    ("auth_type", "client_id", "client_secret", "token"),
    [
        ("pat", None, None, "pat-canary"),
        ("oauth-m2m", None, "secret", None),
        ("oauth-m2m", "client", None, None),
        ("azure-cli", None, None, None),
    ],
)
def test_default_factory_rejects_non_app_authentication(
    monkeypatch: pytest.MonkeyPatch,
    auth_type: str,
    client_id: str | None,
    client_secret: str | None,
    token: str | None,
) -> None:
    class FakeConfig:
        host = "https://workspace.azuredatabricks.net"
        authenticate = object()

        def __init__(self) -> None:
            self.auth_type = auth_type
            self.client_id = client_id
            self.client_secret = client_secret
            self.token = token

    monkeypatch.setattr("dbtobsb_app.repository.Config", FakeConfig)

    with pytest.raises(AppDataAccessError, match="DBTOBSB_APP_AUTH_INVALID"):
        databricks_repository(_bindings())
