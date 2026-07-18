from __future__ import annotations

import io
import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from dbtobsb_installer.release_cli import (
    InstallationState,
    ReleaseCliError,
    ReleaseManager,
    _load_state,
    _save_state,
    _select,
    main,
)

_DIGEST = "a" * 64
_FINAL_WHEELS = {
    "contracts": f"dbtobsb_contracts-0.3.0+dbtobsb.final.{_DIGEST}-py3-none-any.whl",
    "capture": f"dbtobsb_capture-0.3.0+dbtobsb.final.{_DIGEST}-py3-none-any.whl",
    "collector": f"dbtobsb_collector-0.3.0+dbtobsb.final.{_DIGEST}-py3-none-any.whl",
}


class _NoCommandRunner:
    def run(
        self,
        command: tuple[str, ...],
        *,
        timeout_seconds: int,
        stdin: bytes | None = None,
    ) -> bytes:
        del command, timeout_seconds, stdin
        raise AssertionError("No external command was expected")


def _state(*, stage: str = "INSTALLED") -> InstallationState:
    return InstallationState(
        schema="dbtobsb.installer-state.v1",
        stage=stage,
        profile="paid-azure-test",
        host="https://adb-1234567890123456.10.azuredatabricks.net",
        workspace_id=1234567890123456,
        actor="admin@example.test",
        evidence_catalog="observability",
        evidence_schema="dbtobsb",
        dbt_catalog="analytics",
        dbt_schema="weather_prod",
        warehouse_id="0123456789abcdef",
        warehouse_http_path="/sql/1.0/warehouses/0123456789abcdef",
        observed_service_principal_name="observed-application-id",
        observed_service_principal_display="dbtobsb-observed-runtime",
        collector_service_principal_name="collector-application-id",
        collector_service_principal_display="dbtobsb-collector-runtime",
        job_manager_group_name="dbtobsb-job-managers",
        app_user_group_name="dbtobsb-job-managers",
        source_project_relative_path="customer_weather",
        policy_relative_path="dbtobsb_onboarding/policy.json",
        source_contract_sha256=_DIGEST,
        expected_runtime_policy_sha256=_DIGEST,
        candidate_id=_DIGEST,
        candidate_wheels=_FINAL_WHEELS,
        final_wheels=_FINAL_WHEELS,
        final_environment_sha256=_DIGEST,
        installation_id=_DIGEST,
        observed_job_id=11,
        collector_job_id=12,
        reconciler_job_id=13,
    )


class _LifecycleManager(ReleaseManager):
    def __init__(self, root: Path, answers: str = "") -> None:
        self.events: list[tuple[Any, ...]] = []
        self.fail_temporary = False
        super().__init__(
            root=root,
            runner=_NoCommandRunner(),
            input_stream=io.StringIO(answers),
            output_stream=io.StringIO(),
        )

    def _run_temporary_job(self, state: InstallationState, **kwargs: Any) -> None:
        del state
        if self.fail_temporary:
            raise ReleaseCliError("DBTOBSB_INSTALLER_TEMPORARY_JOB_FAILED")
        self.events.append(("temporary", kwargs))

    def _update_product_grants(self, state: InstallationState, *, add: bool) -> None:
        del state
        self.events.append(("grants", add))

    def _deploy_app(self, state: InstallationState) -> None:
        del state
        self.events.append(("app-deploy",))

    def _stop_state(self, state: InstallationState) -> None:
        del state
        self.events.append(("stop",))

    def _delete_app_if_present(self, state: InstallationState) -> None:
        del state
        self.events.append(("app-delete",))

    def _verify_retained_objects(self, state: InstallationState) -> None:
        del state
        self.events.append(("retain-readback",))

    def _delete_product_objects(self, state: InstallationState) -> None:
        self._run_temporary_job(
            state,
            key="dbtobsb_delete",
            entry_point="uninstall-delete",
            parameters=("--catalog", state.evidence_catalog, "--schema", state.evidence_schema),
            expected_event="dbtobsb_delete_uninstall_verified",
            reconcile_bundle=False,
        )

    def _destroy_bundle(self, state: InstallationState) -> None:
        del state
        self.events.append(("bundle-destroy",))

    def _clear_local_state(self) -> None:
        self.events.append(("local-cleanup",))


class _FailedWaiter:
    def result(self, *, timeout: int) -> None:
        del timeout
        raise RuntimeError("remote run became terminal before waiter completed")


