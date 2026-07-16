"""Adversarial tests for the sealed native Databricks platform adapters."""

from __future__ import annotations

import hashlib
import io
import json
import os
import signal
import stat
import subprocess
import sys
import time
import uuid
from collections.abc import Buffer, Mapping
from pathlib import Path
from typing import cast

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dbtobsb_installer.auth import (
    InstallerConnectionInputs,
    ValidatedInstallerConnection,
    validate_connection,
)
from dbtobsb_installer.native_bridge import (
    _EXPECTED_CLI,
    _EXPECTED_SDK,
    _MAX_OUTPUT_BYTES,
    _NATIVE_FAILURE_CODES,
    _PRE_NETWORK_NATIVE_CODES,
    DatabricksPlatformAdapterError,
    FailureStage,
    NativeProcessResult,
    RetryClass,
    SubprocessNativeRunner,
    _NativeBridgeLauncher,
    _VerifiedNativeExecutable,
)
from dbtobsb_installer.operations import (
    CleanupAction,
    CleanupPrivilege,
    Ed25519MarkerSigner,
    MarkerTextKind,
    PreparationLocator,
    SecurableType,
    SignedPreparationMarker,
    render_preparation_statement,
    sign_preparation_marker,
)
from dbtobsb_installer.platform_adapters import (
    ActorFingerprintObservation,
    DatabricksQueryCancellationClient,
    DatabricksQueryHistoryClient,
    FingerprintEnrollmentApprovalProof,
    NativeBoundSession,
    NativeStatementSubmitter,
    _observe_actor_fingerprint,
    _open_native_bound_session,
    observe_actor_fingerprint,
    open_native_bound_session,
    verify_fingerprint_enrollment_approval,
    verify_signed_actor_configuration,
)
from dbtobsb_installer.recovery import (
    CancellationHandle,
    CancellationOutcome,
    QueryHistoryRequest,
    QueryHistoryStatus,
    RecoveryOutcome,
    locate_operation,
)
from dbtobsb_installer.statement_contracts import StatementDisposition

_PROFILE = "dbtobsb-operator"
_HOST = "https://adb-1234567890123456.10.azuredatabricks.net"
_WAREHOUSE_ID = "0123456789abcdef"
_ACTOR_SHA256 = hashlib.sha256(b"operator@example.test").hexdigest()
_QUERY_ID = "87654321-4321-4abc-8abc-ba0987654321"
_CANARY = "customer-secret-canary"
_PROTOCOL = "dbtobsb.native-bridge.v1"


def _connection(*, warehouse_id: str = _WAREHOUSE_ID) -> ValidatedInstallerConnection:
    return validate_connection(
        InstallerConnectionInputs(
            profile=_PROFILE,
            canonical_host=_HOST,
            installer_warehouse_id=warehouse_id,
        )
    )


def _connection_sha256(connection: ValidatedInstallerConnection | None = None) -> str:
    selected = connection or _connection()
    document = {
        "canonical_host": selected.canonical_host,
        "installer_warehouse_id": selected.installer_warehouse_id,
        "profile": selected.profile,
        "schema": "dbtobsb.installer-connection.v1",
    }
    return hashlib.sha256(
        json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def _canonical(document: Mapping[str, object]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode()
        + b"\n"
    )


def _signer() -> Ed25519MarkerSigner:
    return Ed25519MarkerSigner(Ed25519PrivateKey.generate())


def _actor_configuration(
    signer: Ed25519MarkerSigner | None = None,
    *,
    connection: ValidatedInstallerConnection | None = None,
):
    selected_signer = signer or _signer()
    selected_connection = connection or _connection()
    document = _canonical(
        {
            "approved_actor_sha256": _ACTOR_SHA256,
            "connection_sha256": _connection_sha256(selected_connection),
            "schema": "dbtobsb.signed-actor-binding.v1",
            "signer_key_id": selected_signer.key_id,
        }
    )
    return verify_signed_actor_configuration(
        connection=selected_connection,
        document=document,
        signature=selected_signer.sign(document),
        verifier=selected_signer.verifier(),
    )


def _enrollment_approval(signer: Ed25519MarkerSigner | None = None):
    selected_signer = signer or _signer()
    document = _canonical(
        {
            "browser_identity_confirmation_sha256": hashlib.sha256(
                b"browser-confirmed"
            ).hexdigest(),
            "connection_sha256": _connection_sha256(),
            "cost_acknowledgement_sha256": hashlib.sha256(b"cost-approved").hexdigest(),
            "schema": "dbtobsb.actor-fingerprint-enrollment-approval.v1",
            "signer_key_id": selected_signer.key_id,
        }
    )
    return verify_fingerprint_enrollment_approval(
        connection=_connection(),
        document=document,
        signature=selected_signer.sign(document),
        verifier=selected_signer.verifier(),
    )


def _native_response(
    *,
    code: str,
    result: object | None = None,
    ok: bool = True,
) -> bytes:
    document: dict[str, object] = {"code": code, "ok": ok, "protocol": _PROTOCOL}
    if ok:
        document["result"] = result
    return _canonical(document)


def _actor_matched() -> NativeProcessResult:
    return NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_ACTOR_MATCHED",
            result={"kind": "actor_identity_check", "matched": True},
        ),
    )


