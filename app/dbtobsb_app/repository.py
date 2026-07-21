"""Fixed-query Databricks SQL repository for sanitized observability views."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol, cast

from databricks import sql
from databricks.sdk.core import Config
from pydantic import ValidationError

from dbtobsb_app.configuration import ResourceBindings
from dbtobsb_app.models import CollectionHealth, NodeHealth, RunHealth, TrendPoint

MAX_LIMIT = 100
DEFAULT_LIMIT = 25

RUN_COLUMNS: tuple[str, ...] = (
    "workspace_id",
    "dbt_task_run_id",
    "observed_job_id",
    "observed_job_run_id",
    "observed_task_key",
    "repair_count",
    "execution_count",
    "attempt_number",
    "task_start_time",
    "task_end_time",
    "lakeflow_result_state",
    "retrieval_state",
    "capture_state",
    "pair_state",
    "dbt_include_deps",
    "issue_code",
    "logs_truncated",
    "structured_log_state",
    "deps_structured_log_state",
    "structured_log_expected_dbt_common_version",
    "invocation_id",
    "expected_node_count",
    "collected_at",
    "published_at",
    "generated_at",
    "elapsed_time",
    "dbt_version",
    "adapter_type",
    "result_count",
)

NODE_COLUMNS: tuple[str, ...] = (
    "workspace_id",
    "dbt_task_run_id",
    "observed_job_id",
    "observed_job_run_id",
    "observed_task_key",
    "capture_state",
    "lakeflow_result_state",
    "invocation_id",
    "unique_id",
    "resource_type",
    "status",
    "execution_time",
    "failures",
)

COLLECTION_COLUMNS: tuple[str, ...] = (
    "workspace_id",
    "dbt_task_run_id",
    "observed_job_id",
    "observed_job_run_id",
    "observed_task_key",
    "repair_count",
    "execution_count",
    "attempt_number",
    "task_start_time",
    "task_end_time",
    "lakeflow_result_state",
    "collector_state",
    "collection_issue_code",
    "first_discovered_at",
    "last_attempted_at",
    "collection_attempt_count",
    "published_at",
    "last_reconciliation_run_id",
)

TREND_COLUMNS: tuple[str, ...] = (
    "observed_job_run_id",
    "observed_at",
    "failed_node_results",
    "model_results",
)
TREND_SOURCE_COLUMNS: tuple[str, ...] = (
    "observed_job_run_id",
    "dbt_task_run_id",
    "observed_at",
    "pair_state",
    "resource_type",
    "status",
)


class ObservabilityRepository(Protocol):
    """Read-only dependency injected into HTTP handlers."""

    def recent_runs(self, limit: int) -> tuple[RunHealth, ...]: ...

    def recent_nodes(self, limit: int) -> tuple[NodeHealth, ...]: ...

    def recent_collection(self, limit: int) -> tuple[CollectionHealth, ...]: ...

    def recent_trends(self, limit: int) -> tuple[TrendPoint, ...]: ...


class Cursor(Protocol):
    """Minimal SQL cursor used by this repository."""

    def __enter__(self) -> Cursor: ...

    def __exit__(self, *args: object) -> None: ...

    def execute(self, operation: str, parameters: dict[str, int]) -> object: ...

    def fetchall(self) -> Sequence[Sequence[Any]]: ...


class Connection(Protocol):
    """Minimal SQL connection used by this repository."""

    def __enter__(self) -> Connection: ...

    def __exit__(self, *args: object) -> None: ...

    def cursor(self) -> Cursor: ...


ConnectionFactory = Callable[[], Connection]


class AppDataAccessError(RuntimeError):
    """Safe data-access category that never contains connector response text."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _query(columns: tuple[str, ...], view: str, order_by: str) -> str:
    selected = ",\n  ".join(f"`{column}`" for column in columns)
    return f"SELECT\n  {selected}\nFROM {view}\nORDER BY {order_by}\nLIMIT :limit"


