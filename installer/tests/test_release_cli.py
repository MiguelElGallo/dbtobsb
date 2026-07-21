from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import struct
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from databricks.sdk.errors import NotFound
from dbtobsb_contracts import load_support_manifest

import dbtobsb_installer.release_cli as release_cli_module
from dbtobsb_installer.onboarding import DbtOnboardingPlan, DbtOnboardingPreview
from dbtobsb_installer.release_cli import (
    BootstrapPreflight,
    DirectStateIdentity,
    InstallationState,
    ReleaseCliError,
    ReleaseManager,
    SubprocessRunner,
    _load_state,
    _save_state,
    _SealedCliCredentials,
    _select,
    _supported_catalogs,
    _temporary_job_diagnostic_code,
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


def _operator_diagnostic_line(code: str, *, canary: str = "") -> str:
    return json.dumps(
        {
            "action": f"Use the fixed local runbook.{canary}",
            "code": code,
            "component": "fixed bootstrap component",
            "consequence": "Bootstrap stopped.",
            "outcome": "denied",
            "responsible_actor": "UC operator",
            "summary": "Denied: bootstrap is not ready.",
        },
        separators=(",", ":"),
        sort_keys=True,
    )


@pytest.mark.parametrize(
    "code",
    [
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_INTERNAL_ERROR",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_OBJECT_CONFLICT",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_PLATFORM_UNSUPPORTED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_SQL_INCOMPATIBLE",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE",
    ],
)
def test_temporary_job_diagnostic_extracts_only_allowlisted_code(code: str) -> None:
    canary = "SENSITIVE_NATIVE_TASK_TEXT_CANARY"

    observed = _temporary_job_diagnostic_code(
        {"logs": f"untrusted prefix\n{_operator_diagnostic_line(code, canary=canary)}\n"}
    )

    assert observed == code
    assert observed is not None
    assert canary not in observed


@pytest.mark.parametrize(
    "logs",
    [
        _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_UNKNOWN"),
        json.dumps(
            {
                **json.loads(
                    _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE")
                ),
                "native_message": "SENSITIVE_NATIVE_TASK_TEXT_CANARY",
            }
        ),
        (
            _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE")
            + "\n"
            + _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED")
        ),
        "x" * 1_000_001,
        "SENSITIVE_NATIVE_TASK_TEXT_CANARY",
    ],
)
def test_temporary_job_diagnostic_rejects_unknown_malformed_conflicting_or_raw(
    logs: str,
) -> None:
    assert _temporary_job_diagnostic_code({"logs": logs}) is None


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


class _RecordingBundleRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(
        self,
        command: tuple[str, ...],
        *,
        timeout_seconds: int,
        stdin: bytes | None = None,
    ) -> bytes:
        del timeout_seconds, stdin
        self.calls.append(command)
        return b""


class _TaskOutput:
    def __init__(self, document: object) -> None:
        self.document = document

    def as_dict(self) -> object:
        return self.document


class _TemporaryJobs:
    def __init__(self, logs: str) -> None:
        self.logs = logs
        self.list_calls: list[dict[str, object]] = []
        self.output_calls: list[int] = []

    def list_runs(self, **kwargs: object) -> list[SimpleNamespace]:
        self.list_calls.append(dict(kwargs))
        if not kwargs.get("completed_only"):
            return []
        return [
            SimpleNamespace(
                run_id=901,
                start_time=1,
                state=SimpleNamespace(result_state=SimpleNamespace(value="FAILED")),
                tasks=[SimpleNamespace(run_id=902)],
            )
        ]

    def get_run_output(self, run_id: int) -> _TaskOutput:
        self.output_calls.append(run_id)
        return _TaskOutput({"logs": self.logs})


class _TemporaryJobManager(ReleaseManager):
    def __init__(
        self,
        root: Path,
        logs: str,
        *,
        cleanup_failure: bool = False,
    ) -> None:
        self.bundle_runner = _RecordingBundleRunner()
        self.jobs = _TemporaryJobs(logs)
        self.deploy_calls: list[str | None] = []
        self.cleanup_failure = cleanup_failure
        super().__init__(
            root=root,
            runner=self.bundle_runner,
            input_stream=io.StringIO(),
            output_stream=io.StringIO(),
        )

    def _client(self, profile: str) -> Any:
        del profile
        return SimpleNamespace(jobs=self.jobs)

    def _deploy(
        self,
        state: InstallationState,
        wheels: Mapping[str, str],
        *,
        select: str | None = None,
    ) -> None:
        del state, wheels
        self.deploy_calls.append(select)
        if select is None and self.cleanup_failure:
            raise ReleaseCliError("SENSITIVE_NATIVE_CLEANUP_TEXT_CANARY")

    def _temporary_job_id(self, state: InstallationState, key: str) -> int:
        del state, key
        return 900

    def bootstrap(self) -> None:
        self._run_temporary_job(
            _state(stage="FINAL_DEPLOYED"),
            key="dbtobsb_bootstrap",
            entry_point="bootstrap",
            parameters=("--fixed",),
            expected_event="dbtobsb_bootstrap_verified",
        )


@pytest.mark.parametrize(
    "code",
    [
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_INTERNAL_ERROR",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_OBJECT_CONFLICT",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_PLATFORM_UNSUPPORTED",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_SQL_INCOMPATIBLE",
        "DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE",
    ],
)
def test_failed_temporary_job_surfaces_only_allowlisted_code_and_cleans_up(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    code: str,
) -> None:
    canary = "SENSITIVE_NATIVE_TASK_TEXT_CANARY"
    manager = _TemporaryJobManager(
        tmp_path,
        _operator_diagnostic_line(code, canary=canary),
    )

    assert main(["bootstrap"], manager=manager) == 2

    captured = capsys.readouterr()
    progress = cast(io.StringIO, manager.output).getvalue()
    assert captured.err == f"{code}\n"
    assert captured.out == ""
    assert canary not in captured.err
    assert canary not in progress
    assert len(manager.bundle_runner.calls) == 1
    assert manager.bundle_runner.calls[0][:3] == (
        "databricks",
        "bundle",
        "run",
    )
    assert manager.deploy_calls == ["jobs.dbtobsb_bootstrap", None]
    assert manager.jobs.output_calls == [902]
    assert "fixed temporary Job submitted" in progress
    assert "temporary Job cleanup verified" in progress
    assert not (tmp_path / ".dbtobsb-bundle-base/99-lifecycle.generated.yml").exists()


@pytest.mark.parametrize(
    "logs",
    [
        _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_UNKNOWN"),
        "SENSITIVE_NATIVE_TASK_TEXT_CANARY",
        (
            _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE")
            + "\n"
            + _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_TABLE_CREATE_AUTHORIZATION_FAILED")
        ),
        json.dumps(
            {
                **json.loads(
                    _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE")
                ),
                "native_message": "SENSITIVE_NATIVE_TASK_TEXT_CANARY",
            }
        ),
    ],
)
def test_failed_temporary_job_uses_generic_code_for_untrusted_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    logs: str,
) -> None:
    manager = _TemporaryJobManager(tmp_path, logs)

    assert main(["bootstrap"], manager=manager) == 2

    captured = capsys.readouterr()
    progress = cast(io.StringIO, manager.output).getvalue()
    assert captured.err == "DBTOBSB_INSTALLER_TEMPORARY_JOB_FAILED\n"
    assert "SENSITIVE_NATIVE_TASK_TEXT_CANARY" not in captured.err
    assert "SENSITIVE_NATIVE_TASK_TEXT_CANARY" not in progress
    assert len(manager.bundle_runner.calls) == 1
    assert manager.deploy_calls == ["jobs.dbtobsb_bootstrap", None]
    assert not (tmp_path / ".dbtobsb-bundle-base/99-lifecycle.generated.yml").exists()


