"""Prove the Bundle and generated dbt onboarding match the packaged support contract."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NoReturn, cast

import yaml

from dbtobsb_contracts import (
    DbtRuntimePolicySnapshot,
    OperatorDiagnostic,
    load_support_manifest,
    parse_dbt_runtime_policy,
)

_REPO_ROOT = Path(__file__).parents[2]
_BUNDLE_PATH = _REPO_ROOT / "databricks.yml"
_OBSERVED_JOB_KEY = "dbtobsb_observed"
_DBT_TASK_KEY = "dbt_build"
_COLLECT_TASK_KEY = "collect_dbt_evidence"
_ONBOARDING_PROJECT = re.compile(r"^\./dbtobsb_onboarding/(?P<source>[0-9a-f]{64})/project$")
_INSTALLED_ONBOARDING_PROJECT = re.compile(
    r"^\$\{workspace\.file_path\}/dbtobsb_onboarding/(?P<source>[0-9a-f]{64})/project$"
)
_ROOT_FIELDS = frozenset(
    {"bundle", "include", "sync", "variables", "artifacts", "resources", "targets"}
)
_BUNDLE_FIELDS = frozenset({"name", "databricks_cli_version", "engine"})
_INCLUDE_FILES = (
    ".dbtobsb-observed.generated.yml",
    ".dbtobsb-app-bindings.generated.yml",
    ".dbtobsb-bundle-base/*.yml",
)
_SYNC_EXCLUDES = (
    "app/tests/**",
    "capture/tests/**",
    "collector/tests/**",
    "contracts/tests/**",
)
_SYNC_INCLUDES = ("dbtobsb_onboarding/**",)
_VARIABLE_FIELDS = frozenset({"description", "default"})
_VARIABLE_KEYS = frozenset(
    {
        "warehouse_id",
        "evidence_catalog",
        "evidence_schema",
        "observed_service_principal_name",
        "collector_service_principal_name",
        "job_manager_group_name",
        "contracts_wheel_filename",
        "capture_wheel_filename",
        "collector_wheel_filename",
    }
)
_VARIABLE_DEFAULTS = {
    "warehouse_id": "0000000000000000",
    "evidence_catalog": "replace_me",
    "evidence_schema": "dbtobsb",
    "observed_service_principal_name": "replace_me",
    "collector_service_principal_name": "replace_me",
    "job_manager_group_name": "replace_me",
    "contracts_wheel_filename": "dbtobsb_contracts-0.5.0-py3-none-any.whl",
    "capture_wheel_filename": "dbtobsb_capture-0.5.0-py3-none-any.whl",
    "collector_wheel_filename": "dbtobsb_collector-0.5.0-py3-none-any.whl",
}
_EXPECTED_ARTIFACTS = {
    "contracts_wheel": {
        "type": "whl",
        "path": "./contracts",
        "build": "uv build --wheel --out-dir dist --no-create-gitignore",
        "files": [{"source": "./contracts/dist/${var.contracts_wheel_filename}"}],
    },
    "capture_wheel": {
        "type": "whl",
        "path": "./capture",
        "build": "uv build --wheel --out-dir dist --no-create-gitignore",
        "files": [{"source": "./capture/dist/${var.capture_wheel_filename}"}],
    },
    "collector_wheel": {
        "type": "whl",
        "path": "./collector",
        "build": "uv build --wheel --out-dir dist --no-create-gitignore",
        "files": [{"source": "./collector/dist/${var.collector_wheel_filename}"}],
    },
}
_OBSERVED_JOB_FIELDS = frozenset(
    {
        "name",
        "description",
        "max_concurrent_runs",
        "timeout_seconds",
        "performance_target",
        "run_as",
        "permissions",
        "tasks",
        "environments",
    }
)
_DBT_RUNNER_FIELDS = frozenset({"package_name", "entry_point", "parameters"})
_DBT_TASK_WRAPPER_FIELDS = frozenset(
    {
        "task_key",
        "timeout_seconds",
        "max_retries",
        "retry_on_timeout",
        "environment_key",
        "python_wheel_task",
    }
)
_COLLECT_TASK_WRAPPER_FIELDS = frozenset(
    {
        "task_key",
        "depends_on",
        "run_if",
        "timeout_seconds",
        "max_retries",
        "retry_on_timeout",
        "run_job_task",
    }
)
_COLLECT_JOB_PARAMETERS = {
    "workspace_id": "{{workspace.id}}",
    "observed_job_id": "{{job.id}}",
    "observed_job_run_id": "{{job.run_id}}",
    "dbt_task_run_id": "{{tasks.dbt_build.run_id}}",
    "observed_task_key": "dbt_build",
    "repair_count": "{{job.repair_count}}",
    "execution_count": "{{tasks.dbt_build.execution_count}}",
}
_DBT_RUNNER_PARAMETER_PREFIX = (
    "--workspace_id",
    "{{workspace.id}}",
    "--observed_job_id",
    "{{job.id}}",
    "--observed_job_run_id",
    "{{job.run_id}}",
    "--dbt_task_run_id",
    "{{task.run_id}}",
    "--repair_count",
    "{{job.repair_count}}",
    "--execution_count",
    "{{task.execution_count}}",
    "--project_directory",
)
_COLLECTOR_JOB_PARAMETER_DEFAULTS = {
    "workspace_id": "0",
    "observed_job_id": "0",
    "observed_job_run_id": "0",
    "dbt_task_run_id": "0",
    "observed_task_key": "unresolved",
    "repair_count": "0",
    "execution_count": "0",
}
_COLLECTOR_TASK_PARAMETERS = (
    "--workspace_id",
    "{{job.parameters.workspace_id}}",
    "--observed_job_id",
    "{{job.parameters.observed_job_id}}",
    "--observed_job_run_id",
    "{{job.parameters.observed_job_run_id}}",
    "--dbt_task_run_id",
    "{{job.parameters.dbt_task_run_id}}",
    "--observed_task_key",
    "{{job.parameters.observed_task_key}}",
    "--repair_count",
    "{{job.parameters.repair_count}}",
    "--execution_count",
    "{{job.parameters.execution_count}}",
)
_RECONCILER_TASK_PARAMETERS = (
    "--workspace_id",
    "{{workspace.id}}",
    "--reconciler_job_id",
    "{{job.id}}",
    "--reconciliation_run_id",
    "{{job.run_id}}",
)
_COLLECTOR_RUN_AS = {"service_principal_name": "${var.collector_service_principal_name}"}
_OBSERVED_RUN_AS = {"service_principal_name": "${var.observed_service_principal_name}"}
_COLLECTOR_PERMISSIONS = (
    {
        "level": "CAN_VIEW",
        "service_principal_name": "${var.collector_service_principal_name}",
    },
    {
        "level": "CAN_MANAGE_RUN",
        "service_principal_name": "${var.observed_service_principal_name}",
    },
    {"level": "CAN_MANAGE", "group_name": "${var.job_manager_group_name}"},
)
_OBSERVED_PERMISSIONS = (
    {
        "level": "CAN_VIEW",
        "service_principal_name": "${var.collector_service_principal_name}",
    },
    {"level": "CAN_MANAGE", "group_name": "${var.job_manager_group_name}"},
)
_RECONCILER_PERMISSIONS = (
    {
        "level": "CAN_VIEW",
        "service_principal_name": "${var.collector_service_principal_name}",
    },
    {"level": "CAN_MANAGE", "group_name": "${var.job_manager_group_name}"},
)
_DBT_ENVIRONMENT_WRAPPER_FIELDS = frozenset({"environment_key", "spec"})
_DBT_ENVIRONMENT_FIELDS = frozenset({"client", "dependencies"})
_COLLECTOR_ENVIRONMENT_DEPENDENCIES = (
    "./contracts/dist/${var.contracts_wheel_filename}",
    "./capture/dist/${var.capture_wheel_filename}",
    "./collector/dist/${var.collector_wheel_filename}",
    "databricks-sdk==0.117.0",
)
_GENERATED_SOURCE_ROOTS = frozenset({"logs", "target"})


class BundleContractError(ValueError):
    """Stable failure raised when the Bundle or generated onboarding drifts."""


def _bundle_component(code: str) -> str:
    if any(token in code for token in ("COLLECT", "JOB_PARAMETERS")):
        return "collector handoff"
    if any(token in code for token in ("TARGET", "VARIABLE")):
        return "deployment target binding"
    if any(
        token in code
        for token in (
            "SOURCE",
            "PROJECT",
            "PROFILE",
            "SELECTOR",
            "POLICY",
            "ONBOARDED",
        )
    ):
        return "onboarded dbt source"
    if any(
        token in code
        for token in ("COMMAND", "DEPENDENCY", "ENVIRONMENT", "SERVERLESS", "PACKAGES")
    ):
        return "dbt runtime contract"
    if "DBT_TASK" in code:
        return "dbt task policy"
    return "Bundle release envelope"


def bundle_failure_diagnostic(error: BundleContractError) -> OperatorDiagnostic:
    """Map every internal checker code to one non-sensitive operator recovery."""
    code = str(error)
    component = _bundle_component(code)
    return OperatorDiagnostic(
        code=code,
        outcome="denied",
        component=component,
        summary=f"Denied: the {component} differs from the generated release contract.",
        consequence="No Databricks Job was run by this local check.",
        responsible_actor="deployment/seal verifier",
        action="Regenerate onboarding and rerun the Bundle contract check.",
    )


def bundle_success_diagnostic() -> OperatorDiagnostic:
    """Describe the narrow local proof without claiming a deployment seal."""
    return OperatorDiagnostic(
        code="DBTOBSB_BUNDLE_DBT_CONTRACT_OK",
        outcome="accepted",
        component="local generated onboarding and Bundle contract",
        summary="Accepted for the supported private release.",
        consequence="Installed deployment integrity is not sealed or verified by this check.",
        responsible_actor="deployment/seal verifier",
        action="Continue with the documented deployment-and-seal workflow.",
    )


def _print_diagnostic(diagnostic: OperatorDiagnostic, *, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(diagnostic.as_dict(), sort_keys=True, separators=(",", ":")))
    else:
        print(diagnostic.human())


def _fail(code: str) -> NoReturn:
    raise BundleContractError(code)


def _mapping(value: object, *, code: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        _fail(code)
    return cast(Mapping[str, object], value)


def _sequence(value: object, *, code: str) -> Sequence[object]:
    if not isinstance(value, list):
        _fail(code)
    return value


def _string_sequence(value: object, *, code: str) -> tuple[str, ...]:
    values = _sequence(value, code=code)
    if any(not isinstance(item, str) for item in values):
        _fail(code)
    return tuple(item for item in values if isinstance(item, str))


def _one_mapping(
    values: Sequence[object], *, key: str, expected: str, code: str
) -> Mapping[str, object]:
    mappings = tuple(_mapping(value, code=code) for value in values)
    matches = tuple(value for value in mappings if value.get(key) == expected)
    if len(matches) != 1:
        _fail(code)
    return matches[0]


def _load_yaml(path: Path, *, invalid_code: str) -> Mapping[str, object]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise BundleContractError(invalid_code) from exc
    return _mapping(document, code=invalid_code)


def _validate_bundle_envelope(root: Mapping[str, object]) -> None:
    if frozenset(root) != _ROOT_FIELDS:
        _fail("DBTOBSB_BUNDLE_ROOT_EXTENSION_UNSUPPORTED")

    if _string_sequence(root.get("include"), code="DBTOBSB_BUNDLE_INCLUDE_INVALID") != (
        _INCLUDE_FILES
    ):
        _fail("DBTOBSB_BUNDLE_INCLUDE_INVALID")

    sync = _mapping(root.get("sync"), code="DBTOBSB_BUNDLE_SYNC_INVALID")
    if (
        frozenset(sync) != {"exclude", "include"}
        or _string_sequence(sync.get("include"), code="DBTOBSB_BUNDLE_SYNC_INVALID")
        != _SYNC_INCLUDES
        or _string_sequence(sync.get("exclude"), code="DBTOBSB_BUNDLE_SYNC_INVALID")
        != _SYNC_EXCLUDES
    ):
        _fail("DBTOBSB_BUNDLE_SYNC_INVALID")

    variables = _mapping(root.get("variables"), code="DBTOBSB_BUNDLE_VARIABLES_INVALID")
    if frozenset(variables) != _VARIABLE_KEYS:
        _fail("DBTOBSB_BUNDLE_VARIABLES_INVALID")
    for key, value in variables.items():
        variable = _mapping(value, code="DBTOBSB_BUNDLE_VARIABLES_INVALID")
        if (
            frozenset(variable) != _VARIABLE_FIELDS
            or variable.get("default") != _VARIABLE_DEFAULTS[key]
        ):
            _fail("DBTOBSB_BUNDLE_VARIABLES_INVALID")

    artifacts = _mapping(root.get("artifacts"), code="DBTOBSB_BUNDLE_ARTIFACTS_INVALID")
    if artifacts != _EXPECTED_ARTIFACTS:
        _fail("DBTOBSB_BUNDLE_ARTIFACTS_INVALID")

    targets = _mapping(root.get("targets"), code="DBTOBSB_BUNDLE_TARGET_INVALID")
    if frozenset(targets) != {"smoke"}:
        _fail("DBTOBSB_BUNDLE_TARGET_INVALID")
    smoke = _mapping(targets.get("smoke"), code="DBTOBSB_BUNDLE_TARGET_INVALID")
    if frozenset(smoke) != {"default", "workspace"} or smoke.get("default") is not True:
        _fail("DBTOBSB_BUNDLE_TARGET_INVALID")
    workspace = _mapping(smoke.get("workspace"), code="DBTOBSB_BUNDLE_TARGET_INVALID")
    if workspace != {"root_path": "/Workspace/dbtobsb/.bundle/${bundle.name}/${bundle.target}"}:
        _fail("DBTOBSB_BUNDLE_TARGET_INVALID")


def _load_and_validate_onboarded_policy(
    *, bundle_path: Path, project_directory: str
) -> DbtRuntimePolicySnapshot:
    bundle_root = bundle_path.parent.resolve()
    match = _INSTALLED_ONBOARDING_PROJECT.fullmatch(project_directory)
    if match is None:
        _fail("DBTOBSB_BUNDLE_PROJECT_DIRECTORY_DRIFT")
    declared_project_directory = f"./dbtobsb_onboarding/{match.group('source')}/project"
    project_root = (bundle_root / declared_project_directory).resolve()
    expected_root = bundle_root / "dbtobsb_onboarding" / match.group("source") / "project"
    if (
        not project_root.is_relative_to(bundle_root)
        or project_root != expected_root.resolve()
        or project_root.is_symlink()
        or not project_root.is_dir()
    ):
        _fail("DBTOBSB_BUNDLE_PROJECT_DIRECTORY_DRIFT")
    policy_path = project_root.parent / "dbt-policy-v1.json"
    try:
        policy = parse_dbt_runtime_policy(policy_path.read_bytes())
    except (OSError, ValueError):
        _fail("DBTOBSB_BUNDLE_DBT_POLICY_INVALID")
    if (
        policy.project_directory != declared_project_directory
        or policy.profiles_directory != declared_project_directory
        or policy.source_contract_sha256 != match.group("source")
    ):
        _fail("DBTOBSB_BUNDLE_DBT_POLICY_INVALID")

    expected_files = frozenset(policy.source_sha256)
    actual_files: set[str] = set()
    try:
        candidates = tuple(project_root.rglob("*"))
    except OSError as exc:
        raise BundleContractError("DBTOBSB_ONBOARDED_SOURCE_FILE_SET_DRIFT") from exc
    for candidate in candidates:
        relative = candidate.relative_to(project_root)
        if relative.parts and relative.parts[0] in _GENERATED_SOURCE_ROOTS:
            continue
        if candidate.is_symlink():
            _fail("DBTOBSB_ONBOARDED_SOURCE_FILE_SET_DRIFT")
        if candidate.is_file():
            actual_files.add(relative.as_posix())
    if actual_files != expected_files:
        _fail("DBTOBSB_ONBOARDED_SOURCE_FILE_SET_DRIFT")

    actual_hashes: dict[str, str] = {}
    try:
        for relative in sorted(expected_files):
            actual_hashes[relative] = hashlib.sha256(
                (project_root / relative).read_bytes()
            ).hexdigest()
    except OSError as exc:
        raise BundleContractError("DBTOBSB_ONBOARDED_SOURCE_HASH_DRIFT") from exc
    if actual_hashes != dict(policy.source_sha256):
        _fail("DBTOBSB_ONBOARDED_SOURCE_HASH_DRIFT")
    return policy


def _validate_collector_wrapper(tasks: Sequence[object]) -> None:
    collect = _one_mapping(
        tasks,
        key="task_key",
        expected=_COLLECT_TASK_KEY,
        code="DBTOBSB_BUNDLE_COLLECT_TASK_INVALID",
    )
    if frozenset(collect) != _COLLECT_TASK_WRAPPER_FIELDS:
        _fail("DBTOBSB_BUNDLE_COLLECT_TASK_INVALID")
    if (
        collect.get("timeout_seconds") != 900
        or collect.get("max_retries") != 0
        or collect.get("retry_on_timeout") is not False
        or collect.get("run_if") != "ALL_DONE"
        or collect.get("depends_on") != [{"task_key": _DBT_TASK_KEY}]
    ):
        _fail("DBTOBSB_BUNDLE_COLLECT_TASK_INVALID")
    run_job = _mapping(collect.get("run_job_task"), code="DBTOBSB_BUNDLE_COLLECT_TASK_INVALID")
    if (
        frozenset(run_job) != {"job_id", "job_parameters"}
        or run_job.get("job_id") != "${resources.jobs.dbtobsb_collector.id}"
    ):
        _fail("DBTOBSB_BUNDLE_COLLECT_TASK_INVALID")
    parameters = _mapping(run_job.get("job_parameters"), code="DBTOBSB_BUNDLE_COLLECT_TASK_INVALID")
    if parameters != _COLLECT_JOB_PARAMETERS:
        _fail("DBTOBSB_BUNDLE_COLLECT_TASK_INVALID")


def _validate_collector_environment(job: Mapping[str, object], *, code: str) -> None:
    environments = _sequence(job.get("environments"), code=code)
    if len(environments) != 1:
        _fail(code)
    environment = _mapping(environments[0], code=code)
    if frozenset(environment) != _DBT_ENVIRONMENT_WRAPPER_FIELDS:
        _fail(code)
    if environment.get("environment_key") != "collector":
        _fail(code)
    spec = _mapping(environment.get("spec"), code=code)
    if (
        frozenset(spec) != _DBT_ENVIRONMENT_FIELDS
        or spec.get("client") != "5"
        or _string_sequence(spec.get("dependencies"), code=code)
        != _COLLECTOR_ENVIRONMENT_DEPENDENCIES
    ):
        _fail(code)


def _validate_runtime_jobs(jobs: Mapping[str, object]) -> None:
    if frozenset(jobs) != {"dbtobsb_collector", "dbtobsb_reconciler", _OBSERVED_JOB_KEY}:
        _fail("DBTOBSB_BUNDLE_JOBS_INVALID")

    collector = _mapping(jobs.get("dbtobsb_collector"), code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    if frozenset(collector) != {
        "name",
        "description",
        "max_concurrent_runs",
        "timeout_seconds",
        "performance_target",
        "run_as",
        "permissions",
        "parameters",
        "tasks",
        "environments",
    } or (
        collector.get("name"),
        collector.get("max_concurrent_runs"),
        collector.get("timeout_seconds"),
        collector.get("performance_target"),
    ) != (
        "dbtobsb-collector",
        1,
        900,
        "STANDARD",
    ):
        _fail("DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    if (
        _mapping(collector.get("run_as"), code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
        != _COLLECTOR_RUN_AS
        or tuple(
            _mapping(item, code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
            for item in _sequence(
                collector.get("permissions"),
                code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID",
            )
        )
        != _COLLECTOR_PERMISSIONS
    ):
        _fail("DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    job_parameters = _sequence(
        collector.get("parameters"), code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID"
    )
    actual_defaults = {
        str(parameter.get("name")): parameter.get("default")
        for value in job_parameters
        for parameter in [_mapping(value, code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")]
        if frozenset(parameter) == {"name", "default"}
    }
    if len(job_parameters) != len(_COLLECTOR_JOB_PARAMETER_DEFAULTS) or (
        actual_defaults != _COLLECTOR_JOB_PARAMETER_DEFAULTS
    ):
        _fail("DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    collector_tasks = _sequence(collector.get("tasks"), code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    if len(collector_tasks) != 1:
        _fail("DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    collector_task = _mapping(collector_tasks[0], code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    if frozenset(collector_task) != {
        "task_key",
        "timeout_seconds",
        "max_retries",
        "retry_on_timeout",
        "environment_key",
        "python_wheel_task",
    } or (
        collector_task.get("task_key"),
        collector_task.get("timeout_seconds"),
        collector_task.get("max_retries"),
        collector_task.get("retry_on_timeout"),
        collector_task.get("environment_key"),
    ) != ("collect", 900, 0, False, "collector"):
        _fail("DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    collector_wheel = _mapping(
        collector_task.get("python_wheel_task"), code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID"
    )
    if (
        frozenset(collector_wheel) != {"package_name", "entry_point", "parameters"}
        or collector_wheel.get("package_name") != "dbtobsb-collector"
        or collector_wheel.get("entry_point") != "collect"
        or _string_sequence(
            collector_wheel.get("parameters"), code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID"
        )
        != _COLLECTOR_TASK_PARAMETERS
    ):
        _fail("DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")
    _validate_collector_environment(collector, code="DBTOBSB_BUNDLE_COLLECTOR_JOB_INVALID")

    reconciler = _mapping(
        jobs.get("dbtobsb_reconciler"), code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID"
    )
    expected_fields = {
        "name",
        "description",
        "max_concurrent_runs",
        "timeout_seconds",
        "performance_target",
        "run_as",
        "permissions",
        "schedule",
        "tasks",
        "environments",
    }
    if frozenset(reconciler) != expected_fields or (
        reconciler.get("name"),
        reconciler.get("max_concurrent_runs"),
        reconciler.get("timeout_seconds"),
        reconciler.get("performance_target"),
    ) != ("dbtobsb-reconciler", 1, 900, "STANDARD"):
        _fail("DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
    if (
        _mapping(reconciler.get("run_as"), code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
        != _COLLECTOR_RUN_AS
        or tuple(
            _mapping(item, code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
            for item in _sequence(
                reconciler.get("permissions"),
                code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID",
            )
        )
        != _RECONCILER_PERMISSIONS
        or _mapping(reconciler.get("schedule"), code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
        != {
            "quartz_cron_expression": "0 0/15 * * * ?",
            "timezone_id": "UTC",
            "pause_status": "PAUSED",
        }
    ):
        _fail("DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
    reconcile_tasks = _sequence(
        reconciler.get("tasks"), code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID"
    )
    if len(reconcile_tasks) != 1:
        _fail("DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
    reconcile_task = _mapping(reconcile_tasks[0], code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
    if frozenset(reconcile_task) != {
        "task_key",
        "timeout_seconds",
        "max_retries",
        "retry_on_timeout",
        "environment_key",
        "python_wheel_task",
    } or (
        reconcile_task.get("task_key"),
        reconcile_task.get("timeout_seconds"),
        reconcile_task.get("max_retries"),
        reconcile_task.get("retry_on_timeout"),
        reconcile_task.get("environment_key"),
    ) != ("reconcile", 900, 0, False, "collector"):
        _fail("DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
    reconcile_wheel = _mapping(
        reconcile_task.get("python_wheel_task"),
        code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID",
    )
    if (
        frozenset(reconcile_wheel) != {"package_name", "entry_point", "parameters"}
        or reconcile_wheel.get("package_name") != "dbtobsb-collector"
        or reconcile_wheel.get("entry_point") != "reconcile"
        or _string_sequence(
            reconcile_wheel.get("parameters"),
            code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID",
        )
        != _RECONCILER_TASK_PARAMETERS
    ):
        _fail("DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")
    _validate_collector_environment(reconciler, code="DBTOBSB_BUNDLE_RECONCILER_JOB_INVALID")


def validate_bundle(path: Path) -> None:
    """Validate the base Bundle and the one installer-generated observed dbt Job."""
    root = _load_yaml(path, invalid_code="DBTOBSB_BUNDLE_YAML_INVALID")
    manifest = load_support_manifest()
    _validate_bundle_envelope(root)

    bundle = _mapping(root.get("bundle"), code="DBTOBSB_BUNDLE_METADATA_INVALID")
    if frozenset(bundle) != _BUNDLE_FIELDS or bundle.get("name") != "dbtobsb":
        _fail("DBTOBSB_BUNDLE_METADATA_INVALID")
    if bundle.get("databricks_cli_version") != manifest.platform["databricks_cli"]:
        _fail("DBTOBSB_BUNDLE_CLI_VERSION_DRIFT")
    if bundle.get("engine") != str(manifest.platform["bundle_engine"]).lower():
        _fail("DBTOBSB_BUNDLE_ENGINE_DRIFT")

    resources = _mapping(root.get("resources"), code="DBTOBSB_BUNDLE_RESOURCES_INVALID")
    if frozenset(resources) != {"jobs"}:
        _fail("DBTOBSB_BUNDLE_RESOURCES_INVALID")
    base_jobs = _mapping(resources.get("jobs"), code="DBTOBSB_BUNDLE_JOBS_INVALID")
    if frozenset(base_jobs) != {"dbtobsb_collector", "dbtobsb_reconciler"}:
        _fail("DBTOBSB_BUNDLE_JOBS_INVALID")
    observed_overlay = _load_yaml(
        path.parent / ".dbtobsb-observed.generated.yml",
        invalid_code="DBTOBSB_BUNDLE_OBSERVED_OVERLAY_INVALID",
    )
    if frozenset(observed_overlay) != {"resources"}:
        _fail("DBTOBSB_BUNDLE_OBSERVED_OVERLAY_INVALID")
    overlay_resources = _mapping(
        observed_overlay.get("resources"),
        code="DBTOBSB_BUNDLE_OBSERVED_OVERLAY_INVALID",
    )
    if frozenset(overlay_resources) != {"jobs"}:
        _fail("DBTOBSB_BUNDLE_OBSERVED_OVERLAY_INVALID")
    overlay_jobs = _mapping(
        overlay_resources.get("jobs"),
        code="DBTOBSB_BUNDLE_OBSERVED_OVERLAY_INVALID",
    )
    if frozenset(overlay_jobs) != {_OBSERVED_JOB_KEY}:
        _fail("DBTOBSB_BUNDLE_OBSERVED_OVERLAY_INVALID")
    jobs = {**base_jobs, **overlay_jobs}
    _validate_runtime_jobs(jobs)
    job = _mapping(jobs.get(_OBSERVED_JOB_KEY), code="DBTOBSB_BUNDLE_DBT_JOB_INVALID")
    if frozenset(job) != _OBSERVED_JOB_FIELDS or (
        job.get("name"),
        job.get("max_concurrent_runs"),
        job.get("timeout_seconds"),
        job.get("performance_target"),
    ) != ("dbtobsb-observed", 1, 1200, "STANDARD"):
        _fail("DBTOBSB_BUNDLE_DBT_JOB_INVALID")
    if (
        _mapping(job.get("run_as"), code="DBTOBSB_BUNDLE_DBT_JOB_INVALID") != _OBSERVED_RUN_AS
        or tuple(
            _mapping(item, code="DBTOBSB_BUNDLE_DBT_JOB_INVALID")
            for item in _sequence(job.get("permissions"), code="DBTOBSB_BUNDLE_DBT_JOB_INVALID")
        )
        != _OBSERVED_PERMISSIONS
    ):
        _fail("DBTOBSB_BUNDLE_DBT_JOB_INVALID")

    tasks = _sequence(job.get("tasks"), code="DBTOBSB_BUNDLE_DBT_TASK_INVALID")
    task_keys = tuple(
        _mapping(task, code="DBTOBSB_BUNDLE_DBT_TASK_INVALID").get("task_key") for task in tasks
    )
    if task_keys != (_DBT_TASK_KEY, _COLLECT_TASK_KEY):
        _fail("DBTOBSB_BUNDLE_DBT_TASK_INVALID")
    task = _one_mapping(
        tasks,
        key="task_key",
        expected=_DBT_TASK_KEY,
        code="DBTOBSB_BUNDLE_DBT_TASK_INVALID",
    )
    if frozenset(task) != _DBT_TASK_WRAPPER_FIELDS or (
        task.get("timeout_seconds"),
        task.get("max_retries"),
        task.get("retry_on_timeout"),
        task.get("environment_key"),
    ) != (900, 0, False, "dbt"):
        _fail("DBTOBSB_BUNDLE_DBT_TASK_CONFIGURATION_UNSUPPORTED")

    runner = _mapping(task.get("python_wheel_task"), code="DBTOBSB_BUNDLE_DBT_TASK_INVALID")
    if (
        frozenset(runner) != _DBT_RUNNER_FIELDS
        or runner.get("package_name") != "dbtobsb-collector"
        or runner.get("entry_point") != "run-dbt"
    ):
        _fail("DBTOBSB_BUNDLE_DBT_TASK_CONFIGURATION_UNSUPPORTED")
    runner_parameters = _string_sequence(
        runner.get("parameters"), code="DBTOBSB_BUNDLE_DBT_TASK_CONFIGURATION_UNSUPPORTED"
    )
    if (
        len(runner_parameters) != 16
        or runner_parameters[:13] != _DBT_RUNNER_PARAMETER_PREFIX
        or runner_parameters[14] != "--policy_path"
    ):
        _fail("DBTOBSB_BUNDLE_DBT_TASK_CONFIGURATION_UNSUPPORTED")
    project_directory = runner_parameters[13]
    policy_path = runner_parameters[15]
    if policy_path != project_directory.rsplit("/project", maxsplit=1)[0] + "/dbt-policy-v1.json":
        _fail("DBTOBSB_BUNDLE_PROJECT_DIRECTORY_DRIFT")
    policy = _load_and_validate_onboarded_policy(
        bundle_path=path,
        project_directory=project_directory,
    )
    if not policy.commands:
        _fail("DBTOBSB_BUNDLE_DBT_COMMAND_DRIFT")

    _validate_collector_wrapper(tasks)

    environments = _sequence(job.get("environments"), code="DBTOBSB_BUNDLE_DBT_ENVIRONMENT_INVALID")
    if len(environments) != 1:
        _fail("DBTOBSB_BUNDLE_DBT_ENVIRONMENT_INVALID")
    environment = _one_mapping(
        environments,
        key="environment_key",
        expected="dbt",
        code="DBTOBSB_BUNDLE_DBT_ENVIRONMENT_INVALID",
    )
    if frozenset(environment) != _DBT_ENVIRONMENT_WRAPPER_FIELDS:
        _fail("DBTOBSB_BUNDLE_DBT_ENVIRONMENT_OVERRIDE_UNSUPPORTED")
    spec = _mapping(environment.get("spec"), code="DBTOBSB_BUNDLE_DBT_ENVIRONMENT_INVALID")
    if frozenset(spec) != _DBT_ENVIRONMENT_FIELDS:
        _fail("DBTOBSB_BUNDLE_DBT_ENVIRONMENT_OVERRIDE_UNSUPPORTED")
    if spec.get("client") != manifest.platform["serverless_environment_client"]:
        _fail("DBTOBSB_BUNDLE_SERVERLESS_CLIENT_DRIFT")

    packages = _mapping(manifest.dbt["packages"], code="DBTOBSB_SUPPORT_PACKAGES_INVALID")
    expected_dependencies = (
        *_COLLECTOR_ENVIRONMENT_DEPENDENCIES[:3],
        *tuple(f"{name}=={version}" for name, version in sorted(packages.items())),
    )
    if (
        _string_sequence(spec.get("dependencies"), code="DBTOBSB_BUNDLE_DBT_DEPENDENCY_DRIFT")
        != expected_dependencies
    ):
        _fail("DBTOBSB_BUNDLE_DBT_DEPENDENCY_DRIFT")


def main() -> None:
    arguments = sys.argv[1:]
    if arguments not in ([], ["--format", "human"], ["--format", "json"]):
        raise SystemExit("DBTOBSB_BUNDLE_CHECK_ARGUMENTS_INVALID")
    output_format = arguments[-1] if arguments else "human"
    try:
        validate_bundle(_BUNDLE_PATH)
    except BundleContractError as exc:
        _print_diagnostic(bundle_failure_diagnostic(exc), output_format=output_format)
        raise SystemExit(1) from None
    _print_diagnostic(bundle_success_diagnostic(), output_format=output_format)


if __name__ == "__main__":
    main()