class _Runner:
    def __init__(self, results: list[NativeProcessResult | Exception] | None = None) -> None:
        self.results = results or [_actor_matched()]
        self.calls: list[tuple[str, bytes, dict[str, str], float, int]] = []

    def run(
        self,
        executable: _VerifiedNativeExecutable,
        *,
        stdin: bytes,
        environment: Mapping[str, str],
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> NativeProcessResult:
        self.calls.append(
            (
                executable.installed_path,
                stdin,
                dict(environment),
                timeout_seconds,
                max_output_bytes,
            )
        )
        result = self.results[len(self.calls) - 1]
        if isinstance(result, Exception):
            raise result
        return result


def _release_layout(tmp_path: Path, *, helper: bytes = b"sealed-helper-v1") -> tuple[Path, str]:
    layout = tmp_path / "darwin-arm64"
    layout.mkdir(mode=0o700, parents=True)
    executable = layout / "dbtobsb-native-bridge"
    executable.write_bytes(helper)
    executable.chmod(0o700)
    manifest = {
        "arch": "arm64",
        "databricks_cli": _EXPECTED_CLI,
        "helper": {
            "filename": "dbtobsb-native-bridge",
            "sha256": hashlib.sha256(helper).hexdigest(),
            "size": len(helper),
        },
        "os": "darwin",
        "protocol": _PROTOCOL,
        "schema": "dbtobsb.native-helper-release.v1",
        "sdk": _EXPECTED_SDK,
    }
    raw = _canonical(manifest)
    manifest_path = layout / "manifest.json"
    manifest_path.write_bytes(raw)
    manifest_path.chmod(0o600)
    return layout, hashlib.sha256(raw).hexdigest()


def _launcher(
    tmp_path: Path,
    runner: _Runner,
    *,
    environment: Mapping[str, str] | None = None,
) -> _NativeBridgeLauncher:
    layout, manifest_sha256 = _release_layout(tmp_path)
    return _NativeBridgeLauncher._for_test(
        layout_directory=layout,
        expected_manifest_sha256=manifest_sha256,
        runner=runner,
        environment=environment or {"HOME": "/safe/operator", "PATH": "/hostile"},
    )


def _verified_test_executable(tmp_path: Path) -> _VerifiedNativeExecutable:
    executable = tmp_path / "verified-native-helper"
    executable.write_bytes(b"sealed-test-helper")
    executable.chmod(0o700)
    return _VerifiedNativeExecutable._for_test(executable)


def _execute_installed_path_for_process_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    """Assert lifecycle tests execute only from the private verified-byte staging copy."""

    native_popen = subprocess.Popen

    def popen(args, **kwargs):
        assert args == ("dbtobsb-native-bridge",)
        assert kwargs["executable"].startswith("/private/tmp/dbtobsb-native-")
        assert kwargs["executable"].endswith("/dbtobsb-native-bridge")
        assert "pass_fds" not in kwargs
        return native_popen(args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", popen)


def _session(tmp_path: Path, runner: _Runner) -> NativeBoundSession:
    return _open_native_bound_session(
        connection=_connection(),
        actor_configuration=_actor_configuration(),
        launcher=_launcher(tmp_path, runner),
    )


def _preparation_statement():
    signer = _signer()
    operation_uuid = uuid.UUID("12345678-1234-4abc-8abc-1234567890ab")
    locator = PreparationLocator(
        installation_id="a" * 64,
        generation=1,
        sequence=1,
        operation_uuid=operation_uuid,
        envelope_sha256="b" * 64,
        statement_sha256="c" * 64,
        operator_group="dbtobsb migration operators",
        warehouse_id=_WAREHOUSE_ID,
        securable_type=SecurableType.TABLE,
        securable_name="observability.dbtobsb.installation_state",
        privilege=CleanupPrivilege.MODIFY,
        action=CleanupAction.REMOVE_EXACT_PRODUCT_GRANT,
    )
    marker = sign_preparation_marker(locator, signer)
    return render_preparation_statement(marker, signer.verifier()), marker


def _signed_history_query_text() -> tuple[SignedPreparationMarker, Ed25519MarkerSigner, str]:
    signer = _signer()
    locator = PreparationLocator(
        installation_id="a" * 64,
        generation=1,
        sequence=1,
        operation_uuid=uuid.UUID("12345678-1234-4abc-8abc-1234567890ab"),
        envelope_sha256="b" * 64,
        statement_sha256="c" * 64,
        operator_group="dbtobsb migration operators",
        warehouse_id=_WAREHOUSE_ID,
        securable_type=SecurableType.TABLE,
        securable_name="observability.dbtobsb.installation_state",
        privilege=CleanupPrivilege.MODIFY,
        action=CleanupAction.REMOVE_EXACT_PRODUCT_GRANT,
    )
    marker = sign_preparation_marker(locator, signer)
    query_text = render_preparation_statement(marker, signer.verifier())._transport_text()
    return marker, signer, query_text


def _locate_cancellation_handle(
    history: DatabricksQueryHistoryClient,
    *,
    marker: SignedPreparationMarker,
    signer: Ed25519MarkerSigner,
) -> CancellationHandle:
    result = locate_operation(
        client=history,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.PREPARATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    assert result.outcome is RecoveryOutcome.UNIQUE_NONTERMINAL
    assert isinstance(result.cancellation_handle, CancellationHandle)
    return result.cancellation_handle


def _history_result(
    *,
    status: str = "RUNNING",
    query_text: str = "SELECT closed_marker",
    next_page_token: str | None = None,
) -> dict[str, object]:
    return {
        "kind": "query_history_page",
        "next_page_token": next_page_token,
        "records": [
            {
                "query_reference": _QUERY_ID,
                "query_text": query_text,
                "status": status,
                "warehouse_id": _WAREHOUSE_ID,
            }
        ],
    }


def _request(*, warehouse_id: str = _WAREHOUSE_ID) -> QueryHistoryRequest:
    return QueryHistoryRequest(
        warehouse_id=warehouse_id,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )


@pytest.mark.parametrize("disposition", tuple(StatementDisposition))
def test_native_statement_submitter_sends_only_fixed_registry_descriptor(
    tmp_path: Path,
    disposition: StatementDisposition,
) -> None:
    runner = _Runner(
        [
            NativeProcessResult(
                0,
                _native_response(
                    code="DBTOBSB_NATIVE_STATEMENT_RECEIPT",
                    result={
                        "disposition": disposition.value,
                        "kind": "statement_execution_submit",
                    },
                ),
            )
        ]
    )
    session = _session(tmp_path, runner)
    submitter = NativeStatementSubmitter(connection=_connection(), session=session)
    statement, marker = _preparation_statement()

    receipt = submitter.submit(_connection(), statement)

    assert receipt.disposition is disposition
    assert repr(submitter) == "NativeStatementSubmitter(<redacted>)"
    assert len(runner.calls) == 1
    request = json.loads(runner.calls[0][1])
    assert request["operation"] == "statement_execution_submit"
    assert request["payload"] == {
        "expected_actor_sha256": _ACTOR_SHA256,
        "parameters": {"marker_token": marker.compact_token},
        "registry_operation": "preparation_marker_v1",
        "registry_version": "dbtobsb.native-operation-registry.v1",
        "semantic_sha256": statement.semantic_sha256,
        "warehouse_id": _WAREHOUSE_ID,
    }
    serialized = runner.calls[0][1].decode()
    assert statement._transport_text() not in serialized
    assert '"statement"' not in serialized
    assert "SELECT" not in serialized


def test_native_statement_submitter_rejects_wrong_session_and_untyped_receipts(
    tmp_path: Path,
) -> None:
    wrong_connection = _connection(warehouse_id="fedcba9876543210")
    session = _session(tmp_path, _Runner())
    with pytest.raises(DatabricksPlatformAdapterError, match="BOUND_SESSION_MISMATCH"):
        NativeStatementSubmitter(connection=wrong_connection, session=session)

    statement, _ = _preparation_statement()
    malformed = _Runner(
        [
            NativeProcessResult(
                0,
                _native_response(
                    code="DBTOBSB_NATIVE_STATEMENT_RECEIPT",
                    result={"disposition": "SUCCEEDED", "kind": "statement_execution_submit"},
                ),
            )
        ]
    )
    submitter = NativeStatementSubmitter(
        connection=_connection(),
        session=_session(tmp_path / "malformed", malformed),
    )
    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        submitter.submit(_connection(), statement)
    assert captured.value.failure.code == "DBTOBSB_INSTALLER_STATEMENT_RESPONSE_INVALID"
    assert captured.value.failure.stage is FailureStage.STATEMENT_SUBMISSION
    assert captured.value.failure.possible_running_or_cost is True


def test_signed_actor_configuration_is_canonical_signature_and_connection_bound() -> None:
    signer = _signer()
    configuration = _actor_configuration(signer)

    assert repr(configuration) == "VerifiedSignedActorConfiguration(<redacted>)"
    assert configuration.signed_config_sha256 not in repr(configuration)

    document = _canonical(
        {
            "approved_actor_sha256": _ACTOR_SHA256,
            "connection_sha256": _connection_sha256(),
            "schema": "dbtobsb.signed-actor-binding.v1",
            "signer_key_id": signer.key_id,
        }
    )
    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        verify_signed_actor_configuration(
            connection=_connection(),
            document=document,
            signature=b"x" * 64,
            verifier=signer.verifier(),
        )
    assert captured.value.code == "DBTOBSB_INSTALLER_ACTOR_CONFIG_SIGNATURE_INVALID"


def test_session_is_opaque_and_opening_it_does_not_create_a_stale_actor_gate(
    tmp_path: Path,
) -> None:
    runner = _Runner()
    session = _session(tmp_path, runner)

    assert runner.calls == []
    assert repr(session) == "NativeBoundSession(<redacted>)"


def test_actor_mismatch_in_protected_history_invocation_blocks_result(tmp_path: Path) -> None:
    runner = _Runner(
        [
            NativeProcessResult(
                1,
                _native_response(code="DBTOBSB_NATIVE_ACTOR_MISMATCH", ok=False),
            )
        ]
    )
    client = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        client.list_page(_request())

    assert captured.value.code == "DBTOBSB_INSTALLER_ACTOR_MISMATCH"
    assert captured.value.failure.possible_running_or_cost is True
    request = json.loads(runner.calls[0][1])
    assert request["operation"] == "query_history_list"
    assert request["payload"]["expected_actor_sha256"] == _ACTOR_SHA256


def test_enrollment_observe_requires_signed_cost_and_browser_confirmation_and_is_non_authorizing(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        [
            NativeProcessResult(
                0,
                _native_response(
                    code="DBTOBSB_NATIVE_ACTOR_FINGERPRINT_OBSERVED",
                    result={"actor_sha256": _ACTOR_SHA256},
                ),
            )
        ]
    )
    observation = _observe_actor_fingerprint(
        connection=_connection(),
        approval=_enrollment_approval(),
        launcher=_launcher(tmp_path, runner),
    )

    request = json.loads(runner.calls[0][1])
    assert request["operation"] == "actor_fingerprint_observe"
    assert request["payload"] == {"warehouse_id": _WAREHOUSE_ID}
    assert isinstance(observation, ActorFingerprintObservation)
    assert not isinstance(observation, (FingerprintEnrollmentApprovalProof, NativeBoundSession))
    assert _ACTOR_SHA256 not in repr(observation)


def test_production_entrypoints_have_no_path_or_launcher_parameters() -> None:
    assert open_native_bound_session.__kwdefaults__ is None
    assert observe_actor_fingerprint.__kwdefaults__ is None


def test_history_uses_native_page_of_one_and_preserves_all_fields(tmp_path: Path) -> None:
    history_response = NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_HISTORY_PAGE",
            result=_history_result(next_page_token="next+page/token"),
        ),
    )
    runner = _Runner([history_response])
    client = DatabricksQueryHistoryClient(
        connection=_connection(),
        session=_session(tmp_path, runner),
    )

    page = client.list_page(_request())

    assert len(page.records) == 1
    assert page.records[0].query_reference == _QUERY_ID
    assert page.records[0].query_text == "SELECT closed_marker"
    assert page.records[0].status == "RUNNING"
    assert page.next_page_token == "next+page/token"
    native_request = json.loads(runner.calls[0][1])
    assert native_request["operation"] == "query_history_list"
    assert native_request["payload"] == {
        "end_time_ms": 2_000,
        "expected_actor_sha256": _ACTOR_SHA256,
        "start_time_ms": 1_000,
        "warehouse_id": _WAREHOUSE_ID,
    }


@pytest.mark.parametrize("status", [status.value for status in QueryHistoryStatus])
def test_history_accepts_each_closed_ga_status(tmp_path: Path, status: str) -> None:
    runner = _Runner(
        [
            NativeProcessResult(
                0,
                _native_response(
                    code="DBTOBSB_NATIVE_HISTORY_PAGE",
                    result=_history_result(status=status),
                ),
            ),
        ]
    )
    client = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )
    assert client.list_page(_request()).records[0].status == status


