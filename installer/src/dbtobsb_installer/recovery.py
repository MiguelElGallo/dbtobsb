"""GA Query History recovery interfaces for signed installer operations.

The concrete Databricks API adapter is intentionally deferred.  This module freezes the closed
pagination, matching, status, and cancellation semantics against fake clients without making cloud
calls or depending on the Preview query-history system table.
"""

from __future__ import annotations

import uuid
import weakref
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Protocol

from dbtobsb_installer.operations import (
    InstallerOperationError,
    MarkerTextKind,
    MarkerVerifier,
    SignedPreparationMarker,
    parse_query_marker,
)

_MAX_PAGES = 100
_MAX_WINDOW_MILLISECONDS = 20 * 60 * 1000
_CANCELLATION_HANDLE_TOKEN = object()


class QueryHistoryStatus(Enum):
    """Closed GA Query History state vocabulary accepted by the foundation."""

    QUEUED = "QUEUED"
    STARTED = "STARTED"
    COMPILING = "COMPILING"
    COMPILED = "COMPILED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class RecoveryOutcome(Enum):
    UNIQUE_TERMINAL_SUCCESS = "UNIQUE_TERMINAL_SUCCESS"
    UNIQUE_TERMINAL_FAILURE = "UNIQUE_TERMINAL_FAILURE"
    CANCELLATION_NONTERMINAL = "CANCELLATION_NONTERMINAL"
    UNIQUE_NONTERMINAL = "UNIQUE_NONTERMINAL"
    NOT_FOUND_INDETERMINATE = "NOT_FOUND_INDETERMINATE"
    AMBIGUOUS_INDETERMINATE = "AMBIGUOUS_INDETERMINATE"
    UNKNOWN_STATUS_INDETERMINATE = "UNKNOWN_STATUS_INDETERMINATE"
    PAGINATION_CYCLE_INDETERMINATE = "PAGINATION_CYCLE_INDETERMINATE"
    PAGE_LIMIT_INDETERMINATE = "PAGE_LIMIT_INDETERMINATE"
    HISTORY_UNAVAILABLE_INDETERMINATE = "HISTORY_UNAVAILABLE_INDETERMINATE"
    INVALID_MARKER_INDETERMINATE = "INVALID_MARKER_INDETERMINATE"
    MALFORMED_REFERENCE_INDETERMINATE = "MALFORMED_REFERENCE_INDETERMINATE"
    CANCELLATION_TARGET_UNAVAILABLE_INDETERMINATE = "CANCELLATION_TARGET_UNAVAILABLE_INDETERMINATE"


class CancellationOutcome(Enum):
    REQUEST_ACCEPTED_NONTERMINAL = "REQUEST_ACCEPTED_NONTERMINAL"
    REQUEST_REJECTED_NONTERMINAL = "REQUEST_REJECTED_NONTERMINAL"
    REQUEST_INDETERMINATE = "REQUEST_INDETERMINATE"


@dataclass(frozen=True, slots=True, repr=False)
class QueryHistoryRequest:
    """Narrow dedicated-warehouse query window; page tokens remain internal."""

    warehouse_id: str = field(repr=False)
    start_time_ms: int
    end_time_ms: int
    page_token: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return "QueryHistoryRequest(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class QueryHistoryRecord:
    """Minimum GA response projection needed for recovery."""

    query_reference: str = field(repr=False)
    warehouse_id: str = field(repr=False)
    query_text: str = field(repr=False)
    status: str

    def __repr__(self) -> str:
        return f"QueryHistoryRecord(status={self.status!r}, <redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class QueryHistoryPage:
    records: tuple[QueryHistoryRecord, ...] = field(repr=False)
    next_page_token: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"QueryHistoryPage(record_count={len(self.records)}, <redacted>)"


class QueryHistoryClient(Protocol):
    """Adapter for the GA Query History list API only."""

    def list_page(self, request: QueryHistoryRequest) -> QueryHistoryPage: ...


class QueryCancellationClient(Protocol):
    """Adapter for an explicit native cancellation request, never a success proof."""

    def request_cancel(self, target: CancellationHandle) -> CancellationOutcome: ...


@dataclass(frozen=True, slots=True, repr=False)
class RecoveryResult:
    """Sanitized result; the native reference is retained only for bounded cancellation."""

    outcome: RecoveryOutcome
    pages_read: int
    matching_record_count: int
    cancellation_handle: CancellationHandle | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return (
            "RecoveryResult("
            f"outcome={self.outcome.value}, pages_read={self.pages_read}, "
            f"matching_record_count={self.matching_record_count}, <redacted>)"
        )


@dataclass(frozen=True, slots=True)
class CancellationReceipt:
    """Safe cancellation receipt; accepted cancellation remains nonterminal."""

    outcome: CancellationOutcome