class _StopJobs:
    def __init__(self, readbacks: list[list[SimpleNamespace]]) -> None:
        self.readbacks = iter(readbacks)
        self.cancelled: list[int] = []

    def list_runs(self, *, active_only: bool) -> list[SimpleNamespace]:
        assert active_only is True
        return next(self.readbacks)

    def cancel_run(self, run_id: int) -> _FailedWaiter:
        self.cancelled.append(run_id)
        return _FailedWaiter()


class _StoppedApp:
    def as_dict(self) -> dict[str, dict[str, str]]:
        return {"compute_status": {"state": "STOPPED"}}


class _StopApps:
    def get(self, app_name: str) -> _StoppedApp:
        assert app_name == "dbtobsb-smoke"
        return _StoppedApp()


class _StopManager(ReleaseManager):
    def __init__(self, root: Path, readbacks: list[list[SimpleNamespace]]) -> None:
        super().__init__(
            root=root,
            runner=_NoCommandRunner(),
            input_stream=io.StringIO(),
            output_stream=io.StringIO(),
        )
        self.jobs = _StopJobs(readbacks)
        self.client = SimpleNamespace(jobs=self.jobs, apps=_StopApps())

    def _client(self, profile: str) -> Any:
        assert profile == "paid-azure-test"
        return self.client

    def _pause_reconciler(self, state: InstallationState) -> None:
        assert state.reconciler_job_id == 13


def test_stop_accepts_cancel_waiter_race_after_terminal_readback(tmp_path: Path) -> None:
    active_run = SimpleNamespace(job_id=11, run_id=101)
    manager = _StopManager(tmp_path, [[active_run], []])

    manager._stop_state(_state())

    assert manager.jobs.cancelled == [101]


def test_stop_rejects_cancel_waiter_error_when_run_remains_active(tmp_path: Path) -> None:
    active_run = SimpleNamespace(job_id=11, run_id=101)
    manager = _StopManager(tmp_path, [[active_run], [active_run]])

    with pytest.raises(ReleaseCliError, match="DBTOBSB_STOP_READBACK_FAILED"):
        manager._stop_state(_state())


def _required_state(root: Path) -> InstallationState:
    state = _load_state(root)
    assert state is not None
    return state


def test_state_is_atomic_private_and_strict(tmp_path: Path) -> None:
    expected = _state()

    _save_state(tmp_path, expected)

    path = tmp_path / ".dbtobsb" / "release-installation-v1.json"
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert _load_state(tmp_path) == expected
    document = json.loads(path.read_bytes())
    document["unexpected"] = "rejected"
    path.write_text(json.dumps(document), encoding="utf-8")
    os.chmod(path, 0o600)
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_STATE_INVALID"):
        _load_state(tmp_path)


def test_world_readable_state_is_rejected(tmp_path: Path) -> None:
    _save_state(tmp_path, _state())
    path = tmp_path / ".dbtobsb" / "release-installation-v1.json"
    os.chmod(path, 0o644)

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_STATE_INVALID"):
        _load_state(tmp_path)


def test_selection_is_sorted_and_accepts_only_canonical_number() -> None:
    choices = [{"name": "Zulu"}, {"name": "Alpha"}]
    output = io.StringIO()

    selected = _select(
        "Resource",
        choices,
        label_key="name",
        input_stream=io.StringIO("1\n"),
        output_stream=output,
    )

    assert selected == {"name": "Alpha"}
    assert output.getvalue().index("Alpha") < output.getvalue().index("Zulu")
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_SELECTION_INVALID"):
        _select(
            "Resource",
            choices,
            label_key="name",
            input_stream=io.StringIO("01\n"),
            output_stream=io.StringIO(),
        )


def test_bootstrap_resumes_after_final_deploy_without_repeating_completed_stages(
    tmp_path: Path,
) -> None:
    _save_state(tmp_path, _state(stage="FINAL_DEPLOYED"))
    manager = _LifecycleManager(tmp_path)

    manager.bootstrap()

    assert [event[0] for event in manager.events] == ["temporary", "grants", "app-deploy"]
    temporary = manager.events[0][1]
    assert temporary["key"] == "dbtobsb_bootstrap"
    assert temporary["entry_point"] == "bootstrap"
    assert temporary["expected_event"] == "dbtobsb_bootstrap_verified"
    assert _required_state(tmp_path).stage == "INSTALLED"

    manager.events.clear()
    manager.bootstrap()
    assert manager.events == []


def test_interrupted_bootstrap_keeps_last_verified_stage_and_resumes(tmp_path: Path) -> None:
    _save_state(tmp_path, _state(stage="FINAL_DEPLOYED"))
    interrupted = _LifecycleManager(tmp_path)

    interrupted.fail_temporary = True
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_TEMPORARY_JOB_FAILED"):
        interrupted.bootstrap()
    assert _required_state(tmp_path).stage == "FINAL_DEPLOYED"

    resumed = _LifecycleManager(tmp_path)
    resumed.bootstrap()
    assert _required_state(tmp_path).stage == "INSTALLED"


