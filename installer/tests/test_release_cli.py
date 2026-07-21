from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import struct
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from databricks.sdk.errors import NotFound
from dbtobsb_contracts import load_support_manifest

from dbtobsb_installer.release_cli import (
    BootstrapPreflight,
    InstallationState,
    ReleaseCliError,
    ReleaseManager,
    SubprocessRunner,
    _load_state,
    _save_state,
    _SealedCliCredentials,
    _select,
    _verify_databricks_cli_executable,
    main,
)

_DIGEST = "a" * 64
_FINAL_WHEELS = {
    "contracts": f"dbtobsb_contracts-0.4.0+dbtobsb.final.{_DIGEST}-py3-none-any.whl",
    "capture": f"dbtobsb_capture-0.4.0+dbtobsb.final.{_DIGEST}-py3-none-any.whl",
    "collector": f"dbtobsb_collector-0.4.0+dbtobsb.final.{_DIGEST}-py3-none-any.whl",
}
_CANDIDATE_WHEELS = {
    key: value.replace("+dbtobsb.final.", "+dbtobsb.candidate.")
    for key, value in _FINAL_WHEELS.items()
}
_COMMIT = "b" * 40


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
    has_direct_state = stage not in {"CONFIGURED", "ONBOARDED"}
    return InstallationState(
        schema="dbtobsb.installer-state.v2",
        release_version="0.4.0",
        support_contract_sha256=load_support_manifest().canonical_sha256,
        release_source_commit=_COMMIT,
        databricks_cli_sha256=("e6107da75e9dfc16c462563e11958c65689ea47d04d54cb4b31d0eb961f40be7"),
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
        candidate_wheels=_CANDIDATE_WHEELS,
        final_wheels=_FINAL_WHEELS,
        final_environment_sha256=_DIGEST,
        installation_id=_DIGEST,
        observed_job_id=11,
        collector_job_id=12,
        reconciler_job_id=13,
        direct_state_lineage=("12345678-1234-1234-1234-123456789abc" if has_direct_state else None),
        direct_state_serial=1 if has_direct_state else None,
        direct_state_sha256=_DIGEST if has_direct_state else None,
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

    def _release_source_commit(self) -> str:
        return _COMMIT

    def _update_product_grants(self, state: InstallationState, *, add: bool) -> None:
        del state
        self.events.append(("grants", add))

    def _deploy_app(self, state: InstallationState) -> None:
        del state
        self.events.append(("app-deploy",))

    def _stop_state(self, state: InstallationState) -> None:
        del state
        self.events.append(("stop",))

    def _warehouse_cost_receipt(self, state: InstallationState) -> dict[str, Any]:
        del state
        return {
            "warehouse_auto_stop_mins": 5,
            "warehouse_cost_may_continue": False,
            "warehouse_managed_by_product": False,
            "warehouse_next_action": "NONE",
            "warehouse_state": "STOPPED",
        }

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


class _Warehouse:
    def __init__(self, state: str, auto_stop_mins: int | None = 5) -> None:
        self._document = {"state": state, "auto_stop_mins": auto_stop_mins}

    def as_dict(self) -> dict[str, Any]:
        return self._document


def test_warehouse_cost_receipt_never_claims_product_management(tmp_path: Path) -> None:
    manager = _LifecycleManager(tmp_path)
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = SimpleNamespace(
        warehouses=SimpleNamespace(get=lambda warehouse_id: _Warehouse("RUNNING", 5))
    )

    receipt = ReleaseManager._warehouse_cost_receipt(manager, _state())

    assert receipt == {
        "warehouse_auto_stop_mins": 5,
        "warehouse_cost_may_continue": True,
        "warehouse_managed_by_product": False,
        "warehouse_next_action": "WAIT_FOR_AUTO_STOP_OR_USE_SEPARATELY_AUTHORIZED_DIRECT_STOP",
        "warehouse_state": "RUNNING",
    }


def test_warehouse_cost_receipt_fails_closed_when_unreadable(tmp_path: Path) -> None:
    manager = _LifecycleManager(tmp_path)
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = SimpleNamespace(
        warehouses=SimpleNamespace(get=lambda warehouse_id: (_ for _ in ()).throw(RuntimeError()))
    )

    with pytest.raises(ReleaseCliError, match="DBTOBSB_WAREHOUSE_STATE_UNREADABLE"):
        ReleaseManager._warehouse_cost_receipt(manager, _state())


class _TerraformWorkspace:
    def __init__(self, outcome: str) -> None:
        self.outcome = outcome
        self.paths: list[str] = []

    def get_status(self, path: str) -> SimpleNamespace:
        self.paths.append(path)
        if self.outcome == "missing" or (
            self.outcome == "direct" and path.endswith("terraform.tfstate")
        ):
            raise NotFound("missing")
        if self.outcome == "error":
            raise RuntimeError("untrusted remote failure")
        return SimpleNamespace(path=path)


class _TerraformStateManager(ReleaseManager):
    def __init__(self, root: Path, outcome: str) -> None:
        super().__init__(
            root=root,
            runner=_NoCommandRunner(),
            input_stream=io.StringIO(),
            output_stream=io.StringIO(),
        )
        self.workspace = _TerraformWorkspace(outcome)

    def _client(self, profile: str) -> Any:
        assert profile == "paid-azure-test"
        return SimpleNamespace(workspace=self.workspace)


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

    path = tmp_path / ".dbtobsb" / "release-installation-v2.json"
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
    path = tmp_path / ".dbtobsb" / "release-installation-v2.json"
    os.chmod(path, 0o644)

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_STATE_INVALID"):
        _load_state(tmp_path)


def test_v04_rejects_legacy_state_before_lifecycle_or_success(tmp_path: Path) -> None:
    legacy = tmp_path / ".dbtobsb" / "release-installation-v1.json"
    legacy.parent.mkdir()
    legacy.write_text('{"schema":"dbtobsb.installer-state.v1","stage":"INSTALLED"}\n')
    os.chmod(legacy, 0o600)
    manager = _LifecycleManager(tmp_path)

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_LEGACY_STATE_UNSUPPORTED"):
        manager.bootstrap()

    assert manager.events == []
    assert "installation_verified" not in cast(io.StringIO, manager.output).getvalue()


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"release_version": "0.3.0"}, "DBTOBSB_INSTALLER_STATE_INVALID"),
        ({"support_contract_sha256": "c" * 64}, "DBTOBSB_INSTALLER_STATE_INVALID"),
        ({"databricks_cli_sha256": "c" * 64}, "DBTOBSB_INSTALLER_STATE_INVALID"),
        (
            {
                "final_wheels": {
                    **_FINAL_WHEELS,
                    "collector": _FINAL_WHEELS["collector"].replace("0.4.0", "0.3.0"),
                }
            },
            "DBTOBSB_INSTALLER_STATE_INVALID",
        ),
    ],
)
def test_v04_state_rejects_unknown_or_mixed_release_identity(
    changes: dict[str, Any], code: str
) -> None:
    with pytest.raises(ReleaseCliError, match=code):
        replace(_state(), **changes)