def test_temporary_job_cleanup_failure_overrides_operation_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manager = _TemporaryJobManager(
        tmp_path,
        _operator_diagnostic_line("DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE"),
        cleanup_failure=True,
    )

    assert main(["bootstrap"], manager=manager) == 2

    captured = capsys.readouterr()
    progress = cast(io.StringIO, manager.output).getvalue()
    assert captured.err == "DBTOBSB_INSTALLER_TEMPORARY_JOB_CLEANUP_FAILED\n"
    assert "SENSITIVE_NATIVE_CLEANUP_TEXT_CANARY" not in captured.err
    assert "temporary Job cleanup not verified" in progress
    assert len(manager.bundle_runner.calls) == 1
    assert manager.deploy_calls == ["jobs.dbtobsb_bootstrap", None]


def test_agent_install_docs_do_not_reintroduce_repeated_approval_prompts() -> None:
    repository = Path(__file__).resolve().parents[2]
    expected_policy = {
        "AGENTS.md": "must answer the installer's confirmation prompts itself",
        ".agents/skills/install-and-run-dbtobsb/SKILL.md": (
            "`APPROVE` at every matching preview without asking the user again"
        ),
        "README.md": "answers the installer's confirmation prompts itself",
        "docs/site/how-to-guides/install-private-release.md": (
            "answers the installer's confirmation prompts itself"
        ),
        "docs/operators/tutorials/install-private-release.md": (
            "enters `APPROVE` itself at matching previews"
        ),
        "docs/releases/v0.4.0-support-contract.md": "Agent task authorization",
    }

    for relative_path, required_text in expected_policy.items():
        document = (repository / relative_path).read_text(encoding="utf-8")
        assert required_text in " ".join(document.split())
        assert "standing approval" not in document.casefold()
        assert "pause again" not in document.casefold()

    recovery_guide = (repository / "docs/site/how-to-guides/install-private-release.md").read_text(
        encoding="utf-8"
    )
    assert "## Recover a failed bootstrap" in recovery_guide
    for code in sorted(release_cli_module._TEMPORARY_JOB_BOOTSTRAP_CODES):
        assert f"`{code}`" in recovery_guide


