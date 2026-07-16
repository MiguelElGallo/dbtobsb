"""Fixed-query Databricks SQL repository for sanitized observability views."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol, cast

from databricks import sql
from databricks.sdk.core import Config
from pydantic import ValidationError

from dbtobsb_app.configuration import ResourceBindings
from dbtobsb_app.models import CollectionHealth, NodeHealth, RunHealth

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


class ObservabilityRepository(Protocol):
    """Read-only dependency injected into HTTP handlers."""

    def recent_runs(self, limit: int) -> tuple[RunHealth, ...]: ...

    def recent_nodes(self, limit: int) -> tuple[NodeHealth, ...]: ...

    def recent_collection(self, limit: int) -> tuple[CollectionHealth, ...]: ...


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
