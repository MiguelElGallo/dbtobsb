"""Installed-policy reconciler provenance and bounded discovery tests."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import iam, jobs
from dbtobsb_contracts import (
    DbtRuntimePolicyInputs,
    DbtRuntimePolicySnapshot,
    DbtRuntimeTarget,
    render_dbt_runtime_policy,
)

from dbtobsb_collector import reconcile as reconcile_module
from dbtobsb_collector.bootstrap import (
    BASE_OBSERVABILITY_CONTRACT_SHA256,
    OBJECT_CONTRACT_SHA256,
    OBJECT_MANIFEST_VERSION,
    InstallationSeal,
    collector_environment_sha256,
)
from dbtobsb_collector.delta import CollectionAttemptState
from dbtobsb_collector.reconcile import (
    InstalledPolicyReconciliationController,
    ReconciliationError,
    reconcile_installed_policy,
)


def _enum(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


_COLLECTOR_DEPENDENCIES = (
    "/Workspace/product/artifacts/.internal/dbtobsb_contracts-0.4.0-py3-none-any.whl",
    "/Workspace/product/artifacts/.internal/dbtobsb_capture-0.4.0-py3-none-any.whl",
    "/Workspace/product/artifacts/.internal/dbtobsb_collector-0.4.0-py3-none-any.whl",
    "databricks-sdk==0.117.0",
)
_SOURCE_FILES = {
    "dbt_project.yml": b"name: customer_weather\nprofile: customer_weather\n",
    "models/weather.sql": b"select 1 as observation_count\n",
    "profiles.yml": b"customer_weather:\n  target: dbtobsb\n",
    "selectors.yml": b"selectors:\n  - name: weather_release\n",
}


def _policy(*, schema: str = "weather_prod") -> DbtRuntimePolicySnapshot:
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
                schema=schema,
                artifact_catalog="observability",
                artifact_schema="dbtobsb",
            ),
        )
    )


def _seal() -> InstallationSeal:
    policy = _policy()
    return InstallationSeal(
        manifest_version=OBJECT_MANIFEST_VERSION,
        object_contract_sha256=OBJECT_CONTRACT_SHA256,
        source_contract_sha256=policy.source_contract_sha256,
        expected_runtime_policy_sha256=policy.expected_runtime_policy_sha256,
        base_observability_contract_sha256=BASE_OBSERVABILITY_CONTRACT_SHA256,
        installation_id="a" * 64,
        workspace_id=101,
        evidence_catalog="catalog",
        evidence_schema="evidence",
        warehouse_id="0123456789abcdef",
        observed_job_id=201,
        collector_job_id=202,
        reconciler_job_id=203,
        observed_service_principal_name="observed-sp",
        collector_service_principal_name="collector-sp",
        job_manager_group_name="job-managers",
        collector_environment_sha256=collector_environment_sha256(_COLLECTOR_DEPENDENCIES),
    )


def _resolved_commands(*, task_run_id: int, repair_count: int) -> list[str]:
    unresolved = (
        "w{{workspace.id}}-j{{job.id}}-r{{job.run_id}}-t{{task.run_id}}"
        "-p{{job.repair_count}}-e{{task.execution_count}}"
    )
    key = f"w101-j201-r301-t{task_run_id}-p{repair_count}-e1"
    return [command.replace(unresolved, key) for command in _policy().commands]


def _dbt_task(*, task_run_id: int, repair_count: int) -> SimpleNamespace:
    project = (
        "/Workspace/Users/reviewer@example.com/.bundle/dbtobsb/smoke/files/"
        f"{_policy().project_directory.removeprefix('./')}"
    )
    configured = [
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
        project,
        "--policy_path",
        f"{project.rsplit('/project', maxsplit=1)[0]}/dbt-policy-v1.json",
    ]
    resolved = configured.copy()
    resolved[1:12:2] = ["101", "201", "301", str(task_run_id), str(repair_count), "1"]
    return SimpleNamespace(
        task_key=_policy().task_key,
        run_id=task_run_id,
        python_wheel_task=SimpleNamespace(
            package_name="dbtobsb-collector",
            entry_point="run-dbt",
            parameters=configured,
        ),
        resolved_values=SimpleNamespace(python_wheel_task=SimpleNamespace(parameters=resolved)),
    )


class _Jobs:
    def __init__(self) -> None:
        self.override: object | None = None
        self.current_trigger = "PERIODIC"
        self.job_run_as_user_name = "collector-sp"
        self.parent_count = 1
        self.parent_pages: dict[str | None, SimpleNamespace] | None = None
        self.nested_task_run_projection = False

    @staticmethod
    def _reconcile_task() -> jobs.RunTask:
        return jobs.RunTask.from_dict(
            {
                "task_key": "reconcile",
                "environment_key": "collector",
                "timeout_seconds": 900,
                "python_wheel_task": {
                    "package_name": "dbtobsb-collector",
                    "entry_point": "reconcile",
                    "parameters": [
                        "--workspace_id",
                        "{{workspace.id}}",
                        "--reconciler_job_id",
                        "{{job.id}}",
                        "--reconciliation_run_id",
                        "{{job.run_id}}",
                    ],
                },
            }
        )

    def get(self, job_id: int) -> jobs.Job:
        assert job_id == 203
        return jobs.Job.from_dict(
            {
                "job_id": 203,
                "run_as_user_name": self.job_run_as_user_name,
                "settings": {
                    "max_concurrent_runs": 1,
                    "timeout_seconds": 900,
                    "performance_target": "STANDARD",
                    "run_as": {"service_principal_name": "collector-sp"},
                    "environments": [
                        {
                            "environment_key": "collector",
                            "spec": {
                                "client": "5",
                                "dependencies": list(_COLLECTOR_DEPENDENCIES),
                            },
                        }
                    ],
                    "parameters": [],
                    "tasks": [self._reconcile_task().as_dict()],
                    "schedule": {
                        "quartz_cron_expression": "0 0/15 * * * ?",
                        "timezone_id": "UTC",
                        "pause_status": "PAUSED",
                    },
                },
            }
        )

    def list_runs(self, *, job_id: int, **kwargs: Any) -> list[SimpleNamespace]:
        if job_id == 203:
            assert kwargs == {"active_only": True, "limit": 2}
            return [SimpleNamespace(run_id=501, job_id=203)]
        assert job_id == 201
        assert kwargs["completed_only"] is True
        assert kwargs["expand_tasks"] is True
        assert kwargs["limit"] == 20
        return [
            SimpleNamespace(run_id=301 + index, job_id=201) for index in range(self.parent_count)
        ]

    def get_run(self, run_id: int, **kwargs: Any) -> Any:
        assert kwargs.get("include_resolved_values") is True
        if run_id == 501:
            run_task = self._reconcile_task().as_dict()
            run_task.pop("timeout_seconds")
            return jobs.Run.from_dict(
                {
                    "run_id": 501,
                    "job_id": 203,
                    "job_run_id": 501,
                    "run_type": "JOB_RUN",
                    "trigger": self.current_trigger,
                    "effective_performance_target": "STANDARD",
                    "overriding_parameters": self.override,
                    "job_parameters": [],
                    "tasks": [run_task],
                }
            )
        if run_id == 301:
            assert kwargs.get("include_history") is True
            if self.parent_pages is not None:
                return self.parent_pages[kwargs.get("page_token")]
            return SimpleNamespace(
                run_id=301,
                job_id=201,
                tasks=[_dbt_task(task_run_id=401, repair_count=0)],
                repair_history=[SimpleNamespace(task_run_ids=[411, 412])],
            )
        if run_id == 411:
            task = _dbt_task(task_run_id=411, repair_count=1)
            if self.nested_task_run_projection:
                return SimpleNamespace(
                    run_id=411,
                    job_id=201,
                    task_key=None,
                    resolved_values=None,
                    tasks=[task],
                )
            return task
        if run_id == 412:
            return SimpleNamespace(
                task_key="collect_dbt_evidence",
                run_id=412,
                resolved_values=None,
            )
        raise AssertionError(f"unexpected run id {run_id}")


def _controller() -> tuple[InstalledPolicyReconciliationController, SimpleNamespace]:
    client = SimpleNamespace(
        jobs=_Jobs(),
        current_user=SimpleNamespace(me=lambda: iam.User(user_name="collector-sp")),
        get_workspace_id=lambda: 101,
    )
    return (
        InstalledPolicyReconciliationController(
            installation_seal=_seal(),
            policy=_policy(),
            client=cast(WorkspaceClient, client),
            sleep=lambda _: None,
        ),
        client,
    )


def _context(task_run_id: int) -> Any:
    return SimpleNamespace(
        workspace_id=101,
        observed_job_id=201,
        observed_job_run_id=301,
        dbt_task_run_id=task_run_id,
        observed_task_key="dbt_build",
        repair_count=0,
        execution_count=1,
    )


class _Tracker:
    def __init__(
        self,
        *,
        discovered: dict[int, str] | None = None,
        claimed: dict[int, str] | None = None,
        failed: dict[int, str] | None = None,
    ) -> None:
        self.discovered = discovered or {}
        self.claimed = claimed or {}
        self.failed = failed or {}
        self.discover_calls: list[int] = []
        self.begin_calls: list[int] = []
        self.failure_calls: list[tuple[int, str]] = []

    @staticmethod
    def _state(name: str) -> CollectionAttemptState:
        return CollectionAttemptState(
            collector_state=name,
            collection_attempt_count=1,
            normalized_digest=None,
        )

    def discover(self, context: Any, **_: Any) -> CollectionAttemptState:
        self.discover_calls.append(context.dbt_task_run_id)
        return self._state(self.discovered.get(context.dbt_task_run_id, "DISCOVERED"))

    def begin_attempt(self, context: Any, **_: Any) -> CollectionAttemptState:
        self.begin_calls.append(context.dbt_task_run_id)
        return self._state(self.claimed.get(context.dbt_task_run_id, "COLLECTING"))

    def record_failure(self, context: Any, *, issue_code: str) -> CollectionAttemptState:
        self.failure_calls.append((context.dbt_task_run_id, issue_code))
        return self._state(self.failed.get(context.dbt_task_run_id, "RETRYABLE"))


def _replay_controller(contexts: list[Any]) -> SimpleNamespace:
    return SimpleNamespace(
        installation_seal=_seal(),
        policy=_policy(),
        client=SimpleNamespace(),
        discover_attempts=lambda **_: tuple(contexts),
    )


def _wire_replay_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tracker: _Tracker,
    installed_seal: InstallationSeal | None = None,
) -> None:
    monkeypatch.setattr(
        reconcile_module,
        "read_installation_seal",
        lambda *_, **__: installed_seal or _seal(),
    )
    monkeypatch.setattr(reconcile_module, "DeltaCollectionTracker", lambda *_, **__: tracker)
    monkeypatch.setattr(reconcile_module, "DeltaEvidenceSink", lambda *_, **__: object())
    monkeypatch.setattr(reconcile_module, "DatabricksArtifactDownloader", lambda: object())
    monkeypatch.setattr(reconcile_module, "VolumeRawArchiveStore", lambda *_, **__: object())
    monkeypatch.setattr(
        reconcile_module.DatabricksJobsEvidenceReader,
        "for_installed_policy",
        lambda *_, **__: SimpleNamespace(),
    )


def test_reconciler_rejects_a_policy_not_bound_by_the_installation_seal() -> None:
    with pytest.raises(ReconciliationError, match="DBTOBSB_RECONCILIATION_BINDING_MISMATCH"):
        InstalledPolicyReconciliationController(
            installation_seal=_seal(),
            policy=_policy(schema="other_schema"),
        )


def test_reconciler_preflight_attests_the_current_executed_run() -> None:
    controller, _ = _controller()

    controller.preflight(
        workspace_id=101,
        reconciler_job_id=203,
        reconciliation_run_id=501,
    )


def test_reconciler_uses_supported_job_and_authenticated_identity_fields() -> None:
    controller, client = _controller()
    current = client.jobs.get_run(501, include_resolved_values=True)

    assert isinstance(current, jobs.Run)
    assert not hasattr(current, "run_as_user_name")
    controller.preflight(
        workspace_id=101,
        reconciler_job_id=203,
        reconciliation_run_id=501,
    )


def test_reconciler_allows_operator_controlled_one_time_run() -> None:
    controller, client = _controller()
    client.jobs.current_trigger = "ONE_TIME"

    controller.preflight(
        workspace_id=101,
        reconciler_job_id=203,
        reconciliation_run_id=501,
    )


def test_reconciler_rejects_authenticated_identity_drift() -> None:
    controller, client = _controller()
    client.current_user = SimpleNamespace(me=lambda: iam.User(user_name="caller-sp"))

    with pytest.raises(ReconciliationError, match="DBTOBSB_RECONCILIATION_BINDING_MISMATCH"):
        controller.preflight(
            workspace_id=101,
            reconciler_job_id=203,
            reconciliation_run_id=501,
        )


def test_reconciler_rejects_job_run_as_drift() -> None:
    controller, client = _controller()
    client.jobs.job_run_as_user_name = "caller-sp"

    with pytest.raises(ReconciliationError, match="DBTOBSB_RECONCILIATION_BINDING_MISMATCH"):
        controller.preflight(
            workspace_id=101,
            reconciler_job_id=203,
            reconciliation_run_id=501,
        )


def test_reconciler_rejects_nested_job_trigger() -> None:
    controller, client = _controller()
    client.jobs.current_trigger = "RUN_JOB_TASK"

    with pytest.raises(ReconciliationError, match="DBTOBSB_RECONCILIATION_BINDING_MISMATCH"):
        controller.preflight(
            workspace_id=101,
            reconciler_job_id=203,
            reconciliation_run_id=501,
        )


def test_reconciler_rejects_legacy_override_before_discovery() -> None:
    controller, client = _controller()
    client.jobs.override = SimpleNamespace(python_params=["--workspace_id", "999"])

    with pytest.raises(ReconciliationError, match="DBTOBSB_RECONCILIATION_BINDING_MISMATCH"):
        controller.preflight(
            workspace_id=101,
            reconciler_job_id=203,
            reconciliation_run_id=501,
        )


def test_reconciler_discovers_original_and_repaired_dbt_attempts() -> None:
    controller, _ = _controller()

    contexts = controller.discover_attempts(now=datetime(2026, 7, 16, 12, tzinfo=UTC))

    assert [(item.dbt_task_run_id, item.repair_count) for item in contexts] == [
        (401, 0),
        (411, 1),
    ]


def test_reconciler_unwraps_native_task_run_projection() -> None:
    controller, client = _controller()
    client.jobs.nested_task_run_projection = True

    contexts = controller.discover_attempts(now=datetime(2026, 7, 16, 12, tzinfo=UTC))

    assert [(item.dbt_task_run_id, item.repair_count) for item in contexts] == [
        (401, 0),
        (411, 1),
    ]


def test_reconciler_fails_closed_above_the_parent_bound() -> None:
    controller, client = _controller()
    client.jobs.parent_count = 101

    with pytest.raises(
        ReconciliationError,
        match="DBTOBSB_RECONCILIATION_PARENT_LIMIT_EXCEEDED",
    ):
        controller.discover_attempts(now=datetime(2026, 7, 16, 12, tzinfo=UTC))


def test_reconciler_consumes_paginated_tasks_and_repair_history() -> None:
    controller, client = _controller()
    client.jobs.parent_pages = {
        None: SimpleNamespace(
            run_id=301,
            job_id=201,
            tasks=[_dbt_task(task_run_id=401, repair_count=0)],
            repair_history=[],
            next_page_token="next",
        ),
        "next": SimpleNamespace(
            run_id=301,
            job_id=201,
            tasks=[],
            repair_history=[SimpleNamespace(task_run_ids=[411])],
            next_page_token=None,
        ),
    }

    contexts = controller.discover_attempts(now=datetime(2026, 7, 16, 12, tzinfo=UTC))

    assert [(item.dbt_task_run_id, item.repair_count) for item in contexts] == [
        (401, 0),
        (411, 1),
    ]


def test_reconciler_rejects_parent_page_token_cycle() -> None:
    controller, client = _controller()
    client.jobs.parent_pages = {
        None: SimpleNamespace(
            run_id=301,
            job_id=201,
            tasks=[],
            repair_history=[],
            next_page_token="repeat",
        ),
        "repeat": SimpleNamespace(
            run_id=301,
            job_id=201,
            tasks=[],
            repair_history=[],
            next_page_token="repeat",
        ),
    }

    with pytest.raises(
        ReconciliationError,
        match="DBTOBSB_RECONCILIATION_PARENT_PAGINATION_INVALID",
    ):
        controller.discover_attempts(now=datetime(2026, 7, 16, 12, tzinfo=UTC))


def test_replay_aborts_on_manifest_mismatch_before_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = _replay_controller([_context(401)])
    controller.discover_attempts = lambda **_: pytest.fail("discovery must not run")
    tracker = _Tracker()
    mismatched = _seal()
    object.__setattr__(mismatched, "installation_id", "b" * 64)
    _wire_replay_dependencies(monkeypatch, tracker=tracker, installed_seal=mismatched)

    with pytest.raises(
        ReconciliationError,
        match="DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH",
    ):
        reconcile_installed_policy(
            controller=cast(Any, controller),
            spark=cast(Any, object()),
            reconciliation_run_id=501,
            now=datetime(2026, 7, 16, 12, tzinfo=UTC),
        )

    assert tracker.discover_calls == []


def test_replay_lifecycle_handles_skips_race_success_and_failure_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contexts = [_context(task_run_id) for task_run_id in range(401, 408)]
    tracker = _Tracker(
        discovered={401: "PUBLISHED", 402: "TERMINAL_FAILURE", 403: "COLLECTING"},
        claimed={404: "PUBLISHED"},
        failed={406: "RETRYABLE", 407: "TERMINAL_FAILURE"},
    )
    _wire_replay_dependencies(monkeypatch, tracker=tracker)
    collection_calls: list[int] = []

    def collect(**kwargs: Any) -> None:
        task_run_id = kwargs["context"].dbt_task_run_id
        collection_calls.append(task_run_id)
        if task_run_id in {406, 407}:
            raise RuntimeError("untrusted native response")

    monkeypatch.setattr(reconcile_module, "collect_task_run", collect)

    summary = reconcile_installed_policy(
        controller=cast(Any, _replay_controller(contexts)),
        spark=cast(Any, object()),
        reconciliation_run_id=501,
        now=datetime(2026, 7, 16, 12, tzinfo=UTC),
    )

    assert summary == {
        "discovered": 7,
        "attempted": 3,
        "published": 1,
        "retryable": 1,
        "terminal_failure": 2,
        "backlog": False,
    }
    assert tracker.begin_calls == [404, 405, 406, 407]
    assert collection_calls == [405, 406, 407]
    assert tracker.failure_calls == [
        (406, "DBTOBSB_RECONCILIATION_COLLECTION_FAILED"),
        (407, "DBTOBSB_RECONCILIATION_COLLECTION_FAILED"),
    ]


def test_replay_caps_work_at_twenty_and_reports_backlog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contexts = [_context(task_run_id) for task_run_id in range(401, 423)]
    tracker = _Tracker()
    _wire_replay_dependencies(monkeypatch, tracker=tracker)
    collection_calls: list[int] = []
    monkeypatch.setattr(
        reconcile_module,
        "collect_task_run",
        lambda **kwargs: collection_calls.append(kwargs["context"].dbt_task_run_id),
    )

    summary = reconcile_installed_policy(
        controller=cast(Any, _replay_controller(contexts)),
        spark=cast(Any, object()),
        reconciliation_run_id=501,
        now=datetime(2026, 7, 16, 12, tzinfo=UTC),
    )

    assert summary == {
        "discovered": 22,
        "attempted": 20,
        "published": 20,
        "retryable": 0,
        "terminal_failure": 0,
        "backlog": True,
    }
    assert tracker.discover_calls == list(range(401, 423))
    assert tracker.begin_calls == list(range(401, 421))
    assert collection_calls == list(range(401, 421))