class _LifecycleManager(ReleaseManager):
    def __init__(self, root: Path, answers: str = "") -> None:
        self.events: list[tuple[Any, ...]] = []
        self.fail_temporary = False
        self.temporary_failure_code = "DBTOBSB_INSTALLER_TEMPORARY_JOB_FAILED"
        super().__init__(
            root=root,
            runner=_NoCommandRunner(),
            input_stream=io.StringIO(answers),
            output_stream=io.StringIO(),
        )

    def _run_temporary_job(self, state: InstallationState, **kwargs: Any) -> None:
        del state
        if self.fail_temporary:
            raise ReleaseCliError(self.temporary_failure_code)
        self.events.append(("temporary", kwargs))

    def _release_source_commit(self) -> str:
        return _COMMIT

    def _reject_terraform_state(self, state: InstallationState) -> None:
        del state

    def _update_product_grants(self, state: InstallationState, *, add: bool) -> None:
        del state
        self.events.append(("grants", add))

    def _deploy_app(self, state: InstallationState) -> InstallationState:
        self.events.append(("app-deploy",))
        return state

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


def test_catalog_discovery_allows_only_managed_writable_catalogs() -> None:
    rows = [
        {"name": "managed", "catalog_type": "MANAGED_CATALOG"},
        {"name": "foreign", "catalog_type": "FOREIGN_CATALOG"},
        {"name": "shared", "catalog_type": "DELTASHARING_CATALOG"},
        {"name": "online", "catalog_type": "MANAGED_ONLINE_CATALOG"},
        {"name": "system", "catalog_type": "SYSTEM_CATALOG"},
        {"name": "internal", "catalog_type": "INTERNAL_CATALOG"},
    ]

    assert _supported_catalogs(rows) == [{"name": "managed", "catalog_type": "MANAGED_CATALOG"}]


def test_schema_discovery_supports_separate_evidence_and_dbt_catalogs(
    tmp_path: Path,
) -> None:
    class SchemaDiscoveryManager(_LifecycleManager):
        def _run_json(self, command: tuple[str, ...], *, timeout_seconds: int = 60) -> Any:
            del timeout_seconds
            assert command[:3] == ("databricks", "schemas", "list")
            rows = {
                "evidence_catalog": [
                    {"name": "empty_evidence", "owner": "admin"},
                    {"name": "used_evidence", "owner": "admin"},
                    {"name": "function_evidence", "owner": "admin"},
                    {"name": "model_evidence", "owner": "admin"},
                ],
                "target_catalog": [
                    {"name": "analytics", "owner": "observed"},
                ],
            }
            return rows[command[3]]

    class Tables:
        def list(
            self,
            catalog_name: str,
            schema_name: str,
            *,
            omit_columns: bool,
            omit_properties: bool,
        ) -> Sequence[SimpleNamespace]:
            assert omit_columns is True
            assert omit_properties is True
            if (catalog_name, schema_name) == ("evidence_catalog", "used_evidence"):
                return [SimpleNamespace(name="existing")]
            return []

    class Volumes:
        def list(self, catalog_name: str, schema_name: str) -> Sequence[SimpleNamespace]:
            del catalog_name, schema_name
            return []

    class Functions:
        def list(self, catalog_name: str, schema_name: str) -> Sequence[SimpleNamespace]:
            if (catalog_name, schema_name) == ("evidence_catalog", "function_evidence"):
                return [SimpleNamespace(name="existing_function")]
            return []

    class RegisteredModels:
        def list(self, *, catalog_name: str, schema_name: str) -> Sequence[SimpleNamespace]:
            if (catalog_name, schema_name) == ("evidence_catalog", "model_evidence"):
                return [SimpleNamespace(name="existing_model")]
            return []

    manager = SchemaDiscoveryManager(tmp_path)
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = SimpleNamespace(
        functions=Functions(),
        registered_models=RegisteredModels(),
        tables=Tables(),
        volumes=Volumes(),
    )

    evidence, target = manager._discover_schema_choices(
        profile="paid-azure-test",
        catalogs=[{"name": "evidence_catalog"}, {"name": "target_catalog"}],
        actor="admin",
        observed_principal="observed",
    )

    assert evidence == [
        {
            "name": "evidence_catalog.empty_evidence",
            "catalog_name": "evidence_catalog",
            "schema_name": "empty_evidence",
        }
    ]
    assert target == [
        {
            "name": "target_catalog.analytics",
            "catalog_name": "target_catalog",
            "schema_name": "analytics",
        }
    ]