def _rows(
    connection_factory: ConnectionFactory,
    *,
    query: str,
    columns: tuple[str, ...],
    limit: int,
    contract_error_code: str,
) -> tuple[dict[str, Any], ...]:
    if isinstance(limit, bool) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError("DBTOBSB_QUERY_LIMIT_INVALID")
    try:
        with connection_factory() as connection, connection.cursor() as cursor:
            cursor.execute(query, {"limit": limit})
            result = cursor.fetchall()
    except AppDataAccessError:
        raise
    except Exception:
        raise AppDataAccessError("DBTOBSB_APP_QUERY_FAILED") from None
    rows: list[dict[str, Any]] = []
    for row in result:
        values = tuple(row)
        if len(values) != len(columns):
            raise AppDataAccessError(contract_error_code)
        rows.append(dict(zip(columns, values, strict=True)))
    return tuple(rows)


def aggregate_trend_rows(rows: Sequence[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Aggregate the fixed sanitized trend projection used by the live repository."""
    attempts: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        if set(row) != set(TREND_SOURCE_COLUMNS):
            raise AppDataAccessError("DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH")
        if row["pair_state"] != "PAIR_VALID":
            continue
        run_id = row["observed_job_run_id"]
        task_run_id = row["dbt_task_run_id"]
        if isinstance(run_id, bool) or not isinstance(run_id, int):
            raise AppDataAccessError("DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH")
        if isinstance(task_run_id, bool) or not isinstance(task_run_id, int):
            raise AppDataAccessError("DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH")
        key = (run_id, task_run_id)
        current = attempts.setdefault(
            key,
            {
                "observed_job_run_id": run_id,
                "observed_at": row["observed_at"],
                "failed_node_results": 0,
                "model_results": 0,
            },
        )
        if current["observed_at"] != row["observed_at"]:
            raise AppDataAccessError("DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH")
        resource_type = row["resource_type"]
        status = row["status"]
        if resource_type is None and status is None:
            continue
        if not isinstance(resource_type, str) or not isinstance(status, str):
            raise AppDataAccessError("DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH")
        if status in {"error", "fail"}:
            current["failed_node_results"] += 1
        if resource_type == "model":
            current["model_results"] += 1
    try:
        return tuple(
            sorted(
                attempts.values(),
                key=lambda item: (item["observed_at"], item["observed_job_run_id"]),
            )
        )
    except TypeError:
        raise AppDataAccessError("DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH") from None


class DatabricksSqlRepository:
    """Query only the three installer-bound sanitized evidence views."""

    def __init__(self, bindings: ResourceBindings, connection_factory: ConnectionFactory) -> None:
        if (
            not bindings.ready
            or bindings.run_health_view is None
            or bindings.node_health_view is None
            or bindings.collection_health_view is None
        ):
            raise ValueError("DBTOBSB_APP_BINDINGS_NOT_READY")
        self._connection_factory = connection_factory
        self._runs_query = _query(
            RUN_COLUMNS,
            bindings.run_health_view.quoted,
            "`task_start_time` DESC, `dbt_task_run_id` DESC",
        )
        self._nodes_query = _query(
            NODE_COLUMNS,
            bindings.node_health_view.quoted,
            "`dbt_task_run_id` DESC, `unique_id` ASC",
        )
        self._collection_query = _query(
            COLLECTION_COLUMNS,
            bindings.collection_health_view.quoted,
            "`first_discovered_at` DESC NULLS LAST, `dbt_task_run_id` DESC",
        )
        self._trends_query = f"""WITH recent_runs AS (
  SELECT
    `observed_job_run_id`,
    `dbt_task_run_id`,
    `generated_at` AS `observed_at`,
    `pair_state`
  FROM {bindings.run_health_view.quoted}
  WHERE `pair_state` = 'PAIR_VALID'
  ORDER BY `generated_at` DESC, `dbt_task_run_id` DESC
  LIMIT :limit
)
SELECT
  r.`observed_job_run_id`,
  r.`dbt_task_run_id`,
  r.`observed_at`,
  r.`pair_state`,
  n.`resource_type`,
  n.`status`
FROM recent_runs AS r
LEFT JOIN {bindings.node_health_view.quoted} AS n
  ON n.`dbt_task_run_id` = r.`dbt_task_run_id`
 AND n.`observed_job_run_id` = r.`observed_job_run_id`
ORDER BY r.`observed_at` ASC, r.`observed_job_run_id` ASC,
  n.`resource_type` ASC, n.`status` ASC"""

    def recent_runs(self, limit: int) -> tuple[RunHealth, ...]:
        """Return a bounded newest-first run view projection."""
        try:
            return tuple(
                RunHealth.model_validate(row)
                for row in _rows(
                    self._connection_factory,
                    query=self._runs_query,
                    columns=RUN_COLUMNS,
                    limit=limit,
                    contract_error_code="DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH",
                )
            )
        except ValidationError:
            raise AppDataAccessError("DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH") from None

    def recent_nodes(self, limit: int) -> tuple[NodeHealth, ...]:
        """Return a bounded newest-attempt-first node view projection."""
        try:
            return tuple(
                NodeHealth.model_validate(row)
                for row in _rows(
                    self._connection_factory,
                    query=self._nodes_query,
                    columns=NODE_COLUMNS,
                    limit=limit,
                    contract_error_code="DBTOBSB_APP_NODE_VIEW_CONTRACT_MISMATCH",
                )
            )
        except ValidationError:
            raise AppDataAccessError("DBTOBSB_APP_NODE_VIEW_CONTRACT_MISMATCH") from None

    def recent_collection(self, limit: int) -> tuple[CollectionHealth, ...]:
        """Return bounded collection/reconciliation lifecycle state."""
        try:
            return tuple(
                CollectionHealth.model_validate(row)
                for row in _rows(
                    self._connection_factory,
                    query=self._collection_query,
                    columns=COLLECTION_COLUMNS,
                    limit=limit,
                    contract_error_code="DBTOBSB_APP_COLLECTION_VIEW_CONTRACT_MISMATCH",
                )
            )
        except ValidationError:
            raise AppDataAccessError("DBTOBSB_APP_COLLECTION_VIEW_CONTRACT_MISMATCH") from None

    def recent_trends(self, limit: int) -> tuple[TrendPoint, ...]:
        """Return oldest-first aggregates for the newest accepted dbt runs."""
        try:
            source_rows = _rows(
                self._connection_factory,
                query=self._trends_query,
                columns=TREND_SOURCE_COLUMNS,
                limit=limit,
                contract_error_code="DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH",
            )
            return tuple(
                TrendPoint.model_validate(row) for row in aggregate_trend_rows(source_rows)
            )
        except (AppDataAccessError, ValidationError):
            raise AppDataAccessError("DBTOBSB_APP_TREND_VIEW_CONTRACT_MISMATCH") from None


def databricks_repository(bindings: ResourceBindings) -> ObservabilityRepository:
    """Use the App service principal through Databricks unified authentication."""
    if bindings.warehouse_id is None:
        raise ValueError("DBTOBSB_APP_BINDINGS_NOT_READY")
    try:
        config = Config()
    except Exception:
        raise AppDataAccessError("DBTOBSB_APP_AUTH_INVALID") from None
    if (
        config.auth_type != "oauth-m2m"
        or not config.client_id
        or not config.client_secret
        or config.token
    ):
        raise AppDataAccessError("DBTOBSB_APP_AUTH_INVALID")

    def connect() -> Connection:
        return cast(
            Connection,
            sql.connect(
                server_hostname=config.host,
                http_path=f"/sql/1.0/warehouses/{bindings.warehouse_id}",
                credentials_provider=lambda: config.authenticate,
                enable_telemetry=0,
            ),
        )

    return DatabricksSqlRepository(bindings, connect)