class CancellationHandle:
    """Opaque native cancellation handle created only after one signed-history match."""

    __slots__ = ("__weakref__",)

    def __init__(
        self,
        *,
        query_reference: str,
        marker_payload_sha256: str,
        source_binding: object,
        _construction_token: object,
    ) -> None:
        if _construction_token is not _CANCELLATION_HANDLE_TOKEN:
            raise InstallerOperationError("DBTOBSB_INSTALLER_CANCELLATION_HANDLE_DENIED")
        if (
            not _is_canonical_query_reference(query_reference)
            or not isinstance(marker_payload_sha256, str)
            or len(marker_payload_sha256) != 64
            or any(character not in "0123456789abcdef" for character in marker_payload_sha256)
        ):
            raise InstallerOperationError("DBTOBSB_INSTALLER_CANCELLATION_HANDLE_INVALID")
        with _CANCELLATION_HANDLE_LOCK:
            _CANCELLATION_HANDLE_STATES[self] = _CancellationHandleState(
                query_reference=query_reference,
                source_binding=source_binding,
            )

    def __repr__(self) -> str:
        return "CancellationHandle(<redacted>)"


@dataclass(slots=True)
class _CancellationHandleState:
    query_reference: str
    source_binding: object
    consumed: bool = False


_CANCELLATION_HANDLE_LOCK = Lock()
_CANCELLATION_HANDLE_STATES: weakref.WeakKeyDictionary[
    CancellationHandle, _CancellationHandleState
] = weakref.WeakKeyDictionary()


def _consume_cancellation_handle(handle: CancellationHandle, *, source_binding: object) -> str:
    """Consume one signed-match handle for its exact bound history session."""

    if not isinstance(handle, CancellationHandle):
        raise InstallerOperationError("DBTOBSB_INSTALLER_CANCELLATION_HANDLE_INVALID")
    with _CANCELLATION_HANDLE_LOCK:
        state = _CANCELLATION_HANDLE_STATES.get(handle)
        if state is None or state.source_binding is not source_binding or state.consumed:
            raise InstallerOperationError("DBTOBSB_INSTALLER_CANCELLATION_HANDLE_INVALID")
        state.consumed = True
        return state.query_reference


