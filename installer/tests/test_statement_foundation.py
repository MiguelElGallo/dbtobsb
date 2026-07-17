"""Safety and recovery tests for the sealed statement-submission contracts."""

from __future__ import annotations

import uuid
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dbtobsb_installer.auth import (
    InstallerAuthError,
    InstallerConnectionInputs,
    ValidatedInstallerConnection,
    reject_inherited_credential_environment,
    validate_connection,
)
from dbtobsb_installer.operations import (
    CleanupAction,
    CleanupPrivilege,
    ClosedStatement,
    Ed25519MarkerSigner,
    InstallerOperationError,
    MarkerTextKind,
    MarkerVerifier,
    PreparationLocator,
    SecurableType,
    SignedPreparationMarker,
    StatementKind,
    _foundation_test_mutation,
    bind_mutation_marker,
    parse_marker_token,
    parse_query_marker,
    render_preparation_statement,
    sign_preparation_marker,
)
from dbtobsb_installer.recovery import (
    CancellationHandle,
    CancellationOutcome,
    QueryCancellationClient,
    QueryHistoryPage,
    QueryHistoryRecord,
    RecoveryOutcome,
    locate_operation,
    request_cancellation,
)
from dbtobsb_installer.statement_contracts import (
    StatementDisposition,
    StatementReceipt,
)
from dbtobsb_installer.workflow import (
    DispatchClaimOutcome,
    MutationDispatcher,
    PreparationGate,
    WorkflowCode,
    WorkflowDisposition,
)

_OPERATION_UUID = uuid.UUID("12345678-1234-4abc-8abc-1234567890ab")
_QUERY_REFERENCE = "87654321-4321-4abc-8abc-ba0987654321"
_WAREHOUSE_ID = "0123456789abcdef"
_HOST = "https://adb-1234567890123456.10.azuredatabricks.net"
_CANARY = "secret-customer-canary"


class _FakeSubmitter:
    """Deterministic test-only implementation; production has no Python fallback."""

    def __init__(self, outcome: StatementReceipt | Exception) -> None:
        self.outcome = outcome
        self.calls: list[tuple[ValidatedInstallerConnection, ClosedStatement]] = []

    def submit(
        self,
        connection: ValidatedInstallerConnection,
        statement: ClosedStatement,
    ) -> StatementReceipt:
        self.calls.append((connection, statement))
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class _HistoryClient:
    def __init__(self, pages: dict[str | None, QueryHistoryPage]) -> None:
        self.pages = pages
        self.tokens: list[str | None] = []

    def list_page(self, request) -> QueryHistoryPage:
        self.tokens.append(request.page_token)
        return self.pages[request.page_token]


class _CancellationClient:
    def __init__(self, outcome: CancellationOutcome) -> None:
        self.outcome = outcome
        self.calls = 0

    def request_cancel(self, target: CancellationHandle) -> CancellationOutcome:
        assert isinstance(target, CancellationHandle)
        self.calls += 1
        return self.outcome


