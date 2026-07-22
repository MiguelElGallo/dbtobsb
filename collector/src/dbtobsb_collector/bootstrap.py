"""Fresh-install-only DDL bootstrap inside an existing customer-owned schema."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from dbtobsb_collector.naming import qualify, quote_identifier

MANIFEST_TABLE = "dbtobsb_object_manifest"
REGISTRY_TABLE = "dbt_artifact_registry"
INVOCATIONS_TABLE = "dbt_invocations"
NODE_RESULTS_TABLE = "dbt_node_results"
RUN_HEALTH_VIEW = "dbt_run_health"
NODE_HEALTH_VIEW = "dbt_node_health"
COLLECTION_HEALTH_VIEW = "dbt_collection_health"
RAW_VOLUME_NAME = "dbtobsb_raw"
STAGE_VOLUME_NAME = "dbtobsb_stage"
OBJECT_MANIFEST_VERSION = "dbtobsb.evidence.v1.0.0-rc.11"

_PRODUCT_PROPERTY = "dbtobsb.product"
_VERSION_PROPERTY = "dbtobsb.object_manifest_version"
_CONTRACT_PROPERTY = "dbtobsb.object_contract_sha256"
_ROLE_PROPERTY = "dbtobsb.object_role"
_WAREHOUSE_ID = re.compile(r"^[0-9a-f]{16}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NATIVE_ERROR_CONDITION = re.compile(r"^[A-Z][A-Z0-9_.]{0,127}$")
_SQLSTATE = re.compile(r"^[A-Z0-9]{5}$")


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
    stage_volume: str
    object_owner: str


@dataclass(frozen=True, slots=True)
class DeleteResult:
    """Verified destructive uninstall result for exactly the v1 product objects."""

    deleted_object_count: int
    schema_owner: str


@dataclass(frozen=True, slots=True)
class InstallationBinding:
    """Deployment-time values sealed into the customer-owned manifest row."""

    workspace_id: int
    warehouse_id: str
    source_contract_sha256: str
    expected_runtime_policy_sha256: str
    observed_job_id: int
    collector_job_id: int
    reconciler_job_id: int
    observed_service_principal_name: str
    collector_service_principal_name: str
    job_manager_group_name: str
    collector_environment_sha256: str


@dataclass(frozen=True, slots=True)
class InstallationSeal:
    """Exact one-row deployment seal consumed by the runtime collector."""

    manifest_version: str
    object_contract_sha256: str
    source_contract_sha256: str
    expected_runtime_policy_sha256: str
    base_observability_contract_sha256: str
    installation_id: str
    workspace_id: int
    evidence_catalog: str
    evidence_schema: str
    warehouse_id: str
    observed_job_id: int
    collector_job_id: int
    reconciler_job_id: int
    observed_service_principal_name: str
    collector_service_principal_name: str
    job_manager_group_name: str
    collector_environment_sha256: str
    artifact_state: str = "FINALIZED_RUNTIME"
    finalization_required: bool = False


MANIFEST_FIELDS: tuple[tuple[str, str], ...] = (
    ("manifest_version", "string"),
    ("object_contract_sha256", "string"),
    ("source_contract_sha256", "string"),
    ("expected_runtime_policy_sha256", "string"),
    ("base_observability_contract_sha256", "string"),
    ("installation_id", "string"),
    ("workspace_id", "bigint"),
    ("evidence_catalog", "string"),
    ("evidence_schema", "string"),
    ("warehouse_id", "string"),
    ("observed_job_id", "bigint"),
    ("collector_job_id", "bigint"),
    ("reconciler_job_id", "bigint"),
    ("observed_service_principal_name", "string"),
    ("collector_service_principal_name", "string"),
    ("job_manager_group_name", "string"),
    ("collector_environment_sha256", "string"),
)

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
    ("dbt_include_deps", "boolean"),
    ("issue_code", "string"),
    ("logs_truncated", "boolean"),
    ("archive_sha256", "string"),
    ("archive_size_bytes", "bigint"),
    ("raw_archive_locator", "string"),
    ("manifest_sha256", "string"),
    ("manifest_size_bytes", "bigint"),
    ("run_results_sha256", "string"),
    ("run_results_size_bytes", "bigint"),
    ("structured_log_state", "string"),
    ("structured_log_sha256", "string"),
    ("structured_log_size_bytes", "bigint"),
    ("structured_log_file_count", "int"),
    ("structured_log_version", "int"),
    ("deps_structured_log_state", "string"),
    ("deps_structured_log_sha256", "string"),
    ("deps_structured_log_size_bytes", "bigint"),
    ("deps_structured_log_file_count", "int"),
    ("deps_structured_log_version", "int"),
    ("structured_log_expected_dbt_common_version", "string"),
    ("invocation_id", "string"),
    ("expected_node_count", "bigint"),
    ("normalized_digest", "string"),
    ("collector_state", "string"),
    ("collected_at", "timestamp"),
    ("published_at", "timestamp"),
    ("first_discovered_at", "timestamp"),
    ("last_attempted_at", "timestamp"),
    ("collection_attempt_count", "int"),
    ("collection_issue_code", "string"),
    ("last_reconciliation_run_id", "bigint"),
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

COLLECTION_HEALTH_FIELDS: tuple[tuple[str, str], ...] = (
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
    ("collector_state", "string"),
    ("collection_issue_code", "string"),
    ("first_discovered_at", "timestamp"),
    ("last_attempted_at", "timestamp"),
    ("collection_attempt_count", "int"),
    ("published_at", "timestamp"),
    ("last_reconciliation_run_id", "bigint"),
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

_TABLE_SPECS: tuple[ObjectSpec, ...] = (
    ObjectSpec(REGISTRY_TABLE, REGISTRY_FIELDS),
    ObjectSpec(INVOCATIONS_TABLE, INVOCATION_FIELDS),
    ObjectSpec(NODE_RESULTS_TABLE, NODE_FIELDS),
)
_VIEW_SPECS: tuple[ObjectSpec, ...] = (
    ObjectSpec(RUN_HEALTH_VIEW, RUN_VIEW_FIELDS),
    ObjectSpec(NODE_HEALTH_VIEW, NODE_VIEW_FIELDS),
    ObjectSpec(COLLECTION_HEALTH_VIEW, COLLECTION_HEALTH_FIELDS),
)
_RELATION_NAMES = frozenset(
    {MANIFEST_TABLE, *(spec.name for spec in _TABLE_SPECS), *(spec.name for spec in _VIEW_SPECS)}
)
_GRANT_ROW_FIELDS = frozenset({"principal", "actiontype", "objecttype", "objectkey"})


def _column_sql(fields: tuple[tuple[str, str], ...]) -> str:
    return ",\n  ".join(
        f"{quote_identifier(name)} {data_type.upper()}" for name, data_type in fields
    )


def _sql_literal(value: str) -> str:
    return f"'{value.replace(chr(39), chr(39) * 2)}'"


def _validate_installation_binding(binding: InstallationBinding) -> None:
    if binding.workspace_id <= 0:
        raise ValueError("DBTOBSB_BOOTSTRAP_WORKSPACE_BINDING_INVALID")
    if _WAREHOUSE_ID.fullmatch(binding.warehouse_id) is None:
        raise ValueError("DBTOBSB_BOOTSTRAP_WAREHOUSE_BINDING_INVALID")
    if (
        _SHA256.fullmatch(binding.source_contract_sha256) is None
        or _SHA256.fullmatch(binding.expected_runtime_policy_sha256) is None
    ):
        raise ValueError("DBTOBSB_BOOTSTRAP_DBT_POLICY_BINDING_INVALID")
    if (
        binding.observed_job_id <= 0
        or binding.collector_job_id <= 0
        or binding.reconciler_job_id <= 0
    ):
        raise ValueError("DBTOBSB_BOOTSTRAP_JOB_BINDING_INVALID")
    principal_names = (
        binding.observed_service_principal_name,
        binding.collector_service_principal_name,
        binding.job_manager_group_name,
    )
    if any(not name or name != name.strip() for name in principal_names) or (
        binding.observed_service_principal_name == binding.collector_service_principal_name
    ):
        raise ValueError("DBTOBSB_BOOTSTRAP_PRINCIPAL_BINDING_INVALID")
    if _SHA256.fullmatch(binding.collector_environment_sha256) is None:
        raise ValueError("DBTOBSB_BOOTSTRAP_ENVIRONMENT_BINDING_INVALID")


def collector_environment_sha256(dependencies: tuple[str, ...]) -> str:
    """Digest the exact ordered dependency tuple observed after Bundle resolution."""
    if (
        len(dependencies) != 4
        or len(set(dependencies)) != len(dependencies)
        or any(not item or item != item.strip() for item in dependencies)
    ):
        raise ValueError("DBTOBSB_BOOTSTRAP_ENVIRONMENT_BINDING_INVALID")
    rendered = json.dumps(dependencies, ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(rendered).hexdigest()


def _installation_id(binding: InstallationBinding, *, catalog: str, schema: str) -> str:
    payload = {
        "workspace_id": binding.workspace_id,
        "catalog": catalog,
        "schema": schema,
        "warehouse_id": binding.warehouse_id,
        "source_contract_sha256": binding.source_contract_sha256,
        "expected_runtime_policy_sha256": binding.expected_runtime_policy_sha256,
        "observed_job_id": binding.observed_job_id,
        "collector_job_id": binding.collector_job_id,
        "reconciler_job_id": binding.reconciler_job_id,
        "observed_service_principal_name": binding.observed_service_principal_name,
        "collector_service_principal_name": binding.collector_service_principal_name,
        "job_manager_group_name": binding.job_manager_group_name,
        "collector_environment_sha256": binding.collector_environment_sha256,
    }
    rendered = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(rendered).hexdigest()


def _expected_manifest_row(
    binding: InstallationBinding, *, catalog: str, schema: str
) -> dict[str, str | int]:
    return {
        "manifest_version": OBJECT_MANIFEST_VERSION,
        "object_contract_sha256": OBJECT_CONTRACT_SHA256,
        "source_contract_sha256": binding.source_contract_sha256,
        "expected_runtime_policy_sha256": binding.expected_runtime_policy_sha256,
        "base_observability_contract_sha256": BASE_OBSERVABILITY_CONTRACT_SHA256,
        "installation_id": _installation_id(binding, catalog=catalog, schema=schema),
        "workspace_id": binding.workspace_id,
        "evidence_catalog": catalog,
        "evidence_schema": schema,
        "warehouse_id": binding.warehouse_id,
        "observed_job_id": binding.observed_job_id,
        "collector_job_id": binding.collector_job_id,
        "reconciler_job_id": binding.reconciler_job_id,
        "observed_service_principal_name": binding.observed_service_principal_name,
        "collector_service_principal_name": binding.collector_service_principal_name,
        "job_manager_group_name": binding.job_manager_group_name,
        "collector_environment_sha256": binding.collector_environment_sha256,
    }


def _manifest_value_sql(value: str | int) -> str:
    if isinstance(value, str):
        return _sql_literal(value)
    return str(value)


def _run_view_query(registry: str, invocations: str) -> str:
    return f"""SELECT
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
  ON r.workspace_id = i.workspace_id
  AND r.dbt_task_run_id = i.dbt_task_run_id
  AND r.normalized_digest = i.normalized_digest