def test_large_single_history_record_stays_within_native_contract(tmp_path: Path) -> None:
    query_text = "x" * (512 * 1024)
    runner = _Runner(
        [
            NativeProcessResult(
                0,
                _native_response(
                    code="DBTOBSB_NATIVE_HISTORY_PAGE",
                    result=_history_result(query_text=query_text),
                ),
            ),
        ]
    )
    client = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )
    assert client.list_page(_request()).records[0].query_text == query_text


def test_worst_case_escaped_history_record_stays_within_exact_native_output_cap(
    tmp_path: Path,
) -> None:
    query_text = "\x01" * (512 * 1024)
    encoded = _native_response(
        code="DBTOBSB_NATIVE_HISTORY_PAGE",
        result=_history_result(query_text=query_text),
    )
    assert 3 * 1024 * 1024 < len(encoded) < _MAX_OUTPUT_BYTES
    runner = _Runner([NativeProcessResult(0, encoded)])
    client = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )

    assert client.list_page(_request()).records[0].query_text == query_text
    assert runner.calls[0][4] == (4 * 1024 * 1024) + (16 * 1024)


def test_wrong_history_warehouse_blocks_before_another_process(tmp_path: Path) -> None:
    runner = _Runner()
    client = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        client.list_page(_request(warehouse_id="fedcba9876543210"))

    assert captured.value.code == "DBTOBSB_INSTALLER_HISTORY_WAREHOUSE_MISMATCH"
    assert runner.calls == []