class _DispatchJournal:
    def __init__(self) -> None:
        self.claims: set[tuple[uuid.UUID, str]] = set()

    def claim_once(
        self,
        operation_uuid: uuid.UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome:
        claim = (operation_uuid, marker_payload_sha256)
        if claim in self.claims:
            return DispatchClaimOutcome.ALREADY_CLAIMED
        self.claims.add(claim)
        return DispatchClaimOutcome.CLAIMED


class _IndeterminateDispatchJournal:
    def claim_once(
        self,
        operation_uuid: uuid.UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome:
        del operation_uuid, marker_payload_sha256
        return DispatchClaimOutcome.INDETERMINATE


class _MarkerJournal:
    def __init__(self) -> None:
        self.claims: set[tuple[uuid.UUID, str]] = set()

    def claim_marker_once(
        self,
        operation_uuid: uuid.UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome:
        claim = (operation_uuid, marker_payload_sha256)
        if claim in self.claims:
            return DispatchClaimOutcome.ALREADY_CLAIMED
        self.claims.add(claim)
        return DispatchClaimOutcome.CLAIMED


def _connection() -> ValidatedInstallerConnection:
    return validate_connection(
        InstallerConnectionInputs(
            profile="dbtobsb-operator",
            canonical_host=_HOST,
            installer_warehouse_id=_WAREHOUSE_ID,
        )
    )


def _closed_operation():
    return _foundation_test_mutation(_OPERATION_UUID)


def _marker() -> tuple[SignedPreparationMarker, Ed25519MarkerSigner]:
    operation = _closed_operation()
    signer = Ed25519MarkerSigner(Ed25519PrivateKey.generate())
    locator = PreparationLocator(
        installation_id="a" * 64,
        generation=1,
        sequence=2,
        operation_uuid=_OPERATION_UUID,
        envelope_sha256="b" * 64,
        statement_sha256=operation.statement_sha256,
        operator_group="dbtobsb migration operators",
        warehouse_id=_WAREHOUSE_ID,
        securable_type=SecurableType.TABLE,
        securable_name="observability.dbtobsb.dbtobsb_migration_ledger",
        privilege=CleanupPrivilege.MODIFY,
        action=CleanupAction.REMOVE_EXACT_PRODUCT_GRANT,
    )
    return sign_preparation_marker(locator, signer), signer


def _submitter(
    disposition: StatementDisposition = StatementDisposition.TERMINAL_SUCCESS,
) -> _FakeSubmitter:
    return _FakeSubmitter(StatementReceipt(disposition))


def _history_record(
    marker: SignedPreparationMarker,
    *,
    verifier: MarkerVerifier,
    kind: MarkerTextKind,
    status: str,
) -> QueryHistoryRecord:
    if kind is MarkerTextKind.PREPARATION:
        text = render_preparation_statement(marker, verifier)._transport_text()
    else:
        text = bind_mutation_marker(_closed_operation(), marker, verifier)._transport_text()
    return QueryHistoryRecord(
        query_reference=_QUERY_REFERENCE,
        warehouse_id=_WAREHOUSE_ID,
        query_text=text,
        status=status,
    )


def test_connection_requires_explicit_canonical_azure_host_and_warehouse() -> None:
    connection = _connection()

    assert connection.profile == "dbtobsb-operator"
    assert connection.canonical_host == _HOST
    with pytest.raises(InstallerAuthError, match="DBTOBSB_INSTALLER_HOST_INVALID"):
        validate_connection(InstallerConnectionInputs("profile", f"{_HOST}/", _WAREHOUSE_ID))
    with pytest.raises(InstallerAuthError, match="DBTOBSB_INSTALLER_WAREHOUSE_INVALID"):
        validate_connection(InstallerConnectionInputs("profile", _HOST, "ABCDEF0123456789"))
    with pytest.raises(InstallerAuthError, match="CONNECTION_CONSTRUCTION_DENIED"):
        ValidatedInstallerConnection(
            profile="profile",
            canonical_host=_HOST,
            installer_warehouse_id=_WAREHOUSE_ID,
            _construction_token=object(),
        )
    assert repr(connection) == "ValidatedInstallerConnection(<redacted>)"
    assert repr(InstallerConnectionInputs("profile", _HOST, _WAREHOUSE_ID)) == (
        "InstallerConnectionInputs(<redacted>)"
    )


def test_inherited_credential_environment_is_rejected_before_native_execution() -> None:
    with pytest.raises(InstallerAuthError, match="INHERITED_CREDENTIAL_REJECTED"):
        reject_inherited_credential_environment({"DATABRICKS_TOKEN": _CANARY})
    with pytest.raises(InstallerAuthError, match="INHERITED_CREDENTIAL_REJECTED"):
        reject_inherited_credential_environment({"AZURE_CLIENT_SECRET": _CANARY})

    reject_inherited_credential_environment({"PATH": "/usr/bin", "DATABRICKS_TOKEN": ""})


def test_statement_contract_is_sanitized_and_has_no_python_implementation() -> None:
    receipt = StatementReceipt(StatementDisposition.CANCELLATION_NONTERMINAL)

    assert receipt.disposition is StatementDisposition.CANCELLATION_NONTERMINAL
    assert _CANARY not in repr(receipt)
    with pytest.raises(TypeError, match="STATEMENT_RECEIPT_INVALID"):
        StatementReceipt(cast(StatementDisposition, object()))


@pytest.mark.parametrize("failure", [TimeoutError(), ConnectionError()])
def test_response_loss_is_indeterminate_and_never_retried(failure: Exception) -> None:
    marker, signer = _marker()
    submitter = _FakeSubmitter(failure)
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.PREPARATION,
                        status="FINISHED",
                    ),
                )
            )
        }
    )
    gate = PreparationGate(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        submission_journal=_MarkerJournal(),
        marker=marker,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )

    first = gate.submit_once()
    second = gate.submit_once()
    recovered = gate.recover()

    assert first.disposition is WorkflowDisposition.INDETERMINATE
    assert second.code is WorkflowCode.PREPARATION_RETRY_BLOCKED
    assert recovered.completion is not None
    assert len(submitter.calls) == 1