def test_v04_state_rejects_changed_source_before_success(tmp_path: Path) -> None:
    _save_state(tmp_path, replace(_state(), release_source_commit="c" * 40))
    manager = _LifecycleManager(tmp_path)

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_STATE_RELEASE_MISMATCH"):
        manager.bootstrap()

    assert manager.events == []
    assert "installation_verified" not in cast(io.StringIO, manager.output).getvalue()


def _fake_macho(path: Path, *, cpu_type: int = 0x0100000C, suffix: bytes = b"official") -> str:
    path.write_bytes(struct.pack("<II", 0xFEEDFACF, cpu_type) + suffix)
    path.chmod(0o755)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cli_seal_rejects_symlink_wrong_arch_and_hash(tmp_path: Path) -> None:
    executable = tmp_path / "databricks"
    digest = _fake_macho(executable)
    _verify_databricks_cli_executable(executable, expected_sha256=digest)

    link = tmp_path / "databricks-link"
    link.symlink_to(executable)
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_CLI_SEAL_INVALID"):
        _verify_databricks_cli_executable(link, expected_sha256=digest)

    wrong_arch = tmp_path / "wrong-arch"
    wrong_arch_digest = _fake_macho(wrong_arch, cpu_type=0x01000007)
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_CLI_SEAL_INVALID"):
        _verify_databricks_cli_executable(wrong_arch, expected_sha256=wrong_arch_digest)

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_CLI_SEAL_INVALID"):
        _verify_databricks_cli_executable(executable, expected_sha256="f" * 64)