WHERE r.collector_state = 'PUBLISHED'"""


def _node_view_query(registry: str, nodes: str) -> str:
    return f"""SELECT
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
  USING (workspace_id, dbt_task_run_id, normalized_digest)
WHERE r.collector_state = 'PUBLISHED'"""


def _collection_health_query(registry: str) -> str:
    return f"""SELECT
  workspace_id,
  dbt_task_run_id,
  observed_job_id,
  observed_job_run_id,
  observed_task_key,
  repair_count,
  execution_count,
  attempt_number,
  task_start_time,
  task_end_time,
  lakeflow_result_state,
  collector_state,
  collection_issue_code,
  first_discovered_at,
  last_attempted_at,
  collection_attempt_count,
  published_at,
  last_reconciliation_run_id
FROM {registry}"""


def _canonical_sql(statement: str) -> str:
    stripped = statement.rstrip().removesuffix(";").strip()
    segments = re.split(r"('(?:''|[^'])*')", stripped)
    return "".join(
        segment if index % 2 else re.sub(r"\s+", " ", segment).casefold()
        for index, segment in enumerate(segments)
    )


def _object_contract_sha256() -> str:
    contract = {
        "manifest": [MANIFEST_TABLE, MANIFEST_FIELDS],
        "tables": [[spec.name, spec.fields] for spec in _TABLE_SPECS],
        "views": [
            [
                _VIEW_SPECS[0].name,
                _VIEW_SPECS[0].fields,
                _run_view_query("__registry__", "__invocations__"),
            ],
            [
                _VIEW_SPECS[1].name,
                _VIEW_SPECS[1].fields,
                _node_view_query("__registry__", "__nodes__"),
            ],
            [
                _VIEW_SPECS[2].name,
                _VIEW_SPECS[2].fields,
                _collection_health_query("__registry__"),
            ],
        ],
        "volumes": [RAW_VOLUME_NAME, STAGE_VOLUME_NAME],
        "version": OBJECT_MANIFEST_VERSION,
    }
    rendered = json.dumps(contract, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(rendered).hexdigest()


OBJECT_CONTRACT_SHA256 = _object_contract_sha256()


def _base_observability_contract_sha256() -> str:
    contract = {
        "domain": "dbtobsb.base-observability-contract.v1",
        "component_key": "BASE_OBSERVABILITY",
        "object_contract_sha256": OBJECT_CONTRACT_SHA256,
    }
    rendered = json.dumps(contract, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(rendered).hexdigest()


BASE_OBSERVABILITY_CONTRACT_SHA256 = _base_observability_contract_sha256()


def _object_properties(role: str) -> dict[str, str]:
    return {
        _PRODUCT_PROPERTY: "dbtobsb",
        _VERSION_PROPERTY: OBJECT_MANIFEST_VERSION,
        _CONTRACT_PROPERTY: OBJECT_CONTRACT_SHA256,
        _ROLE_PROPERTY: role,
    }


def _properties_sql(role: str) -> str:
    return ",\n  ".join(
        f"{_sql_literal(key)} = {_sql_literal(value)}"
        for key, value in _object_properties(role).items()
    )


def _volume_comment(role: str = "raw_volume") -> str:
    return (
        f"dbtobsb|manifest={OBJECT_MANIFEST_VERSION}|contract={OBJECT_CONTRACT_SHA256}|role={role}"
    )


def _collect_rows(frame: Any) -> list[Any]:
    collect = getattr(frame, "collect", None)
    if collect is None:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    try:
        return list(collect())
    except Exception as error:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE") from error


def _row_mapping(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        source = row
    else:
        as_dict = getattr(row, "asDict", None)
        if as_dict is None:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
        source = as_dict(recursive=True)
    if not isinstance(source, dict):
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    normalized: dict[str, Any] = {}
    for key, value in source.items():
        normalized_key = str(key).casefold()
        if normalized_key in normalized:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
        normalized[normalized_key] = value
    return normalized


def _mapping_rows(frame: Any) -> list[dict[str, Any]]:
    return [_row_mapping(row) for row in _collect_rows(frame)]


def _mapping_sql_rows(
    spark: SparkBootstrapSession,
    statement: str,
    *,
    failure_code: str,
) -> list[dict[str, Any]]:
    """Run one fixed metadata query without exposing native exception text."""
    try:
        return _mapping_rows(spark.sql(statement))
    except Exception:
        raise RuntimeError(failure_code) from None


def _native_error_attribute(error: Exception, *names: str, pattern: re.Pattern[str]) -> str:
    try:
        java_exception = getattr(error, "java_exception", None)
    except Exception:
        java_exception = None
    sources = (error, java_exception)
    for source in sources:
        for name in names:
            try:
                accessor = getattr(source, name, None)
            except Exception:
                continue
            if not callable(accessor):
                continue
            try:
                value = accessor()
            except Exception:
                continue
            if isinstance(value, str) and pattern.fullmatch(value) is not None:
                return value
    return ""


def _table_create_failure_code(error: Exception) -> str:
    """Map native error metadata to one fixed family without reading its message."""
    condition = _native_error_attribute(
        error,
        "getCondition",
        "getErrorClass",
        pattern=_NATIVE_ERROR_CONDITION,
    )
    sql_state = _native_error_attribute(error, "getSqlState", pattern=_SQLSTATE)
    if sql_state == "42501" or any(
        marker in condition
        for marker in (
            "ACCESS_DENIED",
            "AUTHENTICATION",
            "PERMISSION",
            "PRIVILEGE",
            "SECURITY",
            "UNAUTHENTICATED",
            "UNAUTHORIZED",
        )
    ):
        return "DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED"
    if "ALREADY_EXISTS" in condition or "DUPLICATE" in condition or sql_state == "42P07":
        return "DBTOBSB_BOOTSTRAP_TABLE_CREATE_OBJECT_CONFLICT"
    if "UNSUPPORTED" in condition or "NOT_SUPPORTED" in condition or sql_state == "0A000":
        return "DBTOBSB_BOOTSTRAP_TABLE_CREATE_PLATFORM_UNSUPPORTED"
    if any(
        marker in condition
        for marker in (
            "ABFS",
            "CONNECTION",
            "CREDENTIAL",
            "EXTERNAL_LOCATION",
            "FILESYSTEM",
            "FILE_SYSTEM",
            "IO_ERROR",
            "NETWORK",
            "STORAGE",
        )
    ):
        return "DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE"
    if sql_state == "42601" or any(
        marker in condition for marker in ("INVALID", "MALFORMED", "PARSE", "SYNTAX", "UNRESOLVED")
    ):
        return "DBTOBSB_BOOTSTRAP_TABLE_CREATE_SQL_INCOMPATIBLE"
    if sql_state.startswith("XX"):
        return "DBTOBSB_BOOTSTRAP_TABLE_CREATE_INTERNAL_ERROR"
    return "DBTOBSB_BOOTSTRAP_TABLE_CREATE_FAILED"


def _execute_sql(
    spark: SparkBootstrapSession,
    statement: str,
    *,
    failure_code: str,
) -> None:
    """Run one fixed bootstrap mutation with a stage-only failure boundary."""
    try:
        spark.sql(statement)
    except Exception as error:
        code = failure_code
        if failure_code == "DBTOBSB_BOOTSTRAP_TABLE_CREATE_FAILED":
            try:
                code = _table_create_failure_code(error)
            except Exception:
                code = failure_code
        raise RuntimeError(code) from None


def _session_user(spark: SparkBootstrapSession) -> str:
    rows = _mapping_sql_rows(
        spark,
        "SELECT session_user() AS session_user",
        failure_code="DBTOBSB_BOOTSTRAP_SESSION_USER_READ_FAILED",
    )
    if len(rows) != 1 or set(rows[0]) != {"session_user"}:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    actor = rows[0]["session_user"]
    if not isinstance(actor, str) or not actor:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    return actor


def _schema_owner(spark: SparkBootstrapSession, *, catalog: str, schema: str) -> str:
    rows = _mapping_sql_rows(
        spark,
        f"""SELECT schema_name, schema_owner
