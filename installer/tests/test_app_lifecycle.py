"""Fresh-install App deployment reconciliation tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import pytest

from dbtobsb_installer import app_lifecycle
from dbtobsb_installer.app_lifecycle import (
    AppComputeState,
    AppDeploymentPage,
    AppDeploymentRecord,
    AppLifecycleError,
    AppObservation,
    DeploymentMode,
    DeploymentStatus,
    ReconciledDeployment,
    StableDeploymentContract,
    deploy_bound_app_once,
)

_DEPLOYMENT_ID = "0123456789abcdef0123456789abcdef"
_SECOND_DEPLOYMENT_ID = "fedcba9876543210fedcba9876543210"


@pytest.fixture(autouse=True)
def _bounded_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [0.0]

    def sleep(seconds: float) -> None:
        now[0] += seconds

    monkeypatch.setattr(app_lifecycle, "_STOP_TIMEOUT_SECONDS", 4)
    monkeypatch.setattr(app_lifecycle, "_POLL_INTERVAL_SECONDS", 1.0)
    monkeypatch.setattr(app_lifecycle, "_monotonic", lambda: now[0])
    monkeypatch.setattr(app_lifecycle, "_sleep", sleep)


def _contract() -> StableDeploymentContract:
    return StableDeploymentContract(
        source_code_path="/Workspace/dbtobsb/.bundle/dbtobsb/release_v050/files/app",
        source_tree_sha256="a" * 64,
        resource_bindings_sha256="b" * 64,
        command=("uvicorn", "dbtobsb_app.main:app"),
        environment=tuple(
            sorted(
                (
                    ("DBTOBSB_WAREHOUSE_ID", "dbtobsb-app-warehouse"),
                    (
                        "DBTOBSB_RUNTIME_TRUST_STATUS_VIEW",
                        "dbtobsb-runtime-trust-status",
                    ),
                    ("DBTOBSB_RUN_HEALTH_VIEW", "dbtobsb-run-health"),
                    ("DBTOBSB_NODE_HEALTH_VIEW", "dbtobsb-node-health"),
                    (
                        "DBTOBSB_COLLECTION_HEALTH_VIEW",
                        "dbtobsb-collection-health",
                    ),
                )
            )
        ),
    )


def _record(deployment_id: str = _DEPLOYMENT_ID) -> AppDeploymentRecord:
    return AppDeploymentRecord(
        deployment_id=deployment_id,
        mode=DeploymentMode.SNAPSHOT.value,
        status=DeploymentStatus.SUCCEEDED.value,
        deployment_artifact_source_code_path=(
            f"/Workspace/Users/platform-generated/src/{deployment_id}"
        ),
        contract=_contract(),
    )


class _Client:
    def __init__(self) -> None:
        self.before_pages: dict[str | None, AppDeploymentPage] = {None: AppDeploymentPage(())}
        self.after_pages: dict[str | None, AppDeploymentPage] = {
            None: AppDeploymentPage((_record(),))
        }
        self.before_observation = AppObservation(AppComputeState.STOPPED.value)
        self.after_observation = AppObservation(
            AppComputeState.STOPPED.value,
            active_deployment_id=_DEPLOYMENT_ID,
        )
        self.run_calls = 0
        self.stop_calls = 0
        self.run_error: BaseException | None = None
        self.stop_error: BaseException | None = None
        self.before_inventory_error: BaseException | None = None
        self.after_inventory_error: BaseException | None = None
        self.after_invocation = False
        self.page_tokens: list[str | None] = []

    def list_deployments(self, page_token: str | None) -> AppDeploymentPage:
        self.page_tokens.append(page_token)
        if not self.after_invocation and self.before_inventory_error is not None:
            raise self.before_inventory_error
        if self.after_invocation and self.after_inventory_error is not None:
            raise self.after_inventory_error
        pages = self.after_pages if self.after_invocation else self.before_pages
        return pages[page_token]

    def observe_app(self) -> AppObservation:
        return self.after_observation if self.after_invocation else self.before_observation

    def run_bound_bundle_once(self) -> None:
        self.run_calls += 1
        self.after_invocation = True
        if self.run_error is not None:
            raise self.run_error

    def stop_app(self) -> None:
        self.stop_calls += 1
        if self.stop_error is not None:
            raise self.stop_error


def test_exactly_one_matching_snapshot_is_reconciled_after_stop() -> None:
    client = _Client()

    result = deploy_bound_app_once(client, expected_contract=_contract())

    assert result.stable_deployment_sha256 == _contract().sha256
    assert result.pages_read == 2
    assert client.run_calls == 1
    assert client.stop_calls == 1
    assert _DEPLOYMENT_ID not in repr(result)


def test_lost_runner_response_is_never_retried_and_after_set_wins() -> None:
    client = _Client()
    client.run_error = TimeoutError()

    result = deploy_bound_app_once(client, expected_contract=_contract())

    assert isinstance(result, ReconciledDeployment)
    assert client.run_calls == 1
    assert client.stop_calls == 1


def test_runner_interrupt_returns_authoritative_stopped_matching_proof() -> None:
    client = _Client()
    client.run_error = KeyboardInterrupt()

    result = deploy_bound_app_once(client, expected_contract=_contract())

    assert isinstance(result, ReconciledDeployment)
    assert client.run_calls == 1
    assert client.stop_calls == 1


def test_runner_error_with_two_distinct_deployments_is_ambiguous() -> None:
    client = _Client()
    client.run_error = TimeoutError()
    client.after_pages = {None: AppDeploymentPage((_record(), _record(_SECOND_DEPLOYMENT_ID)))}

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "APP_DEPLOYMENT_SET_AMBIGUOUS"
    assert client.run_calls == 1
    assert client.stop_calls == 1


def test_multiple_deployments_never_mask_unverified_running_compute() -> None:
    client = _Client()
    client.run_error = TimeoutError()
    client.stop_error = TimeoutError()
    client.after_pages = {None: AppDeploymentPage((_record(), _record(_SECOND_DEPLOYMENT_ID)))}
    client.after_observation = AppObservation(AppComputeState.ACTIVE.value)

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "APP_STOP_FAILED_RUNNING_UNVERIFIED"
    assert client.stop_calls == 1


@pytest.mark.parametrize(
    "before_observation",
    [
        AppObservation(AppComputeState.ACTIVE.value),
        AppObservation(AppComputeState.STOPPED.value, active_deployment_id=_DEPLOYMENT_ID),
        AppObservation(AppComputeState.STOPPED.value, pending_deployment_id=_DEPLOYMENT_ID),
    ],
)
def test_nonempty_or_nonstopped_baseline_blocks_before_runner_and_stop(
    before_observation: AppObservation,
) -> None:
    client = _Client()
    client.before_observation = before_observation

    with pytest.raises(AppLifecycleError, match="UNSUPPORTED_EXISTING_APP_DEPLOYMENT"):
        deploy_bound_app_once(client, expected_contract=_contract())

    assert client.run_calls == 0
    assert client.stop_calls == 0


@pytest.mark.parametrize(
    "before_observation",
    [
        AppObservation(AppComputeState.ACTIVE.value),
        AppObservation(AppComputeState.STOPPED.value, active_deployment_id=_DEPLOYMENT_ID),
        AppObservation(AppComputeState.STOPPED.value, pending_deployment_id=_DEPLOYMENT_ID),
    ],
)
def test_unsafe_baseline_is_rejected_before_inventory_can_mask_it(
    before_observation: AppObservation,
) -> None:
    client = _Client()
    client.before_observation = before_observation
    client.before_inventory_error = OSError()
    client.before_pages = {None: AppDeploymentPage((_record(), _record(_SECOND_DEPLOYMENT_ID)))}

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "UNSUPPORTED_EXISTING_APP_DEPLOYMENT"
    assert client.page_tokens == []
    assert client.run_calls == 0
    assert client.stop_calls == 0


def test_any_existing_deployment_blocks_fresh_install() -> None:
    client = _Client()
    client.before_pages = {None: AppDeploymentPage((_record(),))}

    with pytest.raises(AppLifecycleError, match="UNSUPPORTED_EXISTING_APP_DEPLOYMENT"):
        deploy_bound_app_once(client, expected_contract=_contract())

    assert client.run_calls == 0
    assert client.stop_calls == 0


@pytest.mark.parametrize(
    ("records", "code"),
    [
        ((), "APP_STAGE_DEPLOY_INDETERMINATE"),
        ((_record(), _record(_SECOND_DEPLOYMENT_ID)), "APP_DEPLOYMENT_SET_AMBIGUOUS"),
        (
            (replace(_record(), mode=DeploymentMode.AUTO_SYNC.value),),
            "APP_DEPLOYMENT_ACTIVE_MISMATCH",
        ),
        (
            (replace(_record(), status=DeploymentStatus.IN_PROGRESS.value),),
            "APP_DEPLOYMENT_PENDING_TIMEOUT",
        ),
        (
            (replace(_record(), status=DeploymentStatus.FAILED.value),),
            "APP_DEPLOYMENT_ACTIVE_MISMATCH",
        ),
        (
            (replace(_record(), status=DeploymentStatus.CANCELLED.value),),
            "APP_DEPLOYMENT_ACTIVE_MISMATCH",
        ),
        (
            (replace(_record(), contract=replace(_contract(), source_tree_sha256="c" * 64)),),
            "APP_DEPLOYMENT_ACTIVE_MISMATCH",
        ),
    ],
)
def test_zero_multiple_pending_failed_auto_sync_or_mismatch_never_proceeds(
    records: tuple[AppDeploymentRecord, ...], code: str
) -> None:
    client = _Client()
    client.after_pages = {None: AppDeploymentPage(records)}

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == code
    assert client.run_calls == 1
    assert client.stop_calls == 1


def test_pending_pointer_or_failed_stop_reports_cost_risk() -> None:
    client = _Client()
    client.stop_error = RuntimeError()
    client.after_observation = AppObservation(
        AppComputeState.ACTIVE.value,
        active_deployment_id=_DEPLOYMENT_ID,
        pending_deployment_id=_DEPLOYMENT_ID,
    )

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "APP_STOP_FAILED_RUNNING_UNVERIFIED"
    assert client.stop_calls == 1


def test_proved_stopped_state_allows_exact_inventory_failure_to_surface() -> None:
    client = _Client()
    client.stop_error = TimeoutError()
    client.after_inventory_error = OSError()

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "DBTOBSB_APP_DEPLOYMENT_INVENTORY_INDETERMINATE"
    assert client.stop_calls == 1


def test_lost_stop_response_is_harmless_after_independent_stopped_proof() -> None:
    client = _Client()
    client.stop_error = TimeoutError()

    result = deploy_bound_app_once(client, expected_contract=_contract())

    assert isinstance(result, ReconciledDeployment)
    assert client.stop_calls == 1


def test_pagination_failure_never_masks_unverified_running_compute() -> None:
    client = _Client()
    client.stop_error = TimeoutError()
    client.after_pages = {
        None: AppDeploymentPage((), "next"),
        "next": AppDeploymentPage((), "next"),
    }
    client.after_observation = AppObservation(AppComputeState.ACTIVE.value)

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "APP_STOP_FAILED_RUNNING_UNVERIFIED"


def test_inventory_failure_is_reported_only_after_stopped_no_pending_is_proved() -> None:
    client = _Client()
    client.after_pages = {
        None: AppDeploymentPage((), "next"),
        "next": AppDeploymentPage((), "next"),
    }

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "DBTOBSB_APP_DEPLOYMENT_PAGINATION_INVALID"


def test_duplicate_deployment_ids_use_the_one_documented_ambiguity_code() -> None:
    client = _Client()
    client.after_pages = {None: AppDeploymentPage((_record(), _record()))}

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "APP_DEPLOYMENT_SET_AMBIGUOUS"


def test_stopped_app_with_pending_pointer_times_out_as_pending() -> None:
    client = _Client()
    client.after_pages = {
        None: AppDeploymentPage((replace(_record(), status=DeploymentStatus.IN_PROGRESS.value),))
    }
    client.after_observation = AppObservation(
        AppComputeState.STOPPED.value,
        pending_deployment_id=_DEPLOYMENT_ID,
    )

    with pytest.raises(AppLifecycleError) as caught:
        deploy_bound_app_once(client, expected_contract=_contract())

    assert caught.value.code == "APP_DEPLOYMENT_PENDING_TIMEOUT"


def test_pending_deployment_is_polled_to_one_terminal_stopped_snapshot() -> None:
    class _EventuallyTerminalClient(_Client):
        def __init__(self) -> None:
            super().__init__()
            self.after_reads = 0

        def list_deployments(self, page_token: str | None) -> AppDeploymentPage:
            if not self.after_invocation:
                return super().list_deployments(page_token)
            self.page_tokens.append(page_token)
            self.after_reads += 1
            status = (
                DeploymentStatus.IN_PROGRESS.value
                if self.after_reads < 3
                else DeploymentStatus.SUCCEEDED.value
            )
            return AppDeploymentPage((replace(_record(), status=status),))

        def observe_app(self) -> AppObservation:
            if not self.after_invocation or self.after_reads >= 3:
                return super().observe_app()
            return AppObservation(
                AppComputeState.STOPPED.value,
                pending_deployment_id=_DEPLOYMENT_ID,
            )

    client = _EventuallyTerminalClient()

    result = deploy_bound_app_once(client, expected_contract=_contract())

    assert client.after_reads == 3
    assert result.pages_read == 4
    assert client.run_calls == 1
    assert client.stop_calls == 1


def test_failed_partial_inventory_pages_are_counted_in_reconciled_proof() -> None:
    class _TransientPartialFailureClient(_Client):
        def __init__(self) -> None:
            super().__init__()
            self.after_calls = 0

        def list_deployments(self, page_token: str | None) -> AppDeploymentPage:
            if not self.after_invocation:
                return super().list_deployments(page_token)
            self.page_tokens.append(page_token)
            self.after_calls += 1
            if self.after_calls == 1:
                return AppDeploymentPage((), "second")
            if self.after_calls == 2:
                raise OSError
            return AppDeploymentPage((_record(),))

    client = _TransientPartialFailureClient()

    result = deploy_bound_app_once(client, expected_contract=_contract())

    assert client.after_calls == 3
    assert result.pages_read == 4


def test_reconciliation_proof_enforces_exact_full_polling_page_budget() -> None:
    result = ReconciledDeployment(
        deployment_id=_DEPLOYMENT_ID,
        stable_deployment_sha256=_contract().sha256,
        pages_read=60_200,
        _construction_token=app_lifecycle._RECONCILED_TOKEN,
    )

    assert result.pages_read == 60_200
    with pytest.raises(AppLifecycleError) as caught:
        ReconciledDeployment(
            deployment_id=_DEPLOYMENT_ID,
            stable_deployment_sha256=_contract().sha256,
            pages_read=60_201,
            _construction_token=app_lifecycle._RECONCILED_TOKEN,
        )
    assert caught.value.code == "DBTOBSB_APP_RECONCILIATION_PROOF_INVALID"


def test_all_deployment_pages_are_consumed_and_cycles_fail_closed() -> None:
    client = _Client()
    client.after_pages = {
        None: AppDeploymentPage((), "next"),
        "next": AppDeploymentPage((_record(),)),
    }

    result = deploy_bound_app_once(client, expected_contract=_contract())

    assert result.pages_read == 3
    assert client.page_tokens == [None, None, "next"]

    cycle = _Client()
    cycle.after_pages = {
        None: AppDeploymentPage((), "next"),
        "next": AppDeploymentPage((), "next"),
    }
    with pytest.raises(AppLifecycleError, match="APP_DEPLOYMENT_PAGINATION_INVALID"):
        deploy_bound_app_once(cycle, expected_contract=_contract())
    assert cycle.run_calls == 1
    assert cycle.stop_calls == 1


def test_native_ids_and_records_are_redacted_and_proof_cannot_be_forged() -> None:
    record = _record()
    page = AppDeploymentPage((record,), "secret-page-token")
    observation = AppObservation(
        AppComputeState.STOPPED.value,
        active_deployment_id=_DEPLOYMENT_ID,
    )
    values = "\n".join((repr(record), repr(page), repr(observation), repr(_contract())))

    assert _DEPLOYMENT_ID not in values
    assert "secret-page-token" not in values
    assert _contract().source_code_path not in values
    with pytest.raises(AppLifecycleError, match="APP_RECONCILIATION_PROOF_DENIED"):
        ReconciledDeployment(
            deployment_id=_DEPLOYMENT_ID,
            stable_deployment_sha256=_contract().sha256,
            pages_read=1,
            _construction_token=object(),
        )


def test_deployment_contract_rejects_mutable_command_environment_and_artifact_aliases() -> None:
    with pytest.raises(AppLifecycleError, match="APP_DEPLOYMENT_CONTRACT_INVALID"):
        replace(_contract(), command=("python", "caller.py"))
    with pytest.raises(AppLifecycleError, match="APP_DEPLOYMENT_CONTRACT_INVALID"):
        replace(
            _contract(),
            environment=(("DBTOBSB_WAREHOUSE_ID", "caller-resource"),),
        )
    with pytest.raises(AppLifecycleError, match="APP_DEPLOYMENT_RECORD_INVALID"):
        replace(
            _record(),
            deployment_artifact_source_code_path=(
                "/Workspace/Users/platform-generated/src/ffffffffffffffffffffffffffffffff"
            ),
        )
    with pytest.raises(AppLifecycleError, match="APP_DEPLOYMENT_RECORD_INVALID"):
        replace(
            _record(),
            deployment_artifact_source_code_path=f"relative/src/{_DEPLOYMENT_ID}",
        )


@pytest.mark.parametrize(
    ("factory", "code"),
    [
        (
            lambda: replace(_record(), mode="/Workspace/canary"),
            "DBTOBSB_APP_DEPLOYMENT_RECORD_INVALID",
        ),
        (
            lambda: replace(_record(), status="secret-token-canary"),
            "DBTOBSB_APP_DEPLOYMENT_RECORD_INVALID",
        ),
        (
            lambda: AppObservation("/Workspace/secret-canary"),
            "DBTOBSB_APP_OBSERVATION_INVALID",
        ),
    ],
)
def test_unknown_native_state_is_rejected_without_echoing_canary(
    factory: Callable[[], object],
    code: str,
) -> None:
    with pytest.raises(AppLifecycleError) as caught:
        factory()

    assert caught.value.code == code
    assert "canary" not in str(caught.value)
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("source_tree_sha256", None),
        ("source_tree_sha256", 1),
        ("resource_bindings_sha256", None),
        ("resource_bindings_sha256", 1),
    ],
)
def test_deployment_contract_rejects_malformed_digest_types_with_sanitized_code(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(AppLifecycleError) as caught:
        replace(_contract(), **{field_name: value})

    assert caught.value.code == "DBTOBSB_APP_DEPLOYMENT_CONTRACT_INVALID"
