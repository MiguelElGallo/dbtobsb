"""Typed production adapters backed only by the sealed native Databricks bridge."""

from __future__ import annotations

import hashlib
import json
import re
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, cast

from dbtobsb_installer.auth import (
    InstallerAuthError,
    InstallerConnectionInputs,
    ValidatedInstallerConnection,
    validate_connection,
)
from dbtobsb_installer.native_bridge import (
    AdapterFailure,
    DatabricksPlatformAdapterError,
    FailureStage,
    NativeResponse,
    _failure_for_code,
    _is_sha256,
    _NativeBridgeLauncher,
    _strict_json_object,
)
from dbtobsb_installer.operations import ClosedStatement, Ed25519MarkerVerifier
from dbtobsb_installer.recovery import (
    CancellationHandle,
    CancellationOutcome,
    QueryHistoryPage,
    QueryHistoryRecord,
    QueryHistoryRequest,
    QueryHistoryStatus,
    _consume_cancellation_handle,
)
from dbtobsb_installer.statement_contracts import (
    StatementDisposition,
    StatementReceipt,
)

_SIGNED_ACTOR_SCHEMA = "dbtobsb.signed-actor-binding.v1"
_ENROLLMENT_APPROVAL_SCHEMA = "dbtobsb.actor-fingerprint-enrollment-approval.v1"
_MAX_SIGNED_CONFIG_BYTES = 4_096
_MAX_HISTORY_WINDOW_MILLISECONDS = 20 * 60 * 1_000
_MAX_QUERY_TEXT_BYTES = 512 * 1024
_MAX_PAGE_TOKEN_BYTES = 4_096
_VERIFIED_ACTOR_TOKEN = object()
_ENROLLMENT_APPROVAL_TOKEN = object()
_FINGERPRINT_OBSERVATION_TOKEN = object()
_BOUND_SESSION_TOKEN = object()
_CANONICAL_QUERY_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _connection_digest(connection: ValidatedInstallerConnection) -> str:
    document = {
        "canonical_host": connection.canonical_host,
        "installer_warehouse_id": connection.installer_warehouse_id,
        "profile": connection.profile,
        "schema": "dbtobsb.installer-connection.v1",
    }
    canonical = json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _validate_connection(connection: ValidatedInstallerConnection) -> None:
    if not isinstance(connection, ValidatedInstallerConnection):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_CONNECTION_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    try:
        validated = validate_connection(
            InstallerConnectionInputs(
                profile=connection.profile,
                canonical_host=connection.canonical_host,
                installer_warehouse_id=connection.installer_warehouse_id,
            )
        )
    except InstallerAuthError as error:
        raise _failure_for_code(error.code, FailureStage.ACTOR_IDENTITY) from None
    if validated != connection:
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_CONNECTION_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )


@dataclass(frozen=True, slots=True, repr=False)
class VerifiedSignedActorConfiguration:
    """Approved pseudonymous actor binding produced only after signature verification."""

    connection_sha256: str = field(repr=False)
    approved_actor_sha256: str = field(repr=False)
    signed_config_sha256: str

    def __init__(
        self,
        *,
        connection_sha256: str,
        approved_actor_sha256: str,
        signed_config_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _VERIFIED_ACTOR_TOKEN:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_ACTOR_CONFIG_CONSTRUCTION_DENIED",
                FailureStage.ACTOR_IDENTITY,
            )
        if not all(
            _is_sha256(value)
            for value in (connection_sha256, approved_actor_sha256, signed_config_sha256)
        ):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_ACTOR_CONFIG_INVALID",
                FailureStage.ACTOR_IDENTITY,
            )
        object.__setattr__(self, "connection_sha256", connection_sha256)
        object.__setattr__(self, "approved_actor_sha256", approved_actor_sha256)
        object.__setattr__(self, "signed_config_sha256", signed_config_sha256)

    def __repr__(self) -> str:
        return "VerifiedSignedActorConfiguration(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class FingerprintEnrollmentApprovalProof:
    """Opaque proof that attended cost and browser-identity confirmation were signed."""

    connection_sha256: str = field(repr=False)
    approval_sha256: str

    def __init__(
        self,
        *,
        connection_sha256: str,
        approval_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _ENROLLMENT_APPROVAL_TOKEN or not all(
            _is_sha256(value) for value in (connection_sha256, approval_sha256)
        ):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_ENROLLMENT_APPROVAL_INVALID",
                FailureStage.ACTOR_IDENTITY,
            )
        object.__setattr__(self, "connection_sha256", connection_sha256)
        object.__setattr__(self, "approval_sha256", approval_sha256)

    def __repr__(self) -> str:
        return "FingerprintEnrollmentApprovalProof(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class ActorFingerprintObservation:
    """Enrollment observation that cannot be used as a bound session."""

    actor_fingerprint_sha256: str = field(repr=False)
    approval_sha256: str

    def __init__(
        self,
        *,
        actor_fingerprint_sha256: str,
        approval_sha256: str,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _FINGERPRINT_OBSERVATION_TOKEN or not all(
            _is_sha256(value) for value in (actor_fingerprint_sha256, approval_sha256)
        ):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_ACTOR_OBSERVATION_INVALID",
                FailureStage.ACTOR_IDENTITY,
            )
        object.__setattr__(self, "actor_fingerprint_sha256", actor_fingerprint_sha256)
        object.__setattr__(self, "approval_sha256", approval_sha256)

    def __repr__(self) -> str:
        return "ActorFingerprintObservation(<redacted>)"


