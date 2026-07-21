"""Databricks Python-wheel entrypoints with fixed bootstrap/runtime separation."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any, NoReturn

from dbtobsb_contracts import OperatorDiagnostic

from dbtobsb_collector.bootstrap import (
    RAW_VOLUME_NAME,
    InstallationBinding,
    bootstrap_objects,
    delete_installation_objects,
    read_installation_seal,
)
from dbtobsb_collector.contracts import AttemptContext
from dbtobsb_collector.custody import VolumeRawArchiveStore
from dbtobsb_collector.delta import DeltaEvidenceSink
from dbtobsb_collector.deployment import load_deployed_runtime_contract
from dbtobsb_collector.jobs import DatabricksJobsEvidenceReader, JobsEvidenceError
from dbtobsb_collector.reconcile import (
    RECONCILIATION_OPERATOR_CODES,
    InstalledPolicyReconciliationController,
    ReconciliationError,
    reconcile_installed_policy,
)
from dbtobsb_collector.runtime import collect_task_run
from dbtobsb_collector.volume_archive import DatabricksArtifactDownloader

_DEPLOYED_RUNTIME_CODES = frozenset(
    {
        "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE",
        "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID",
        "DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED",
    }
)
_PRE_APP_BOOTSTRAP_RECOVERY = (
    "Use docs/site/how-to-guides/install-private-release.md#recover-a-failed-bootstrap "
    "and follow the matching code."
)
_BOOTSTRAP_CODES = frozenset(
    {
        "DBTOBSB_BOOTSTRAP_ACTOR_SCHEMA_OWNER_MISMATCH",
        "DBTOBSB_BOOTSTRAP_DBT_POLICY_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_DIRECT_OBJECT_GRANTS_PRESENT",
        "DBTOBSB_BOOTSTRAP_ENVIRONMENT_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_FIXED_OBJECT_NAME_REQUIRED",
        "DBTOBSB_BOOTSTRAP_GRANT_METADATA_INVALID",
        "DBTOBSB_BOOTSTRAP_JOB_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_PRINCIPAL_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH",
        "DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE",
        "DBTOBSB_BOOTSTRAP_OBJECT_KIND_MISMATCH",
        "DBTOBSB_BOOTSTRAP_OBJECT_MARKER_MISMATCH",
        "DBTOBSB_BOOTSTRAP_OBJECT_OWNER_MISMATCH",
        "DBTOBSB_BOOTSTRAP_OBJECT_PROVIDER_MISMATCH",
        "DBTOBSB_BOOTSTRAP_OBJECT_SCHEMA_MISMATCH",
        "DBTOBSB_BOOTSTRAP_PARTIAL_INSTALL",
        "DBTOBSB_BOOTSTRAP_MANIFEST_CREATE_FAILED",
        "DBTOBSB_BOOTSTRAP_MANIFEST_WRITE_FAILED",
        "DBTOBSB_BOOTSTRAP_RELATION_INVENTORY_READ_FAILED",
        "DBTOBSB_BOOTSTRAP_SCHEMA_METADATA_READ_FAILED",
        "DBTOBSB_BOOTSTRAP_SESSION_USER_READ_FAILED",
        "DBTOBSB_BOOTSTRAP_SPARK_SESSION_UNAVAILABLE",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_FAILED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_INTERNAL_ERROR",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_OBJECT_CONFLICT",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_PLATFORM_UNSUPPORTED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_SQL_INCOMPATIBLE",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE",
        "DBTOBSB_BOOTSTRAP_TARGET_SCHEMA_NOT_FOUND",
        "DBTOBSB_BOOTSTRAP_UNSUPPORTED_SCHEMA_STATE",
        "DBTOBSB_BOOTSTRAP_VIEW_CREATE_FAILED",
        "DBTOBSB_BOOTSTRAP_VOLUME_CREATE_FAILED",
        "DBTOBSB_BOOTSTRAP_VOLUME_INVENTORY_READ_FAILED",
        "DBTOBSB_BOOTSTRAP_VIEW_DEFINITION_MISMATCH",
        "DBTOBSB_BOOTSTRAP_WAREHOUSE_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_WORKSPACE_BINDING_INVALID",
    }
)
_COLLECTOR_FAILURES = {
    "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_UNAVAILABLE": (
        "installed deployment binding",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and restore the packaged binding.",
    ),
    "DBTOBSB_DEPLOYED_RUNTIME_CONTRACT_INVALID": (
        "installed deployment binding",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and restore the packaged binding.",
    ),
    "DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED": (
        "installed deployment binding",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and finalize the packaged binding.",
    ),
    "DBTOBSB_DELTA_INSTALLATION_BINDING_MISMATCH": (
        "installed deployment binding",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and reconcile the sealed target.",
    ),
    "DBTOBSB_DELTA_ATTEMPT_BINDING_MISMATCH": (
        "installed attempt binding",
        "deployment/seal verifier",
        "Open /operators/how-to/reconcile-installation/ and reconcile the fixed Job binding.",
    ),
    "DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH": (
        "installed deployment seal",
        "deployment/seal verifier",
        "Run the documented deployment-and-seal reconciliation workflow.",
    ),
    "DBT_RAW_ARCHIVE_WRITE_CONFLICT": (
        "raw archive custody",
        "UC volume operator",
        "Run the documented raw-archive custody reconciliation workflow.",
    ),
    "DBT_RAW_ARCHIVE_READBACK_FAILED": (
        "raw archive custody",
        "UC volume operator",
        "Run the documented raw-archive custody reconciliation workflow.",
    ),
    "DBT_RAW_ARCHIVE_READBACK_MISMATCH": (
        "raw archive custody",
        "UC volume operator",
        "Run the documented raw-archive custody reconciliation workflow.",
    ),
    "DBTOBSB_ATTEMPT_ROOT_DUPLICATE": (
        "evidence publication",
        "data operator",
        "Run the documented evidence-publication reconciliation workflow.",
    ),
    "DBTOBSB_ATTEMPT_ROOT_CONFLICT": (
        "evidence publication",
        "data operator",
        "Run the documented evidence-publication reconciliation workflow.",
    ),
    "DBTOBSB_ATTEMPT_ROOT_READBACK_MISMATCH": (
        "evidence publication",
        "data operator",
        "Run the documented evidence-publication reconciliation workflow.",
    ),
    "DBTOBSB_ATTEMPT_ROOT_WRITE_INDETERMINATE": (
        "evidence publication",
        "data operator",
        "Run the documented evidence-publication reconciliation workflow.",
    ),
    "DBTOBSB_CHILD_READBACK_MISMATCH": (
        "evidence publication",
        "data operator",
        "Run the documented evidence-publication reconciliation workflow.",
    ),
    "DBTOBSB_PUBLISH_SENTINEL_NOT_COMMITTED": (
        "evidence publication",
        "data operator",
        "Run the documented evidence-publication reconciliation workflow.",
    ),
    "DBTOBSB_SUPPORT_MANIFEST_DBT_COMMON_VERSION_INVALID": (
        "release compatibility",
        "deployment/seal verifier",
        "Run the documented deployment-and-seal reconciliation workflow.",
    ),
    "DBTOBSB_SUPPORT_MANIFEST_LOG_VERSION_INVALID": (
        "release compatibility",
        "deployment/seal verifier",
        "Run the documented deployment-and-seal reconciliation workflow.",
    ),
    "DBTOBSB_ACCEPTED_TIMESTAMP_INVALID": (
        "artifact timestamp",
        "data operator",
        "Run the documented evidence-publication reconciliation workflow.",
    ),
}


class _SafeArgumentParser(argparse.ArgumentParser):
    """Reject invalid CLI input without echoing caller-controlled argv."""

    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError("DBTOBSB_ENTRYPOINT_ARGUMENTS_INVALID")


def bootstrap_operator_diagnostic(error: Exception) -> OperatorDiagnostic:
    """Map bootstrap failures to one safe owner and recovery workflow."""
    observed = str(error)
    code = (
        observed
        if observed
        in _BOOTSTRAP_CODES | _DEPLOYED_RUNTIME_CODES | {"DBTOBSB_DEPLOYMENT_BINDING_INVALID"}
        else "DBTOBSB_BOOTSTRAP_FAILED"
    )
    responsible_actor = "UC operator"
    if code == "DBTOBSB_BOOTSTRAP_ACTOR_SCHEMA_OWNER_MISMATCH":
        component = "schema ownership"
        action = "Run the documented schema-ownership reconciliation workflow."
    elif code == "DBTOBSB_BOOTSTRAP_TARGET_SCHEMA_NOT_FOUND":
        component = "customer schema prerequisite"
        action = "Run the documented schema-readiness workflow."
    elif code == "DBTOBSB_BOOTSTRAP_PARTIAL_INSTALL":
        component = "partial fresh installation"
        action = "Run the documented partial-install cleanup workflow."
    elif code in {
        "DBTOBSB_BOOTSTRAP_DIRECT_OBJECT_GRANTS_PRESENT",
        "DBTOBSB_BOOTSTRAP_GRANT_METADATA_INVALID",
    }:
        component = "evidence-object grants"
        action = "Run the documented evidence-object grant reconciliation workflow."
    elif code == "DBTOBSB_BOOTSTRAP_NATIVE_METADATA_UNAVAILABLE":
        component = "Databricks metadata compatibility"
        action = "Run the documented bootstrap compatibility reconciliation workflow."
    elif code == "DBTOBSB_BOOTSTRAP_SPARK_SESSION_UNAVAILABLE":
        component = "serverless Spark session"
        action = "Run the documented bootstrap compatibility reconciliation workflow."
    elif code in {
        "DBTOBSB_BOOTSTRAP_RELATION_INVENTORY_READ_FAILED",
        "DBTOBSB_BOOTSTRAP_SCHEMA_METADATA_READ_FAILED",
        "DBTOBSB_BOOTSTRAP_SESSION_USER_READ_FAILED",
        "DBTOBSB_BOOTSTRAP_VOLUME_INVENTORY_READ_FAILED",
    }:
        component = "serverless bootstrap metadata"
        action = "Run the documented bootstrap compatibility reconciliation workflow."
    elif code in {
        "DBTOBSB_BOOTSTRAP_MANIFEST_CREATE_FAILED",
        "DBTOBSB_BOOTSTRAP_MANIFEST_WRITE_FAILED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_FAILED",
        "DBTOBSB_BOOTSTRAP_VIEW_CREATE_FAILED",
        "DBTOBSB_BOOTSTRAP_VOLUME_CREATE_FAILED",
    }:
        component = "fresh-install object creation"
        action = "Run the documented evidence-object reconciliation workflow."
    elif code == "DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED":
        component = "table creation authorization"
        action = _PRE_APP_BOOTSTRAP_RECOVERY
    elif code == "DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE":
        component = "managed storage connectivity"
        action = _PRE_APP_BOOTSTRAP_RECOVERY
    elif code == "DBTOBSB_BOOTSTRAP_TABLE_CREATE_OBJECT_CONFLICT":
        component = "fresh-install table conflict"
        action = _PRE_APP_BOOTSTRAP_RECOVERY
    elif code == "DBTOBSB_BOOTSTRAP_TABLE_CREATE_PLATFORM_UNSUPPORTED":
        component = "serverless DDL support"
        action = _PRE_APP_BOOTSTRAP_RECOVERY
    elif code == "DBTOBSB_BOOTSTRAP_TABLE_CREATE_SQL_INCOMPATIBLE":
        component = "Databricks DDL compatibility"
        action = _PRE_APP_BOOTSTRAP_RECOVERY
    elif code == "DBTOBSB_BOOTSTRAP_TABLE_CREATE_INTERNAL_ERROR":
        component = "Databricks table creation runtime"
        action = _PRE_APP_BOOTSTRAP_RECOVERY
    elif code in {
        "DBTOBSB_BOOTSTRAP_DBT_POLICY_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_JOB_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH",
        "DBTOBSB_BOOTSTRAP_PRINCIPAL_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_WAREHOUSE_BINDING_INVALID",
        "DBTOBSB_BOOTSTRAP_WORKSPACE_BINDING_INVALID",
        "DBTOBSB_DEPLOYMENT_BINDING_INVALID",
        *_DEPLOYED_RUNTIME_CODES,
    }:
        component = "installed deployment binding"
        responsible_actor = "deployment/seal verifier"
        action = "Run the documented deployment-and-seal reconciliation workflow."
    else:
        component = "fresh-install object contract"
        action = "Run the documented evidence-object reconciliation workflow."
    return OperatorDiagnostic(
        code=code,
        outcome="denied",
        component=component,
        summary=f"Denied: the {component} is not ready for bootstrap.",
        consequence="Bootstrap stopped and runtime collection remains unavailable.",
        responsible_actor=responsible_actor,
        action=action,
    )


def collector_operator_diagnostic(error: Exception) -> OperatorDiagnostic:
    """Map every runtime escape to one static, non-sensitive recovery boundary."""
    observed = str(error)
    known = _COLLECTOR_FAILURES.get(observed)
    if known is None:
        code = "DBTOBSB_COLLECTOR_FAILED"
        component = "collector runtime"
        responsible_actor = "data operator"
        action = "Run the documented collector-runtime reconciliation workflow."
    else:
        code = observed
        component, responsible_actor, action = known
    return OperatorDiagnostic(
        code=code,
        outcome="denied",
        component=component,
        summary=f"Denied: the {component} did not complete the fixed collection workflow.",
        consequence="No published evidence was claimed for this collector execution.",
        responsible_actor=responsible_actor,
        action=action,
    )


def _active_spark() -> Any:
    spark_module = importlib.import_module("pyspark.sql")
    session_type = spark_module.SparkSession
    session = session_type.getActiveSession()
    if session is None:
        session = session_type.builder.getOrCreate()
    return session


def _active_bootstrap_spark() -> Any:
    """Start Spark behind a bootstrap-specific, non-sensitive failure code."""
    try:
        return _active_spark()
    except Exception:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_SPARK_SESSION_UNAVAILABLE") from None


def _positive_integer(value: str, *, field: str, allow_zero: bool = False) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a resolved decimal integer") from None
    minimum = 0 if allow_zero else 1
    if parsed < minimum or str(parsed) != value:
        raise ValueError(f"{field} must be a canonical resolved decimal integer")
    return parsed


def _run_bootstrap(
    *,
    workspace_id: str,
    catalog: str,
    schema: str,
    warehouse_id: str,
    observed_job_id: str,
    collector_job_id: str,
    reconciler_job_id: str,
    observed_service_principal_name: str,
    collector_service_principal_name: str,
    job_manager_group_name: str,
    collector_environment_sha256: str,
) -> None:
    deployed = load_deployed_runtime_contract()
    seal = deployed.seal
    parsed_workspace_id = _positive_integer(workspace_id, field="workspace_id")
    parsed_observed_job_id = _positive_integer(observed_job_id, field="observed_job_id")
    parsed_collector_job_id = _positive_integer(collector_job_id, field="collector_job_id")
    parsed_reconciler_job_id = _positive_integer(reconciler_job_id, field="reconciler_job_id")
    if (
        parsed_workspace_id != seal.workspace_id
        or catalog != seal.evidence_catalog
        or schema != seal.evidence_schema
        or warehouse_id != seal.warehouse_id
        or parsed_observed_job_id != seal.observed_job_id
        or parsed_collector_job_id != seal.collector_job_id
        or parsed_reconciler_job_id != seal.reconciler_job_id
        or observed_service_principal_name != seal.observed_service_principal_name
        or collector_service_principal_name != seal.collector_service_principal_name
        or job_manager_group_name != seal.job_manager_group_name
        or collector_environment_sha256 != seal.collector_environment_sha256
    ):
        raise RuntimeError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
    result = bootstrap_objects(
        _active_bootstrap_spark(),
        catalog=catalog,
        schema=schema,
        binding=InstallationBinding(
            workspace_id=parsed_workspace_id,
            warehouse_id=warehouse_id,
            source_contract_sha256=seal.source_contract_sha256,
            expected_runtime_policy_sha256=seal.expected_runtime_policy_sha256,
            observed_job_id=parsed_observed_job_id,
            collector_job_id=parsed_collector_job_id,
            reconciler_job_id=parsed_reconciler_job_id,
            observed_service_principal_name=observed_service_principal_name,
            collector_service_principal_name=collector_service_principal_name,
            job_manager_group_name=job_manager_group_name,
            collector_environment_sha256=collector_environment_sha256,
        ),
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
    deployed_runtime = load_deployed_runtime_contract()
    deployed_seal = deployed_runtime.seal
    policy = deployed_runtime.policy
    jobs_reader = DatabricksJobsEvidenceReader.for_installed_policy(
        installation_seal=deployed_seal,
        policy=policy,
    )
    jobs_reader.preflight(context)
    spark = _active_spark()
    installation_seal = read_installation_seal(
        spark,
        catalog=deployed_seal.evidence_catalog,
        schema=deployed_seal.evidence_schema,
    )
    if installation_seal != deployed_seal:
        raise RuntimeError("DBTOBSB_BOOTSTRAP_MANIFEST_ROW_MISMATCH")
    record = collect_task_run(
        context=context,
        jobs=jobs_reader,
        downloader=DatabricksArtifactDownloader(),
        raw_store=VolumeRawArchiveStore(
            (
                f"/Volumes/{deployed_seal.evidence_catalog}/"
                f"{deployed_seal.evidence_schema}/{RAW_VOLUME_NAME}"
            ),
            require_volume=True,
        ),
        sink=DeltaEvidenceSink(
            spark,
            catalog=deployed_seal.evidence_catalog,
            schema=deployed_seal.evidence_schema,
            installation_seal=deployed_seal,
        ),
        installed_policy=policy.installed_policy,
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
                "configuration_scope": "installed_policy_v1",
                "runtime_policy_sha256": policy.expected_runtime_policy_sha256,
                "installation_binding_evidence": "manifest_row_matches_release",
                "deployed_source_at_collection": "verified",
            },
            sort_keys=True,
        )
    )


def bootstrap() -> None:
    """Parse fixed bootstrap arguments passed by the Databricks wheel runner."""
    parser = _SafeArgumentParser(prog="dbtobsb-bootstrap", allow_abbrev=False)
    for name in (
        "workspace_id",
        "catalog",
        "schema",
        "warehouse_id",
        "observed_job_id",
        "collector_job_id",
        "reconciler_job_id",
        "observed_service_principal_name",
        "collector_service_principal_name",
        "job_manager_group_name",
        "collector_environment_sha256",
    ):
        parser.add_argument(f"--{name}", required=True)
    try:
        arguments = parser.parse_args()
        _run_bootstrap(
            workspace_id=arguments.workspace_id,
            catalog=arguments.catalog,
            schema=arguments.schema,
            warehouse_id=arguments.warehouse_id,
            observed_job_id=arguments.observed_job_id,
            collector_job_id=arguments.collector_job_id,
            reconciler_job_id=arguments.reconciler_job_id,
            observed_service_principal_name=arguments.observed_service_principal_name,
            collector_service_principal_name=arguments.collector_service_principal_name,
            job_manager_group_name=arguments.job_manager_group_name,
            collector_environment_sha256=arguments.collector_environment_sha256,
        )
    except Exception as error:
        print(
            json.dumps(
                bootstrap_operator_diagnostic(error).as_dict(),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from None


def uninstall_delete() -> None:
    """Delete only the verified v1 objects from the sealed installed schema."""

    parser = _SafeArgumentParser(prog="dbtobsb-uninstall-delete", allow_abbrev=False)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    try:
        arguments = parser.parse_args()
        deployed = load_deployed_runtime_contract()
        if (
            arguments.catalog != deployed.seal.evidence_catalog
            or arguments.schema != deployed.seal.evidence_schema
        ):
            raise RuntimeError("DBTOBSB_DEPLOYMENT_BINDING_INVALID")
        result = delete_installation_objects(
            _active_spark(),
            catalog=arguments.catalog,
            schema=arguments.schema,
        )
        print(
            json.dumps(
                {
                    "deleted_object_count": result.deleted_object_count,
                    "event": "dbtobsb_delete_uninstall_verified",
                    "schema_preserved": True,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
    except Exception as error:
        print(
            json.dumps(
                bootstrap_operator_diagnostic(error).as_dict(),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from None


def collect() -> None:
    """Parse fixed runtime arguments passed by the Databricks wheel runner."""
    parser = _SafeArgumentParser(prog="dbtobsb-collect", allow_abbrev=False)
    for name in (
        "workspace_id",
        "observed_job_id",
        "observed_job_run_id",
        "dbt_task_run_id",
        "observed_task_key",
        "repair_count",
        "execution_count",
    ):
        parser.add_argument(f"--{name}", required=True)
    try:
        arguments = parser.parse_args()
        _run_collect(
            workspace_id=arguments.workspace_id,
            observed_job_id=arguments.observed_job_id,
            observed_job_run_id=arguments.observed_job_run_id,
            dbt_task_run_id=arguments.dbt_task_run_id,
            observed_task_key=arguments.observed_task_key,
            repair_count=arguments.repair_count,
            execution_count=arguments.execution_count,
        )
    except JobsEvidenceError as exc:
        print(
            json.dumps(exc.operator_diagnostic().as_dict(), sort_keys=True, separators=(",", ":"))
        )
        raise SystemExit(1) from None
    except Exception as exc:
        print(
            json.dumps(
                collector_operator_diagnostic(exc).as_dict(),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from None


def _run_reconcile(
    *,
    workspace_id: str,
    reconciler_job_id: str,
    reconciliation_run_id: str,
) -> None:
    parsed_workspace_id = _positive_integer(workspace_id, field="workspace_id")
    parsed_job_id = _positive_integer(reconciler_job_id, field="reconciler_job_id")
    parsed_run_id = _positive_integer(reconciliation_run_id, field="reconciliation_run_id")
    deployed_runtime = load_deployed_runtime_contract()
    seal = deployed_runtime.seal
    controller = InstalledPolicyReconciliationController(
        installation_seal=seal,
        policy=deployed_runtime.policy,
    )
    controller.preflight(
        workspace_id=parsed_workspace_id,
        reconciler_job_id=parsed_job_id,
        reconciliation_run_id=parsed_run_id,
    )
    summary = reconcile_installed_policy(
        controller=controller,
        spark=_active_spark(),
        reconciliation_run_id=parsed_run_id,
    )
    print(
        json.dumps(
            {"event": "dbtobsb_reconciliation_completed", **summary},
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def reconcile() -> None:
    """Parse only the three native identities of the fixed reconciliation Job."""
    parser = _SafeArgumentParser(prog="dbtobsb-reconcile", allow_abbrev=False)
    for name in ("workspace_id", "reconciler_job_id", "reconciliation_run_id"):
        parser.add_argument(f"--{name}", required=True)
    try:
        arguments = parser.parse_args()
        _run_reconcile(
            workspace_id=arguments.workspace_id,
            reconciler_job_id=arguments.reconciler_job_id,
            reconciliation_run_id=arguments.reconciliation_run_id,
        )
    except Exception as error:
        observed = str(error)
        deployment_runtime_codes = {
            *_DEPLOYED_RUNTIME_CODES,
            "DBTOBSB_DELTA_ATTEMPT_BINDING_MISMATCH",
            "DBTOBSB_DELTA_INSTALLATION_BINDING_MISMATCH",
        }
        known_reconciliation_error = (
            isinstance(error, ReconciliationError) and observed in RECONCILIATION_OPERATOR_CODES
        )
        if known_reconciliation_error or observed in deployment_runtime_codes:
            code = observed
        else:
            code = "DBTOBSB_RECONCILIATION_FAILED"
        deployment_error = code in deployment_runtime_codes | {
            "DBTOBSB_RECONCILIATION_BINDING_MISMATCH",
            "DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH",
        }
        diagnostic = OperatorDiagnostic(
            code=code,
            outcome="denied",
            component="collection reconciliation",
            summary="Denied: the fixed collection reconciliation did not complete.",
            consequence="No complete reconciliation scan was claimed.",
            responsible_actor=("deployment/seal verifier" if deployment_error else "data operator"),
            action=(
                "Open /operators/how-to/reconcile-installation/ and reconcile the sealed "
                "installation binding and object manifest."
                if deployment_error
                else "Open /operators/how-to/reconcile-collection/ and follow the matching code."
            ),
        )
        print(json.dumps(diagnostic.as_dict(), sort_keys=True, separators=(",", ":")))
        raise SystemExit(1) from None


def main() -> None:
    """Explain the runtime-only entrypoints without exposing a dynamic command surface."""
    print("Use the fixed Databricks runtime wheel entrypoint 'collect' or 'reconcile'.")