def test_product_grants_add_and_revoke_target_catalog_use(tmp_path: Path) -> None:
    class Grants:
        def __init__(self) -> None:
            self.values: dict[tuple[str, str, str], set[str]] = {}

        def get(self, securable_type: str, full_name: str) -> SimpleNamespace:
            assignments = [
                {"principal": principal, "privileges": sorted(privileges)}
                for (kind, name, principal), privileges in self.values.items()
                if kind == securable_type and name == full_name and privileges
            ]
            return SimpleNamespace(as_dict=lambda: {"privilege_assignments": assignments})

        def update(
            self,
            securable_type: str,
            full_name: str,
            *,
            changes: Sequence[Any],
        ) -> None:
            for change in changes:
                key = (securable_type, full_name, change.principal)
                values = self.values.setdefault(key, set())
                if change.add:
                    values.update(item.value for item in change.add)
                if change.remove:
                    values.difference_update(item.value for item in change.remove)

    manager = _LifecycleManager(tmp_path)
    grants = Grants()
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = SimpleNamespace(grants=grants)
    state = _state(stage="CONFIGURED")

    ReleaseManager._update_product_grants(manager, state, add=True)

    assert grants.values[("catalog", "analytics", "observed-application-id")] == {"USE_CATALOG"}

    ReleaseManager._update_product_grants(manager, state, add=False)

    assert grants.values[("catalog", "analytics", "observed-application-id")] == set()