def verify_fingerprint_enrollment_approval(
    *,
    connection: ValidatedInstallerConnection,
    document: bytes,
    signature: bytes,
    verifier: Ed25519MarkerVerifier,
) -> FingerprintEnrollmentApprovalProof:
    """Verify the signed prerequisite for the one read-only enrollment observation."""

    _validate_connection(connection)
    if (
        not isinstance(document, bytes)
        or not document
        or len(document) > _MAX_SIGNED_CONFIG_BYTES
        or not isinstance(signature, bytes)
        or len(signature) != 64
        or not isinstance(verifier, Ed25519MarkerVerifier)
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ENROLLMENT_APPROVAL_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    parsed = _strict_json_object(
        document,
        "DBTOBSB_INSTALLER_ENROLLMENT_APPROVAL_INVALID",
        FailureStage.ACTOR_IDENTITY,
    )
    if set(parsed) != {
        "browser_identity_confirmation_sha256",
        "connection_sha256",
        "cost_acknowledgement_sha256",
        "schema",
        "signer_key_id",
    }:
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ENROLLMENT_APPROVAL_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    canonical = (
        json.dumps(parsed, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
        + b"\n"
    )
    connection_sha256 = _connection_digest(connection)
    if (
        document != canonical
        or parsed["schema"] != _ENROLLMENT_APPROVAL_SCHEMA
        or parsed["signer_key_id"] != verifier.key_id
        or parsed["connection_sha256"] != connection_sha256
        or not _is_sha256(parsed["browser_identity_confirmation_sha256"])
        or not _is_sha256(parsed["cost_acknowledgement_sha256"])
        or not verifier.verify(document, signature)
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ENROLLMENT_APPROVAL_SIGNATURE_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    return FingerprintEnrollmentApprovalProof(
        connection_sha256=connection_sha256,
        approval_sha256=hashlib.sha256(document).hexdigest(),
        _construction_token=_ENROLLMENT_APPROVAL_TOKEN,
    )


def observe_actor_fingerprint(
    *,
    connection: ValidatedInstallerConnection,
    approval: FingerprintEnrollmentApprovalProof,
) -> ActorFingerprintObservation:
    """Production enrollment observation; the result grants no later access."""

    return _observe_actor_fingerprint(
        connection=connection,
        approval=approval,
        launcher=_NativeBridgeLauncher(),
    )


def _observe_actor_fingerprint(
    *,
    connection: ValidatedInstallerConnection,
    approval: FingerprintEnrollmentApprovalProof,
    launcher: _NativeBridgeLauncher,
) -> ActorFingerprintObservation:
    _validate_connection(connection)
    if (
        not isinstance(approval, FingerprintEnrollmentApprovalProof)
        or approval.connection_sha256 != _connection_digest(connection)
        or not isinstance(launcher, _NativeBridgeLauncher)
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ENROLLMENT_APPROVAL_CONNECTION_MISMATCH",
            FailureStage.ACTOR_IDENTITY,
        )
    response = launcher._invoke(
        stage=FailureStage.ACTOR_IDENTITY,
        operation="actor_fingerprint_observe",
        profile=connection.profile,
        canonical_host=connection.canonical_host,
        payload={"warehouse_id": connection.installer_warehouse_id},
    )
    expected_keys = {"actor_sha256"}
    if (
        response.code != "DBTOBSB_NATIVE_ACTOR_FINGERPRINT_OBSERVED"
        or not isinstance(response.result, dict)
        or set(response.result) != expected_keys
        or not _is_sha256(response.result["actor_sha256"])
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ACTOR_OBSERVATION_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    return ActorFingerprintObservation(
        actor_fingerprint_sha256=cast(str, response.result["actor_sha256"]),
        approval_sha256=approval.approval_sha256,
        _construction_token=_FINGERPRINT_OBSERVATION_TOKEN,
    )


def verify_signed_actor_configuration(
    *,
    connection: ValidatedInstallerConnection,
    document: bytes,
    signature: bytes,
    verifier: Ed25519MarkerVerifier,
) -> VerifiedSignedActorConfiguration:
    """Verify one exact signed actor/connection binding; raw identity is never accepted."""

    _validate_connection(connection)
    if (
        not isinstance(document, bytes)
        or not document
        or len(document) > _MAX_SIGNED_CONFIG_BYTES
        or not isinstance(signature, bytes)
        or len(signature) != 64
        or not isinstance(verifier, Ed25519MarkerVerifier)
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ACTOR_CONFIG_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    parsed = _strict_json_object(
        document,
        "DBTOBSB_INSTALLER_ACTOR_CONFIG_INVALID",
        FailureStage.ACTOR_IDENTITY,
    )
    if set(parsed) != {
        "approved_actor_sha256",
        "connection_sha256",
        "schema",
        "signer_key_id",
    }:
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ACTOR_CONFIG_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    canonical = (
        json.dumps(parsed, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")
        + b"\n"
    )
    expected_connection = _connection_digest(connection)
    if (
        document != canonical
        or parsed["schema"] != _SIGNED_ACTOR_SCHEMA
        or parsed["signer_key_id"] != verifier.key_id
        or parsed["connection_sha256"] != expected_connection
        or not _is_sha256(parsed["approved_actor_sha256"])
        or not verifier.verify(document, signature)
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ACTOR_CONFIG_SIGNATURE_INVALID",
            FailureStage.ACTOR_IDENTITY,
        )
    return VerifiedSignedActorConfiguration(
        connection_sha256=expected_connection,
        approved_actor_sha256=cast(str, parsed["approved_actor_sha256"]),
        signed_config_sha256=hashlib.sha256(document).hexdigest(),
        _construction_token=_VERIFIED_ACTOR_TOKEN,
    )


@dataclass(frozen=True, slots=True, repr=False)
class NativeBoundSession:
    """Opaque actor-bound session proof; it cannot be created from public constructor values."""

    _connection: ValidatedInstallerConnection = field(repr=False)
    _actor_configuration: VerifiedSignedActorConfiguration = field(repr=False)
    _launcher: _NativeBridgeLauncher = field(repr=False)
    _nonce: object = field(repr=False)
    _claimed_cancellation_references: set[str] = field(repr=False)
    _possible_running_or_cost: bool = field(repr=False)
    _lock: threading.Lock = field(repr=False)

    def __init__(
        self,
        *,
        connection: ValidatedInstallerConnection,
        actor_configuration: VerifiedSignedActorConfiguration,
        launcher: _NativeBridgeLauncher,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _BOUND_SESSION_TOKEN:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_BOUND_SESSION_CONSTRUCTION_DENIED",
                FailureStage.ACTOR_IDENTITY,
            )
        object.__setattr__(self, "_connection", connection)
        object.__setattr__(self, "_actor_configuration", actor_configuration)
        object.__setattr__(self, "_launcher", launcher)
        object.__setattr__(self, "_nonce", object())
        object.__setattr__(self, "_claimed_cancellation_references", set())
        object.__setattr__(self, "_possible_running_or_cost", False)
        object.__setattr__(self, "_lock", threading.Lock())

    def __repr__(self) -> str:
        return "NativeBoundSession(<redacted>)"

    def _assert_connection(self, connection: ValidatedInstallerConnection) -> None:
        if (
            not isinstance(connection, ValidatedInstallerConnection)
            or connection != self._connection
            or self._actor_configuration.connection_sha256 != _connection_digest(connection)
        ):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_BOUND_SESSION_MISMATCH",
                FailureStage.ACTOR_IDENTITY,
            )

    def _invoke(
        self, *, stage: FailureStage, operation: str, payload: dict[str, object]
    ) -> NativeResponse:
        with self._lock:
            if operation not in {
                "query_history_list",
                "statement_execution_cancel",
                "statement_execution_submit",
            }:
                raise _failure_for_code(
                    "DBTOBSB_INSTALLER_NATIVE_OPERATION_DENIED",
                    stage,
                )
            protected_payload = dict(payload)
            warehouse_id = protected_payload.setdefault(
                "warehouse_id", self._connection.installer_warehouse_id
            )
            if warehouse_id != self._connection.installer_warehouse_id:
                raise _failure_for_code(
                    "DBTOBSB_INSTALLER_NATIVE_WAREHOUSE_MISMATCH",
                    stage,
                )
            protected_payload["expected_actor_sha256"] = (
                self._actor_configuration.approved_actor_sha256
            )
            try:
                response = self._launcher._invoke(
                    stage=stage,
                    operation=operation,
                    profile=self._connection.profile,
                    canonical_host=self._connection.canonical_host,
                    payload=protected_payload,
                )
            except DatabricksPlatformAdapterError as error:
                if error.failure.possible_running_or_cost:
                    object.__setattr__(self, "_possible_running_or_cost", True)
                if self._possible_running_or_cost and not error.failure.possible_running_or_cost:
                    failure = error.failure
                    raise DatabricksPlatformAdapterError(
                        AdapterFailure(
                            code=failure.code,
                            stage=failure.stage,
                            possible_running_or_cost=True,
                            responsible_actor=failure.responsible_actor,
                            retry_class=failure.retry_class,
                            safe_next_action=failure.safe_next_action,
                        )
                    ) from None
                raise
            object.__setattr__(self, "_possible_running_or_cost", True)
            return response

    def _claim_cancellation_source(
        self,
        query_reference: str,
        marker_payload_sha256: str,
    ) -> object | None:
        if not _is_canonical_query_id(query_reference) or not _is_sha256(marker_payload_sha256):
            return None
        with self._lock:
            if query_reference in self._claimed_cancellation_references:
                return None
            self._claimed_cancellation_references.add(query_reference)
            return self._nonce


def open_native_bound_session(
    *,
    connection: ValidatedInstallerConnection,
    actor_configuration: VerifiedSignedActorConfiguration,
) -> NativeBoundSession:
    """Create a signed actor binding; every protected call verifies it natively in-process."""

    return _open_native_bound_session(
        connection=connection,
        actor_configuration=actor_configuration,
        launcher=_NativeBridgeLauncher(),
    )


def _open_native_bound_session(
    *,
    connection: ValidatedInstallerConnection,
    actor_configuration: VerifiedSignedActorConfiguration,
    launcher: _NativeBridgeLauncher,
) -> NativeBoundSession:
    _validate_connection(connection)
    if (
        not isinstance(actor_configuration, VerifiedSignedActorConfiguration)
        or actor_configuration.connection_sha256 != _connection_digest(connection)
        or not isinstance(launcher, _NativeBridgeLauncher)
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_ACTOR_CONFIG_CONNECTION_MISMATCH",
            FailureStage.ACTOR_IDENTITY,
        )
    return NativeBoundSession(
        connection=connection,
        actor_configuration=actor_configuration,
        launcher=launcher,
        _construction_token=_BOUND_SESSION_TOKEN,
    )


class NativeStatementSubmitter:
    """Submit one fixed registry operation through the actor-bound native helper."""

    def __init__(
        self,
        *,
        connection: ValidatedInstallerConnection,
        session: NativeBoundSession,
    ) -> None:
        _validate_connection(connection)
        if not isinstance(session, NativeBoundSession):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_BOUND_SESSION_REQUIRED",
                FailureStage.STATEMENT_SUBMISSION,
            )
        session._assert_connection(connection)
        self._connection = connection
        self._session = session

    def __repr__(self) -> str:
        return "NativeStatementSubmitter(<redacted>)"

    def submit(
        self,
        connection: ValidatedInstallerConnection,
        statement: ClosedStatement,
    ) -> StatementReceipt:
        self._session._assert_connection(connection)
        if not isinstance(statement, ClosedStatement):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_CLOSED_STATEMENT_REQUIRED",
                FailureStage.STATEMENT_SUBMISSION,
            )
        descriptor = statement._native_transport()
        if set(descriptor) != {
            "parameters",
            "registry_operation",
            "registry_version",
            "semantic_sha256",
        }:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_NATIVE_DESCRIPTOR_INVALID",
                FailureStage.STATEMENT_SUBMISSION,
            )
        response = self._session._invoke(
            stage=FailureStage.STATEMENT_SUBMISSION,
            operation="statement_execution_submit",
            payload=descriptor,
        )
        if (
            response.code != "DBTOBSB_NATIVE_STATEMENT_RECEIPT"
            or not isinstance(response.result, dict)
            or set(response.result) != {"disposition", "kind"}
            or response.result["kind"] != "statement_execution_submit"
        ):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_STATEMENT_RESPONSE_INVALID",
                FailureStage.STATEMENT_SUBMISSION,
                possible_running_or_cost=True,
            )
        try:
            disposition = StatementDisposition(response.result["disposition"])
        except (TypeError, ValueError):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_STATEMENT_RESPONSE_INVALID",
                FailureStage.STATEMENT_SUBMISSION,
                possible_running_or_cost=True,
            ) from None
        return StatementReceipt(disposition)