def test_durable_marker_claim_forces_recovery_after_process_restart() -> None:
    marker, signer = _marker()
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.PREPARATION,
                        status="FINISHED",
                    ),
                )
            )
        }
    )
    submitter = _FakeSubmitter(ConnectionError())
    journal = _MarkerJournal()
    first_process = PreparationGate(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        submission_journal=journal,
        marker=marker,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    first = first_process.submit_once()
    submissions_after_loss = len(submitter.calls)
    restarted_process = PreparationGate(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        submission_journal=journal,
        marker=marker,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )

    second = restarted_process.submit_once()
    recovered = restarted_process.recover()

    assert first.code is WorkflowCode.PREPARATION_INDETERMINATE
    assert second.code is WorkflowCode.PREPARATION_RETRY_BLOCKED
    assert recovered.completion is not None
    assert len(submitter.calls) == submissions_after_loss


def test_mutation_requires_completed_marker_and_has_exactly_one_sealed_submission() -> None:
    marker, signer = _marker()
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.PREPARATION,
                        status="FINISHED",
                    ),
                )
            )
        }
    )
    submitter = _submitter()
    gate = PreparationGate(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        submission_journal=_MarkerJournal(),
        marker=marker,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    dispatcher = MutationDispatcher(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        dispatch_journal=_DispatchJournal(),
        start_time_ms=1_000,
        end_time_ms=2_000,
    )

    denied = dispatcher.dispatch_once(_closed_operation(), None)
    assert denied.code is WorkflowCode.MUTATION_MARKER_REQUIRED
    assert len(submitter.calls) == 0
    gate.submit_once()
    completion = gate.recover().completion
    assert completion is not None
    before_mutation = len(submitter.calls)
    submitted = dispatcher.dispatch_once(_closed_operation(), completion)
    blocked_retry = dispatcher.dispatch_once(_closed_operation(), completion)

    assert submitted.code is WorkflowCode.MUTATION_SUBMITTED_PENDING_POSTSTATE
    assert blocked_retry.code is WorkflowCode.MUTATION_RETRY_BLOCKED
    assert len(submitter.calls) == before_mutation + 1
    assert "DBTOBSB_MUTATION_MARKER_V1" in submitter.calls[-1][1]._transport_text()


def test_durable_dispatch_claim_blocks_resend_after_process_restart() -> None:
    marker, signer = _marker()
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.PREPARATION,
                        status="FINISHED",
                    ),
                )
            )
        }
    )
    submitter = _FakeSubmitter(ConnectionError())
    gate = PreparationGate(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        submission_journal=_MarkerJournal(),
        marker=marker,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    gate.submit_once()
    completion = gate.recover().completion
    assert completion is not None
    journal = _DispatchJournal()

    first_process = MutationDispatcher(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        dispatch_journal=journal,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    first = first_process.dispatch_once(_closed_operation(), completion)
    submissions_after_loss = len(submitter.calls)
    restarted_process = MutationDispatcher(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        dispatch_journal=journal,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    second = restarted_process.dispatch_once(_closed_operation(), completion)

    assert first.code is WorkflowCode.MUTATION_INDETERMINATE
    assert second.code is WorkflowCode.MUTATION_RETRY_BLOCKED
    assert len(submitter.calls) == submissions_after_loss


def test_indeterminate_dispatch_claim_blocks_send_and_later_retry() -> None:
    marker, signer = _marker()
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.PREPARATION,
                        status="FINISHED",
                    ),
                )
            )
        }
    )
    submitter = _submitter()
    gate = PreparationGate(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        submission_journal=_MarkerJournal(),
        marker=marker,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    gate.submit_once()
    completion = gate.recover().completion
    assert completion is not None
    dispatcher = MutationDispatcher(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        dispatch_journal=_IndeterminateDispatchJournal(),
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    submissions_before_dispatch = len(submitter.calls)

    first = dispatcher.dispatch_once(_closed_operation(), completion)
    second = dispatcher.dispatch_once(_closed_operation(), completion)

    assert first.code is WorkflowCode.MUTATION_CLAIM_INDETERMINATE
    assert second.code is WorkflowCode.MUTATION_RETRY_BLOCKED
    assert len(submitter.calls) == submissions_before_dispatch


def test_malicious_sql_and_locator_input_cannot_enter_closed_renderer() -> None:
    marker, signer = _marker()
    with pytest.raises(InstallerOperationError, match="STATEMENT_CONSTRUCTION_DENIED"):
        ClosedStatement(
            kind=StatementKind.MUTATION,
            text="CALLER SUPPLIED STATEMENT",
            semantic_sha256="a" * 64,
            _construction_token=object(),
        )
    with pytest.raises(InstallerOperationError, match="OPERATOR_GROUP_INVALID"):
        replace(marker.locator, operator_group="operators'; untrusted --")
    with pytest.raises(InstallerOperationError, match="OPERATOR_GROUP_INVALID"):
        replace(marker.locator, operator_group="operators--comment")
    with pytest.raises(InstallerOperationError, match="OPERATOR_GROUP_INVALID"):
        replace(marker.locator, operator_group="operators/*comment*/")
    with pytest.raises(InstallerOperationError, match="SECURABLE_INVALID"):
        replace(marker.locator, securable_name="catalog.schema.table untrusted")

    observed = parse_query_marker(
        render_preparation_statement(marker, signer.verifier())._transport_text(),
        MarkerTextKind.PREPARATION,
        signer.verifier(),
    )
    assert observed == marker
    assert repr(marker.locator) == "PreparationLocator(<redacted>)"
    assert marker.compact_token.replace(".", "").isalnum()
    assert all(token not in marker.compact_token for token in ("'", '"', "--", "/*", "*/"))


def test_marker_is_opaque_and_exact_signature_is_rechecked_before_render() -> None:
    marker, signer = _marker()
    with pytest.raises(InstallerOperationError, match="MARKER_CONSTRUCTION_DENIED"):
        SignedPreparationMarker(
            locator=marker.locator,
            compact_token=marker.compact_token,
            payload_sha256=marker.payload_sha256,
            _construction_token=object(),
        )
    object.__setattr__(marker, "compact_token", f"{marker.compact_token}'/*")

    with pytest.raises(InstallerOperationError, match=r"MARKER_(?:ENCODING|SIGNATURE)_INVALID"):
        render_preparation_statement(marker, signer.verifier())


def test_noncanonical_base32_pad_bits_cannot_alias_a_signed_marker() -> None:
    marker, signer = _marker()
    key_id, payload_segment, signature_segment = marker.compact_token.split(".")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    assert len(signature_segment) % 8 == 7
    alternate_last = alphabet[alphabet.index(signature_segment[-1]) ^ 1]
    aliased = f"{key_id}.{payload_segment}.{signature_segment[:-1]}{alternate_last}"

    with pytest.raises(InstallerOperationError, match="MARKER_ENCODING_INVALID"):
        parse_marker_token(aliased, signer.verifier())


def test_query_history_consumes_empty_pages_and_detects_token_cycle() -> None:
    marker, signer = _marker()
    matching = _history_record(
        marker,
        verifier=signer.verifier(),
        kind=MarkerTextKind.PREPARATION,
        status="FINISHED",
    )
    paged = _HistoryClient(
        {
            None: QueryHistoryPage((), "page-2"),
            "page-2": QueryHistoryPage((matching,)),
        }
    )

    recovered = locate_operation(
        client=paged,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.PREPARATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )

    assert recovered.outcome is RecoveryOutcome.UNIQUE_TERMINAL_SUCCESS
    assert paged.tokens == [None, "page-2"]

    cycle = _HistoryClient(
        {
            None: QueryHistoryPage((), "again"),
            "again": QueryHistoryPage((), "again"),
        }
    )
    blocked = locate_operation(
        client=cycle,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.PREPARATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    assert blocked.outcome is RecoveryOutcome.PAGINATION_CYCLE_INDETERMINATE


def test_duplicate_marker_history_never_completes_mutation_gate() -> None:
    marker, signer = _marker()
    matching = _history_record(
        marker,
        verifier=signer.verifier(),
        kind=MarkerTextKind.PREPARATION,
        status="FINISHED",
    )
    history = _HistoryClient({None: QueryHistoryPage((matching, matching))})
    submitter = _submitter()
    gate = PreparationGate(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        submission_journal=_MarkerJournal(),
        marker=marker,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    gate.submit_once()
    readback = gate.recover()
    dispatcher = MutationDispatcher(
        connection=_connection(),
        submitter=submitter,
        history_client=history,
        verifier=signer.verifier(),
        dispatch_journal=_DispatchJournal(),
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    submissions_before_dispatch = len(submitter.calls)

    receipt = dispatcher.dispatch_once(_closed_operation(), readback.completion)

    assert readback.receipt.disposition is WorkflowDisposition.INDETERMINATE
    assert readback.completion is None
    assert receipt.code is WorkflowCode.MUTATION_MARKER_REQUIRED
    assert len(submitter.calls) == submissions_before_dispatch


def test_unknown_history_status_is_indeterminate_and_cancellation_is_nonterminal() -> None:
    marker, signer = _marker()
    unknown = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.MUTATION,
                        status="NEW_STATE",
                    ),
                )
            )
        }
    )
    result = locate_operation(
        client=unknown,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.MUTATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    assert result.outcome is RecoveryOutcome.UNKNOWN_STATUS_INDETERMINATE

    canceled = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.MUTATION,
                        status="CANCELED",
                    ),
                )
            )
        }
    )
    result = locate_operation(
        client=canceled,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.MUTATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    cancellation_client = _CancellationClient(CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL)
    receipt = request_cancellation(cancellation_client, result.cancellation_handle)

    assert result.outcome is RecoveryOutcome.CANCELLATION_NONTERMINAL
    assert result.cancellation_handle is None
    assert receipt.outcome is CancellationOutcome.REQUEST_REJECTED_NONTERMINAL
    assert cancellation_client.calls == 0


@pytest.mark.parametrize("status", ["QUEUED", "STARTED", "COMPILING", "COMPILED", "RUNNING"])
def test_ga_in_progress_query_history_states_are_closed_nonterminal(status: str) -> None:
    marker, signer = _marker()
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.MUTATION,
                        status=status,
                    ),
                )
            )
        }
    )

    result = locate_operation(
        client=history,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.MUTATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )

    assert result.outcome is RecoveryOutcome.UNIQUE_NONTERMINAL
    assert result.cancellation_handle is not None