FROM {qualify(catalog, "information_schema", "schemata")}
WHERE lower(schema_name) = lower({_sql_literal(schema)})""",
        failure_code="DBTOBSB_BOOTSTRAP_SCHEMA_METADATA_READ_FAILED",
    )
    if len(rows) != 1 or str(rows[0].get("schema_name", "")).casefold() != schema.casefold():
        raise RuntimeError("DBTOBSB_BOOTSTRAP_TARGET_SCHEMA_NOT_FOUND")
    owner = rows[0].get("schema_owner")
    if not isinstance(owner, str) or not owner:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    return owner


def _inventory(
    spark: SparkBootstrapSession, *, catalog: str, schema: str
) -> tuple[frozenset[str], dict[str, dict[str, Any]]]:
    relation_rows = _mapping_sql_rows(
        spark,
        f"""SELECT table_name, table_type
FROM {qualify(catalog, "information_schema", "tables")}
WHERE lower(table_schema) = lower({_sql_literal(schema)})""",
        failure_code="DBTOBSB_BOOTSTRAP_RELATION_INVENTORY_READ_FAILED",
    )
    relation_names: set[str] = set()
    for row in relation_rows:
        name = row.get("table_name")
        if not isinstance(name, str):
            raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
        if name.casefold() not in _RELATION_NAMES:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_UNSUPPORTED_SCHEMA_STATE")
        if name.casefold() in relation_names:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
        relation_names.add(name.casefold())

    volume_rows = _mapping_sql_rows(
        spark,
        f"""SELECT volume_name, volume_type, volume_owner, comment