class DatabricksQueryHistoryClient:
    """GA Query History projection available only through an actor-bound native session."""

    def __init__(
        self,
        *,
        connection: ValidatedInstallerConnection,
        session: NativeBoundSession,
    ) -> None:
        _validate_connection(connection)
        if not isinstance(session, NativeBoundSession):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_BOUND_SESSION_REQUIRED",
                FailureStage.QUERY_HISTORY,
            )
        session._assert_connection(connection)
        self._connection = connection
        self._session = session

    def __repr__(self) -> str:
        return "DatabricksQueryHistoryClient(<redacted>)"

    def list_page(self, request: QueryHistoryRequest) -> QueryHistoryPage:
        if not isinstance(request, QueryHistoryRequest):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_HISTORY_REQUEST_INVALID",
                FailureStage.QUERY_HISTORY,
            )
        if request.warehouse_id != self._connection.installer_warehouse_id:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_HISTORY_WAREHOUSE_MISMATCH",
                FailureStage.QUERY_HISTORY,
            )
        if (
            isinstance(request.start_time_ms, bool)
            or not isinstance(request.start_time_ms, int)
            or isinstance(request.end_time_ms, bool)
            or not isinstance(request.end_time_ms, int)
            or request.start_time_ms < 0
            or request.end_time_ms <= request.start_time_ms
            or request.end_time_ms - request.start_time_ms > _MAX_HISTORY_WINDOW_MILLISECONDS
        ):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_HISTORY_WINDOW_INVALID",
                FailureStage.QUERY_HISTORY,
            )
        if request.page_token is not None and not _is_page_token(request.page_token):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_HISTORY_PAGE_TOKEN_INVALID",
                FailureStage.QUERY_HISTORY,
            )
        payload: dict[str, object] = {
            "end_time_ms": request.end_time_ms,
            "start_time_ms": request.start_time_ms,
            "warehouse_id": request.warehouse_id,
        }
        if request.page_token is not None:
            payload["page_token"] = request.page_token
        response = self._session._invoke(
            stage=FailureStage.QUERY_HISTORY,
            operation="query_history_list",
            payload=payload,
        )
        if response.code != "DBTOBSB_NATIVE_HISTORY_PAGE":
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_HISTORY_RESPONSE_INVALID",
                FailureStage.QUERY_HISTORY,
            )
        page = _parse_history_result(response.result, request.warehouse_id)
        return page

    def _claim_cancellation_source(
        self,
        query_reference: str,
        marker_payload_sha256: str,
    ) -> object | None:
        """Called only by signed-locator recovery after exactly one nonterminal match."""

        return self._session._claim_cancellation_source(
            query_reference,
            marker_payload_sha256,
        )