def test_cli_runner_uses_private_copy_and_rechecks_before_every_execution(tmp_path: Path) -> None:
    executable = tmp_path / "databricks"
    digest = _fake_macho(executable)
    runner = SubprocessRunner(
        tmp_path,
        databricks_cli_source=executable,
        expected_databricks_cli_sha256=digest,
    )
    sealed = runner._databricks_cli
    assert sealed != executable
    assert sealed.parent.stat().st_mode & 0o777 == 0o700
    assert sealed.stat().st_mode & 0o777 == 0o500

    _fake_macho(executable, suffix=b"PATH replacement")
    assert hashlib.sha256(sealed.read_bytes()).hexdigest() == digest

    sealed.chmod(0o700)
    sealed.write_bytes(sealed.read_bytes() + b"tampered after verification")
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_CLI_SEAL_INVALID"):
        runner.run(("databricks", "version"), timeout_seconds=1)


def test_sdk_credentials_use_only_sealed_runner_and_explicit_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TokenRunner:
        def __init__(self) -> None:
            self.calls: list[tuple[str, ...]] = []

        def run(
            self,
            command: tuple[str, ...],
            *,
            timeout_seconds: int,
            stdin: bytes | None = None,
        ) -> bytes:
            assert timeout_seconds == 60
            assert stdin is None
            self.calls.append(command)
            return b'{"access_token":"secret-in-memory-only"}\n'

    runner = TokenRunner()
    monkeypatch.setenv("PATH", "/path/that/must/not/be-used")
    headers = _SealedCliCredentials(runner, "paid-azure-test")(None)()

    assert headers == {"Authorization": "Bearer secret-in-memory-only"}
    assert runner.calls == [
        (
            "databricks",
            "auth",
            "token",
            "--profile",
            "paid-azure-test",
            "--output",
            "json",
        )
    ]


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


def _preflight(*, warehouse_state: str = "STOPPED") -> BootstrapPreflight:
    return BootstrapPreflight.from_document(
        {
            "app": {
                "end_user_acl": {"group": "dbtobsb-job-managers", "level": "CAN_USE"},
                "environment": {"DBTOBSB_WAREHOUSE_ID": "dbtobsb-app-warehouse"},
                "resource_bindings": [
                    {
                        "name": "dbtobsb-app-warehouse",
                        "sql_warehouse": {
                            "id": "0123456789abcdef",
                            "permission": "CAN_USE",
                        },
                    }
                ],
                "resources": [
                    "dbtobsb-app-warehouse",
                    "dbtobsb-run-health",
                    "dbtobsb-node-health",
                    "dbtobsb-collection-health",
                ],
            },
            "authority": {"named_oauth_profile": "paid-azure-test"},
            "compute": {
                "approved_operations": [
                    "BOUNDED_SERVERLESS_BUNDLE_JOBS",
                    "TWO_BOUNDED_APP_DEPLOYMENT_CHECKS",
                ],
                "warehouse_auto_stop_mins": 5,
                "warehouse_cluster_size": "2X-Small",
                "warehouse_state": warehouse_state,
            },
            "finish": {
                "app": "STOPPED",
                "jobs": "TERMINAL",
                "reconciler": "PAUSED",
                "warehouse": "UNCHANGED_BY_PRODUCT_REPORT_OBSERVED_STATE",
            },
            "planned": {
                "direct_grants": [{"principal": "COLLECTOR", "privileges": ["SELECT"]}],
                "jobs": ["dbtobsb-observed", "dbtobsb-collector", "dbtobsb-reconciler"],
                "objects": [{"kind": "MANAGED_TABLE", "name": "dbt_artifact_registry"}],
                "principal_bindings": {
                    "COLLECTOR_SERVICE_PRINCIPAL": "dbtobsb-collector-runtime",
                    "OBSERVED_SERVICE_PRINCIPAL": "dbtobsb-observed-runtime",
                },
                "temporary_jobs": ["dbtobsb-bootstrap", "dbtobsb-delete"],
                "workspace_acl": {
                    "collector": "CAN_READ",
                    "job_manager_group": "CAN_MANAGE",
                    "observed": "CAN_READ",
                },
            },
            "project": {
                "commands": ["dbt build --selector qualification"],
                "selector": "qualification",
            },
        }
    )