def test_absent_native_privilege_assignments_are_an_empty_direct_grant_set() -> None:
    assert (
        ReleaseManager._principal_privileges(
            {"privilege_assignments": None}, "observed-application-id"
        )
        == set()
    )
    assert ReleaseManager._principal_privileges({}, "observed-application-id") == set()


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
                    "ONE_BOUNDED_APP_DEPLOYMENT_CHECK",
                ],
                "warehouse_auto_stop_mins": 5,
                "warehouse_cluster_size": "2X-Small",
                "warehouse_state": warehouse_state,
            },
            "customer_state": {
                "evidence_catalog_direct_grants": {"privilege_assignments": []},
                "existing_evidence_objects": [],
                "existing_product_jobs": [],
                "schema_direct_grants": {"privilege_assignments": []},
                "target_catalog_direct_grants": {"privilege_assignments": []},
                "bundle_state": "TERRAFORM_AND_DIRECT_ABSENT_FRESH",
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
                "expected_runtime_policy_sha256": _DIGEST,
                "file_count": 4,
                "include_deps": False,
                "job_patch_sha256": _DIGEST,
                "job_patch_relative_path": "dbtobsb_onboarding/job.yml",
                "policy_contract_version": "dbtobsb.dbt-runtime-policy.v1",
                "policy_relative_path": "dbtobsb_onboarding/policy.json",
                "policy_sha256": _DIGEST,
                "profiles_relative_path": "dbtobsb_onboarding/project/profiles.yml",
                "project_relative_path": "dbtobsb_onboarding/project",
                "relative_path": "customer_weather",
                "receipt_relative_path": "dbtobsb_onboarding/receipt.json",
                "selector": "qualification",
                "source_contract_sha256": _DIGEST,
                "support_contract_sha256": _DIGEST,
            },
            "release": {
                "databricks_cli_sha256": _DIGEST,
                "release_source_commit": _COMMIT,
                "support_contract_sha256": _DIGEST,
                "version": "0.4.0",
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
    assert "App deployment: one bounded check, followed by stopped ACL readback" in output
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
        "Project contract:",
        "Release identity:",
        "Fresh-state readback:",
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


def _direct_state_raw(
    *, extra_resource: str | None = None, include_app_permissions: bool = False
) -> bytes:
    resources = {
        "resources.apps.dbtobsb_smoke": {},
        "resources.jobs.dbtobsb_collector": {},
        "resources.jobs.dbtobsb_collector.permissions": {},
        "resources.jobs.dbtobsb_observed": {},
        "resources.jobs.dbtobsb_observed.permissions": {},
        "resources.jobs.dbtobsb_reconciler": {},
        "resources.jobs.dbtobsb_reconciler.permissions": {},
    }
    if include_app_permissions:
        resources["resources.apps.dbtobsb_smoke.permissions"] = {}
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


def _workspace_with_direct_state(raw: bytes) -> SimpleNamespace:
    class Workspace:
        def get_status(self, remote_path: str) -> SimpleNamespace:
            if remote_path.endswith("terraform.tfstate"):
                raise NotFound("missing")
            return SimpleNamespace(path=remote_path)

        def export(self, remote_path: str) -> SimpleNamespace:
            assert remote_path.endswith("state/resources.json")
            return SimpleNamespace(content=base64.b64encode(raw).decode())

    return SimpleNamespace(workspace=Workspace())


def test_resume_requires_identical_local_remote_direct_state_and_bound_identity(
    tmp_path: Path,
) -> None:
    raw = _direct_state_raw()
    path = tmp_path / ".databricks" / "bundle" / "smoke" / "resources.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)

    manager = _LifecycleManager(tmp_path)
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = _workspace_with_direct_state(raw)
    state = replace(
        _state(stage="BASE_DEPLOYED"),
        direct_state_serial=7,
        direct_state_sha256=hashlib.sha256(raw).hexdigest(),
    )

    ReleaseManager._reject_terraform_state(manager, state)

    path.write_bytes(_direct_state_raw(extra_resource="resources.jobs.foreign"))
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_DIRECT_STATE_INVALID"):
        ReleaseManager._reject_terraform_state(manager, state)


def test_cli_1_8_direct_state_accepts_exact_permission_subresources(tmp_path: Path) -> None:
    raw = _direct_state_raw(include_app_permissions=True)
    path = tmp_path / ".databricks" / "bundle" / "smoke" / "resources.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    manager = _LifecycleManager(tmp_path)
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = _workspace_with_direct_state(raw)

    identity = ReleaseManager._read_direct_state(
        manager, _state(stage="BASE_DEPLOYED"), allow_temporary=False
    )

    assert identity.serial == 7


def test_bootstrap_verifies_direct_state_before_resumed_mutation_or_success(
    tmp_path: Path,
) -> None:
    raw = _direct_state_raw()
    path = tmp_path / ".databricks" / "bundle" / "smoke" / "resources.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)

    class GuardedLifecycleManager(_LifecycleManager):
        def _reject_terraform_state(self, state: InstallationState) -> None:
            ReleaseManager._reject_terraform_state(self, state)

    for stage in ("OBJECTS_BOOTSTRAPPED", "INSTALLED"):
        state = replace(
            _state(stage=stage),
            direct_state_serial=7,
            direct_state_sha256=hashlib.sha256(raw).hexdigest(),
        )
        _save_state(tmp_path, state)
        manager = GuardedLifecycleManager(tmp_path)
        cast(dict[str, Any], manager._clients)["paid-azure-test"] = _workspace_with_direct_state(
            raw
        )
        manager.bootstrap()
        if stage == "OBJECTS_BOOTSTRAPPED":
            assert manager.events[0] == ("grants", True)
        else:
            assert manager.events == []
            assert "dbtobsb_installation_verified" in cast(io.StringIO, manager.output).getvalue()

    path.unlink()
    _save_state(
        tmp_path,
        replace(
            _state(stage="OBJECTS_BOOTSTRAPPED"),
            direct_state_serial=7,
            direct_state_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    blocked = GuardedLifecycleManager(tmp_path)
    cast(dict[str, Any], blocked._clients)["paid-azure-test"] = _workspace_with_direct_state(raw)
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_DIRECT_STATE_INVALID"):
        blocked.bootstrap()
    assert blocked.events == []

    path.write_bytes(raw)
    _save_state(
        tmp_path,
        replace(
            _state(stage="INSTALLED"),
            direct_state_serial=7,
            direct_state_sha256="b" * 64,
        ),
    )
    mismatched = GuardedLifecycleManager(tmp_path)
    cast(dict[str, Any], mismatched._clients)["paid-azure-test"] = _workspace_with_direct_state(raw)
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_DIRECT_STATE_MISMATCH"):
        mismatched.bootstrap()
    assert "dbtobsb_installation_verified" not in cast(io.StringIO, mismatched.output).getvalue()

    foreign = _direct_state_raw(extra_resource="resources.jobs.foreign")
    path.write_bytes(foreign)
    _save_state(
        tmp_path,
        replace(
            _state(stage="INSTALLED"),
            direct_state_serial=7,
            direct_state_sha256=hashlib.sha256(foreign).hexdigest(),
        ),
    )
    unexpected = GuardedLifecycleManager(tmp_path)
    cast(dict[str, Any], unexpected._clients)["paid-azure-test"] = _workspace_with_direct_state(
        foreign
    )
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_DIRECT_STATE_INVALID"):
        unexpected.bootstrap()


def test_direct_state_changed_bytes_require_higher_serial(tmp_path: Path) -> None:
    original = _direct_state_raw()
    changed = original.rstrip() + b" \n"
    path = tmp_path / ".databricks" / "bundle" / "smoke" / "resources.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(changed)
    manager = _LifecycleManager(tmp_path)
    cast(dict[str, Any], manager._clients)["paid-azure-test"] = _workspace_with_direct_state(
        changed
    )
    state = replace(
        _state(stage="BASE_DEPLOYED"),
        direct_state_serial=7,
        direct_state_sha256=hashlib.sha256(original).hexdigest(),
    )

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_DIRECT_STATE_MISMATCH"):
        ReleaseManager._capture_direct_state(manager, state, allow_temporary=False)


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


def test_app_deploy_checkpoints_direct_state_before_deployment_readback(
    tmp_path: Path,
) -> None:
    state = _state(stage="GRANTS_APPLIED")
    updated = DirectStateIdentity(
        lineage=cast(str, state.direct_state_lineage),
        serial=cast(int, state.direct_state_serial) + 1,
        sha256="c" * 64,
    )

    class InterruptedAppManager(ReleaseManager):
        def __init__(self) -> None:
            super().__init__(
                root=tmp_path,
                runner=_NoCommandRunner(),
                input_stream=io.StringIO(),
                output_stream=io.StringIO(),
            )

        def _deploy(
            self,
            state: InstallationState,
            wheels: Mapping[str, str],
            *,
            select: str | None = None,
        ) -> None:
            del wheels, select
            self._direct_state_overrides[state.profile] = updated

        def _list_deployments(self, state: InstallationState) -> list[Mapping[str, Any]]:
            del state
            raise ReleaseCliError("DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED")

    manager = InterruptedAppManager()

    class Apps:
        def __init__(self) -> None:
            self.compute_state = "ACTIVE"

        def get(self, app_name: str) -> SimpleNamespace:
            assert app_name == state.app_name
            return SimpleNamespace(
                as_dict=lambda: {"compute_status": {"state": self.compute_state}}
            )

        def stop(self, app_name: str) -> SimpleNamespace:
            assert app_name == state.app_name
            self.compute_state = "STOPPED"
            return SimpleNamespace(result=lambda timeout: None)

    apps = Apps()
    cast(dict[str, Any], manager._clients)[state.profile] = SimpleNamespace(apps=apps)

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_APP_DEPLOYMENT_READBACK_FAILED"):
        manager._deploy_app(state)

    checkpoint = _required_state(tmp_path)
    assert checkpoint.stage == "GRANTS_APPLIED"
    assert checkpoint.direct_state_lineage == updated.lineage
    assert checkpoint.direct_state_serial == updated.serial
    assert checkpoint.direct_state_sha256 == updated.sha256
    assert apps.compute_state == "STOPPED"


def test_app_deploy_uses_one_apply_one_deployment_and_one_stopped_acl_update(
    tmp_path: Path,
) -> None:
    state = _state(stage="GRANTS_APPLIED")
    updated = DirectStateIdentity(
        lineage=cast(str, state.direct_state_lineage),
        serial=cast(int, state.direct_state_serial) + 1,
        sha256="c" * 64,
    )
    deployment = {
        "deployment_id": "deployment",
        "mode": "SNAPSHOT",
        "source_code_path": "/Workspace/dbtobsb/.bundle/dbtobsb/smoke/files/app",
        "env_vars": [
            {"name": "DBTOBSB_WAREHOUSE_ID"},
            {"name": "DBTOBSB_RUN_HEALTH_VIEW"},
            {"name": "DBTOBSB_NODE_HEALTH_VIEW"},
            {"name": "DBTOBSB_COLLECTION_HEALTH_VIEW"},
        ],
        "status": {"state": "SUCCEEDED"},
    }

    class Runner:
        def __init__(self) -> None:
            self.calls: list[tuple[str, ...]] = []

        def run(
            self,
            command: tuple[str, ...],
            *,
            timeout_seconds: int,
            stdin: bytes | None = None,
        ) -> bytes:
            del timeout_seconds, stdin
            self.calls.append(command)
            return b""

    class Apps:
        def __init__(self, resources: list[Mapping[str, Any]]) -> None:
            self.compute_state = "ACTIVE"
            self.direct = False
            self.permission_updates = 0
            self.resources = resources

        def get(self, app_name: str) -> SimpleNamespace:
            assert app_name == state.app_name
            return SimpleNamespace(
                as_dict=lambda: {
                    "compute_status": {"state": self.compute_state},
                    "resources": self.resources,
                }
            )

        def stop(self, app_name: str) -> SimpleNamespace:
            assert app_name == state.app_name
            self.compute_state = "STOPPED"
            return SimpleNamespace(result=lambda timeout: None)

        def get_permissions(self, app_name: str) -> SimpleNamespace:
            assert app_name == state.app_name
            entries = []
            if self.direct:
                entries.append(
                    {
                        "group_name": state.app_user_group_name,
                        "all_permissions": [{"permission_level": "CAN_USE", "inherited": False}],
                    }
                )
            return SimpleNamespace(as_dict=lambda: {"access_control_list": entries})

        def update_permissions(self, app_name: str, *, access_control_list: object) -> None:
            assert app_name == state.app_name
            assert len(cast(list[Any], access_control_list)) == 1
            assert self.compute_state == "STOPPED"
            self.permission_updates += 1
            self.direct = True

    runner = Runner()

    class SuccessfulAppManager(ReleaseManager):
        def __init__(self) -> None:
            self.deploy_selections: list[str | None] = []
            self.deployment_reads = 0
            super().__init__(
                root=tmp_path,
                runner=runner,
                input_stream=io.StringIO(),
                output_stream=io.StringIO(),
            )

        def _deploy(
            self,
            state: InstallationState,
            wheels: Mapping[str, str],
            *,
            select: str | None = None,
        ) -> None:
            del wheels
            self.deploy_selections.append(select)
            self._direct_state_overrides[state.profile] = updated

        def _list_deployments(self, state: InstallationState) -> list[Mapping[str, Any]]:
            del state
            self.deployment_reads += 1
            return [] if self.deployment_reads == 1 else [deployment]

    manager = SuccessfulAppManager()
    resources = list(manager._expected_app_resources(state).values())
    apps = Apps(resources)
    cast(dict[str, Any], manager._clients)[state.profile] = SimpleNamespace(apps=apps)

    returned = manager._deploy_app(state)

    assert manager.deploy_selections == [None]
    assert len(runner.calls) == 1
    assert runner.calls[0][:3] == ("databricks", "bundle", "run")
    assert manager.deployment_reads == 2
    assert apps.permission_updates == 1
    assert apps.compute_state == "STOPPED"
    assert returned.direct_state_serial == updated.serial
    checkpoint = _required_state(tmp_path)
    assert checkpoint.stage == "GRANTS_APPLIED"
    assert checkpoint.direct_state_serial == updated.serial


def test_direct_app_acl_keeps_only_non_inherited_assignments() -> None:
    document = {
        "access_control_list": [
            {
                "group_name": "dbtobsb-job-managers",
                "all_permissions": [
                    {"permission_level": "CAN_USE", "inherited": False},
                    {"permission_level": "CAN_MANAGE", "inherited": True},
                ],
            },
            {
                "service_principal_name": "foreign",
                "all_permissions": [
                    {"permission_level": "CAN_MANAGE", "inherited": False},
                ],
            },
            {
                "user_name": "foreign@example.test",
                "all_permissions": [
                    {"permission_level": "CAN_USE", "inherited": False},
                ],
            },
        ]
    }

    assert ReleaseManager._direct_app_acl(document) == {
        ("group", "dbtobsb-job-managers", "CAN_USE"),
        ("service_principal", "foreign", "CAN_MANAGE"),
        ("user", "foreign@example.test", "CAN_USE"),
    }


@pytest.mark.parametrize(
    "document",
    [
        {"access_control_list": "invalid"},
        {"access_control_list": ["invalid"]},
        {
            "access_control_list": [
                {
                    "group_name": "group",
                    "user_name": "user@example.test",
                    "all_permissions": [{"permission_level": "CAN_USE", "inherited": False}],
                }
            ]
        },
        {
            "access_control_list": [
                {
                    "group_name": "group",
                    "all_permissions": [
                        {"permission_level": "CAN_USE", "inherited": False},
                        {"permission_level": "CAN_USE", "inherited": False},
                    ],
                }
            ]
        },
        {
            "access_control_list": [
                {
                    "group_name": "group",
                    "all_permissions": "invalid",
                }
            ]
        },
        {
            "access_control_list": [
                {
                    "group_name": "group",
                    "all_permissions": [{"permission_level": "CAN_USE"}],
                }
            ]
        },
        {
            "access_control_list": [
                {
                    "group_name": "group",
                    "all_permissions": [{"permission_level": "UNKNOWN", "inherited": False}],
                }
            ]
        },
    ],
)
def test_direct_app_acl_rejects_malformed_or_ambiguous_readback(
    document: Mapping[str, Any],
) -> None:
    with pytest.raises(ValueError):
        ReleaseManager._direct_app_acl(document)


def test_targeted_app_user_access_is_idempotent_and_keeps_app_stopped(tmp_path: Path) -> None:
    state = _state()
    manager = _LifecycleManager(tmp_path)
    resources = list(manager._expected_app_resources(state).values())

    class Apps:
        def __init__(self) -> None:
            self.direct = False
            self.updates = 0

        def get(self, app_name: str) -> SimpleNamespace:
            assert app_name == state.app_name
            return SimpleNamespace(
                as_dict=lambda: {
                    "compute_status": {"state": "STOPPED"},
                    "resources": resources,
                }
            )

        def get_permissions(self, app_name: str) -> SimpleNamespace:
            assert app_name == state.app_name
            entries = []
            if self.direct:
                entries.append(
                    {
                        "group_name": state.app_user_group_name,
                        "all_permissions": [{"permission_level": "CAN_USE", "inherited": False}],
                    }
                )
            return SimpleNamespace(as_dict=lambda: {"access_control_list": entries})

        def update_permissions(self, app_name: str, *, access_control_list: object) -> None:
            assert app_name == state.app_name
            assert len(cast(list[Any], access_control_list)) == 1
            self.updates += 1
            self.direct = True

    apps = Apps()
    cast(dict[str, Any], manager._clients)[state.profile] = SimpleNamespace(apps=apps)

    manager._grant_app_user_access(state)
    manager._grant_app_user_access(state)

    assert apps.updates == 1


def test_onboarding_output_must_match_every_approved_project_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _LifecycleManager(tmp_path)
    state = replace(_state(stage="CONFIGURED"), source_project_relative_path="project")
    preview = DbtOnboardingPreview(
        commands=("dbt build --selector qualification",),
        include_deps=False,
        selector="qualification",
    )
    plan = DbtOnboardingPlan(
        expected_runtime_policy_sha256=_DIGEST,
        file_count=4,
        include_deps=False,
        job_patch_sha256=_DIGEST,
        job_patch_relative_path="dbtobsb_onboarding/job.yml",
        policy_contract_version="dbtobsb.dbt-runtime-policy.v1",
        policy_relative_path="dbtobsb_onboarding/policy.json",
        policy_sha256=_DIGEST,
        profiles_relative_path="dbtobsb_onboarding/project/profiles.yml",
        project_relative_path="dbtobsb_onboarding/project",
        receipt_relative_path="dbtobsb_onboarding/receipt.json",
        source_contract_sha256=_DIGEST,
        support_contract_sha256=load_support_manifest().canonical_sha256,
    )
    approved = manager._project_preflight_document(state, preview, plan)
    monkeypatch.setattr(release_cli_module, "preview_onboarding_project", lambda path: preview)
    monkeypatch.setattr(release_cli_module, "build_onboarding_plan", lambda inputs: plan)

    onboarded = manager._onboard(state, approved_project=approved)
    assert onboarded.stage == "ONBOARDED"

    changed_plan = replace(plan, job_patch_sha256="b" * 64)
    monkeypatch.setattr(release_cli_module, "build_onboarding_plan", lambda inputs: changed_plan)
    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_ONBOARDING_APPROVAL_MISMATCH"):
        manager._onboard(state, approved_project=approved)


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


def test_classified_bootstrap_failure_keeps_app_undeployed_and_last_stage(
    tmp_path: Path,
) -> None:
    _save_state(tmp_path, _state(stage="FINAL_DEPLOYED"))
    interrupted = _LifecycleManager(tmp_path)
    interrupted.fail_temporary = True
    interrupted.temporary_failure_code = "DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE"

    with pytest.raises(
        ReleaseCliError,
        match="DBTOBSB_BOOTSTRAP_TABLE_CREATE_STORAGE_UNAVAILABLE",
    ):
        interrupted.bootstrap()

    assert _required_state(tmp_path).stage == "FINAL_DEPLOYED"
    assert interrupted.events == []


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


def test_interrupted_app_phase_can_stop_and_retain_uninstall(tmp_path: Path) -> None:
    _save_state(tmp_path, _state(stage="GRANTS_APPLIED"))
    stopped = _LifecycleManager(tmp_path)

    stopped.stop()

    assert stopped.events == [("stop",)]

    retained = _LifecycleManager(tmp_path, "RETAIN\n")
    retained.uninstall(delete=False)

    assert [event[0] for event in retained.events] == [
        "stop",
        "app-delete",
        "grants",
        "retain-readback",
        "bundle-destroy",
        "local-cleanup",
    ]


def test_interrupted_app_phase_cannot_delete_evidence(tmp_path: Path) -> None:
    _save_state(tmp_path, _state(stage="GRANTS_APPLIED"))
    manager = _LifecycleManager(tmp_path, "DELETE\nDELETE PRODUCT DATA\n")

    with pytest.raises(ReleaseCliError, match="DBTOBSB_INSTALLER_INSTALLED_STATE_REQUIRED"):
        manager.uninstall(delete=True)

    assert manager.events == []


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