FROM {qualify(catalog, "information_schema", "volumes")}
WHERE lower(volume_schema) = lower({_sql_literal(schema)})""",
        failure_code="DBTOBSB_BOOTSTRAP_VOLUME_INVENTORY_READ_FAILED",
    )
    volumes: dict[str, dict[str, Any]] = {}
    for row in volume_rows:
        name = row.get("volume_name")
        if not isinstance(name, str):
            raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
        normalized = name.casefold()
        if normalized not in {RAW_VOLUME_NAME, STAGE_VOLUME_NAME} or normalized in volumes:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_UNSUPPORTED_SCHEMA_STATE")
        volumes[normalized] = row
    return frozenset(relation_names), volumes


def _describe_relation(spark: SparkBootstrapSession, name: str) -> dict[str, Any]:
    rows = _collect_rows(spark.sql(f"DESCRIBE TABLE EXTENDED {name} AS JSON"))
    if len(rows) != 1:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    row = rows[0]
    try:
        if isinstance(row, dict):
            values = list(row.values())
            raw = values[0] if len(values) == 1 else None
        else:
            raw = row[0]
        if not isinstance(raw, str | bytes | bytearray):
            raise TypeError
        payload = json.loads(raw)
    except (IndexError, KeyError, TypeError, ValueError) as error:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE") from error
    if not isinstance(payload, dict):
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    return {str(key).casefold(): value for key, value in payload.items()}


def _actual_fields(spark: SparkBootstrapSession, name: str) -> tuple[tuple[str, str], ...]:
    try:
        schema = spark.table(name).schema
        return tuple((field.name, field.dataType.simpleString().lower()) for field in schema.fields)
    except Exception as error:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE") from error


def _normalize_sql(statement: str) -> str:
    return _canonical_sql(statement)


def read_installation_seal(
    spark: SparkBootstrapSession, *, catalog: str, schema: str
) -> InstallationSeal:
    """Read one exact, release-compatible installation seal without adopting drift."""
    manifest = qualify(catalog, schema, MANIFEST_TABLE)
    rows = _mapping_rows(
        spark.sql(
            f"""SELECT
  manifest_version,
  object_contract_sha256,
  source_contract_sha256,
  expected_runtime_policy_sha256,
  base_observability_contract_sha256,
  installation_id,
  workspace_id,
  evidence_catalog,
  evidence_schema,
  warehouse_id,
  observed_job_id,
  collector_job_id,
  reconciler_job_id,
  observed_service_principal_name,
  collector_service_principal_name,
  job_manager_group_name,
  collector_environment_sha256