def test_each_history_call_is_one_actor_protected_native_invocation(tmp_path: Path) -> None:
    page = NativeProcessResult(
        0,
        _native_response(code="DBTOBSB_NATIVE_HISTORY_PAGE", result=_history_result()),
    )
    runner = _Runner([page, page])
    client = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )
    client.list_page(_request())
    client.list_page(_request())

    assert [json.loads(call[1])["operation"] for call in runner.calls] == [
        "query_history_list",
        "query_history_list",
    ]
    assert all(
        json.loads(call[1])["payload"]["expected_actor_sha256"] == _ACTOR_SHA256
        for call in runner.calls
    )


def test_history_failure_after_actor_gate_reports_possible_cost_and_sequence(
    tmp_path: Path,
) -> None:
    runner = _Runner(
        [
            NativeProcessResult(
                1,
                _native_response(code="DBTOBSB_NATIVE_HISTORY_UNAVAILABLE", ok=False),
            ),
        ]
    )
    client = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        client.list_page(_request())

    assert captured.value.failure.possible_running_or_cost is True
    assert captured.value.failure.safe_next_action.count("Query History") == 1
    assert [json.loads(call[1])["operation"] for call in runner.calls] == [
        "query_history_list",
    ]


def test_pre_network_auth_failure_is_cost_false_until_remote_state_becomes_possible(
    tmp_path: Path,
) -> None:
    auth_failure = NativeProcessResult(
        1,
        _native_response(code="DBTOBSB_NATIVE_AUTH_UNAVAILABLE", ok=False),
    )
    first_runner = _Runner([auth_failure])
    first_history = DatabricksQueryHistoryClient(
        connection=_connection(), session=_session(tmp_path / "first", first_runner)
    )

    with pytest.raises(DatabricksPlatformAdapterError) as first:
        first_history.list_page(_request())

    assert first.value.failure.stage is FailureStage.AUTH_CONFIGURATION
    assert first.value.failure.possible_running_or_cost is False

    marker, signer, query_text = _signed_history_query_text()
    page = NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_HISTORY_PAGE",
            result=_history_result(query_text=query_text),
        ),
    )
    sticky_runner = _Runner([page, auth_failure])
    sticky_session = _session(tmp_path / "sticky", sticky_runner)
    sticky_history = DatabricksQueryHistoryClient(connection=_connection(), session=sticky_session)
    handle = _locate_cancellation_handle(sticky_history, marker=marker, signer=signer)
    cancellation = DatabricksQueryCancellationClient(
        connection=_connection(), session=sticky_session
    )

    with pytest.raises(DatabricksPlatformAdapterError) as sticky:
        cancellation.request_cancel(handle)

    assert sticky.value.failure.stage is FailureStage.AUTH_CONFIGURATION
    assert sticky.value.failure.possible_running_or_cost is True
    assert sticky.value.failure.retry_class is RetryClass.RETRY_AFTER_CORRECTION
    assert "managed OS account" in sticky.value.failure.safe_next_action


@pytest.mark.parametrize(
    "code,accepted,outcome",
    [
        (
            "DBTOBSB_NATIVE_CANCEL_ACCEPTED",
            True,
            CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL,
        ),
        (
            "DBTOBSB_NATIVE_CANCEL_REJECTED",
            False,
            CancellationOutcome.REQUEST_REJECTED_NONTERMINAL,
        ),
    ],
)
def test_cancel_accepted_and_explicit_ok_true_rejection_are_typed_nonterminal_outcomes(
    tmp_path: Path,
    code: str,
    accepted: bool,
    outcome: CancellationOutcome,
) -> None:
    marker, signer, query_text = _signed_history_query_text()
    runner = _Runner(
        [
            NativeProcessResult(
                0,
                _native_response(
                    code="DBTOBSB_NATIVE_HISTORY_PAGE",
                    result=_history_result(query_text=query_text),
                ),
            ),
            NativeProcessResult(
                0,
                _native_response(
                    code=code,
                    result={"accepted": accepted, "kind": "statement_execution_cancel"},
                ),
            ),
        ]
    )
    session = _session(tmp_path, runner)
    history = DatabricksQueryHistoryClient(connection=_connection(), session=session)
    handle = _locate_cancellation_handle(history, marker=marker, signer=signer)
    client = DatabricksQueryCancellationClient(connection=_connection(), session=session)

    assert client.request_cancel(handle) is outcome
    assert [json.loads(call[1])["operation"] for call in runner.calls] == [
        "query_history_list",
        "statement_execution_cancel",
    ]
    assert json.loads(runner.calls[1][1])["payload"] == {
        "expected_actor_sha256": _ACTOR_SHA256,
        "statement_id": _QUERY_ID,
        "warehouse_id": _WAREHOUSE_ID,
    }


def test_cancel_rejects_valid_but_unobserved_uuid_before_another_process(tmp_path: Path) -> None:
    runner = _Runner()
    client = DatabricksQueryCancellationClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        client.request_cancel(cast(CancellationHandle, _QUERY_ID))

    assert captured.value.code == "DBTOBSB_INSTALLER_CANCELLATION_HANDLE_REQUIRED"
    assert runner.calls == []


def test_cancel_rejects_bad_reference_before_process(tmp_path: Path) -> None:
    runner = _Runner()
    client = DatabricksQueryCancellationClient(
        connection=_connection(), session=_session(tmp_path, runner)
    )
    with pytest.raises(DatabricksPlatformAdapterError):
        client.request_cancel(cast(CancellationHandle, f"{_QUERY_ID}/{_CANARY}"))
    assert runner.calls == []