def test_delete_uninstall_uses_second_approval_and_never_redeploys_bundle(
    tmp_path: Path,
) -> None:
    _save_state(tmp_path, _state())
    manager = _LifecycleManager(tmp_path, "DELETE\nDELETE PRODUCT DATA\n")

    manager.uninstall(delete=True)

    assert [event[0] for event in manager.events] == [
        "stop",
        "app-delete",
        "grants",
        "temporary",
        "bundle-destroy",
        "local-cleanup",
    ]
    assert manager.events[2] == ("grants", False)
    temporary = manager.events[3][1]
    assert temporary["entry_point"] == "uninstall-delete"
    assert temporary["reconcile_bundle"] is False


def test_retain_uninstall_preserves_objects_after_readback(tmp_path: Path) -> None:
    _save_state(tmp_path, _state())
    manager = _LifecycleManager(tmp_path, "RETAIN\n")

    manager.uninstall(delete=False)

    assert [event[0] for event in manager.events] == [
        "stop",
        "app-delete",
        "grants",
        "retain-readback",
        "bundle-destroy",
        "local-cleanup",
    ]


def test_uninstall_denial_has_no_side_effects(tmp_path: Path) -> None:
    _save_state(tmp_path, _state())
    manager = _LifecycleManager(tmp_path, "no\n")

    with pytest.raises(ReleaseCliError, match="DBTOBSB_UNINSTALL_APPROVAL_REQUIRED"):
        manager.uninstall(delete=False)

    assert manager.events == []


def test_uninstall_resumes_from_last_verified_checkpoint(tmp_path: Path) -> None:
    state = replace(
        _state(),
        uninstall_mode="RETAIN",
        uninstall_stage="APP_DELETED",
    )
    _save_state(tmp_path, state)
    manager = _LifecycleManager(tmp_path, "RETAIN\n")

    manager.uninstall(delete=False)

    assert [event[0] for event in manager.events] == [
        "grants",
        "retain-readback",
        "bundle-destroy",
        "local-cleanup",
    ]


class _DispatchManager(ReleaseManager):
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool | None]] = []

    def bootstrap(self) -> None:
        self.calls.append(("bootstrap", None))

    def start(self) -> None:
        self.calls.append(("start", None))

    def stop(self) -> None:
        self.calls.append(("stop", None))

    def uninstall(self, *, delete: bool) -> None:
        self.calls.append(("uninstall", delete))


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["bootstrap"], ("bootstrap", None)),
        (["start"], ("start", None)),
        (["stop"], ("stop", None)),
        (["uninstall", "--retain"], ("uninstall", False)),
        (["uninstall", "--delete"], ("uninstall", True)),
    ],
)
def test_main_dispatches_only_supported_lifecycle_commands(
    argv: list[str], expected: tuple[str, bool | None]
) -> None:
    manager = _DispatchManager()

    assert main(argv, manager=manager) == 0
    assert manager.calls == [expected]


def test_main_rejects_unsupported_arguments_without_native_diagnostics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    manager = _DispatchManager()

    assert main(["bootstrap", "--profile", "secret"], manager=manager) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "DBTOBSB_INSTALLER_ARGUMENTS_INVALID\n"
    assert manager.calls == []


def test_temporary_delete_job_contains_only_fixed_wheel_entrypoint(tmp_path: Path) -> None:
    manager = _LifecycleManager(tmp_path)

    document = manager._temporary_job_document(
        _state(),
        key="dbtobsb_delete",
        entry_point="uninstall-delete",
        parameters=("--catalog", "observability", "--schema", "dbtobsb"),
    )

    job = document["resources"]["jobs"]["dbtobsb_delete"]
    task = job["tasks"][0]
    assert task["python_wheel_task"] == {
        "package_name": "dbtobsb-collector",
        "entry_point": "uninstall-delete",
        "parameters": ["--catalog", "observability", "--schema", "dbtobsb"],
    }
    assert "spark_python_task" not in task
    assert "notebook_task" not in task
    assert "sql_task" not in task
    dependencies = job["environments"][0]["spec"]["dependencies"]
    assert dependencies[:3] == [
        f"../contracts/dist/{_FINAL_WHEELS['contracts']}",
        f"../capture/dist/{_FINAL_WHEELS['capture']}",
        f"../collector/dist/{_FINAL_WHEELS['collector']}",
    ]
