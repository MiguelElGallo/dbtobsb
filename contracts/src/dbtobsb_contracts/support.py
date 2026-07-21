"""Strict loader for the packaged dbtobsb v1 support contract."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from types import MappingProxyType
from typing import Any

_MANIFEST_NAME = "support-manifest-v1.json"
_TOP_LEVEL_KEYS = {
    "contract_version",
    "release_state",
    "platform",
    "installation",
    "customer_state",
    "dbt",
    "onboarding",
    "governed_output",
    "app",
    "lifecycle",
    "qualification",
    "outcome_axes",
    "distribution",
}
_PLATFORM_KEYS = {
    "cloud",
    "bundle_engine",
    "databricks_cli",
    "bootstrap_compute",
    "dbt_task_compute",
    "app_compute",
    "serverless_environment_client",
    "python",
}
_INSTALLATION_KEYS = {
    "mode",
    "launcher",
    "host",
    "authentication",
    "human_actor_count",
    "independent_human_separation",
    "data_mutation_observer_separation",
    "independent_sp_role_reviewer",
    "schema_requirement",
    "bootstrap_run_as",
    "bootstrap_job_lifecycle",
    "native_mutation_registry",
    "bundle_sql_hooks",
    "bootstrap_idempotency",
    "post_binding_resume",
    "runtime_trust_ledger",
}
_CUSTOMER_STATE_KEYS = {"schema_created", "objects", "direct_grants", "trusted_roots"}
_DBT_KEYS = {
    "adapter_type",
    "packages",
    "command_sequence",
    "primary_command",
    "selector_contract",
    "selector_pattern",
    "attempt_key_template",
    "attempt_root_template",
    "deps_ordinal",
    "build_ordinal",
    "manifest_schema",
    "manifest_schema_sha256",
    "manifest_schema_exceptions",
    "run_results_schema",
    "run_results_schema_sha256",
    "structured_log_version",
}
_ONBOARDING_KEYS = {
    "policy_contract_version",
    "source_type",
    "task_key",
    "environment_key",
    "project_directory",
    "profiles_directory",
    "profile_policy",
    "profile_target",
    "required_files",
    "excluded_roots",
    "selector_count",
    "dependency_definition_files",
    "dependency_lock_file",
    "dependency_policy",
    "generated_patch",
    "rollback",
    "policy_change",
    "release_change",
}
_OUTPUT_KEYS = {
    "anonymous_usage",
    "artifact_ingest_upload",
    "write_json",
    "file_log_format",
    "file_log_level",
    "file_log_max_bytes",
    "file_log_max_files",
    "file_log_total_max_bytes",
    "primary_artifact_max_bytes",
    "paths",
    "raw_archive_custody",
}
_APP_KEYS = {
    "initial_state",
    "installation_deployment_checks",
    "end_user_acl_provisioner",
    "start_command",
    "stop_command",
    "landing_queries",
    "load_action",
    "warehouse_may_auto_start_after_load",
    "browser_close_stops_compute",
    "dashboard_rendering",
    "dashboard_metrics",
    "resources",
    "first_answer",
}
_LIFECYCLE_KEYS = {"default_action", "operations"}
_LIFECYCLE_OPERATION_KEYS = {
    "action",
    "command",
    "approval",
    "persistent_state",
    "app_state",
    "jobs_state",
    "compute_state",
    "destructive",
    "safe_default",
    "indeterminate_action",
}
_QUALIFICATION_KEYS = {"local_cases", "live_cases"}
_DISTRIBUTION_KEYS = {
    "marketplace",
    "required_external_telemetry",
    "read_only_app",
    "production_use",
    "regulated_use",
}
_PACKAGE_KEYS = {
    "databricks-sdk",
    "databricks-sql-connector",
    "dbt-adapters",
    "dbt-common",
    "dbt-core",
    "dbt-databricks",
    "dbt-protos",
    "dbt-spark",
}
_PACKAGE_VERSIONS = {
    "databricks-sdk": "0.117.0",
    "databricks-sql-connector": "4.3.0",
    "dbt-adapters": "1.24.5",
    "dbt-common": "1.37.5",
    "dbt-core": "1.11.12",
    "dbt-databricks": "1.12.2",
    "dbt-protos": "1.0.541",
    "dbt-spark": "1.10.3",
}
_EXPECTED_CANONICAL_SHA256 = "00cd8d3633474ad8b5e8a9153aa55a44f02e00fc90ef61fbab7a8f302474a5e2"


def _mapping(value: Any, *, name: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"DBTOBSB_SUPPORT_MANIFEST_{name}_SHAPE_INVALID")
    if any(not isinstance(key, str) for key in value):
        raise ValueError(f"DBTOBSB_SUPPORT_MANIFEST_{name}_SHAPE_INVALID")
    return value


def _string(value: Any, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"DBTOBSB_SUPPORT_MANIFEST_{name}_INVALID")
    return value


def _sha256(value: Any, *, name: str) -> str:
    text = _string(value, name=name)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"DBTOBSB_SUPPORT_MANIFEST_{name}_INVALID")
    return text


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class SupportManifest:
    """Validated immutable compatibility contract shipped with a supported release."""

    contract_version: str
    release_state: str
    platform: Mapping[str, Any]
    installation: Mapping[str, Any]
    customer_state: Mapping[str, Any]
    dbt: Mapping[str, Any]
    onboarding: Mapping[str, Any]
    governed_output: Mapping[str, Any]
    app: Mapping[str, Any]
    lifecycle: Mapping[str, Any]
    qualification: Mapping[str, Any]
    outcome_axes: tuple[str, ...]
    distribution: Mapping[str, Any]
    canonical_sha256: str


def parse_support_manifest(raw: bytes) -> SupportManifest:
    """Parse exact UTF-8 JSON bytes and reject extensions or weakened v1 controls."""
    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    try:
        document = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_JSON_INVALID") from exc

    root = _mapping(document, name="ROOT", keys=_TOP_LEVEL_KEYS)
    platform = _mapping(root["platform"], name="PLATFORM", keys=_PLATFORM_KEYS)
    installation = _mapping(root["installation"], name="INSTALLATION", keys=_INSTALLATION_KEYS)
    customer_state = _mapping(
        root["customer_state"], name="CUSTOMER_STATE", keys=_CUSTOMER_STATE_KEYS
    )
    dbt = _mapping(root["dbt"], name="DBT", keys=_DBT_KEYS)
    onboarding = _mapping(root["onboarding"], name="ONBOARDING", keys=_ONBOARDING_KEYS)
    output = _mapping(root["governed_output"], name="OUTPUT", keys=_OUTPUT_KEYS)
    app = _mapping(root["app"], name="APP", keys=_APP_KEYS)
    lifecycle = _mapping(root["lifecycle"], name="LIFECYCLE", keys=_LIFECYCLE_KEYS)
    qualification = _mapping(root["qualification"], name="QUALIFICATION", keys=_QUALIFICATION_KEYS)
    distribution = _mapping(root["distribution"], name="DISTRIBUTION", keys=_DISTRIBUTION_KEYS)
    packages = _mapping(dbt["packages"], name="PACKAGES", keys=_PACKAGE_KEYS)

    expected_scalars = {
        "contract_version": "dbtobsb.support.v1",
        "release_state": "FINAL",
        "cloud": "AZURE_DATABRICKS",
        "bundle_engine": "DIRECT",
        "databricks_cli": "1.8.0",
        "bootstrap_compute": "SERVERLESS_LAKEFLOW_PYTHON_WHEEL_JOB",
        "dbt_task_compute": "SERVERLESS_LAKEFLOW_JOB",
        "app_compute": "DATABRICKS_APP_SERVERLESS",
        "serverless_environment_client": "5",
        "python": "3.12.3",
        "adapter_type": "databricks",
        "primary_command": "build",
        "selector_contract": "INSTALLED_NAMED_SELECTOR",
        "selector_pattern": "^[A-Za-z][A-Za-z0-9_-]{0,63}$",
        "attempt_key_template": (
            "w{{workspace.id}}-j{{job.id}}-r{{job.run_id}}-t{{task.run_id}}-"
            "p{{job.repair_count}}-e{{task.execution_count}}"
        ),
        "attempt_root_template": "$PWD/target/dbtobsb/attempts/{attempt_key}",
        "deps_ordinal": "000-deps",
        "build_ordinal": "001-build",
        "manifest_schema": "https://schemas.getdbt.com/dbt/manifest/v12.json",
        "manifest_schema_sha256": (
            "b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3"
        ),
        "run_results_schema": "https://schemas.getdbt.com/dbt/run-results/v6.json",
        "run_results_schema_sha256": (
            "1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf"
        ),
    }
    actual_scalars = {
        "contract_version": root["contract_version"],
        "release_state": root["release_state"],
        **{key: platform[key] for key in _PLATFORM_KEYS},
        **{
            key: dbt[key]
            for key in (
                "adapter_type",
                "primary_command",
                "selector_contract",
                "selector_pattern",
                "attempt_key_template",
                "attempt_root_template",
                "deps_ordinal",
                "build_ordinal",
                "manifest_schema",
                "manifest_schema_sha256",
                "run_results_schema",
                "run_results_schema_sha256",
            )
        },
    }
    if actual_scalars != expected_scalars:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_BASELINE_INVALID")

    if dbt["command_sequence"] != ["OPTIONAL_DEPS", "REQUIRED_BUILD"]:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_COMMAND_SEQUENCE_INVALID")
    if root["outcome_axes"] != [
        "LAKEFLOW_TASK",
        "ARTIFACT_RETRIEVAL",
        "ARTIFACT_PAIR",
        "DBT_INVOCATION",
        "COLLECTION",
    ]:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_OUTCOME_AXES_INVALID")
    if packages != _PACKAGE_VERSIONS:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_PACKAGE_VERSION_INVALID")

    _sha256(dbt["manifest_schema_sha256"], name="MANIFEST_SCHEMA_SHA256")
    _sha256(dbt["run_results_schema_sha256"], name="RUN_RESULTS_SCHEMA_SHA256")
    if dbt["manifest_schema_exceptions"] != [
        {
            "document_path": (
                "macros.macro.dbt.materialization_function_default.supported_languages"
            ),
            "schema_path": (
                "properties.macros.additionalProperties.properties.supported_languages.anyOf"
            ),
            "accepted_value": ["sql", "python", "javascript"],
        }
    ]:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_SCHEMA_EXCEPTION_INVALID")
    if dbt["structured_log_version"] != 3:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_LOG_VERSION_INVALID")
    expected_output = {
        "anonymous_usage": False,
        "artifact_ingest_upload": False,
        "write_json": True,
        "file_log_format": "json",
        "file_log_level": "info",
        "file_log_max_bytes": 20 * 1024 * 1024,
        "file_log_max_files": 6,
        "file_log_total_max_bytes": 120 * 1024 * 1024,
        "primary_artifact_max_bytes": 128 * 1024 * 1024,
        "paths": "PRODUCT_GENERATED_PER_ATTEMPT",
        "raw_archive_custody": "MANDATORY_FOR_EVERY_RETRIEVED_ARCHIVE",
    }
    if output != expected_output:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_OUTPUT_POLICY_INVALID")
    if distribution != {
        "marketplace": False,
        "required_external_telemetry": False,
        "read_only_app": True,
        "production_use": "ONLY_AFTER_LOCAL_RC_AND_LIVE_AZURE_GATES",
        "regulated_use": ("CUSTOMER_GOVERNANCE_APPROVAL_REQUIRED_NO_CERTIFICATION_OR_ATTESTATION"),
    }:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_DISTRIBUTION_INVALID")

    expected_installation = {
        "mode": "COMBINED_ROLE",
        "launcher": "dbtobsb bootstrap",
        "host": "MANAGED_MACOS_ARM64",
        "authentication": "DATABRICKS_CLI_OAUTH_U2M_NAMED_PROFILE",
        "human_actor_count": 1,
        "independent_human_separation": False,
        "data_mutation_observer_separation": False,
        "independent_sp_role_reviewer": False,
        "schema_requirement": "EXISTING_DEDICATED_SCHEMA_SESSION_USER_IS_OWNER",
        "bootstrap_run_as": "BUNDLE_DEPLOYER_COMBINED_ADMIN",
        "bootstrap_job_lifecycle": "TEMPORARY_REMOVE_AFTER_TERMINAL_READBACK",
        "native_mutation_registry": "FOUNDATION_NOT_INVOKED_V0_4",
        "bundle_sql_hooks": False,
        "bootstrap_idempotency": "EXACT_PRE_BINDING_ONLY",
        "post_binding_resume": "LIFECYCLE_READBACK_NO_BOOTSTRAP_REPLAY",
        "runtime_trust_ledger": "NOT_IN_V0_4_SUPPORTED_PATH",
    }
    if installation != expected_installation:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_INSTALLATION_INVALID")
    if customer_state["schema_created"] is not False:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_CUSTOMER_STATE_INVALID")
    objects = customer_state["objects"]
    if not isinstance(objects, list) or any(
        not isinstance(item, dict) or set(item) != {"name", "kind"} for item in objects
    ):
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_CUSTOMER_STATE_INVALID")
    if [item["name"] for item in objects] != [
        "dbtobsb_object_manifest",
        "dbt_artifact_registry",
        "dbt_invocations",
        "dbt_node_results",
        "dbt_run_health",
        "dbt_node_health",
        "dbt_collection_health",
        "dbtobsb_raw",
        "dbtobsb_stage",
    ]:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_CUSTOMER_STATE_INVALID")
    grants = customer_state["direct_grants"]
    if not isinstance(grants, list) or len(grants) != 18:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_GRANTS_INVALID")
    if any(
        not isinstance(item, dict)
        or set(item) != {"principal", "securable", "privileges", "provisioner"}
        or not isinstance(item["privileges"], list)
        for item in grants
    ):
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_GRANTS_INVALID")
    if customer_state["trusted_roots"] != [
        "SCHEMA_AND_OBJECT_OWNER",
        "CATALOG_OR_METASTORE_ADMIN",
        "WORKSPACE_ADMIN",
        "JOB_MANAGER_GROUP",
        "APP_MANAGER",
    ]:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_CUSTOMER_STATE_INVALID")

    expected_onboarding = {
        "policy_contract_version": "dbtobsb.dbt-policy.v1",
        "source_type": "WORKSPACE",
        "task_key": "dbt_build",
        "environment_key": "dbt",
        "project_directory": "PRODUCT_GENERATED_BUNDLE_RELATIVE_SNAPSHOT",
        "profiles_directory": "MATCH_PROJECT_DIRECTORY",
        "profile_policy": "PRODUCT_GENERATED_PROJECT_ROOT_PROFILE",
        "profile_target": {
            "profile_name_source": "DBT_PROJECT_YML_PROFILE_SCALAR",
            "profile_name_pattern": "^[A-Za-z][A-Za-z0-9_-]{0,127}$",
            "target_name": "dbtobsb",
            "connection_source": "PRODUCT_GENERATED_PROJECT_ROOT_PROFILE",
            "dbt_task_warehouse_id": "ABSENT_CUSTOM_PROFILE",
            "dbt_task_catalog": "ABSENT_CUSTOM_PROFILE",
            "dbt_task_schema": "ABSENT_CUSTOM_PROFILE",
            "dbt_task_profiles_directory": "MATCH_PROJECT_DIRECTORY",
            "output_keys": [
                "type",
                "method",
                "host",
                "http_path",
                "token",
                "catalog",
                "schema",
                "threads",
            ],
            "type": "databricks",
            "method": "http",
            "host": "INSTALLER_RENDERED_CANONICAL_WORKSPACE_SERVER_HOSTNAME",
            "host_source": "AUTHENTICATED_NAMED_DATABRICKS_CLI_PROFILE",
            "host_canonicalization": "HTTPS_AZURE_WORKSPACE_URL_TO_LOWERCASE_DNS_NAME",
            "http_path": "INSTALLER_RESOLVED_EXISTING_SQL_WAREHOUSE_HTTP_PATH",
            "token": "{{ env_var('DBT_ACCESS_TOKEN') }}",
            "catalog": "INSTALLER_RENDERED_LITERAL_CATALOG",
            "schema": "INSTALLER_RENDERED_LITERAL_SCHEMA",
            "threads": 1,
            "secret_values_in_snapshot": False,
            "run_as_authentication": "DATABRICKS_INJECTED_DBT_ACCESS_TOKEN",
            "operator_supplied_connection_fields": [],
        },
        "required_files": ["dbt_project.yml", "profiles.yml", "selectors.yml"],
        "excluded_roots": ["logs", "target"],
        "selector_count": 1,
        "dependency_definition_files": ["dependencies.yml", "packages.yml"],
        "dependency_lock_file": "package-lock.yml",
        "dependency_policy": "NO_DEPENDENCIES_OR_COMMITTED_MATCHING_LOCK",
        "generated_patch": "SOURCE_CONTROLLED_NON_MUTATING_UNTIL_APPROVED",
        "rollback": "RESTORE_PREVIOUS_JOB_DEFINITION",
        "policy_change": "RESCAN_AND_REAPPROVE_WITHIN_SUPPORT_MANIFEST",
        "release_change": "NEW_SUPPORT_MANIFEST_RELEASE_AND_LIVE_QUALIFICATION",
    }
    if onboarding != expected_onboarding:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_ONBOARDING_INVALID")
    if app != {
        "initial_state": "STOPPED",
        "installation_deployment_checks": 1,
        "end_user_acl_provisioner": "TARGETED_APPS_PERMISSION_API_WHILE_STOPPED",
        "start_command": "dbtobsb start",
        "stop_command": "dbtobsb stop",
        "landing_queries": False,
        "load_action": "EXPLICIT_LOAD_OBSERVABILITY",
        "warehouse_may_auto_start_after_load": True,
        "browser_close_stops_compute": False,
        "dashboard_rendering": "NATIVE_SERVER_RENDERED_APP_NO_EXTERNAL_DASHBOARD_RESOURCE",
        "dashboard_metrics": [
            "FAILED_NODE_RESULTS_PER_RUN",
            "MODEL_RESULTS_PER_RUN",
        ],
        "resources": [
            "APP_QUERY_WAREHOUSE",
            "dbt_run_health",
            "dbt_node_health",
            "dbt_collection_health",
        ],
        "first_answer": [
            "LAKEFLOW_TASK",
            "ARTIFACT_RETRIEVAL",
            "ARTIFACT_PAIR",
            "DBT_INVOCATION",
            "NODE_RESULTS",
            "COLLECTION",
            "NEXT_ACTION",
        ],
    }:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_APP_INVALID")

    operations = lifecycle["operations"]
    if not isinstance(operations, list) or any(
        not isinstance(item, dict) or set(item) != _LIFECYCLE_OPERATION_KEYS for item in operations
    ):
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_LIFECYCLE_INVALID")
    expected_actions = [
        "BOOTSTRAP",
        "RESUME",
        "START",
        "STOP",
        "RETAIN_UNINSTALL",
        "DELETE_UNINSTALL",
    ]
    if (
        lifecycle["default_action"] != "STOP"
        or [item["action"] for item in operations] != expected_actions
    ):
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_LIFECYCLE_INVALID")
    operation_by_action = {item["action"]: item for item in operations}
    if (
        sum(item["safe_default"] is True for item in operations) != 1
        or operation_by_action["STOP"]["safe_default"] is not True
        or operation_by_action["DELETE_UNINSTALL"]["destructive"] is not True
    ):
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_LIFECYCLE_INVALID")
    if (
        not isinstance(qualification["local_cases"], list)
        or not isinstance(qualification["live_cases"], list)
        or len(qualification["local_cases"]) != len(set(qualification["local_cases"]))
        or len(qualification["live_cases"]) != len(set(qualification["live_cases"]))
        or "ZERO_PRODUCT_STARTED_COMPUTE" not in qualification["live_cases"]
    ):
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_QUALIFICATION_INVALID")

    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    canonical_sha256 = hashlib.sha256(canonical.encode()).hexdigest()
    if canonical_sha256 != _EXPECTED_CANONICAL_SHA256:
        raise ValueError("DBTOBSB_SUPPORT_MANIFEST_BASELINE_DIGEST_INVALID")
    return SupportManifest(
        contract_version=_string(root["contract_version"], name="CONTRACT_VERSION"),
        release_state=_string(root["release_state"], name="RELEASE_STATE"),
        platform=_deep_freeze(platform),
        installation=_deep_freeze(installation),
        customer_state=_deep_freeze(customer_state),
        dbt=_deep_freeze(dbt),
        onboarding=_deep_freeze(onboarding),
        governed_output=_deep_freeze(output),
        app=_deep_freeze(app),
        lifecycle=_deep_freeze(lifecycle),
        qualification=_deep_freeze(qualification),
        outcome_axes=tuple(root["outcome_axes"]),
        distribution=_deep_freeze(distribution),
        canonical_sha256=canonical_sha256,
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DBTOBSB_SUPPORT_MANIFEST_DUPLICATE_KEY")
        result[key] = value
    return result


def load_support_manifest() -> SupportManifest:
    """Load the exact manifest packaged in the installed distribution."""
    raw = files("dbtobsb_contracts").joinpath(_MANIFEST_NAME).read_bytes()
    return parse_support_manifest(raw)