FROM {manifest}"""
        )
    )
    expected_keys = {name for name, _ in MANIFEST_FIELDS}
    if len(rows) != 1 or set(rows[0]) != expected_keys:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH")
    row = rows[0]
    if (
        row["manifest_version"] != OBJECT_MANIFEST_VERSION
        or row["object_contract_sha256"] != OBJECT_CONTRACT_SHA256
        or not isinstance(row["source_contract_sha256"], str)
        or _SHA256.fullmatch(row["source_contract_sha256"]) is None
        or not isinstance(row["expected_runtime_policy_sha256"], str)
        or _SHA256.fullmatch(row["expected_runtime_policy_sha256"]) is None
        or row["base_observability_contract_sha256"] != BASE_OBSERVABILITY_CONTRACT_SHA256
        or not isinstance(row["installation_id"], str)
        or type(row["workspace_id"]) is not int
        or row["evidence_catalog"] != catalog
        or row["evidence_schema"] != schema
        or not isinstance(row["warehouse_id"], str)
        or type(row["observed_job_id"]) is not int
        or type(row["collector_job_id"]) is not int
        or type(row["reconciler_job_id"]) is not int
        or not isinstance(row["observed_service_principal_name"], str)
        or not isinstance(row["collector_service_principal_name"], str)
        or not isinstance(row["job_manager_group_name"], str)
        or not isinstance(row["collector_environment_sha256"], str)
    ):
        raise RuntimeError("DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH")
    binding = InstallationBinding(
        workspace_id=row["workspace_id"],
        warehouse_id=row["warehouse_id"],
        source_contract_sha256=row["source_contract_sha256"],
        expected_runtime_policy_sha256=row["expected_runtime_policy_sha256"],
        observed_job_id=row["observed_job_id"],
        collector_job_id=row["collector_job_id"],
        reconciler_job_id=row["reconciler_job_id"],
        observed_service_principal_name=row["observed_service_principal_name"],
        collector_service_principal_name=row["collector_service_principal_name"],
        job_manager_group_name=row["job_manager_group_name"],
        collector_environment_sha256=row["collector_environment_sha256"],
    )
    try:
        _validate_installation_binding(binding)
    except ValueError as error:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH") from error
    expected_installation_id = _installation_id(binding, catalog=catalog, schema=schema)
    if row["installation_id"] != expected_installation_id:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH")
    return InstallationSeal(
        manifest_version=OBJECT_MANIFEST_VERSION,
        object_contract_sha256=OBJECT_CONTRACT_SHA256,
        source_contract_sha256=binding.source_contract_sha256,
        expected_runtime_policy_sha256=binding.expected_runtime_policy_sha256,
        base_observability_contract_sha256=BASE_OBSERVABILITY_CONTRACT_SHA256,
        installation_id=expected_installation_id,
        workspace_id=binding.workspace_id,
        evidence_catalog=catalog,
        evidence_schema=schema,
        warehouse_id=binding.warehouse_id,
        observed_job_id=binding.observed_job_id,
        collector_job_id=binding.collector_job_id,
        reconciler_job_id=binding.reconciler_job_id,
        observed_service_principal_name=binding.observed_service_principal_name,
        collector_service_principal_name=binding.collector_service_principal_name,
        job_manager_group_name=binding.job_manager_group_name,
        collector_environment_sha256=binding.collector_environment_sha256,
        artifact_state="FINALIZED_RUNTIME",
        finalization_required=False,
    )


def _verify_manifest_row(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
    binding: InstallationBinding,
) -> None:
    seal = read_installation_seal(spark, catalog=catalog, schema=schema)
    if (
        seal.warehouse_id != binding.warehouse_id
        or seal.workspace_id != binding.workspace_id
        or seal.source_contract_sha256 != binding.source_contract_sha256
        or seal.expected_runtime_policy_sha256 != binding.expected_runtime_policy_sha256
        or seal.observed_job_id != binding.observed_job_id
        or seal.collector_job_id != binding.collector_job_id
        or seal.reconciler_job_id != binding.reconciler_job_id
        or seal.observed_service_principal_name != binding.observed_service_principal_name
        or seal.collector_service_principal_name != binding.collector_service_principal_name
        or seal.job_manager_group_name != binding.job_manager_group_name
        or seal.collector_environment_sha256 != binding.collector_environment_sha256
    ):
        raise RuntimeError("DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH")


def _verify_relation(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
    spec: ObjectSpec,
    expected_type: str,
    expected_role: str,
    expected_view_text: str | None = None,
) -> str:
    name = qualify(catalog, schema, spec.name)
    metadata = _describe_relation(spark, name)
    if (
        str(metadata.get("catalog_name", "")).casefold() != catalog.casefold()
        or str(metadata.get("schema_name", "")).casefold() != schema.casefold()
        or str(metadata.get("table_name", "")).casefold() != spec.name.casefold()
        or str(metadata.get("type", "")).upper() != expected_type
    ):
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_KIND_MISMATCH")
    provider = metadata.get("provider")
    if expected_type == "MANAGED" and str(provider).casefold() != "delta":
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_PROVIDER_MISMATCH")
    if expected_type == "VIEW" and provider not in {None, ""}:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_PROVIDER_MISMATCH")
    if _actual_fields(spark, name) != spec.fields:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_SCHEMA_MISMATCH")

    properties = metadata.get("table_properties")
    if not isinstance(properties, dict):
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_MARKER_MISMATCH")
    expected_properties = _object_properties(expected_role)
    if any(properties.get(key) != value for key, value in expected_properties.items()):
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_MARKER_MISMATCH")

    if expected_view_text is not None:
        view_text = metadata.get("view_text")
        if not isinstance(view_text, str) or _normalize_sql(view_text) != _normalize_sql(
            expected_view_text
        ):
            raise RuntimeError("DBTOBSB_BOOTSTRAP_VIEW_DEFINITION_MISMATCH")
    owner = metadata.get("owner")
    if not isinstance(owner, str) or not owner:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
    return owner


def _grant_identity(value: str) -> str:
    return value.casefold()


def _verify_no_direct_grants_on_object(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
    object_name: str,
    securable_type: str,
) -> None:
    fully_qualified_name = qualify(catalog, schema, object_name)
    rows = _mapping_rows(spark.sql(f"SHOW GRANTS ON {securable_type} {fully_qualified_name}"))
    target_key = _grant_identity(f"{catalog}.{schema}.{object_name}")
    schema_key = _grant_identity(f"{catalog}.{schema}")
    catalog_key = _grant_identity(catalog)
    expected_type = securable_type.casefold()
    seen: set[tuple[str, str, str, str]] = set()

    for row in rows:
        if set(row) != _GRANT_ROW_FIELDS or any(
            not isinstance(row[field], str) or not row[field] or row[field] != row[field].strip()
            for field in _GRANT_ROW_FIELDS
        ):
            raise RuntimeError("DBTOBSB_BOOTSTRAP_GRANT_METADATA_INVALID")
        normalized = (
            row["principal"],
            row["actiontype"],
            row["objecttype"].casefold(),
            _grant_identity(row["objectkey"]),
        )
        if normalized in seen:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_GRANT_METADATA_INVALID")
        seen.add(normalized)

        object_type = normalized[2]
        object_key = normalized[3]
        if object_type == expected_type and object_key == target_key:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_DIRECT_OBJECT_GRANTS_PRESENT")
        inherited_from_schema = object_type in {"schema", "database"} and object_key == schema_key
        inherited_from_catalog = object_type == "catalog" and object_key == catalog_key
        if not inherited_from_schema and not inherited_from_catalog:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_GRANT_METADATA_INVALID")


def _verify_no_direct_object_grants(
    spark: SparkBootstrapSession, *, catalog: str, schema: str
) -> None:
    for object_name in (MANIFEST_TABLE, *(spec.name for spec in _TABLE_SPECS)):
        _verify_no_direct_grants_on_object(
            spark,
            catalog=catalog,
            schema=schema,
            object_name=object_name,
            securable_type="TABLE",
        )
    for spec in _VIEW_SPECS:
        _verify_no_direct_grants_on_object(
            spark,
            catalog=catalog,
            schema=schema,
            object_name=spec.name,
            securable_type="VIEW",
        )
    _verify_no_direct_grants_on_object(
        spark,
        catalog=catalog,
        schema=schema,
        object_name=RAW_VOLUME_NAME,
        securable_type="VOLUME",
    )
    _verify_no_direct_grants_on_object(
        spark,
        catalog=catalog,
        schema=schema,
        object_name=STAGE_VOLUME_NAME,
        securable_type="VOLUME",
    )


def _attest_objects(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
    binding: InstallationBinding,
) -> tuple[str, tuple[str, ...]]:
    registry = qualify(catalog, schema, REGISTRY_TABLE)
    invocations = qualify(catalog, schema, INVOCATIONS_TABLE)
    nodes = qualify(catalog, schema, NODE_RESULTS_TABLE)
    owners = {
        _verify_relation(
            spark,
            catalog=catalog,
            schema=schema,
            spec=ObjectSpec(MANIFEST_TABLE, MANIFEST_FIELDS),
            expected_type="MANAGED",
            expected_role="object_manifest",
        )
    }
    _verify_manifest_row(spark, catalog=catalog, schema=schema, binding=binding)
    for spec in _TABLE_SPECS:
        owners.add(
            _verify_relation(
                spark,
                catalog=catalog,
                schema=schema,
                spec=spec,
                expected_type="MANAGED",
                expected_role=spec.name,
            )
        )
    for spec, expected_text in (
        (_VIEW_SPECS[0], _run_view_query(registry, invocations)),
        (_VIEW_SPECS[1], _node_view_query(registry, nodes)),
        (_VIEW_SPECS[2], _collection_health_query(registry)),
    ):
        owners.add(
            _verify_relation(
                spark,
                catalog=catalog,
                schema=schema,
                spec=spec,
                expected_type="VIEW",
                expected_role=spec.name,
                expected_view_text=expected_text,
            )
        )
    if len(owners) != 1:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_OWNER_MISMATCH")
    _verify_no_direct_object_grants(spark, catalog=catalog, schema=schema)
    verified = tuple(qualify(catalog, schema, name) for name in sorted(_RELATION_NAMES))
    return next(iter(owners)), verified


def _create_fresh_objects(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
    binding: InstallationBinding,
) -> None:
    registry = qualify(catalog, schema, REGISTRY_TABLE)
    invocations = qualify(catalog, schema, INVOCATIONS_TABLE)
    nodes = qualify(catalog, schema, NODE_RESULTS_TABLE)
    run_view = qualify(catalog, schema, RUN_HEALTH_VIEW)
    node_view = qualify(catalog, schema, NODE_HEALTH_VIEW)
    collection_view = qualify(catalog, schema, COLLECTION_HEALTH_VIEW)
    volume = qualify(catalog, schema, RAW_VOLUME_NAME)
    stage_volume = qualify(catalog, schema, STAGE_VOLUME_NAME)

    for spec in _TABLE_SPECS:
        name = qualify(catalog, schema, spec.name)
        _execute_sql(
            spark,
            f"""CREATE TABLE {name} (
  {_column_sql(spec.fields)}
) USING DELTA
TBLPROPERTIES (
  {_properties_sql(spec.name)}
)""",
            failure_code="DBTOBSB_BOOTSTRAP_TABLE_CREATE_FAILED",
        )
    _execute_sql(
        spark,
        f"CREATE VOLUME {volume} COMMENT {_sql_literal(_volume_comment())}",
        failure_code="DBTOBSB_BOOTSTRAP_VOLUME_CREATE_FAILED",
    )
    _execute_sql(
        spark,
        f"CREATE VOLUME {stage_volume} COMMENT {_sql_literal(_volume_comment('artifact_stage'))}",
        failure_code="DBTOBSB_BOOTSTRAP_VOLUME_CREATE_FAILED",
    )
    _execute_sql(
        spark,
        f"""CREATE VIEW {run_view}
