"""Closed contracts for fixed-operation submission through the sealed native helper."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from dbtobsb_installer.auth import ValidatedInstallerConnection
from dbtobsb_installer.operations import ClosedStatement


class StatementDisposition(Enum):
    """Exhaustive submission classification; cancellation is deliberately nonterminal."""

    TERMINAL_SUCCESS = "TERMINAL_SUCCESS"
    TERMINAL_FAILURE = "TERMINAL_FAILURE"
    CANCELLATION_NONTERMINAL = "CANCELLATION_NONTERMINAL"
    NONTERMINAL = "NONTERMINAL"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class StatementReceipt:
    """Sanitized receipt containing no SQL, native identifier, or customer value."""

    disposition: StatementDisposition

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, StatementDisposition):
            raise TypeError("DBTOBSB_STATEMENT_RECEIPT_INVALID")


class StatementSubmitter(Protocol):
    """Submit one closed statement and return one sanitized exhaustive receipt.

    Production uses ``NativeStatementSubmitter``. Python deliberately provides no network,
    credential, arbitrary-SQL, or automatic-retry implementation.
    """

    def submit(
        self,
        connection: ValidatedInstallerConnection,
        statement: ClosedStatement,
    ) -> StatementReceipt: ...
