"""Installed-policy reconciler provenance and bounded discovery tests."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from databricks.sdk import WorkspaceClient
from dbtobsb_contracts import (
    DbtRuntimePolicyInputs,
    DbtRuntimePolicySnapshot,
    DbtRuntimeTarget,
    render_dbt_runtime_policy,
)

from dbtobsb_collector.bootstrap import (
    BASE_OBSERVABILITY_CONTRACT_SHA256,
    OBJECT_CONTRACT_SHA256,
    OBJECT_MANIFEST_VERSION,
    InstallationSeal,
    collector_environment_sha256,
)
from dbtobsb_collector.reconcile import (
    InstalledPolicyReconciliationController,
    ReconciliationError,
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
    return SimpleNamespace(
        task_key=_policy().task_key,
        run_id=task_run_id,
        dbt_task=SimpleNamespace(),
        resolved_values=SimpleNamespace(
            dbt_task=SimpleNamespace(
                commands=_resolved_commands(
                    task_run_id=task_run_id,
                    repair_count=repair_count,
                )
            )
        ),
    )


class _Jobs:
    def __init__(self) -> None:
        self.override: object | None = None
        self.parent_count = 1
        self.parent_pages: dict[str | None, SimpleNamespace] | None = None

    @staticmethod
    def _reconcile_task() -> SimpleNamespace:
        return SimpleNamespace(
            task_key="reconcile",
            environment_key="collector",
            timeout_seconds=900,
            max_retries=0,
            retry_on_timeout=False,
            python_wheel_task=SimpleNamespace(
                package_name="dbtobsb-collector",
                entry_point="reconcile",
                parameters=[
                    "--workspace_id",
                    "{{workspace.id}}",
                    "--reconciler_job_id",
                    "{{job.id}}",
                    "--reconciliation_run_id",
                    "{{job.run_id}}",
                ],
            ),
        )

    def get(self, job_id: int) -> SimpleNamespace:
        assert job_id == 203
        return SimpleNamespace(
            job_id=203,
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
                parameters=[],
                tasks=[self._reconcile_task()],
                schedule=SimpleNamespace(
                    quartz_cron_expression="0 0/15 * * * ?",
                    timezone_id="UTC",
                    pause_status=_enum("PAUSED"),
                ),
            ),
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

    def get_run(self, run_id: int, **kwargs: Any) -> SimpleNamespace:
        assert kwargs.get("include_resolved_values") is True
        if run_id == 501:
            return SimpleNamespace(
                run_id=501,
                job_id=203,
                run_as_user_name="collector-sp",
                effective_performance_target=_enum("STANDARD"),
                overriding_parameters=self.override,
                job_parameters=[],
                tasks=[self._reconcile_task()],
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
            return _dbt_task(task_run_id=411, repair_count=1)
        if run_id == 412:
            return SimpleNamespace(
                task_key="collect_dbt_evidence",
                run_id=412,
                resolved_values=None,
            )
        raise AssertionError(f"unexpected run id {run_id}")


def _controller() -> tuple[InstalledPolicyReconciliationController, SimpleNamespace]:
    client = SimpleNamespace(jobs=_Jobs(), get_workspace_id=lambda: 101)
    return (
        InstalledPolicyReconciliationController(
            installation_seal=_seal(),
            policy=_policy(),
            client=cast(WorkspaceClient, client),
            sleep=lambda _: None,
        ),
        client,
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
