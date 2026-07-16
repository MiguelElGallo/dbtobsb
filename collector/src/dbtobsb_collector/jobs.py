"""Databricks Jobs API adapter for one observed dbt task run."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from itertools import islice
from typing import Any, Self
from urllib.parse import urlsplit

from databricks.sdk import WorkspaceClient
from dbtobsb_contracts import (
    DbtRuntimePolicySnapshot,
    OperatorDiagnostic,
    load_support_manifest,
)

from dbtobsb_collector.bootstrap import InstallationSeal, collector_environment_sha256
from dbtobsb_collector.contracts import (
    ArtifactReference,
    AttemptContext,
    ObservedTaskEvidence,
)

_UNRESOLVED_ATTEMPT_KEY = (
    "w{{workspace.id}}-j{{job.id}}-r{{job.run_id}}-t{{task.run_id}}"
    "-p{{job.repair_count}}-e{{task.execution_count}}"
)
_RESOLVED_ATTEMPT_KEY = re.compile(
    r"w(?P<workspace>[1-9][0-9]*)-j(?P<job>[1-9][0-9]*)-"
    r"r(?P<job_run>[1-9][0-9]*)-t(?P<task_run>[1-9][0-9]*)-"
    r"p(?P<repair>[0-9]+)-e(?P<execution>[1-9][0-9]*)"
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
_DEPLOYMENT_JOB_ERRORS = {
    "DBT_JOBS_DBT_SOURCE_UNSUPPORTED": "dbt task source",
    "DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH": "deployed dbt project binding",
    "DBT_JOBS_DBT_COMMAND_CONTRACT_MISMATCH": "dbt command contract",
    "DBT_JOBS_DBT_ENVIRONMENT_CONTRACT_MISMATCH": "dbt environment contract",
    "DBT_JOBS_DBT_TARGET_BINDING_INVALID": "dbt target binding",
    "DBT_JOBS_DBT_TASK_POLICY_MISMATCH": "dbt task policy",
    "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED": "Job or compute override",
    "DBT_JOBS_INSTALLED_JOB_BINDING_MISMATCH": "installed observed Job binding",
    "DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH": "installed collector Job binding",
    "DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED": "deployed dbt source attestation",
    "DBT_JOBS_WORKSPACE_BINDING_MISMATCH": "installed workspace binding",
    "DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH": "resolved attempt binding",
    "DBT_JOBS_DBT_CONFIGURATION_NOT_READY": "fixed dbt configuration",
}
_COLLECTION_JOB_ERRORS = {
    "DBT_JOBS_PARENT_CORRELATION_MISMATCH": "parent Job correlation",
    "DBT_JOBS_PARENT_PAGINATION_INVALID": "parent Job pagination",
    "DBT_JOBS_TASK_CORRELATION_MISMATCH": "dbt task correlation",
    "DBT_JOBS_TASK_NOT_TERMINAL": "dbt task lifecycle",
    "DBT_JOBS_TASK_RESULT_UNAVAILABLE": "dbt task result",
    "DBT_JOBS_OUTPUT_CORRELATION_MISMATCH": "dbt output correlation",
}


class JobsEvidenceError(RuntimeError):
    """Static Jobs evidence error that excludes native response content."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

    def operator_diagnostic(self) -> OperatorDiagnostic:
        """Return a fixed recovery message without echoing observed Jobs values."""
        known_components = {**_DEPLOYMENT_JOB_ERRORS, **_COLLECTION_JOB_ERRORS}
        code = self.code if self.code in known_components else "DBT_JOBS_EVIDENCE_FAILED"
        component = known_components.get(code, "Databricks Jobs evidence")
        deployment_error = code in _DEPLOYMENT_JOB_ERRORS
        return OperatorDiagnostic(
            code=code,
            outcome="denied",
            component=component,
            summary=f"Denied: the {component} could not be verified for the installed policy.",
            consequence="The artifact archive was not downloaded or published for this attempt.",
            responsible_actor=("deployment/seal verifier" if deployment_error else "data operator"),
            action=(
                "Open /operators/how-to/reconcile-installation/ and follow the matching code."
                if deployment_error
                else "Open /operators/how-to/reconcile-collection/ and follow the matching code."
            ),
        )


