"""Databricks Jobs artifact-link transport classification tests."""

import hashlib
import json
from io import BytesIO
from types import SimpleNamespace
from typing import Any, cast

import pytest
from databricks.sdk import WorkspaceClient
from dbtobsb_contracts import (
    DbtRuntimePolicyInputs,
    DbtRuntimeTarget,
    render_dbt_runtime_policy,
)

from dbtobsb_collector import AttemptContext
from dbtobsb_collector.bootstrap import (
    BASE_OBSERVABILITY_CONTRACT_SHA256,
    OBJECT_CONTRACT_SHA256,
    OBJECT_MANIFEST_VERSION,
    InstallationSeal,
    collector_environment_sha256,
)
from dbtobsb_collector.jobs import (
    DatabricksJobsEvidenceReader,
    JobsEvidenceError,
    _allow_internal_artifact_http,
)


def _enum(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


_COLLECTOR_DEPENDENCIES = (
    "/Workspace/product/artifacts/.internal/dbtobsb_contracts-0.3.0b1-py3-none-any.whl",
    "/Workspace/product/artifacts/.internal/dbtobsb_capture-0.3.0b1-py3-none-any.whl",
    "/Workspace/product/artifacts/.internal/dbtobsb_collector-0.3.0b1-py3-none-any.whl",
    "databricks-sdk==0.120.0",
)
_SOURCE_FILES = {
    "dbt_project.yml": b"name: customer_weather\nprofile: customer_weather\n",
    "models/weather.sql": b"select 1 as observation_count\n",
    "profiles.yml": b"customer_weather:\n  target: dbtobsb\n",
    "selectors.yml": b"selectors:\n  - name: weather_release\n",
}


def _policy():
    source = {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(_SOURCE_FILES.items())}
    source_contract = hashlib.sha256(
        json.dumps(
            {
                "domain": "dbtobsb.dbt-source-contract.v1",
                "source_sha256": source,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    return render_dbt_runtime_policy(
        DbtRuntimePolicyInputs(
            source_sha256=source,
            source_contract_sha256=source_contract,
            project_directory=f"./dbtobsb_onboarding/{source_contract}/project",
            profile_name="customer_weather",
            selector="weather_release",
            include_deps=False,
            dependency_definition_files=(),
            dependency_lock_sha256=None,
            target=DbtRuntimeTarget(
                host="adb-1234567890123456.10.azuredatabricks.net",
                warehouse_id="fedcba9876543210",
                http_path="/sql/1.0/warehouses/fedcba9876543210",
                catalog="analytics",
                schema="weather_prod",
            ),
        )
    )


def _context() -> AttemptContext:
    return AttemptContext(101, 201, 301, 401, "dbt_build", 0, 1)


def _seal() -> InstallationSeal:
    return InstallationSeal(
        manifest_version=OBJECT_MANIFEST_VERSION,
        object_contract_sha256=OBJECT_CONTRACT_SHA256,
        source_contract_sha256=_policy().source_contract_sha256,
        expected_runtime_policy_sha256=_policy().expected_runtime_policy_sha256,
        base_observability_contract_sha256=BASE_OBSERVABILITY_CONTRACT_SHA256,
        installation_id="a" * 64,
        workspace_id=101,
        evidence_catalog="evidence_catalog",
        evidence_schema="evidence_schema",
        warehouse_id="0123456789abcdef",
        observed_job_id=201,
        collector_job_id=202,
        reconciler_job_id=203,
        observed_service_principal_name="observed-sp",
        collector_service_principal_name="collector-sp",
        job_manager_group_name="job-managers",
        collector_environment_sha256=collector_environment_sha256(_COLLECTOR_DEPENDENCIES),
    )


def _canonical_commands() -> list[str]:
    return list(_policy().commands)


def _resolved_commands() -> list[str]:
    unresolved = (
        "w{{workspace.id}}-j{{job.id}}-r{{job.run_id}}-t{{task.run_id}}"
        "-p{{job.repair_count}}-e{{task.execution_count}}"
    )
    return [
        command.replace(unresolved, _context().as_dbt_attempt_identity().key)
        for command in _canonical_commands()
    ]


class _Jobs:
    def __init__(self, pages: list[SimpleNamespace], task: SimpleNamespace) -> None:
        self._pages = pages
        self._task = task
        self.run_calls = 0
        self.dbt_output_calls = 0
        self.collector_output_calls = 0
        self.overriding_parameters: object | None = None
        self.active_context = _context()
        self.historical_runs: dict[int, SimpleNamespace] = {}

    def get(self, job_id: int) -> SimpleNamespace:
        if job_id == 201:
            dependencies = [
                "dbt-core==1.11.12",
                "dbt-databricks==1.12.2",
                "dbt-adapters==1.24.5",
                "dbt-common==1.37.5",
                "dbt-spark==1.10.3",
                "dbt-protos==1.0.541",
                "databricks-sdk==0.117.0",
                "databricks-sql-connector==4.3.0",
            ]
            return SimpleNamespace(
                job_id=201,
                settings=SimpleNamespace(
                    max_concurrent_runs=1,
                    timeout_seconds=1200,
                    performance_target=_enum("STANDARD"),
                    run_as=SimpleNamespace(service_principal_name="observed-sp"),
                    environments=[
                        SimpleNamespace(
                            environment_key="dbt",
                            spec=SimpleNamespace(client="5", dependencies=dependencies),
                        )
                    ],
                ),
            )
        assert job_id == 202
        parameters = [
            SimpleNamespace(name=name, default=default)
            for name, default in {
                "workspace_id": "0",
                "observed_job_id": "0",
                "observed_job_run_id": "0",
                "dbt_task_run_id": "0",
                "observed_task_key": "unresolved",
                "repair_count": "0",
                "execution_count": "0",
            }.items()
        ]
        wheel_parameters = [
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
        ]
        task = SimpleNamespace(
            task_key="collect",
            environment_key="collector",
            timeout_seconds=900,
            max_retries=0,
            retry_on_timeout=False,
            python_wheel_task=SimpleNamespace(
                package_name="dbtobsb-collector",
                entry_point="collect",
                parameters=wheel_parameters,
            ),
        )
        return SimpleNamespace(
            job_id=202,
            settings=SimpleNamespace(
                max_concurrent_runs=1,
                timeout_seconds=900,
                performance_target=_enum("STANDARD"),
                run_as=SimpleNamespace(service_principal_name="collector-sp"),
                environments=[
                    SimpleNamespace(
                        environment_key="collector",
                        spec=SimpleNamespace(
                            client="5",
                            dependencies=list(_COLLECTOR_DEPENDENCIES),
                        ),
                    )
                ],
                parameters=parameters,
                tasks=[task],
            ),
        )

    def list_runs(self, *, job_id: int, active_only: bool, limit: int) -> list[SimpleNamespace]:
        assert (job_id, active_only, limit) == (202, True, 2)
        return [
            SimpleNamespace(
                job_id=202,
                run_id=501,
            )
        ]

    def _active_job_parameters(self) -> list[SimpleNamespace]:
        context = self.active_context
        return [
            SimpleNamespace(name=name, value=value)
            for name, value in {
                "workspace_id": str(context.workspace_id),
                "observed_job_id": str(context.observed_job_id),
                "observed_job_run_id": str(context.observed_job_run_id),
                "dbt_task_run_id": str(context.dbt_task_run_id),
                "observed_task_key": context.observed_task_key,
                "repair_count": str(context.repair_count),
                "execution_count": str(context.execution_count),
            }.items()
        ]

    def get_run(
        self,
        run_id: int,
        *,
        page_token: str | None = None,
        include_resolved_values: bool,
    ) -> SimpleNamespace:
        assert include_resolved_values is True
        if run_id == 501:
            collector_job = self.get(202)
            return SimpleNamespace(
                run_id=501,
                job_id=202,
                tasks=collector_job.settings.tasks,
                job_parameters=self._active_job_parameters(),
                overriding_parameters=self.overriding_parameters,
                effective_performance_target=_enum("STANDARD"),
                run_as_user_name="collector-sp",
            )
        if run_id in self.historical_runs:
            return self.historical_runs[run_id]
        assert run_id == 301
        self.run_calls += 1
        index = 0 if page_token is None else int(page_token)
        return self._pages[index]

    def get_run_output(self, run_id: int) -> SimpleNamespace:
        if run_id == 402:
            self.collector_output_calls += 1
            return SimpleNamespace(run_job_output=SimpleNamespace(run_id=501))
        assert run_id == 401 or run_id in self.historical_runs
        self.dbt_output_calls += 1
        return SimpleNamespace(
            metadata=SimpleNamespace(run_id=run_id, job_id=201, job_run_id=301),
            dbt_output=SimpleNamespace(
                artifacts_link="https://signed.invalid/archive",
                artifacts_headers={"x-required": "value"},
            ),
            logs_truncated=False,
        )


def _collector_parent_task() -> SimpleNamespace:
    return SimpleNamespace(
        task_key="collect_dbt_evidence",
        run_id=402,
        dbt_task=None,
        run_job_task=SimpleNamespace(job_id=202),
        depends_on=[SimpleNamespace(task_key="dbt_build")],
        run_if=_enum("ALL_DONE"),
    )


class _Workspace:
    def __init__(self, project_directory: str) -> None:
        self._project_directory = project_directory.rstrip("/")
        self._files = dict(_SOURCE_FILES)

    def list(self, path: str, *, recursive: bool) -> list[SimpleNamespace]:
        assert path == self._project_directory
        assert recursive is True
        return [
            SimpleNamespace(path=f"{self._project_directory}/{relative}")
            for relative in sorted(self._files)
        ]

    def download(self, path: str) -> BytesIO:
        prefix = f"{self._project_directory}/"
        assert path.startswith(prefix)
        return BytesIO(self._files[path.removeprefix(prefix)])


def _client(
    task: SimpleNamespace,
    *,
    paginated: bool = False,
    parent_overrides: dict[str, Any] | None = None,
) -> SimpleNamespace:
    if paginated:
        pages = [
            SimpleNamespace(run_id=301, job_id=201, tasks=[], next_page_token="1"),
            SimpleNamespace(
                run_id=301,
                job_id=201,
                tasks=[task, _collector_parent_task()],
                next_page_token=None,
            ),
        ]
    else:
        pages = [
            SimpleNamespace(
                run_id=301,
                job_id=201,
                tasks=[task, _collector_parent_task()],
                next_page_token=None,
            )
        ]
    for page in pages:
        page.effective_performance_target = _enum("STANDARD")
        page.git_source = None
        page.job_parameters = None
        page.overriding_parameters = None
        for key, value in (parent_overrides or {}).items():
            setattr(page, key, value)
    return SimpleNamespace(
        jobs=_Jobs(pages, task),
        workspace=_Workspace(task.dbt_task.project_directory),
        config=SimpleNamespace(host="https://adb-999.8.azuredatabricks.net"),
        get_workspace_id=lambda: 101,
    )


def _task(
    *,
    current_state: str = "TERMINATED",
    result: str = "SUCCESS",
    commands: list[str] | None = None,
    project_directory: str | None = None,
    task_overrides: dict[str, Any] | None = None,
    dbt_overrides: dict[str, Any] | None = None,
) -> SimpleNamespace:
    resolved_project_directory = project_directory or (
        "/Workspace/Users/reviewer@example.com/.bundle/dbtobsb/smoke/files/"
        f"{_policy().project_directory.removeprefix('./')}"
    )
    dbt_task = SimpleNamespace(
        commands=_canonical_commands() if commands is None else commands,
        source=_enum("WORKSPACE"),
        project_directory=resolved_project_directory,
        profiles_directory=resolved_project_directory,
        warehouse_id=None,
        catalog=None,
        schema=None,
    )
    for key, value in (dbt_overrides or {}).items():
        setattr(dbt_task, key, value)
    task = SimpleNamespace(
        task_key="dbt_build",
        run_id=401,
        dbt_task=dbt_task,
        environment_key="dbt",
        timeout_seconds=900,
        max_retries=0,
        retry_on_timeout=False,
        run_if=_enum("ALL_SUCCESS"),
        git_source=None,
        depends_on=None,
        libraries=None,
        existing_cluster_id=None,
        job_cluster_key=None,
        new_cluster=None,
        status=SimpleNamespace(
            state=_enum(current_state),
            termination_details=SimpleNamespace(code=_enum(result)),
        ),
        state=SimpleNamespace(life_cycle_state=_enum("TERMINATED"), result_state=_enum("FAILED")),
        start_time=1_000,
        end_time=2_000,
        attempt_number=0,
        resolved_values=SimpleNamespace(dbt_task=SimpleNamespace(commands=_resolved_commands())),
    )
    for key, value in (task_overrides or {}).items():
        setattr(task, key, value)
    return task


def _reader(client: SimpleNamespace) -> DatabricksJobsEvidenceReader:
    return DatabricksJobsEvidenceReader.for_installed_policy(
        cast(WorkspaceClient, client),
        installation_seal=_seal(),
        policy=_policy(),
    )


def test_azure_databricks_internal_http_link_is_recognized() -> None:
    original = "http://adb-123.4.azuredatabricks.net/path/archive?opaque=secret"

    assert _allow_internal_artifact_http(
        original, workspace_host="https://adb-999.8.azuredatabricks.net"
    )


def test_databricks_com_internal_http_link_is_recognized() -> None:
    original = "http://artifacts.cloud.databricks.com/path/archive?opaque=secret"

    assert _allow_internal_artifact_http(
        original, workspace_host="https://adb-999.8.azuredatabricks.net"
    )


def test_https_link_does_not_request_internal_http_capability() -> None:
    original = "https://signed.blob.core.windows.net/path/archive?opaque=secret"

    assert not _allow_internal_artifact_http(
        original, workspace_host="https://adb-999.8.azuredatabricks.net"
    )


def test_untrusted_cleartext_links_are_not_recognized() -> None:
    candidates = (
        "http://signed.blob.core.windows.net/path/archive",
        "http://azuredatabricks.net.attacker.invalid/path/archive",
        "http://databricks.com.attacker.invalid/path/archive",
        "http://user@adb-123.4.azuredatabricks.net/path/archive",
        "http://adb-123.4.azuredatabricks.net:80/path/archive",
    )

    assert not any(
        _allow_internal_artifact_http(value, workspace_host="https://adb-999.8.azuredatabricks.net")
        for value in candidates
    )


def test_untrusted_workspace_host_does_not_grant_capability() -> None:
    original = "http://artifacts.cloud.databricks.com/path/archive?opaque=secret"

    assert not _allow_internal_artifact_http(original, workspace_host="https://attacker.invalid")


def test_reader_paginates_and_prefers_current_terminal_status() -> None:
    client = _client(_task(), paginated=True)

    evidence = _reader(client).read(_context())

    assert evidence.lakeflow_result_state == "SUCCESS"
    assert client.jobs.dbt_output_calls == 1


def test_reconciled_reader_fetches_a_repaired_historical_task_run() -> None:
    client = _client(_task())
    context = AttemptContext(101, 201, 301, 411, "dbt_build", 1, 1)
    historical = _task()
    historical.run_id = 411
    historical.job_id = 201
    historical.job_run_id = 301
    historical.resolved_values.dbt_task.commands = [
        command.replace(
            _context().as_dbt_attempt_identity().key,
            context.as_dbt_attempt_identity().key,
        )
        for command in _resolved_commands()
    ]
    client.jobs.historical_runs[411] = historical

    evidence = _reader(client).read_reconciled(context)

    assert evidence.lakeflow_result_state == "SUCCESS"
    assert client.jobs.dbt_output_calls == 1


def test_reader_rejects_uninstalled_observed_job_before_jobs_api() -> None:
    client = _client(_task())
    context = AttemptContext(101, 999, 301, 401, "dbt_build", 0, 1)

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_INSTALLED_JOB_BINDING_MISMATCH"):
        _reader(client).read(context)

    assert client.jobs.run_calls == 0
    assert client.jobs.dbt_output_calls == 0


@pytest.mark.parametrize(
    ("context", "code"),
    [
        (
            AttemptContext(999, 201, 301, 401, "dbt_build", 0, 1),
            "DBT_JOBS_WORKSPACE_BINDING_MISMATCH",
        ),
        (
            AttemptContext(101, 201, 301, 401, "other_dbt_task", 0, 1),
            "DBT_JOBS_TASK_CORRELATION_MISMATCH",
        ),
        (
            AttemptContext(101, 201, 301, 401, "dbt_build", 9, 1),
            "DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH",
        ),
        (
            AttemptContext(101, 201, 301, 401, "dbt_build", 0, 7),
            "DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH",
        ),
    ],
)
def test_reader_correlates_every_attempt_axis(context: AttemptContext, code: str) -> None:
    client = _client(_task())
    client.jobs.active_context = context

    with pytest.raises(JobsEvidenceError, match=code):
        _reader(client).read(context)

    assert client.jobs.dbt_output_calls == 0


def test_reader_rejects_run_now_python_parameter_override_before_parent_read() -> None:
    client = _client(_task())
    client.jobs.overriding_parameters = SimpleNamespace(
        python_params=["--catalog", "caller-controlled"]
    )

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH"):
        _reader(client).read(_context())

    assert client.jobs.run_calls == 0
    assert client.jobs.dbt_output_calls == 0


def test_reader_rejects_observed_environment_dependency_drift() -> None:
    client = _client(_task())
    original_get = client.jobs.get

    def drifted_get(job_id: int) -> SimpleNamespace:
        result = original_get(job_id)
        if job_id == 201:
            result.settings.environments[0].spec.dependencies[-1] = (
                "databricks-sql-connector==4.3.1"
            )
        return result

    client.jobs.get = drifted_get

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_DBT_ENVIRONMENT_CONTRACT_MISMATCH"):
        _reader(client).read(_context())

    assert client.jobs.run_calls == 0
    assert client.jobs.dbt_output_calls == 0


def test_reader_rejects_resolved_command_text_even_with_expected_attempt_keys() -> None:
    resolved = _resolved_commands()
    resolved[0] = f"{resolved[0]} --caller-controlled"
    task = _task(
        task_overrides={
            "resolved_values": SimpleNamespace(dbt_task=SimpleNamespace(commands=resolved))
        }
    )
    client = _client(task)

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH"):
        _reader(client).read(_context())

    assert client.jobs.dbt_output_calls == 0


@pytest.mark.parametrize("drift", ["content", "extra", "missing"])
def test_reader_rejects_deployed_source_drift_before_requesting_output(drift: str) -> None:
    client = _client(_task())
    workspace = client.workspace
    first = next(iter(workspace._files))
    if drift == "content":
        workspace._files[first] += b"\n"
    elif drift == "extra":
        workspace._files["models/caller.sql"] = b"select 1"
    else:
        del workspace._files[first]

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED"):
        _reader(client).read(_context())

    assert client.jobs.dbt_output_calls == 0


def test_reader_rejects_nonterminal_task_before_requesting_output() -> None:
    client = _client(_task(current_state="RUNNING"))

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_TASK_NOT_TERMINAL"):
        _reader(client).read(_context())

    assert client.jobs.dbt_output_calls == 0


def test_reader_rejects_dbt_command_mismatch_before_requesting_output() -> None:
    client = _client(_task(commands=["dbt build --selector caller_controlled"]))

    with pytest.raises(JobsEvidenceError, match="DBT_JOBS_DBT_COMMAND_CONTRACT_MISMATCH"):
        _reader(client).read(_context())

    assert client.jobs.dbt_output_calls == 0


def test_reader_accepts_the_exact_declared_workspace_project_path() -> None:
    client = _client(_task(project_directory=_policy().project_directory))

    evidence = _reader(client).read(_context())

    assert evidence.lakeflow_result_state == "SUCCESS"
    assert client.jobs.dbt_output_calls == 1


def test_generic_reader_construction_without_an_inspected_snapshot_is_impossible() -> None:
    client = _client(_task())

    with pytest.raises(TypeError, match="installation_seal"):
        cast(Any, DatabricksJobsEvidenceReader)(cast(WorkspaceClient, client))

    assert client.jobs.run_calls == 0
    assert client.jobs.dbt_output_calls == 0


@pytest.mark.parametrize(
    ("scope", "field", "value", "code"),
    [
        ("dbt", "source", _enum("GIT"), "DBT_JOBS_DBT_SOURCE_UNSUPPORTED"),
        (
            "dbt",
            "project_directory",
            "/Workspace/Shared/caller/demo_dbt",
            "DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH",
        ),
        (
            "dbt",
            "profiles_directory",
            "/Workspace/Shared/caller",
            "DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH",
        ),
        ("dbt", "warehouse_id", "caller", "DBT_JOBS_DBT_TARGET_BINDING_INVALID"),
        ("dbt", "catalog", "caller", "DBT_JOBS_DBT_TARGET_BINDING_INVALID"),
        ("dbt", "schema", "caller", "DBT_JOBS_DBT_TARGET_BINDING_INVALID"),
        ("task", "environment_key", "caller", "DBT_JOBS_DBT_TASK_POLICY_MISMATCH"),
        ("task", "timeout_seconds", 0, "DBT_JOBS_DBT_TASK_POLICY_MISMATCH"),
        ("task", "max_retries", 1, "DBT_JOBS_DBT_TASK_POLICY_MISMATCH"),
        ("task", "retry_on_timeout", True, "DBT_JOBS_DBT_TASK_POLICY_MISMATCH"),
        ("task", "run_if", _enum("ALL_DONE"), "DBT_JOBS_DBT_TASK_POLICY_MISMATCH"),
        (
            "task",
            "git_source",
            SimpleNamespace(git_url="https://invalid"),
            "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED",
        ),
        (
            "task",
            "depends_on",
            [SimpleNamespace(task_key="caller")],
            "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED",
        ),
        ("task", "libraries", [SimpleNamespace()], "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED"),
        ("task", "existing_cluster_id", "caller", "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED"),
        ("task", "job_cluster_key", "caller", "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED"),
        ("task", "new_cluster", SimpleNamespace(), "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED"),
        (
            "parent",
            "git_source",
            SimpleNamespace(git_url="https://invalid"),
            "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED",
        ),
        (
            "parent",
            "job_parameters",
            [SimpleNamespace(name="caller", value="true")],
            "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED",
        ),
        (
            "parent",
            "overriding_parameters",
            SimpleNamespace(jar_params=["caller"]),
            "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED",
        ),
    ],
)
def test_runtime_configuration_drift_is_rejected_before_output(
    scope: str, field: str, value: object, code: str
) -> None:
    task_overrides = {field: value} if scope == "task" else None
    dbt_overrides = {field: value} if scope == "dbt" else None
    parent_overrides = {field: value} if scope == "parent" else None
    client = _client(
        _task(task_overrides=task_overrides, dbt_overrides=dbt_overrides),
        parent_overrides=parent_overrides,
    )

    with pytest.raises(JobsEvidenceError, match=code):
        _reader(client).read(_context())

    assert client.jobs.dbt_output_calls == 0


def test_arbitrary_actor_text_in_resolved_project_path_is_not_exposed() -> None:
    canary = "SENSITIVE_ACTOR_CANARY"
    client = _client(
        _task(dbt_overrides={"project_directory": f"/Workspace/Users/{canary}/other/demo_dbt"})
    )

    with pytest.raises(JobsEvidenceError) as exc_info:
        _reader(client).read(_context())

    assert str(exc_info.value) == "DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH"
    assert canary not in repr(exc_info.value)
    assert client.jobs.dbt_output_calls == 0


@pytest.mark.parametrize(
    "code",
    [
        "DBT_JOBS_DBT_SOURCE_UNSUPPORTED",
        "DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH",
        "DBT_JOBS_DBT_COMMAND_CONTRACT_MISMATCH",
        "DBT_JOBS_DBT_TARGET_BINDING_INVALID",
        "DBT_JOBS_DBT_TASK_POLICY_MISMATCH",
        "DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED",
    ],
)
def test_runtime_denial_has_one_safe_recovery_action(code: str) -> None:
    canary = "SENSITIVE_ACTOR_PATH_COMMAND_SELECTOR_ID_SQL_CANARY"
    diagnostic = JobsEvidenceError(code).operator_diagnostic()
    rendered = str(diagnostic.as_dict())

    assert diagnostic.outcome == "denied"
    assert diagnostic.code == code
    assert diagnostic.responsible_actor == "deployment/seal verifier"
    assert diagnostic.action == (
        "Open /operators/how-to/reconcile-installation/ and follow the matching code."
    )
    assert diagnostic.human().count("Next action:") == 1
    assert "not downloaded or published" in diagnostic.consequence
    assert canary not in rendered


def test_unknown_jobs_error_code_is_not_disclosed() -> None:
    canary = "SENSITIVE_JOBS_EXCEPTION_CANARY"

    diagnostic = JobsEvidenceError(canary).operator_diagnostic()

    assert diagnostic.code == "DBT_JOBS_EVIDENCE_FAILED"
    assert canary not in str(diagnostic.as_dict())


@pytest.mark.parametrize(
    "code",
    [
        "DBT_JOBS_PARENT_PAGINATION_INVALID",
        "DBT_JOBS_TASK_NOT_TERMINAL",
        "DBT_JOBS_TASK_RESULT_UNAVAILABLE",
        "DBT_JOBS_OUTPUT_CORRELATION_MISMATCH",
    ],
)
def test_collection_lifecycle_diagnostics_route_to_data_operator(code: str) -> None:
    diagnostic = JobsEvidenceError(code).operator_diagnostic()

    assert diagnostic.responsible_actor == "data operator"
    assert diagnostic.action == (
        "Open /operators/how-to/reconcile-collection/ and follow the matching code."
    )
    assert "not downloaded or published" in diagnostic.consequence
