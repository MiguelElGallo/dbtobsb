"""Safe, stable operator diagnostics with one recovery action."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class OperatorDiagnostic:
    """Allowlisted diagnostic text that never includes observed platform values."""

    code: str
    outcome: Literal["accepted", "denied"]
    component: str
    summary: str
    consequence: str
    responsible_actor: str
    action: str

    def as_dict(self) -> dict[str, str]:
        """Return the stable machine-readable representation."""
        return asdict(self)

    def human(self) -> str:
        """Return a compact human representation with exactly one next action."""
        return (
            f"{self.summary} {self.consequence} Responsible actor: {self.responsible_actor}. "
            f"Next action: {self.action} [{self.code}]"
        )