def _datetime_from_millis(value: int | None) -> datetime | None:
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value / 1000, tz=UTC)


def _enum_value(value: Any, *, fallback: str) -> str:
    if isinstance(value, str):
        return value
    native = getattr(value, "value", None)
    return native if isinstance(native, str) else fallback


def _empty(value: Any) -> bool:
    return value is None or value == [] or value == {} or value == ()


def _empty_override(value: Any) -> bool:
    if value is None:
        return True
    as_dict = getattr(value, "as_dict", None)
    return _empty(as_dict() if as_dict is not None else value)


def _collector_environment_matches(settings: Any, *, expected_sha256: str) -> bool:
    environments = list(getattr(settings, "environments", None) or ())
    if len(environments) != 1:
        return False
    environment = environments[0]
    spec = getattr(environment, "spec", None)
    dependencies = tuple(getattr(spec, "dependencies", None) or ())
    try:
        observed_sha256 = collector_environment_sha256(dependencies)
    except ValueError:
        return False
    return (
        getattr(environment, "environment_key", None) == "collector"
        and getattr(spec, "client", None) == "5"
        and observed_sha256 == expected_sha256
    )


def _installed_project_directory(value: Any, *, declared: str) -> bool:
    if not isinstance(value, str):
        return False
    suffix = f"/files/{declared.removeprefix('./')}"
    return value == declared or (
        value.startswith("/Workspace/") and value.endswith(suffix) and ".." not in value.split("/")
    )


def _allow_internal_artifact_http(value: str, *, workspace_host: str) -> bool:
    """Recognize a Databricks-issued internal URL in an authenticated Azure workspace."""
    parts = urlsplit(value)
    if parts.scheme.lower() != "http":
        return False
    try:
        port = parts.port
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    trusted_host = host.endswith(".azuredatabricks.net") or host.endswith(".databricks.com")
    if (
        not trusted_host
        or parts.username is not None
        or parts.password is not None
        or port is not None
    ):
        return False
    workspace = urlsplit(workspace_host)
    try:
        workspace_port = workspace.port
    except ValueError:
        return False
    workspace_name = (workspace.hostname or "").lower()
    return not (
        workspace.scheme.lower() != "https"
        or not workspace_name.endswith(".azuredatabricks.net")
        or workspace.username is not None
        or workspace.password is not None
        or workspace_port is not None
        or workspace.path not in {"", "/"}
        or workspace.query
        or workspace.fragment
    )


def attempt_context_from_resolved_task(
    task: Any,
    *,
    policy: DbtRuntimePolicySnapshot,
) -> AttemptContext:
    """Extract and then fully revalidate one policy-derived dbt AttemptKey."""
    if (
        not isinstance(policy, DbtRuntimePolicySnapshot)
        or getattr(task, "task_key", None) != policy.task_key
        or getattr(task, "dbt_task", None) is None
    ):
        raise JobsEvidenceError("DBT_JOBS_TASK_CORRELATION_MISMATCH")
    resolved = getattr(task, "resolved_values", None)
    resolved_dbt = getattr(resolved, "dbt_task", None)
    resolved_commands = getattr(resolved_dbt, "commands", None)
    if not isinstance(resolved_commands, list) or any(
        not isinstance(command, str) for command in resolved_commands
    ):
        raise JobsEvidenceError("DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH")
    matches = list(_RESOLVED_ATTEMPT_KEY.finditer("\n".join(resolved_commands)))
    if not matches or any(match.groupdict() != matches[0].groupdict() for match in matches[1:]):
        raise JobsEvidenceError("DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH")
    values = matches[0].groupdict()
    context = AttemptContext(
        workspace_id=int(values["workspace"]),
        observed_job_id=int(values["job"]),
        observed_job_run_id=int(values["job_run"]),
        dbt_task_run_id=int(values["task_run"]),
        observed_task_key=policy.task_key,
        repair_count=int(values["repair"]),
        execution_count=int(values["execution"]),
    )
    if getattr(task, "run_id", None) != context.dbt_task_run_id:
        raise JobsEvidenceError("DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH")
    expected = tuple(
        command.replace(_UNRESOLVED_ATTEMPT_KEY, context.as_dbt_attempt_identity().key)
        for command in policy.commands
    )
    if tuple(resolved_commands) != expected:
        raise JobsEvidenceError("DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH")
    return context