TBLPROPERTIES (
  {_properties_sql(RUN_HEALTH_VIEW)}
)
AS
{_run_view_query(registry, invocations)}""",
        failure_code="DBTOBSB_BOOTSTRAP_VIEW_CREATE_FAILED",
    )
    _execute_sql(
        spark,
        f"""CREATE VIEW {node_view}
TBLPROPERTIES (
  {_properties_sql(NODE_HEALTH_VIEW)}
)
AS
{_node_view_query(registry, nodes)}""",
        failure_code="DBTOBSB_BOOTSTRAP_VIEW_CREATE_FAILED",
    )
    _execute_sql(
        spark,
        f"""CREATE VIEW {collection_view}
TBLPROPERTIES (
  {_properties_sql(COLLECTION_HEALTH_VIEW)}
)
AS
{_collection_health_query(registry)}""",
        failure_code="DBTOBSB_BOOTSTRAP_VIEW_CREATE_FAILED",
    )
    manifest = qualify(catalog, schema, MANIFEST_TABLE)
    _execute_sql(
        spark,
        f"""CREATE TABLE {manifest} (
  {_column_sql(MANIFEST_FIELDS)}
) USING DELTA
TBLPROPERTIES (
  {_properties_sql("object_manifest")}
)""",
        failure_code="DBTOBSB_BOOTSTRAP_MANIFEST_CREATE_FAILED",
    )
    expected = _expected_manifest_row(binding, catalog=catalog, schema=schema)
    columns = ", ".join(expected)
    values = ", ".join(_manifest_value_sql(value) for value in expected.values())
    _execute_sql(
        spark,
        f"INSERT INTO {manifest} ({columns})\nVALUES ({values})",
        failure_code="DBTOBSB_BOOTSTRAP_MANIFEST_WRITE_FAILED",
    )


def bootstrap_objects(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
    binding: InstallationBinding,
    raw_volume_name: str = RAW_VOLUME_NAME,
) -> BootstrapResult:
    """Install once into a fresh reserved namespace, or attest an exact v1 rerun."""
    if raw_volume_name != RAW_VOLUME_NAME:
        raise ValueError("DBTOBSB_BOOTSTRAP_FIXED_OBJECT_NAME_REQUIRED")
    _validate_installation_binding(binding)

    session_actor = _session_user(spark)
    schema_owner = _schema_owner(spark, catalog=catalog, schema=schema)
    if session_actor != schema_owner:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_ACTOR_SCHEMA_OWNER_MISMATCH")
    relation_names, volumes = _inventory(spark, catalog=catalog, schema=schema)
    any_present = bool(relation_names) or bool(volumes)
    all_present = relation_names == _RELATION_NAMES and set(volumes) == {
        RAW_VOLUME_NAME,
        STAGE_VOLUME_NAME,
    }
    if any_present and not all_present:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_PARTIAL_INSTALL")
    if not any_present:
        _create_fresh_objects(spark, catalog=catalog, schema=schema, binding=binding)
        relation_names, volumes = _inventory(spark, catalog=catalog, schema=schema)
        if relation_names != _RELATION_NAMES or set(volumes) != {
            RAW_VOLUME_NAME,
            STAGE_VOLUME_NAME,
        }:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_PARTIAL_INSTALL")

    volume_owners: set[str] = set()
    for name, role in ((RAW_VOLUME_NAME, "raw_volume"), (STAGE_VOLUME_NAME, "artifact_stage")):
        volume_metadata = volumes.get(name)
        if volume_metadata is None:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_PARTIAL_INSTALL")
        if (
            str(volume_metadata.get("volume_name", "")).casefold() != name
            or str(volume_metadata.get("volume_type", "")).upper() != "MANAGED"
        ):
            raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_KIND_MISMATCH")
        if volume_metadata.get("comment") != _volume_comment(role):
            raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_MARKER_MISMATCH")
        volume_owner = volume_metadata.get("volume_owner")
        if not isinstance(volume_owner, str) or not volume_owner:
            raise RuntimeError("DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE")
        volume_owners.add(volume_owner)

    relation_owner, verified_objects = _attest_objects(
        spark, catalog=catalog, schema=schema, binding=binding
    )
    if volume_owners != {relation_owner} or relation_owner != schema_owner:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_OBJECT_OWNER_MISMATCH")
    return BootstrapResult(
        manifest_version=OBJECT_MANIFEST_VERSION,
        verified_objects=verified_objects,
        raw_volume=qualify(catalog, schema, RAW_VOLUME_NAME),
        stage_volume=qualify(catalog, schema, STAGE_VOLUME_NAME),
        object_owner=relation_owner,
    )


def delete_installation_objects(
    spark: SparkBootstrapSession,
    *,
    catalog: str,
    schema: str,
) -> DeleteResult:
    """Verify and delete exactly the nine v1 objects while preserving the schema."""

    seal = read_installation_seal(spark, catalog=catalog, schema=schema)
    binding = InstallationBinding(
        workspace_id=seal.workspace_id,
        warehouse_id=seal.warehouse_id,
        source_contract_sha256=seal.source_contract_sha256,
        expected_runtime_policy_sha256=seal.expected_runtime_policy_sha256,
        observed_job_id=seal.observed_job_id,
        collector_job_id=seal.collector_job_id,
        reconciler_job_id=seal.reconciler_job_id,
        observed_service_principal_name=seal.observed_service_principal_name,
        collector_service_principal_name=seal.collector_service_principal_name,
        job_manager_group_name=seal.job_manager_group_name,
        collector_environment_sha256=seal.collector_environment_sha256,
    )
    verified = bootstrap_objects(spark, catalog=catalog, schema=schema, binding=binding)

    for spec in reversed(_VIEW_SPECS):
        spark.sql(f"DROP VIEW {qualify(catalog, schema, spec.name)}")
    for spec in reversed(_TABLE_SPECS):
        spark.sql(f"DROP TABLE {qualify(catalog, schema, spec.name)}")
    spark.sql(f"DROP VOLUME {qualify(catalog, schema, STAGE_VOLUME_NAME)}")
    spark.sql(f"DROP VOLUME {qualify(catalog, schema, RAW_VOLUME_NAME)}")
    spark.sql(f"DROP TABLE {qualify(catalog, schema, MANIFEST_TABLE)}")

    relation_names, volumes = _inventory(spark, catalog=catalog, schema=schema)
    if relation_names or volumes:
        raise RuntimeError("DBTOBSB_DELETE_UNINSTALL_READBACK_FAILED")
    return DeleteResult(deleted_object_count=9, schema_owner=verified.object_owner)
