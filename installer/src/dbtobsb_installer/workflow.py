"""Marker-gated, no-retry installer statement workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol
from uuid import UUID

from dbtobsb_installer.auth import ValidatedInstallerConnection
from dbtobsb_installer.operations import (
    ClosedMutationOperation,
    ClosedStatement,
    InstallerOperationError,
    MarkerTextKind,
    MarkerVerifier,
    SignedPreparationMarker,
    bind_mutation_marker,
    render_preparation_statement,
)
from dbtobsb_installer.recovery import (
    QueryHistoryClient,
    RecoveryOutcome,
    locate_operation,
)
from dbtobsb_installer.statement_contracts import (
    StatementDisposition,
    StatementReceipt,
    StatementSubmitter,
)

_COMPLETION_TOKEN = object()


class WorkflowStage(Enum):
    PREPARATION_SUBMISSION = "PREPARATION_SUBMISSION"
    PREPARATION_READBACK = "PREPARATION_READBACK"
    MUTATION_SUBMISSION = "MUTATION_SUBMISSION"
    MUTATION_RECOVERY = "MUTATION_RECOVERY"


class WorkflowDisposition(Enum):
    TERMINAL_SUCCESS = "TERMINAL_SUCCESS"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"
    CANCELLATION_NONTERMINAL = "CANCELLATION_NONTERMINAL"
    NONTERMINAL = "NONTERMINAL"
    INDETERMINATE = "INDETERMINATE"


class WorkflowCode(Enum):
    PREPARATION_SUBMITTED = "DBTOBSB_PREPARATION_SUBMITTED"
    PREPARATION_FAILED = "DBTOBSB_PREPARATION_FAILED"
    PREPARATION_CANCELLATION_PENDING = "DBTOBSB_PREPARATION_CANCELLATION_PENDING"
    PREPARATION_NONTERMINAL = "DBTOBSB_PREPARATION_NONTERMINAL"
    PREPARATION_INDETERMINATE = "DBTOBSB_PREPARATION_INDETERMINATE"
    PREPARATION_RETRY_BLOCKED = "DBTOBSB_PREPARATION_RETRY_BLOCKED"
    PREPARATION_CLAIM_INDETERMINATE = "DBTOBSB_PREPARATION_CLAIM_INDETERMINATE"
    PREPARATION_COMPLETED = "DBTOBSB_PREPARATION_COMPLETED"
    MUTATION_MARKER_REQUIRED = "DBTOBSB_MUTATION_MARKER_REQUIRED"
    MUTATION_SUBMITTED_PENDING_POSTSTATE = "DBTOBSB_MUTATION_SUBMITTED_PENDING_POSTSTATE"
    MUTATION_FAILED = "DBTOBSB_MUTATION_FAILED"
    MUTATION_CANCELLATION_PENDING = "DBTOBSB_MUTATION_CANCELLATION_PENDING"
    MUTATION_NONTERMINAL = "DBTOBSB_MUTATION_NONTERMINAL"
    MUTATION_INDETERMINATE = "DBTOBSB_MUTATION_INDETERMINATE"
    MUTATION_RETRY_BLOCKED = "DBTOBSB_MUTATION_RETRY_BLOCKED"
    MUTATION_CLAIM_INDETERMINATE = "DBTOBSB_MUTATION_CLAIM_INDETERMINATE"


class DispatchClaimOutcome(Enum):
    CLAIMED = "CLAIMED"
    ALREADY_CLAIMED = "ALREADY_CLAIMED"
    INDETERMINATE = "INDETERMINATE"


class MutationDispatchJournal(Protocol):
    """Durable local claim written before a mutating network send.

    Implementations must atomically persist the operation/marker pair before returning ``CLAIMED``.
    A process restart with the same pair must return ``ALREADY_CLAIMED``; storage ambiguity must
    return ``INDETERMINATE``.  This interface is deliberately not backed by an in-memory default.
    """

    def claim_once(
        self,
        operation_uuid: UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome: ...


class MarkerSubmissionJournal(Protocol):
    """Durable claim that forces recovery before a preparation-marker resubmission."""

    def claim_marker_once(
        self,
        operation_uuid: UUID,
        marker_payload_sha256: str,
    ) -> DispatchClaimOutcome: ...


@dataclass(frozen=True, slots=True)
class WorkflowReceipt:
    """Sanitized state transition containing no SQL, native ID, or customer value."""

    stage: WorkflowStage
    disposition: WorkflowDisposition
    code: WorkflowCode


@dataclass(frozen=True, slots=True, repr=False)
class CompletedPreparationMarker:
    """Opaque proof created only by unique terminal Query History readback."""

    marker: SignedPreparationMarker = field(repr=False)

    def __init__(self, marker: SignedPreparationMarker, *, _token: object) -> None:
        if _token is not _COMPLETION_TOKEN:
            raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_COMPLETION_DENIED")
        object.__setattr__(self, "marker", marker)

    def __repr__(self) -> str:
        return "CompletedPreparationMarker(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class PreparationReadback:
    receipt: WorkflowReceipt
    completion: CompletedPreparationMarker | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"PreparationReadback(receipt={self.receipt!r}, <redacted>)"


def _workflow_disposition(disposition: StatementDisposition) -> WorkflowDisposition:
    return {
        StatementDisposition.TERMINAL_SUCCESS: WorkflowDisposition.TERMINAL_SUCCESS,
        StatementDisposition.TERMINAL_FAILURE: WorkflowDisposition.TERMINAL_FAILURE,
        StatementDisposition.CANCELLATION_NONTERMINAL: (
            WorkflowDisposition.CANCELLATION_NONTERMINAL
        ),
        StatementDisposition.NONTERMINAL: WorkflowDisposition.NONTERMINAL,
        StatementDisposition.INDETERMINATE: WorkflowDisposition.INDETERMINATE,
    }[disposition]


def _submit_once(
    submitter: StatementSubmitter,
    connection: ValidatedInstallerConnection,
    statement: ClosedStatement,
) -> StatementReceipt:
    """Fail closed on a missing, malformed, or failed sealed submitter boundary."""
    try:
        receipt = submitter.submit(connection, statement)
    except Exception:
        return StatementReceipt(StatementDisposition.INDETERMINATE)
    if not isinstance(receipt, StatementReceipt) or not isinstance(
        receipt.disposition, StatementDisposition
    ):
        return StatementReceipt(StatementDisposition.INDETERMINATE)
    return receipt


class PreparationGate:
    """Submit one read-only marker once, then recover it through Query History."""

    def __init__(
        self,
        *,
        connection: ValidatedInstallerConnection,
        submitter: StatementSubmitter,
        history_client: QueryHistoryClient,
        verifier: MarkerVerifier,
        submission_journal: MarkerSubmissionJournal,
        marker: SignedPreparationMarker,
        start_time_ms: int,
        end_time_ms: int,
    ) -> None:
        if marker.locator.warehouse_id != connection.installer_warehouse_id:
            raise InstallerOperationError("DBTOBSB_INSTALLER_MARKER_WAREHOUSE_MISMATCH")
        self._connection = connection
        self._submitter = submitter
        self._history_client = history_client
        self._verifier = verifier
        self._submission_journal = submission_journal
        self._marker = marker
        self._statement = render_preparation_statement(marker, verifier)
        self._start_time_ms = start_time_ms
        self._end_time_ms = end_time_ms
        self._submitted = False

    def submit_once(self) -> WorkflowReceipt:
        """Submit the marker at most once; ambiguity is recovered, never resent."""
        if self._submitted:
            return WorkflowReceipt(
                WorkflowStage.PREPARATION_SUBMISSION,
                WorkflowDisposition.INDETERMINATE,
                WorkflowCode.PREPARATION_RETRY_BLOCKED,
            )
        try:
            claim = self._submission_journal.claim_marker_once(
                self._marker.locator.operation_uuid,
                self._marker.payload_sha256,
            )
        except Exception:
            claim = DispatchClaimOutcome.INDETERMINATE
        self._submitted = True
        if claim is DispatchClaimOutcome.ALREADY_CLAIMED:
            return WorkflowReceipt(
                WorkflowStage.PREPARATION_SUBMISSION,
                WorkflowDisposition.INDETERMINATE,
                WorkflowCode.PREPARATION_RETRY_BLOCKED,
            )
        if claim is not DispatchClaimOutcome.CLAIMED:
            return WorkflowReceipt(
                WorkflowStage.PREPARATION_SUBMISSION,
                WorkflowDisposition.INDETERMINATE,
                WorkflowCode.PREPARATION_CLAIM_INDETERMINATE,
            )
        result = _submit_once(self._submitter, self._connection, self._statement)
        disposition = _workflow_disposition(result.disposition)
        code = {
            WorkflowDisposition.TERMINAL_SUCCESS: WorkflowCode.PREPARATION_SUBMITTED,
            WorkflowDisposition.TERMINAL_FAILURE: WorkflowCode.PREPARATION_FAILED,
            WorkflowDisposition.CANCELLATION_NONTERMINAL: (
                WorkflowCode.PREPARATION_CANCELLATION_PENDING
            ),
            WorkflowDisposition.NONTERMINAL: WorkflowCode.PREPARATION_NONTERMINAL,
            WorkflowDisposition.INDETERMINATE: WorkflowCode.PREPARATION_INDETERMINATE,
        }[disposition]
        return WorkflowReceipt(WorkflowStage.PREPARATION_SUBMISSION, disposition, code)

    def recover(self) -> PreparationReadback:
        """Read every Query History page; only one finished marker completes the gate."""
        if not self._submitted:
            return PreparationReadback(
                WorkflowReceipt(
                    WorkflowStage.PREPARATION_READBACK,
                    WorkflowDisposition.INDETERMINATE,
                    WorkflowCode.PREPARATION_INDETERMINATE,
                )
            )
        recovery = locate_operation(
            client=self._history_client,
            verifier=self._verifier,
            marker=self._marker,
            kind=MarkerTextKind.PREPARATION,
            warehouse_id=self._connection.installer_warehouse_id,
            start_time_ms=self._start_time_ms,
            end_time_ms=self._end_time_ms,
        )
        if recovery.outcome is RecoveryOutcome.UNIQUE_TERMINAL_SUCCESS:
            return PreparationReadback(
                WorkflowReceipt(
                    WorkflowStage.PREPARATION_READBACK,
                    WorkflowDisposition.TERMINAL_SUCCESS,
                    WorkflowCode.PREPARATION_COMPLETED,
                ),
                CompletedPreparationMarker(self._marker, _token=_COMPLETION_TOKEN),
            )
        if recovery.outcome is RecoveryOutcome.UNIQUE_TERMINAL_FAILURE:
            disposition = WorkflowDisposition.TERMINAL_FAILURE
            code = WorkflowCode.PREPARATION_FAILED
        elif recovery.outcome is RecoveryOutcome.CANCELLATION_NONTERMINAL:
            disposition = WorkflowDisposition.CANCELLATION_NONTERMINAL
            code = WorkflowCode.PREPARATION_CANCELLATION_PENDING
        elif recovery.outcome is RecoveryOutcome.UNIQUE_NONTERMINAL:
            disposition = WorkflowDisposition.NONTERMINAL
            code = WorkflowCode.PREPARATION_NONTERMINAL
        else:
            disposition = WorkflowDisposition.INDETERMINATE
            code = WorkflowCode.PREPARATION_INDETERMINATE
        return PreparationReadback(
            WorkflowReceipt(WorkflowStage.PREPARATION_READBACK, disposition, code)
        )


class MutationDispatcher:
    """Consume one completed marker and submit its closed mutation at most once."""

    def __init__(
        self,
        *,
        connection: ValidatedInstallerConnection,
        submitter: StatementSubmitter,
        history_client: QueryHistoryClient,
        verifier: MarkerVerifier,
        dispatch_journal: MutationDispatchJournal,
        start_time_ms: int,
        end_time_ms: int,
    ) -> None:
        self._connection = connection
        self._submitter = submitter
        self._history_client = history_client
        self._verifier = verifier
        self._dispatch_journal = dispatch_journal
        self._start_time_ms = start_time_ms
        self._end_time_ms = end_time_ms
        self._dispatched = False
        self._marker: SignedPreparationMarker | None = None

    def dispatch_once(
        self,
        operation: ClosedMutationOperation,
        completion: CompletedPreparationMarker | None,
    ) -> WorkflowReceipt:
        """Dispatch once after a matching, uniquely recovered preparation marker."""
        if self._dispatched:
            return WorkflowReceipt(
                WorkflowStage.MUTATION_SUBMISSION,
                WorkflowDisposition.INDETERMINATE,
                WorkflowCode.MUTATION_RETRY_BLOCKED,
            )
        if (
            not isinstance(completion, CompletedPreparationMarker)
            or completion.marker.locator.warehouse_id != self._connection.installer_warehouse_id
            or completion.marker.locator.statement_sha256 != operation.statement_sha256
        ):
            return WorkflowReceipt(
                WorkflowStage.MUTATION_SUBMISSION,
                WorkflowDisposition.TERMINAL_FAILURE,
                WorkflowCode.MUTATION_MARKER_REQUIRED,
            )
        bound = bind_mutation_marker(operation, completion.marker, self._verifier)
        try:
            claim = self._dispatch_journal.claim_once(
                completion.marker.locator.operation_uuid,
                completion.marker.payload_sha256,
            )
        except Exception:
            claim = DispatchClaimOutcome.INDETERMINATE
        if claim is DispatchClaimOutcome.ALREADY_CLAIMED:
            self._dispatched = True
            self._marker = completion.marker
            return WorkflowReceipt(
                WorkflowStage.MUTATION_SUBMISSION,
                WorkflowDisposition.INDETERMINATE,
                WorkflowCode.MUTATION_RETRY_BLOCKED,
            )
        if claim is not DispatchClaimOutcome.CLAIMED:
            self._dispatched = True
            self._marker = completion.marker
            return WorkflowReceipt(
                WorkflowStage.MUTATION_SUBMISSION,
                WorkflowDisposition.INDETERMINATE,
                WorkflowCode.MUTATION_CLAIM_INDETERMINATE,
            )
        self._dispatched = True
        self._marker = completion.marker
        result = _submit_once(self._submitter, self._connection, bound)
        disposition = _workflow_disposition(result.disposition)
        code = {
            WorkflowDisposition.TERMINAL_SUCCESS: (
                WorkflowCode.MUTATION_SUBMITTED_PENDING_POSTSTATE
            ),
            WorkflowDisposition.TERMINAL_FAILURE: WorkflowCode.MUTATION_FAILED,
            WorkflowDisposition.CANCELLATION_NONTERMINAL: (
                WorkflowCode.MUTATION_CANCELLATION_PENDING
            ),
            WorkflowDisposition.NONTERMINAL: WorkflowCode.MUTATION_NONTERMINAL,
            WorkflowDisposition.INDETERMINATE: WorkflowCode.MUTATION_INDETERMINATE,
        }[disposition]
        return WorkflowReceipt(WorkflowStage.MUTATION_SUBMISSION, disposition, code)

    def recover(self) -> WorkflowReceipt:
        """Reconcile the dispatched operation through Query History without resubmission."""
        if not self._dispatched or self._marker is None:
            return WorkflowReceipt(
                WorkflowStage.MUTATION_RECOVERY,
                WorkflowDisposition.TERMINAL_FAILURE,
                WorkflowCode.MUTATION_MARKER_REQUIRED,
            )
        recovery = locate_operation(
            client=self._history_client,
            verifier=self._verifier,
            marker=self._marker,
            kind=MarkerTextKind.MUTATION,
            warehouse_id=self._connection.installer_warehouse_id,
            start_time_ms=self._start_time_ms,
            end_time_ms=self._end_time_ms,
        )
        if recovery.outcome is RecoveryOutcome.UNIQUE_TERMINAL_SUCCESS:
            disposition = WorkflowDisposition.TERMINAL_SUCCESS
            code = WorkflowCode.MUTATION_SUBMITTED_PENDING_POSTSTATE
        elif recovery.outcome is RecoveryOutcome.UNIQUE_TERMINAL_FAILURE:
            disposition = WorkflowDisposition.TERMINAL_FAILURE
            code = WorkflowCode.MUTATION_FAILED
        elif recovery.outcome is RecoveryOutcome.CANCELLATION_NONTERMINAL:
            disposition = WorkflowDisposition.CANCELLATION_NONTERMINAL
            code = WorkflowCode.MUTATION_CANCELLATION_PENDING
        elif recovery.outcome is RecoveryOutcome.UNIQUE_NONTERMINAL:
            disposition = WorkflowDisposition.NONTERMINAL
            code = WorkflowCode.MUTATION_NONTERMINAL
        else:
            disposition = WorkflowDisposition.INDETERMINATE
            code = WorkflowCode.MUTATION_INDETERMINATE
        return WorkflowReceipt(WorkflowStage.MUTATION_RECOVERY, disposition, code)