class DatabricksJobsEvidenceReader:
    """Use a pinned SDK client to fetch and cross-check task output and metadata."""

    def __init__(
        self,
        client: WorkspaceClient | None = None,
        *,
        installation_seal: InstallationSeal,
        policy: DbtRuntimePolicySnapshot,
    ) -> None:
        if (
            not isinstance(policy, DbtRuntimePolicySnapshot)
            or installation_seal.source_contract_sha256 != policy.source_contract_sha256
            or installation_seal.expected_runtime_policy_sha256
            != policy.expected_runtime_policy_sha256
        ):
            raise ValueError("DBTOBSB_DBT_POLICY_BINDING_MISMATCH")
        self._policy = policy
        self._installation_seal = installation_seal
        self._client = client or WorkspaceClient()
        self._current_collector_run_id: int | None = None

    @classmethod
    def for_installed_policy(
        cls,
        client: WorkspaceClient | None = None,
        *,
        installation_seal: InstallationSeal,
        policy: DbtRuntimePolicySnapshot,
    ) -> Self:
        """Build the reader for the policy packaged into this collector wheel."""
        return cls(
            client,
            installation_seal=installation_seal,
            policy=policy,
        )

    def _attest_deployed_source(self, project_directory: str) -> None:
        expected = dict(self._policy.source_sha256)
        prefix = f"{project_directory.rstrip('/')}/"
        try:
            objects = tuple(self._client.workspace.list(project_directory, recursive=True))
        except Exception as error:
            raise JobsEvidenceError("DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED") from error

        observed: set[str] = set()
        for item in objects:
            path = getattr(item, "path", None)
            if not isinstance(path, str) or not path.startswith(prefix):
                raise JobsEvidenceError("DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED")
            relative = path.removeprefix(prefix)
            if not relative or relative.split("/", maxsplit=1)[0] in {"logs", "target"}:
                continue
            if relative in observed:
                raise JobsEvidenceError("DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED")
            observed.add(relative)
        if observed != set(expected):
            raise JobsEvidenceError("DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED")

        for relative, expected_sha256 in expected.items():
            try:
                with self._client.workspace.download(f"{prefix}{relative}") as stream:
                    content = stream.read()
            except Exception as error:
                raise JobsEvidenceError("DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED") from error
            if (
                not isinstance(content, bytes)
                or hashlib.sha256(content).hexdigest() != expected_sha256
            ):
                raise JobsEvidenceError("DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED")

    def _collector_task_parameters(self) -> tuple[str, ...]:
        return (
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

    def _attest_observed_job_environment(self) -> None:
        try:
            job = self._client.jobs.get(self._installation_seal.observed_job_id)
        except Exception as error:
            raise JobsEvidenceError("DBT_JOBS_DBT_ENVIRONMENT_CONTRACT_MISMATCH") from error
        settings = getattr(job, "settings", None)
        environments = list(getattr(settings, "environments", None) or ())
        if (
            getattr(job, "job_id", None) != self._installation_seal.observed_job_id
            or len(environments) != 1
            or getattr(settings, "max_concurrent_runs", None) != 1
            or getattr(settings, "timeout_seconds", None) != 1200
            or _enum_value(getattr(settings, "performance_target", None), fallback="UNKNOWN")
            != "STANDARD"
            or getattr(getattr(settings, "run_as", None), "service_principal_name", None)
            != self._installation_seal.observed_service_principal_name
        ):
            raise JobsEvidenceError("DBT_JOBS_DBT_ENVIRONMENT_CONTRACT_MISMATCH")
        environment = environments[0]
        spec = getattr(environment, "spec", None)
        dependencies = tuple(getattr(spec, "dependencies", None) or ())
        packages = load_support_manifest().dbt["packages"]
        expected_dependencies = frozenset(
            f"{name}=={version}" for name, version in packages.items()
        )
        if (
            getattr(environment, "environment_key", None) != self._policy.environment_key
            or getattr(spec, "client", None) != "5"
            or len(dependencies) != len(expected_dependencies)
            or frozenset(dependencies) != expected_dependencies
        ):
            raise JobsEvidenceError("DBT_JOBS_DBT_ENVIRONMENT_CONTRACT_MISMATCH")

    def _attest_current_collector_run(self, context: AttemptContext) -> None:
        seal = self._installation_seal
        try:
            job = self._client.jobs.get(seal.collector_job_id)
            active_runs = tuple(
                islice(
                    self._client.jobs.list_runs(
                        job_id=seal.collector_job_id,
                        active_only=True,
                        limit=2,
                    ),
                    2,
                )
            )
        except Exception as error:
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH") from error
        settings = getattr(job, "settings", None)
        tasks = list(getattr(settings, "tasks", None) or ())
        parameters = list(getattr(settings, "parameters", None) or ())
        actual_defaults = {
            getattr(parameter, "name", None): getattr(parameter, "default", None)
            for parameter in parameters
        }
        if (
            getattr(job, "job_id", None) != seal.collector_job_id
            or getattr(getattr(settings, "run_as", None), "service_principal_name", None)
            != seal.collector_service_principal_name
            or getattr(settings, "max_concurrent_runs", None) != 1
            or getattr(settings, "timeout_seconds", None) != 900
            or _enum_value(getattr(settings, "performance_target", None), fallback="UNKNOWN")
            != "STANDARD"
            or not _collector_environment_matches(
                settings,
                expected_sha256=seal.collector_environment_sha256,
            )
            or len(tasks) != 1
            or actual_defaults != _COLLECTOR_JOB_PARAMETER_DEFAULTS
            or len(parameters) != len(_COLLECTOR_JOB_PARAMETER_DEFAULTS)
            or len(active_runs) != 1
        ):
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")
        if not self._collector_task_matches(tasks[0]):
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")
        current_summary = active_runs[0]
        current_run_id = getattr(current_summary, "run_id", None)
        if (
            getattr(current_summary, "job_id", None) != seal.collector_job_id
            or type(current_run_id) is not int
            or current_run_id <= 0
        ):
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")
        try:
            current = self._client.jobs.get_run(
                current_run_id,
                include_resolved_values=True,
            )
        except Exception as error:
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH") from error
        run_tasks = list(getattr(current, "tasks", None) or ())
        if len(run_tasks) != 1 or not self._collector_task_matches(run_tasks[0]):
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")
        actual_run_parameters = {
            getattr(parameter, "name", None): getattr(parameter, "value", None)
            for parameter in (getattr(current, "job_parameters", None) or ())
        }
        expected_run_parameters = {
            "workspace_id": str(context.workspace_id),
            "observed_job_id": str(context.observed_job_id),
            "observed_job_run_id": str(context.observed_job_run_id),
            "dbt_task_run_id": str(context.dbt_task_run_id),
            "observed_task_key": context.observed_task_key,
            "repair_count": str(context.repair_count),
            "execution_count": str(context.execution_count),
        }
        if (
            getattr(current, "job_id", None) != seal.collector_job_id
            or getattr(current, "run_id", None) != current_run_id
            or getattr(current, "run_as_user_name", None) != seal.collector_service_principal_name
            or actual_run_parameters != expected_run_parameters
            or len(getattr(current, "job_parameters", None) or ()) != len(expected_run_parameters)
            or not _empty_override(getattr(current, "overriding_parameters", None))
            or _enum_value(
                getattr(current, "effective_performance_target", None), fallback="UNKNOWN"
            )
            != "STANDARD"
        ):
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")
        self._current_collector_run_id = current_run_id

    def _collector_task_matches(self, task: Any) -> bool:
        wheel = getattr(task, "python_wheel_task", None)
        return not (
            getattr(task, "task_key", None) != "collect"
            or getattr(task, "environment_key", None) != "collector"
            or getattr(task, "timeout_seconds", None) != 900
            or getattr(task, "max_retries", None) != 0
            or getattr(task, "retry_on_timeout", None) is not False
            or getattr(wheel, "package_name", None) != "dbtobsb-collector"
            or getattr(wheel, "entry_point", None) != "collect"
            or tuple(getattr(wheel, "parameters", None) or ()) != self._collector_task_parameters()
        )

    def _validate_installed_runtime(self, *, parent: Any, task: Any) -> None:
        policy = self._policy
        dbt_task = getattr(task, "dbt_task", None)
        if dbt_task is None:
            raise JobsEvidenceError("DBT_JOBS_TASK_CORRELATION_MISMATCH")

        source = _enum_value(getattr(dbt_task, "source", None), fallback="UNKNOWN")
        run_if = _enum_value(getattr(task, "run_if", None), fallback="ALL_SUCCESS")
        if source != policy.source:
            raise JobsEvidenceError("DBT_JOBS_DBT_SOURCE_UNSUPPORTED")
        if not _installed_project_directory(
            getattr(dbt_task, "project_directory", None),
            declared=policy.project_directory,
        ):
            raise JobsEvidenceError("DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH")
        if not _installed_project_directory(
            getattr(dbt_task, "profiles_directory", None),
            declared=policy.profiles_directory,
        ) or getattr(dbt_task, "profiles_directory", None) != getattr(
            dbt_task, "project_directory", None
        ):
            raise JobsEvidenceError("DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH")
        if tuple(getattr(dbt_task, "commands", None) or ()) != policy.commands:
            raise JobsEvidenceError("DBT_JOBS_DBT_COMMAND_CONTRACT_MISMATCH")
        if any(
            not _empty(getattr(dbt_task, field, None))
            for field in ("warehouse_id", "catalog", "schema")
        ):
            raise JobsEvidenceError("DBT_JOBS_DBT_TARGET_BINDING_INVALID")
        task_policy_matches = (
            getattr(task, "environment_key", None) == policy.environment_key
            and getattr(task, "timeout_seconds", None) == 900
            and getattr(task, "max_retries", None) == 0
            and getattr(task, "retry_on_timeout", None) is False
            and run_if == "ALL_SUCCESS"
            and _enum_value(
                getattr(parent, "effective_performance_target", None), fallback="UNKNOWN"
            )
            == "STANDARD"
        )
        if not task_policy_matches:
            raise JobsEvidenceError("DBT_JOBS_DBT_TASK_POLICY_MISMATCH")
        forbidden_fields_absent = all(
            _empty(value)
            for value in (
                getattr(parent, "git_source", None),
                getattr(parent, "job_parameters", None),
                getattr(parent, "overriding_parameters", None),
                getattr(task, "git_source", None),
                getattr(task, "depends_on", None),
                getattr(task, "libraries", None),
                getattr(task, "existing_cluster_id", None),
                getattr(task, "job_cluster_key", None),
                getattr(task, "new_cluster", None),
            )
        )
        if not forbidden_fields_absent:
            raise JobsEvidenceError("DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED")

    def _preflight_observed_context(self, context: AttemptContext) -> None:
        if context.observed_task_key != self._policy.task_key:
            raise JobsEvidenceError("DBT_JOBS_TASK_CORRELATION_MISMATCH")
        if context.observed_job_id != self._installation_seal.observed_job_id:
            raise JobsEvidenceError("DBT_JOBS_INSTALLED_JOB_BINDING_MISMATCH")
        self._attest_observed_job_environment()
        try:
            workspace_id = self._client.get_workspace_id()
        except Exception as error:
            raise JobsEvidenceError("DBT_JOBS_WORKSPACE_BINDING_MISMATCH") from error
        if (
            workspace_id != context.workspace_id
            or workspace_id != self._installation_seal.workspace_id
        ):
            raise JobsEvidenceError("DBT_JOBS_WORKSPACE_BINDING_MISMATCH")

    def preflight(self, context: AttemptContext) -> None:
        """Verify the current invocation before any Unity Catalog or Volume access."""
        self._preflight_observed_context(context)
        self._attest_current_collector_run(context)

    def read(self, context: AttemptContext) -> ObservedTaskEvidence:
        self.preflight(context)
        return self._read_observed(context, require_direct_parent=True)

    def read_reconciled(self, context: AttemptContext) -> ObservedTaskEvidence:
        """Read a context discovered by the fixed, attested reconciliation runner."""
        self._preflight_observed_context(context)
        return self._read_observed(context, require_direct_parent=False)

    def _read_observed(
        self, context: AttemptContext, *, require_direct_parent: bool
    ) -> ObservedTaskEvidence:
        parent = self._client.jobs.get_run(
            context.observed_job_run_id, include_resolved_values=True
        )
        if parent.run_id != context.observed_job_run_id or parent.job_id != context.observed_job_id:
            raise JobsEvidenceError("DBT_JOBS_PARENT_CORRELATION_MISMATCH")

        tasks = list(parent.tasks or [])
        page_token = parent.next_page_token
        seen_tokens: set[str] = set()
        while page_token:
            if page_token in seen_tokens or len(seen_tokens) >= 100:
                raise JobsEvidenceError("DBT_JOBS_PARENT_PAGINATION_INVALID")
            seen_tokens.add(page_token)
            page = self._client.jobs.get_run(
                context.observed_job_run_id,
                page_token=page_token,
                include_resolved_values=True,
            )
            if (page.run_id is not None and page.run_id != context.observed_job_run_id) or (
                page.job_id is not None and page.job_id != context.observed_job_id
            ):
                raise JobsEvidenceError("DBT_JOBS_PARENT_CORRELATION_MISMATCH")
            tasks.extend(page.tasks or [])
            page_token = page.next_page_token

        matches = [
            task
            for task in tasks
            if task.task_key == context.observed_task_key
            and task.run_id == context.dbt_task_run_id
            and task.dbt_task is not None
        ]
        if not matches and not require_direct_parent:
            historical = self._client.jobs.get_run(
                context.dbt_task_run_id,
                include_resolved_values=True,
            )
            if (
                getattr(historical, "run_id", None) == context.dbt_task_run_id
                and getattr(historical, "job_id", None) == context.observed_job_id
                and getattr(historical, "job_run_id", None) == context.observed_job_run_id
                and getattr(historical, "task_key", None) == context.observed_task_key
                and getattr(historical, "dbt_task", None) is not None
            ):
                matches = [historical]
        if len(matches) != 1:
            raise JobsEvidenceError("DBT_JOBS_TASK_CORRELATION_MISMATCH")
        if require_direct_parent:
            collector_tasks = [
                candidate
                for candidate in tasks
                if candidate.task_key == "collect_dbt_evidence"
                and candidate.run_job_task is not None
            ]
            if len(tasks) != 2 or len(collector_tasks) != 1:
                raise JobsEvidenceError("DBT_JOBS_TASK_CORRELATION_MISMATCH")
            collector_task = collector_tasks[0]
            collector_task_run_id = getattr(collector_task, "run_id", None)
            dependencies = tuple(
                getattr(dependency, "task_key", None)
                for dependency in (getattr(collector_task, "depends_on", None) or ())
            )
            if (
                getattr(collector_task.run_job_task, "job_id", None)
                != self._installation_seal.collector_job_id
                or dependencies != (self._policy.task_key,)
                or _enum_value(getattr(collector_task, "run_if", None), fallback="UNKNOWN")
                != "ALL_DONE"
                or type(collector_task_run_id) is not int
                or self._current_collector_run_id is None
            ):
                raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")
            assert isinstance(collector_task_run_id, int)
            collector_output = self._client.jobs.get_run_output(collector_task_run_id)
            run_job_output = getattr(collector_output, "run_job_output", None)
            if getattr(run_job_output, "run_id", None) != self._current_collector_run_id:
                raise JobsEvidenceError("DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH")
        task = matches[0]
        self._validate_installed_runtime(parent=parent, task=task)
        dbt_task = getattr(task, "dbt_task", None)
        if dbt_task is None:
            raise JobsEvidenceError("DBT_JOBS_TASK_CORRELATION_MISMATCH")
        project_directory = dbt_task.project_directory
        if not isinstance(project_directory, str):
            raise JobsEvidenceError("DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH")
        if attempt_context_from_resolved_task(task, policy=self._policy) != context:
            raise JobsEvidenceError("DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH")
        self._attest_deployed_source(project_directory)

        status = getattr(task, "status", None)
        current_state = getattr(status, "state", None)
        if current_state is not None:
            if _enum_value(current_state, fallback="UNKNOWN") != "TERMINATED":
                raise JobsEvidenceError("DBT_JOBS_TASK_NOT_TERMINAL")
            termination = getattr(status, "termination_details", None)
            result_state = getattr(termination, "code", None)
        else:
            legacy = getattr(task, "state", None)
            life_cycle_state = getattr(legacy, "life_cycle_state", None)
            if _enum_value(life_cycle_state, fallback="UNKNOWN") not in {
                "TERMINATED",
                "SKIPPED",
                "INTERNAL_ERROR",
            }:
                raise JobsEvidenceError("DBT_JOBS_TASK_NOT_TERMINAL")
            result_state = getattr(legacy, "result_state", None)
        if result_state is None:
            raise JobsEvidenceError("DBT_JOBS_TASK_RESULT_UNAVAILABLE")

        output = self._client.jobs.get_run_output(context.dbt_task_run_id)
        metadata = output.metadata
        if metadata is not None:
            comparisons = (
                (metadata.run_id, context.dbt_task_run_id),
                (metadata.job_id, context.observed_job_id),
                (metadata.job_run_id, context.observed_job_run_id),
            )
            if any(actual is not None and actual != expected for actual, expected in comparisons):
                raise JobsEvidenceError("DBT_JOBS_OUTPUT_CORRELATION_MISMATCH")

        dbt_output = output.dbt_output
        reference = None
        if dbt_output is not None and dbt_output.artifacts_link:
            reference = ArtifactReference(
                url=dbt_output.artifacts_link,
                headers=dict(dbt_output.artifacts_headers or {}),
                allow_internal_databricks_http=_allow_internal_artifact_http(
                    dbt_output.artifacts_link, workspace_host=self._client.config.host
                ),
            )

        return ObservedTaskEvidence(
            task_start_time=_datetime_from_millis(task.start_time),
            task_end_time=_datetime_from_millis(task.end_time),
            lakeflow_result_state=_enum_value(result_state, fallback="UNKNOWN"),
            attempt_number=task.attempt_number or 0,
            logs_truncated=output.logs_truncated,
            artifact_reference=reference,
        )
