"""Fixed SQL and unified-auth repository tests."""

from __future__ import annotations

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
    assert "n.`status` IN ('error', 'fail')" in query
    assert "n.`resource_type` = 'model'" in query
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