class _PreviewManager(_LifecycleManager):
    def __init__(self, root: Path, answers: str, snapshots: list[BootstrapPreflight]) -> None:
        super().__init__(root, answers)
        self.snapshots = iter(snapshots)
        self.preflight_reads = 0

    def _bootstrap_preflight(self, state: InstallationState) -> BootstrapPreflight:
        del state
        self.preflight_reads += 1
        return next(self.snapshots)


def test_exact_preview_is_digest_bound_and_denial_has_zero_mutation(tmp_path: Path) -> None:
    snapshot = _preflight()
    manager = _PreviewManager(tmp_path, "DENY\n", [snapshot])

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_APPROVAL_REQUIRED"):
        manager._approve_bootstrap(_state(stage="CONFIGURED"), snapshot)

    output = cast(io.StringIO, manager.output).getvalue()
    assert f"Preview SHA-256: {snapshot.sha256}" in output
    assert "v0.4.0 fresh installation only" in output
    assert "App deployment checks: two bounded checks" in output
    assert "dbtobsb does not manage or stop it" in output
    for expected in (
        "Named OAuth profile: paid-azure-test",
        "Grant role bindings:",
        "Workspace ACL:",
        "App bindings:",
        "App environment:",
        "App end-user ACL:",
        "dbt selector: qualification",
        "Fixed dbt commands:",
        "Serverless cost scope:",
        "size 2X-Small",
        "may auto-start the bound warehouse",
        "Finish state:",
    ):
        assert expected in output
    assert manager.preflight_reads == 0
    assert manager.events == []


def test_approval_rechecks_immutable_preflight_before_mutation(tmp_path: Path) -> None:
    approved = _preflight()
    changed = _preflight(warehouse_state="RUNNING")
    manager = _PreviewManager(tmp_path, "APPROVE\n", [changed])

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_PREFLIGHT_CHANGED"):
        manager._approve_bootstrap(_state(stage="CONFIGURED"), approved)

    assert manager.preflight_reads == 1
    assert manager.events == []


def test_app_readback_requires_exact_resource_names_permissions_and_targets(
    tmp_path: Path,
) -> None:
    manager = _LifecycleManager(tmp_path)
    expected = list(manager._expected_app_resources(_state()).values())

    assert manager._app_resources_match(_state(), expected)
    assert not manager._app_resources_match(_state(), expected[:-1])
    changed = [dict(item) for item in expected]
    changed[0] = {
        "name": "dbtobsb-app-warehouse",
        "sql_warehouse": {"id": "fedcba9876543210", "permission": "CAN_USE"},
    }
    assert not manager._app_resources_match(_state(), changed)


def test_cli_1_8_guard_accepts_only_absent_terraform_state(tmp_path: Path) -> None:
    manager = _TerraformStateManager(tmp_path, "missing")

    manager._reject_terraform_state(_state(stage="ONBOARDED"))

    assert manager.workspace.paths == [
        "/Workspace/dbtobsb/.bundle/dbtobsb/smoke/state/terraform.tfstate",
        "/Workspace/dbtobsb/.bundle/dbtobsb/smoke/state/resources.json",
    ]