class DatabricksQueryCancellationClient:
    """Accepted cancellation remains nonterminal and requires later reconciliation."""

    def __init__(
        self,
        *,
        connection: ValidatedInstallerConnection,
        session: NativeBoundSession,
    ) -> None:
        _validate_connection(connection)
        if not isinstance(session, NativeBoundSession):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_BOUND_SESSION_REQUIRED",
                FailureStage.CANCELLATION,
            )
        session._assert_connection(connection)
        self._connection = connection
        self._session = session

    def __repr__(self) -> str:
        return "DatabricksQueryCancellationClient(<redacted>)"

    def request_cancel(self, target: CancellationHandle) -> CancellationOutcome:
        if not isinstance(target, CancellationHandle):
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_CANCELLATION_HANDLE_REQUIRED",
                FailureStage.CANCELLATION,
            )
        self._session._assert_connection(self._connection)
        try:
            query_reference = _consume_cancellation_handle(
                target,
                source_binding=self._session._nonce,
            )
        except Exception:
            raise _failure_for_code(
                "DBTOBSB_INSTALLER_CANCELLATION_HANDLE_INVALID",
                FailureStage.CANCELLATION,
            ) from None
        response = self._session._invoke(
            stage=FailureStage.CANCELLATION,
            operation="statement_execution_cancel",
            payload={"statement_id": query_reference},
        )
        if response.code == "DBTOBSB_NATIVE_CANCEL_ACCEPTED":
            if response.result != {"accepted": True, "kind": "statement_execution_cancel"}:
                raise _failure_for_code(
                    "DBTOBSB_INSTALLER_CANCELLATION_RESPONSE_INVALID",
                    FailureStage.CANCELLATION,
                )
            return CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL
        if response.code == "DBTOBSB_NATIVE_CANCEL_REJECTED":
            if response.result != {"accepted": False, "kind": "statement_execution_cancel"}:
                raise _failure_for_code(
                    "DBTOBSB_INSTALLER_CANCELLATION_RESPONSE_INVALID",
                    FailureStage.CANCELLATION,
                )
            return CancellationOutcome.REQUEST_REJECTED_NONTERMINAL
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_CANCELLATION_RESPONSE_INVALID",
            FailureStage.CANCELLATION,
        )