def _is_canonical_query_reference(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return str(parsed) == value


def _validate_window(warehouse_id: str, start_time_ms: int, end_time_ms: int) -> None:
    if (
        not isinstance(warehouse_id, str)
        or len(warehouse_id) != 16
        or any(character not in "0123456789abcdef" for character in warehouse_id)
        or isinstance(start_time_ms, bool)
        or isinstance(end_time_ms, bool)
        or not isinstance(start_time_ms, int)
        or not isinstance(end_time_ms, int)
        or start_time_ms < 0
        or end_time_ms <= start_time_ms
        or end_time_ms - start_time_ms > _MAX_WINDOW_MILLISECONDS
    ):
        raise InstallerOperationError("DBTOBSB_INSTALLER_HISTORY_WINDOW_INVALID")


def _is_expected_marker(
    record: QueryHistoryRecord,
    *,
    marker: SignedPreparationMarker,
    kind: MarkerTextKind,
    verifier: MarkerVerifier,
) -> tuple[bool, bool]:
    """Return (matches, malformed_product_marker)."""
    if not isinstance(record.query_text, str):
        return False, True
    if marker.compact_token not in record.query_text:
        return False, False
    try:
        observed = parse_query_marker(record.query_text, kind, verifier)
    except InstallerOperationError:
        return False, True
    return observed == marker, False


def _claim_cancellation_source(
    client: QueryHistoryClient,
    *,
    query_reference: str,
    marker_payload_sha256: str,
) -> object | None:
    claim = getattr(client, "_claim_cancellation_source", None)
    if claim is None:
        return client
    if not callable(claim):
        return None
    try:
        binding = claim(query_reference, marker_payload_sha256)
    except Exception:
        return None
    return binding if binding is not None else None


def locate_operation(
    *,
    client: QueryHistoryClient,
    verifier: MarkerVerifier,
    marker: SignedPreparationMarker,
    kind: MarkerTextKind,
    warehouse_id: str,
    start_time_ms: int,
    end_time_ms: int,
) -> RecoveryResult:
    """Consume every page and locate exactly one signed operation without choosing an ID."""
    _validate_window(warehouse_id, start_time_ms, end_time_ms)
    page_token: str | None = None
    seen_tokens: set[str] = set()
    matches: list[QueryHistoryRecord] = []
    pages_read = 0
    invalid_marker_seen = False
    while True:
        if pages_read >= _MAX_PAGES:
            return RecoveryResult(
                RecoveryOutcome.PAGE_LIMIT_INDETERMINATE,
                pages_read,
                len(matches),
            )
        request = QueryHistoryRequest(
            warehouse_id=warehouse_id,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            page_token=page_token,
        )
        try:
            page = client.list_page(request)
        except Exception:
            return RecoveryResult(
                RecoveryOutcome.HISTORY_UNAVAILABLE_INDETERMINATE,
                pages_read,
                len(matches),
            )
        if not isinstance(page, QueryHistoryPage) or not isinstance(page.records, tuple):
            return RecoveryResult(
                RecoveryOutcome.HISTORY_UNAVAILABLE_INDETERMINATE,
                pages_read,
                len(matches),
            )
        pages_read += 1
        for record in page.records:
            if not isinstance(record, QueryHistoryRecord):
                invalid_marker_seen = True
                continue
            if record.warehouse_id != warehouse_id:
                continue
            matched, invalid = _is_expected_marker(
                record,
                marker=marker,
                kind=kind,
                verifier=verifier,
            )
            invalid_marker_seen = invalid_marker_seen or invalid
            if matched:
                matches.append(record)
        next_token = page.next_page_token
        if next_token is None:
            break
        if (
            not isinstance(next_token, str)
            or not next_token
            or len(next_token) > 4_096
            or any(ord(character) < 33 for character in next_token)
            or next_token in seen_tokens
        ):
            return RecoveryResult(
                RecoveryOutcome.PAGINATION_CYCLE_INDETERMINATE,
                pages_read,
                len(matches),
            )
        seen_tokens.add(next_token)
        page_token = next_token
    if invalid_marker_seen:
        return RecoveryResult(
            RecoveryOutcome.INVALID_MARKER_INDETERMINATE,
            pages_read,
            len(matches),
        )
    if not matches:
        return RecoveryResult(
            RecoveryOutcome.NOT_FOUND_INDETERMINATE,
            pages_read,
            0,
        )
    if len(matches) != 1:
        return RecoveryResult(
            RecoveryOutcome.AMBIGUOUS_INDETERMINATE,
            pages_read,
            len(matches),
        )
    match = matches[0]
    if not _is_canonical_query_reference(match.query_reference):
        return RecoveryResult(
            RecoveryOutcome.MALFORMED_REFERENCE_INDETERMINATE,
            pages_read,
            1,
        )
    try:
        status = QueryHistoryStatus(match.status)
    except (TypeError, ValueError):
        return RecoveryResult(
            RecoveryOutcome.UNKNOWN_STATUS_INDETERMINATE,
            pages_read,
            1,
        )
    cancellation_handle: CancellationHandle | None = None
    if status is QueryHistoryStatus.FINISHED:
        outcome = RecoveryOutcome.UNIQUE_TERMINAL_SUCCESS
    elif status is QueryHistoryStatus.FAILED:
        outcome = RecoveryOutcome.UNIQUE_TERMINAL_FAILURE
    elif status is QueryHistoryStatus.CANCELED:
        outcome = RecoveryOutcome.CANCELLATION_NONTERMINAL
    else:
        outcome = RecoveryOutcome.UNIQUE_NONTERMINAL
        source_binding = _claim_cancellation_source(
            client,
            query_reference=match.query_reference,
            marker_payload_sha256=marker.payload_sha256,
        )
        if source_binding is None:
            return RecoveryResult(
                RecoveryOutcome.CANCELLATION_TARGET_UNAVAILABLE_INDETERMINATE,
                pages_read,
                1,
            )
        cancellation_handle = CancellationHandle(
            query_reference=match.query_reference,
            marker_payload_sha256=marker.payload_sha256,
            source_binding=source_binding,
            _construction_token=_CANCELLATION_HANDLE_TOKEN,
        )
    return RecoveryResult(outcome, pages_read, 1, cancellation_handle)


def request_cancellation(
    client: QueryCancellationClient,
    handle: CancellationHandle | None,
) -> CancellationReceipt:
    """Request cancellation once without ever treating acceptance as terminal."""
    if not isinstance(handle, CancellationHandle):
        return CancellationReceipt(CancellationOutcome.REQUEST_REJECTED_NONTERMINAL)
    try:
        outcome = client.request_cancel(handle)
    except Exception:
        return CancellationReceipt(CancellationOutcome.REQUEST_INDETERMINATE)
    if outcome not in {
        CancellationOutcome.REQUEST_ACCEPTED_NONTERMINAL,
        CancellationOutcome.REQUEST_REJECTED_NONTERMINAL,
    }:
        return CancellationReceipt(CancellationOutcome.REQUEST_INDETERMINATE)
    return CancellationReceipt(outcome)