def test_cancellation_handle_cannot_be_built_from_caller_query_id() -> None:
    with pytest.raises(InstallerOperationError, match="CANCELLATION_HANDLE_DENIED"):
        CancellationHandle(
            query_reference="caller-query-id",
            marker_payload_sha256="a" * 64,
            source_binding=object(),
            _construction_token=object(),
        )
    cancellation_client = _CancellationClient(CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL)

    receipt = request_cancellation(cancellation_client, None)

    assert receipt.outcome is CancellationOutcome.REQUEST_REJECTED_NONTERMINAL
    assert cancellation_client.calls == 0


def test_malformed_query_history_reference_is_indeterminate_and_never_cancelled() -> None:
    marker, signer = _marker()
    malformed = replace(
        _history_record(
            marker,
            verifier=signer.verifier(),
            kind=MarkerTextKind.MUTATION,
            status="RUNNING",
        ),
        query_reference="../other\r\n",
    )
    history = _HistoryClient({None: QueryHistoryPage((malformed,))})

    result = locate_operation(
        client=history,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.MUTATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    cancellation_client = _CancellationClient(CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL)
    receipt = request_cancellation(cancellation_client, result.cancellation_handle)

    assert result.outcome is RecoveryOutcome.MALFORMED_REFERENCE_INDETERMINATE
    assert result.cancellation_handle is None
    assert receipt.outcome is CancellationOutcome.REQUEST_REJECTED_NONTERMINAL
    assert cancellation_client.calls == 0


def test_cancellation_client_cannot_return_a_terminal_or_untyped_success_signal() -> None:
    class _UntypedCancellationClient:
        def request_cancel(self, target: CancellationHandle) -> bool:
            assert isinstance(target, CancellationHandle)
            return True

    marker, signer = _marker()
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.MUTATION,
                        status="RUNNING",
                    ),
                )
            )
        }
    )
    result = locate_operation(
        client=history,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.MUTATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )

    receipt = request_cancellation(
        cast(QueryCancellationClient, _UntypedCancellationClient()),
        result.cancellation_handle,
    )

    assert receipt.outcome is CancellationOutcome.REQUEST_INDETERMINATE