def test_cancellation_handle_is_session_bound_one_shot_and_cannot_be_reminted(
    tmp_path: Path,
) -> None:
    marker, signer, query_text = _signed_history_query_text()
    page = NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_HISTORY_PAGE",
            result=_history_result(query_text=query_text),
        ),
    )
    cancel = NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_CANCEL_ACCEPTED",
            result={"accepted": True, "kind": "statement_execution_cancel"},
        ),
    )
    runner = _Runner([page, cancel, page])
    session = _session(tmp_path, runner)
    history = DatabricksQueryHistoryClient(connection=_connection(), session=session)
    handle = _locate_cancellation_handle(history, marker=marker, signer=signer)
    cancellation = DatabricksQueryCancellationClient(connection=_connection(), session=session)

    assert repr(handle) == "CancellationHandle(<redacted>)"
    assert not hasattr(handle, "_query_reference")
    with pytest.raises(TypeError):
        vars(handle)
    assert cancellation.request_cancel(handle) is CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL
    with pytest.raises(DatabricksPlatformAdapterError) as reused:
        cancellation.request_cancel(handle)
    assert reused.value.code == "DBTOBSB_INSTALLER_CANCELLATION_HANDLE_INVALID"

    second = locate_operation(
        client=history,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.PREPARATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    assert second.outcome is RecoveryOutcome.CANCELLATION_TARGET_UNAVAILABLE_INDETERMINATE
    assert second.cancellation_handle is None
    assert len(runner.calls) == 3


def test_cancellation_handle_from_another_session_is_rejected_without_consuming_it(
    tmp_path: Path,
) -> None:
    marker, signer, query_text = _signed_history_query_text()
    page = NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_HISTORY_PAGE",
            result=_history_result(query_text=query_text),
        ),
    )
    accepted = NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_CANCEL_ACCEPTED",
            result={"accepted": True, "kind": "statement_execution_cancel"},
        ),
    )
    first_runner = _Runner([page, accepted])
    first_session = _session(tmp_path / "first", first_runner)
    first_history = DatabricksQueryHistoryClient(connection=_connection(), session=first_session)
    handle = _locate_cancellation_handle(first_history, marker=marker, signer=signer)
    second_runner = _Runner()
    second_session = _session(tmp_path / "second", second_runner)
    second_cancellation = DatabricksQueryCancellationClient(
        connection=_connection(), session=second_session
    )

    with pytest.raises(DatabricksPlatformAdapterError) as foreign:
        second_cancellation.request_cancel(handle)
    assert foreign.value.code == "DBTOBSB_INSTALLER_CANCELLATION_HANDLE_INVALID"
    assert second_runner.calls == []

    first_cancellation = DatabricksQueryCancellationClient(
        connection=_connection(), session=first_session
    )
    assert (
        first_cancellation.request_cancel(handle)
        is CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL
    )


@pytest.mark.parametrize(
    "status,outcome",
    [
        ("FINISHED", RecoveryOutcome.UNIQUE_TERMINAL_SUCCESS),
        ("FAILED", RecoveryOutcome.UNIQUE_TERMINAL_FAILURE),
        ("CANCELED", RecoveryOutcome.CANCELLATION_NONTERMINAL),
    ],
)
def test_terminal_or_already_canceled_match_never_mints_a_cancellation_handle(
    tmp_path: Path,
    status: str,
    outcome: RecoveryOutcome,
) -> None:
    marker, signer, query_text = _signed_history_query_text()
    page = NativeProcessResult(
        0,
        _native_response(
            code="DBTOBSB_NATIVE_HISTORY_PAGE",
            result=_history_result(status=status, query_text=query_text),
        ),
    )
    runner = _Runner([page, page])
    session = _session(tmp_path, runner)
    history = DatabricksQueryHistoryClient(connection=_connection(), session=session)

    for _ in range(2):
        result = locate_operation(
            client=history,
            verifier=signer.verifier(),
            marker=marker,
            kind=MarkerTextKind.PREPARATION,
            warehouse_id=_WAREHOUSE_ID,
            start_time_ms=1_000,
            end_time_ms=2_000,
        )
        assert result.outcome is outcome
        assert result.cancellation_handle is None


@pytest.mark.parametrize("native_code", sorted(_NATIVE_FAILURE_CODES))
def test_every_native_failure_code_has_safe_json_ready_mapping(
    tmp_path: Path,
    native_code: str,
) -> None:
    runner = _Runner([NativeProcessResult(1, _native_response(code=native_code, ok=False))])
    launcher = _launcher(tmp_path, runner)

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        launcher._invoke(
            stage=FailureStage.ACTOR_IDENTITY,
            operation="actor_identity_check",
            profile=_PROFILE,
            canonical_host=_HOST,
            payload={"expected_actor_sha256": _ACTOR_SHA256, "warehouse_id": _WAREHOUSE_ID},
        )

    rendered = json.dumps(captured.value.failure.as_dict(), sort_keys=True)
    expected_stage = (
        FailureStage.AUTH_CONFIGURATION
        if native_code in _PRE_NETWORK_NATIVE_CODES
        else FailureStage.ACTOR_IDENTITY
    )
    registry_pre_network = native_code in {
        "DBTOBSB_NATIVE_REGISTRY_DIGEST_MISMATCH",
        "DBTOBSB_NATIVE_REGISTRY_OPERATION_DENIED",
        "DBTOBSB_NATIVE_REGISTRY_PARAMETERS_INVALID",
    }
    assert captured.value.failure.stage is expected_stage
    assert captured.value.failure.possible_running_or_cost is (
        native_code not in _PRE_NETWORK_NATIVE_CODES and not registry_pre_network
    )
    assert captured.value.failure.responsible_actor
    assert captured.value.failure.retry_class in RetryClass
    assert captured.value.failure.safe_next_action
    assert _CANARY not in rendered


@pytest.mark.parametrize(
    "result,code",
    [
        (NativeProcessResult(1, _actor_matched().stdout), "NATIVE_EXIT_RESPONSE_MISMATCH"),
        (
            NativeProcessResult(
                0,
                _native_response(code="DBTOBSB_NATIVE_AUTH_UNAVAILABLE", ok=False),
            ),
            "NATIVE_EXIT_RESPONSE_MISMATCH",
        ),
        (NativeProcessResult(2, b""), "NATIVE_NO_OUTPUT"),
        (NativeProcessResult(1, b'{"code":"x","code":"y"}\n'), "NATIVE_RESPONSE_INVALID"),
        (
            NativeProcessResult(
                0,
                b'{"code":"DBTOBSB_NATIVE_ACTOR_MATCHED","ok":true,'
                b'"protocol":"dbtobsb.native-bridge.v1","result":{},"unknown":true}\n',
            ),
            "NATIVE_RESPONSE_INVALID",
        ),
    ],
)
def test_exit_no_output_duplicate_and_unknown_response_combinations_fail_closed(
    tmp_path: Path,
    result: NativeProcessResult,
    code: str,
) -> None:
    runner = _Runner([result])
    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        _launcher(tmp_path, runner)._invoke(
            stage=FailureStage.ACTOR_IDENTITY,
            operation="actor_identity_check",
            profile=_PROFILE,
            canonical_host=_HOST,
            payload={
                "expected_actor_sha256": _ACTOR_SHA256,
                "warehouse_id": _WAREHOUSE_ID,
            },
        )
    assert code in captured.value.code