def test_cli_1_8_guard_rejects_local_or_remote_terraform_state(tmp_path: Path) -> None:
    local_state = tmp_path / ".databricks" / "bundle" / "smoke" / "terraform" / "terraform.tfstate"
    local_state.parent.mkdir(parents=True)
    local_state.write_text("{}", encoding="utf-8")
    local_manager = _TerraformStateManager(tmp_path, "missing")

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_TERRAFORM_STATE_UNSUPPORTED"):
        local_manager._reject_terraform_state(_state(stage="ONBOARDED"))
    assert local_manager.workspace.paths == []

    local_state.unlink()
    direct_state = tmp_path / ".databricks" / "bundle" / "smoke" / "resources.json"
    direct_state.write_text("{}", encoding="utf-8")
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_FRESH_INSTALL_REQUIRED"):
        local_manager._reject_terraform_state(_state(stage="ONBOARDED"))
    assert local_manager.workspace.paths[-1].endswith("state/resources.json")

    direct_state.unlink()
    remote_manager = _TerraformStateManager(tmp_path, "present")
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_TERRAFORM_STATE_UNSUPPORTED"):
        remote_manager._reject_terraform_state(_state(stage="ONBOARDED"))

    remote_direct_manager = _TerraformStateManager(tmp_path, "direct")
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_FRESH_INSTALL_REQUIRED"):
        remote_direct_manager._reject_terraform_state(_state(stage="ONBOARDED"))
    assert remote_direct_manager.workspace.paths[-1].endswith("state/resources.json")


def test_cli_1_8_guard_fails_closed_when_remote_state_cannot_be_read(tmp_path: Path) -> None:
    manager = _TerraformStateManager(tmp_path, "error")

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_TERRAFORM_STATE_CHECK_FAILED"):
        manager._reject_terraform_state(_state(stage="ONBOARDED"))


def _direct_state_raw(*, extra_resource: str | None = None) -> bytes:
    resources = {
        "resources.apps.dbtobsb_smoke": {},
        "resources.jobs.dbtobsb_collector": {},
        "resources.jobs.dbtobsb_observed": {},
        "resources.jobs.dbtobsb_reconciler": {},
    }
    if extra_resource is not None:
        resources[extra_resource] = {}
    return (
        json.dumps(
            {
                "cli_version": "1.8.0",
                "lineage": "12345678-1234-1234-1234-123456789abc",
                "serial": 7,
                "state": resources,
                "state_version": 2,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        + b"\n"
    )


def test_resume_requires_identical_local_remote_direct_state_and_bound_identity(
    tmp_path: Path,
) -> None:
    raw = _direct_state_raw()
    path = tmp_path / ".databricks" / "bundle" / "smoke" / "resources.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)

    class Workspace:
        def get_status(self, remote_path: str) -> SimpleNamespace:
            if remote_path.endswith("terraform.tfstate"):
                raise NotFound("missing")
            return SimpleNamespace(path=remote_path)

        def export(self, remote_path: str) -> SimpleNamespace:
            assert remote_path.endswith("state/resources.json")
            return SimpleNamespace(content=base64.b64encode(raw).decode())

    manager = _LifecycleManager(tmp_path)
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = SimpleNamespace(
        workspace=Workspace()
    )
    state = replace(
        _state(stage="BASE_DEPLOYED"),
        direct_state_serial=7,
        direct_state_sha256=hashlib.sha256(raw).hexdigest(),
    )

    manager._reject_terraform_state(state)

    path.write_bytes(_direct_state_raw(extra_resource="resources.jobs.foreign"))
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_DIRECT_STATE_INVALID"):
        manager._reject_terraform_state(state)


def test_app_deployment_match_requires_exact_snapshot_source_and_environment() -> None:
    deployment = {
        "mode": "SNAPSHOT",
        "source_code_path": "/Workspace/dbtobsb/.bundle/dbtobsb/smoke/files/app",
        "env_vars": [
            {"name": "DBTOBSB_WAREHOUSE_ID"},
            {"name": "DBTOBSB_RUN_HEALTH_VIEW"},
            {"name": "DBTOBSB_NODE_HEALTH_VIEW"},
            {"name": "DBTOBSB_COLLECTION_HEALTH_VIEW"},
        ],
    }

    assert ReleaseManager._app_deployment_matches(deployment)
    for field, value in (
        ("mode", "AUTO_SYNC"),
        ("source_code_path", "/Workspace/foreign/app"),
        ("env_vars", deployment["env_vars"][:-1]),
        ("env_vars", [*deployment["env_vars"], {"name": "EXTRA"}]),
    ):
        changed = dict(deployment)
        changed[field] = value
        assert not ReleaseManager._app_deployment_matches(changed)


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