def _parse_history_result(
    result: dict[str, Any] | None,
    expected_warehouse_id: str,
) -> QueryHistoryPage:
    if not isinstance(result, dict) or set(result) != {"kind", "next_page_token", "records"}:
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_HISTORY_RESPONSE_INVALID",
            FailureStage.QUERY_HISTORY,
        )
    records = result["records"]
    next_page_token = result["next_page_token"]
    if (
        result["kind"] != "query_history_page"
        or not isinstance(records, list)
        or len(records) > 1
        or (next_page_token is not None and not _is_page_token(next_page_token))
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_HISTORY_RESPONSE_INVALID",
            FailureStage.QUERY_HISTORY,
        )
    projected = tuple(
        _parse_history_record(record, expected_warehouse_id=expected_warehouse_id)
        for record in records
    )
    return QueryHistoryPage(records=projected, next_page_token=next_page_token)


def _parse_history_record(
    value: object,
    *,
    expected_warehouse_id: str,
) -> QueryHistoryRecord:
    if not isinstance(value, dict) or set(value) != {
        "query_reference",
        "query_text",
        "status",
        "warehouse_id",
    }:
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_HISTORY_RESPONSE_INVALID",
            FailureStage.QUERY_HISTORY,
        )
    record = cast(dict[str, object], value)
    query_reference = record["query_reference"]
    query_text = record["query_text"]
    warehouse_id = record["warehouse_id"]
    if (
        not _is_canonical_query_id(query_reference)
        or not isinstance(query_text, str)
        or not query_text
        or len(query_text.encode("utf-8")) > _MAX_QUERY_TEXT_BYTES
        or warehouse_id != expected_warehouse_id
    ):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_HISTORY_RESPONSE_INVALID",
            FailureStage.QUERY_HISTORY,
        )
    try:
        status = QueryHistoryStatus(record["status"])
    except (TypeError, ValueError):
        raise _failure_for_code(
            "DBTOBSB_INSTALLER_HISTORY_RESPONSE_INVALID",
            FailureStage.QUERY_HISTORY,
        ) from None
    return QueryHistoryRecord(
        query_reference=cast(str, query_reference),
        warehouse_id=cast(str, warehouse_id),
        query_text=query_text,
        status=status.value,
    )


def _is_page_token(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and len(value.encode("utf-8")) <= _MAX_PAGE_TOKEN_BYTES
        and all(ord(character) >= 33 for character in value)
    )


def _is_canonical_query_id(value: object) -> bool:
    if not isinstance(value, str) or _CANONICAL_QUERY_ID.fullmatch(value) is None:
        return False
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


__all__ = [
    "ActorFingerprintObservation",
    "DatabricksPlatformAdapterError",
    "DatabricksQueryCancellationClient",
    "DatabricksQueryHistoryClient",
    "FingerprintEnrollmentApprovalProof",
    "NativeBoundSession",
    "NativeStatementSubmitter",
    "VerifiedSignedActorConfiguration",
    "observe_actor_fingerprint",
    "open_native_bound_session",
    "verify_fingerprint_enrollment_approval",
    "verify_signed_actor_configuration",
]