def test_fixed_manifest_and_executable_are_verified_before_every_launch(tmp_path: Path) -> None:
    runner = _Runner([_actor_matched(), _actor_matched()])
    launcher = _launcher(tmp_path, runner)
    payload: dict[str, object] = {
        "expected_actor_sha256": _ACTOR_SHA256,
        "warehouse_id": _WAREHOUSE_ID,
    }
    launcher._invoke(
        stage=FailureStage.ACTOR_IDENTITY,
        operation="actor_identity_check",
        profile=_PROFILE,
        canonical_host=_HOST,
        payload=payload,
    )
    executable = Path(runner.calls[0][0])
    executable.write_bytes(b"changed-after-first-launch")
    executable.chmod(0o700)

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        launcher._invoke(
            stage=FailureStage.ACTOR_IDENTITY,
            operation="actor_identity_check",
            profile=_PROFILE,
            canonical_host=_HOST,
            payload=payload,
        )

    assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_EXECUTABLE_SEAL_MISMATCH"
    assert len(runner.calls) == 1


def test_executable_replacement_after_seal_uses_only_the_opened_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_output = _native_response(
        code="DBTOBSB_NATIVE_ACTOR_MATCHED",
        result={"kind": "actor_identity_check", "matched": True},
    )
    original_helper = b"#!/bin/sh\nprintf '%s\\n' '" + original_output.rstrip(b"\n") + b"'\n"
    hostile_helper = b"#!/bin/sh\nprintf 'hostile-path-replacement\\n'\n"
    layout, manifest_sha256 = _release_layout(tmp_path, helper=original_helper)

    class _ReplacingRunner:
        def run(
            self,
            executable: _VerifiedNativeExecutable,
            *,
            stdin: bytes,
            environment: Mapping[str, str],
            timeout_seconds: float,
            max_output_bytes: int,
        ) -> NativeProcessResult:
            installed_path = Path(executable.installed_path)
            installed_path.rename(installed_path.with_suffix(".sealed"))
            installed_path.write_bytes(hostile_helper)
            installed_path.chmod(0o700)

            class _OpenedIdentityProcess:
                pid = 999_990
                stdin = io.BytesIO()
                stdout = io.BytesIO(original_output)
                returncode = 0

                def wait(self, timeout: float | None = None) -> int:
                    del timeout
                    return 0

                def kill(self) -> None:
                    self.returncode = -9

            def inspect_staged_binding(args, **kwargs):
                assert args == ("dbtobsb-native-bridge",)
                staged_path = Path(kwargs["executable"])
                assert staged_path.parent.parent == Path("/private/tmp")
                assert staged_path.read_bytes() == original_helper
                assert stat.S_IMODE(staged_path.stat().st_mode) == 0o500
                assert "pass_fds" not in kwargs
                assert installed_path.read_bytes() == hostile_helper
                current = os.fstat(executable.fd)
                assert (current.st_dev, current.st_ino) == (executable.device, executable.inode)
                return _OpenedIdentityProcess()

            monkeypatch.setattr(subprocess, "Popen", inspect_staged_binding)
            return SubprocessNativeRunner().run(
                executable,
                stdin=stdin,
                environment=environment,
                timeout_seconds=timeout_seconds,
                max_output_bytes=max_output_bytes,
            )

    launcher = _NativeBridgeLauncher._for_test(
        layout_directory=layout,
        expected_manifest_sha256=manifest_sha256,
        runner=_ReplacingRunner(),
        environment={"HOME": "/safe/operator"},
    )

    response = launcher._invoke(
        stage=FailureStage.ACTOR_IDENTITY,
        operation="actor_identity_check",
        profile=_PROFILE,
        canonical_host=_HOST,
        payload={"expected_actor_sha256": _ACTOR_SHA256, "warehouse_id": _WAREHOUSE_ID},
    )

    assert response.code == "DBTOBSB_NATIVE_ACTOR_MATCHED"


def test_missing_no_follow_support_fails_closed_before_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _Runner()
    launcher = _launcher(tmp_path, runner)
    monkeypatch.delattr(os, "O_NOFOLLOW", raising=False)

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        launcher._invoke(
            stage=FailureStage.QUERY_HISTORY,
            operation="query_history_list",
            profile=_PROFILE,
            canonical_host=_HOST,
            payload={
                "end_time_ms": 2_000,
                "expected_actor_sha256": _ACTOR_SHA256,
                "start_time_ms": 1_000,
                "warehouse_id": _WAREHOUSE_ID,
            },
        )

    assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_FD_EXECUTION_UNAVAILABLE"
    assert captured.value.failure.stage is FailureStage.RELEASE_SEAL
    assert captured.value.failure.possible_running_or_cost is False
    assert runner.calls == []


def test_darwin_staged_exec_refusal_has_a_stable_fail_closed_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError(13, "refused")),
    )

    with (
        _verified_test_executable(tmp_path) as executable,
        pytest.raises(DatabricksPlatformAdapterError) as captured,
    ):
        SubprocessNativeRunner().run(
            executable,
            stdin=b"{}",
            environment={"HOME": "/tmp"},
            timeout_seconds=1.0,
            max_output_bytes=100,
        )

    assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_PROCESS_START_UNAVAILABLE"
    assert captured.value.failure.stage is FailureStage.PROCESS
    assert captured.value.failure.possible_running_or_cost is False