def test_full_packaged_source_has_no_legacy_credential_or_direct_statement_sender() -> None:
    package = Path(__file__).parents[1] / "src" / "dbtobsb_installer"
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(package.rglob("*.py")))
    forbidden = (
        "AccessToken",
        "OAuthU2MCredentialProvider",
        "resolve_credential",
        '"Authorization"',
        "Bearer ",
        "http.client",
        "HTTPSConnection",
        "/api/2.0/sql/statements",
        "StatementExecutionTransport",
        "HttpsSingleSendClient",
        "SingleSendHttpClient",
    )

    assert all(value not in source for value in forbidden)
    assert not (package / "transport.py").exists()


def test_safe_receipts_and_representations_never_leak_secrets_sql_ids_or_customer_values() -> None:
    marker, signer = _marker()
    submitter = _submitter(StatementDisposition.CANCELLATION_NONTERMINAL)
    receipt = submitter.submit(
        _connection(), render_preparation_statement(marker, signer.verifier())
    )
    history = _HistoryClient(
        {
            None: QueryHistoryPage(
                (
                    _history_record(
                        marker,
                        verifier=signer.verifier(),
                        kind=MarkerTextKind.MUTATION,
                        status="RUNNING",
                    ),
                )
            )
        }
    )
    recovery = locate_operation(
        client=history,
        verifier=signer.verifier(),
        marker=marker,
        kind=MarkerTextKind.MUTATION,
        warehouse_id=_WAREHOUSE_ID,
        start_time_ms=1_000,
        end_time_ms=2_000,
    )
    values = "\n".join(
        (
            repr(submitter.calls[0][1]),
            repr(receipt),
            repr(recovery),
            repr(marker),
            repr(marker.locator),
            repr(_connection()),
            repr(recovery.cancellation_handle),
        )
    )

    for forbidden in (
        _CANARY,
        "SELECT",
        _QUERY_REFERENCE,
        _WAREHOUSE_ID,
        "dbtobsb migration operators",
        "observability.dbtobsb",
        _HOST,
        "dbtobsb-operator",
    ):
        assert forbidden not in values
    assert receipt.disposition is StatementDisposition.CANCELLATION_NONTERMINAL