@pytest.mark.parametrize("attack", ["symlink", "mode", "manifest"])
def test_release_symlink_mode_and_manifest_attacks_block_before_process(
    tmp_path: Path,
    attack: str,
) -> None:
    runner = _Runner()
    launcher = _launcher(tmp_path, runner)
    layout = Path(launcher._layout.directory)
    if attack == "symlink":
        executable = layout / "dbtobsb-native-bridge"
        target = layout / "target"
        executable.rename(target)
        executable.symlink_to(target)
    elif attack == "mode":
        (layout / "dbtobsb-native-bridge").chmod(0o722)
    else:
        manifest = layout / "manifest.json"
        manifest.write_bytes(manifest.read_bytes().replace(b'"arm64"', b'"amd64"'))

    with pytest.raises(DatabricksPlatformAdapterError):
        launcher._invoke(
            stage=FailureStage.ACTOR_IDENTITY,
            operation="actor_identity_check",
            profile=_PROFILE,
            canonical_host=_HOST,
            payload={"expected_actor_sha256": _ACTOR_SHA256, "warehouse_id": _WAREHOUSE_ID},
        )
    assert runner.calls == []


def test_production_source_tree_has_explicit_release_packaging_blocker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "dbtobsb_installer.native_bridge._GENERATED_MANIFEST_SHA256",
        None,
    )
    launcher = _NativeBridgeLauncher()
    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        launcher._invoke(
            stage=FailureStage.ACTOR_IDENTITY,
            operation="actor_identity_check",
            profile=_PROFILE,
            canonical_host=_HOST,
            payload={"expected_actor_sha256": _ACTOR_SHA256, "warehouse_id": _WAREHOUSE_ID},
        )
    assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_RELEASE_NOT_PACKAGED"


def test_positive_environment_has_no_path_or_credential_steering(tmp_path: Path) -> None:
    runner = _Runner()
    launcher = _launcher(
        tmp_path,
        runner,
        environment={
            "HOME": "/safe/operator",
            "LANG": "en_US.UTF-8",
            "PATH": f"/hostile/{_CANARY}",
            "UNRELATED_SECRET": _CANARY,
        },
    )
    launcher._invoke(
        stage=FailureStage.ACTOR_IDENTITY,
        operation="actor_identity_check",
        profile=_PROFILE,
        canonical_host=_HOST,
        payload={"expected_actor_sha256": _ACTOR_SHA256, "warehouse_id": _WAREHOUSE_ID},
    )
    assert runner.calls[0][2] == {
        "DATABRICKS_AUTH_STORAGE": "secure",
        "HOME": "/safe/operator",
        "LANG": "en_US.UTF-8",
    }


@pytest.mark.parametrize(
    "stage,runner_result,environment,expected_code,expected_stage,possible_running_or_cost",
    [
        (
            FailureStage.QUERY_HISTORY,
            RuntimeError(_CANARY),
            {"HOME": "/safe/operator"},
            "DBTOBSB_INSTALLER_NATIVE_PROCESS_UNAVAILABLE",
            FailureStage.QUERY_HISTORY,
            True,
        ),
        (
            FailureStage.CANCELLATION,
            NativeProcessResult(0, b"not-json\n"),
            {"HOME": "/safe/operator"},
            "DBTOBSB_INSTALLER_NATIVE_RESPONSE_INVALID",
            FailureStage.CANCELLATION,
            True,
        ),
        (
            FailureStage.CANCELLATION,
            NativeProcessResult(
                1,
                _native_response(code="DBTOBSB_NATIVE_CANCEL_INDETERMINATE", ok=False),
            ),
            {"HOME": "/safe/operator"},
            "DBTOBSB_INSTALLER_CANCEL_INDETERMINATE",
            FailureStage.CANCELLATION,
            True,
        ),
        (
            FailureStage.CANCELLATION,
            _actor_matched(),
            {"DATABRICKS_TOKEN": _CANARY, "HOME": "/safe/operator"},
            "DBTOBSB_INSTALLER_INHERITED_CREDENTIAL_REJECTED",
            FailureStage.AUTH_CONFIGURATION,
            False,
        ),
    ],
)
def test_late_boundary_failures_preserve_requested_stage_and_possible_cost(
    tmp_path: Path,
    stage: FailureStage,
    runner_result: NativeProcessResult | Exception,
    environment: Mapping[str, str],
    expected_code: str,
    expected_stage: FailureStage,
    possible_running_or_cost: bool,
) -> None:
    runner = _Runner([runner_result])
    launcher = _launcher(tmp_path, runner, environment=environment)

    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        launcher._invoke(
            stage=stage,
            operation=(
                "query_history_list"
                if stage is FailureStage.QUERY_HISTORY
                else "statement_execution_cancel"
            ),
            profile=_PROFILE,
            canonical_host=_HOST,
            payload={},
        )

    assert captured.value.code == expected_code
    assert captured.value.failure.stage is expected_stage
    assert captured.value.failure.possible_running_or_cost is possible_running_or_cost
    assert _CANARY not in repr(captured.value)


def test_subprocess_runner_caps_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = tmp_path / "oversized-helper"
    executable.write_text("#!/bin/sh\nwhile :; do printf 'xxxxxxxxxxxxxxxx'; done\n")
    executable.chmod(0o700)
    runner = SubprocessNativeRunner()
    _execute_installed_path_for_process_behavior(monkeypatch)
    with _VerifiedNativeExecutable._for_test(executable) as verified:
        result = runner.run(
            verified,
            stdin=b"",
            environment={"HOME": "/tmp"},
            timeout_seconds=5.0,
            max_output_bytes=1_024,
        )
    assert result.output_was_truncated is True
    assert len(result.stdout) == 1_025


def test_subprocess_runner_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    original_popen = subprocess.Popen

    class _TimeoutProcess:
        def __init__(self) -> None:
            self.pid = 999_991
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO()
            self.killed = False

        def wait(self, timeout: float | None = None) -> int:
            if self.killed:
                return -9
            raise subprocess.TimeoutExpired("sealed-helper", timeout or 0.0)

        def kill(self) -> None:
            self.killed = True

    signals: list[int] = []
    monkeypatch.setattr(os, "killpg", lambda pid, number: signals.append(number))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: _TimeoutProcess())
    try:
        with (
            _verified_test_executable(tmp_path) as executable,
            pytest.raises(DatabricksPlatformAdapterError) as captured,
        ):
            SubprocessNativeRunner().run(
                executable,
                stdin=b"{}",
                environment={"HOME": "/tmp"},
                timeout_seconds=0.01,
                max_output_bytes=100,
            )
    finally:
        monkeypatch.setattr(subprocess, "Popen", original_popen)
    assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_PROCESS_TIMEOUT"
    assert signals == [signal.SIGTERM, signal.SIGKILL]


def test_subprocess_runner_interruption_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class _InterruptedProcess:
        def __init__(self) -> None:
            self.pid = 999_992
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO()
            self.killed = False

        def wait(self, timeout: float | None = None) -> int:
            if self.killed:
                return -9
            raise KeyboardInterrupt(_CANARY)

        def kill(self) -> None:
            self.killed = True

    signals: list[int] = []
    monkeypatch.setattr(os, "killpg", lambda pid, number: signals.append(number))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: _InterruptedProcess())
    with (
        _verified_test_executable(tmp_path) as executable,
        pytest.raises(DatabricksPlatformAdapterError) as captured,
    ):
        SubprocessNativeRunner().run(
            executable,
            stdin=b"{}",
            environment={"HOME": "/tmp"},
            timeout_seconds=1.0,
            max_output_bytes=100,
        )
    assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_PROCESS_INTERRUPTED"
    assert _CANARY not in repr(captured.value)
    assert signals == [signal.SIGTERM, signal.SIGKILL]


@pytest.mark.parametrize("mode", ["broken_pipe", "read_failure"])
def test_io_failures_terminate_and_reap_the_process_group(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode: str,
) -> None:
    class _BrokenInput(io.BytesIO):
        def write(self, value: Buffer, /) -> int:
            raise BrokenPipeError

    class _BrokenOutput(io.BytesIO):
        def read(self, size: int | None = -1, /) -> bytes:
            raise OSError

    class _FailedProcess:
        def __init__(self) -> None:
            self.pid = 999_993
            self.stdin = _BrokenInput() if mode == "broken_pipe" else io.BytesIO()
            self.stdout = _BrokenOutput() if mode == "read_failure" else io.BytesIO()
            self.killed = False

        def wait(self, timeout: float | None = None) -> int:
            if self.killed:
                return -9
            raise subprocess.TimeoutExpired("sealed-helper", timeout or 0.0)

        def kill(self) -> None:
            self.killed = True

    process = _FailedProcess()
    signals: list[int] = []

    def kill_group(pid: int, number: int) -> None:
        signals.append(number)
        if number == signal.SIGKILL:
            process.killed = True

    monkeypatch.setattr(os, "killpg", kill_group)
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: process)

    with (
        _verified_test_executable(tmp_path) as executable,
        pytest.raises(DatabricksPlatformAdapterError) as captured,
    ):
        SubprocessNativeRunner().run(
            executable,
            stdin=b"{}",
            environment={"HOME": "/tmp"},
            timeout_seconds=1.0,
            max_output_bytes=100,
        )

    assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_PROCESS_UNAVAILABLE"
    assert signals == [signal.SIGTERM, signal.SIGKILL]


@pytest.mark.parametrize("mode", ["timeout", "oversized", "abnormal_exit"])
def test_abnormal_process_paths_remove_descendants_from_the_new_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    child_pid_file = tmp_path / "child.pid"
    executable = tmp_path / f"group-helper-{mode}"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import os, signal, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "child = os.fork()\n"
        "if child == 0:\n"
        f"    open({str(child_pid_file)!r}, 'w').write(str(os.getpid()))\n"
        "    while True: time.sleep(1)\n"
        f"while not os.path.exists({str(child_pid_file)!r}): time.sleep(0.001)\n"
        + (
            "while True: time.sleep(1)\n"
            if mode == "timeout"
            else (
                "while True: os.write(1, b'x' * 4096)\n" if mode == "oversized" else "os._exit(1)\n"
            )
        )
    )
    executable.chmod(0o700)
    runner = SubprocessNativeRunner()
    _execute_installed_path_for_process_behavior(monkeypatch)
    with _VerifiedNativeExecutable._for_test(executable) as verified:
        if mode == "timeout":
            with pytest.raises(DatabricksPlatformAdapterError) as captured:
                runner.run(
                    verified,
                    stdin=b"",
                    environment={"HOME": "/tmp"},
                    timeout_seconds=1.0,
                    max_output_bytes=1_024,
                )
            assert captured.value.code == "DBTOBSB_INSTALLER_NATIVE_PROCESS_TIMEOUT"
        else:
            result = runner.run(
                verified,
                stdin=b"",
                environment={"HOME": "/tmp"},
                timeout_seconds=5.0,
                max_output_bytes=1_024,
            )
            if mode == "oversized":
                assert result.output_was_truncated is True
            else:
                assert result.return_code == 1

    deadline = time.monotonic() + 2.0
    while not child_pid_file.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert child_pid_file.exists()
    child_pid = int(child_pid_file.read_text().strip())
    while time.monotonic() < deadline:
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.01)
    else:
        pytest.fail("descendant remained after bounded process-group cleanup")


def test_sensitive_values_never_appear_in_repr_errors_or_failure_json(tmp_path: Path) -> None:
    runner = _Runner(
        [NativeProcessResult(1, _native_response(code="DBTOBSB_NATIVE_AUTH_UNAVAILABLE", ok=False))]
    )
    with pytest.raises(DatabricksPlatformAdapterError) as captured:
        _launcher(tmp_path, runner)._invoke(
            stage=FailureStage.ACTOR_IDENTITY,
            operation="actor_identity_check",
            profile=_PROFILE,
            canonical_host=_HOST,
            payload={
                "expected_actor_sha256": _ACTOR_SHA256,
                "warehouse_id": _WAREHOUSE_ID,
            },
        )
    rendered = repr(captured.value) + json.dumps(captured.value.failure.as_dict())
    for canary in (_PROFILE, _HOST, _WAREHOUSE_ID, _ACTOR_SHA256, _QUERY_ID, _CANARY):
        assert canary not in rendered


def test_production_python_has_no_legacy_secret_or_arbitrary_statement_route() -> None:
    root = Path(__file__).parents[1] / "src" / "dbtobsb_installer"
    source = (root / "platform_adapters.py").read_text() + (root / "native_bridge.py").read_text()
    forbidden = (
        "auth token",
        "auth describe",
        "Bearer ",
        "access_token",
        "HttpsSingleSendClient",
        '"statement":',
        "._transport_text()",
    )
    assert all(value not in source for value in forbidden)
    assert not (root / "_secure_oauth_child.py").exists()
    assert not hasattr(DatabricksQueryHistoryClient, "submit")
    assert not hasattr(DatabricksQueryCancellationClient, "submit")
    assert hasattr(NativeStatementSubmitter, "submit")
