"""Public, evidence-safe report contracts for artifact-pair inspection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]

REPORT_SCHEMA_VERSION = "dbtobsb.artifact-pair-report.v1"


class PairState(StrEnum):
    """Whether the two files satisfy the pinned pair contract."""

    VALID = "PAIR_VALID"
    INVALID = "PAIR_INVALID"


@dataclass(frozen=True, slots=True)
class ArtifactPairIssue:
    """One static issue that never contains evidence-derived text."""

    code: str
    component: str
    field: str
    observed_category: str
    impact: str
    next_action: str

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the versioned JSON representation."""
        return {
            "code": self.code,
            "component": self.component,
            "field": self.field,
            "observed_category": self.observed_category,
            "impact": self.impact,
            "next_action": self.next_action,
        }


@dataclass(frozen=True, slots=True)
class NativeStatusCount:
    """Count of one native dbt status without node identity or message data."""

    status: str
    count: int

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the versioned JSON representation."""
        return {"status": self.status, "count": self.count}


@dataclass(frozen=True, slots=True)
class ArtifactPairSummary:
    """Allowlisted facts emitted only after every pair invariant passes."""

    manifest_schema: str
    run_results_schema: str
    dbt_version: str
    adapter_type: str
    command: str
    result_count: int
    status_counts: tuple[NativeStatusCount, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the versioned JSON representation."""
        return {
            "manifest_schema": self.manifest_schema,
            "run_results_schema": self.run_results_schema,
            "dbt_version": self.dbt_version,
            "adapter_type": self.adapter_type,
            "command": self.command,
            "result_count": self.result_count,
            "status_counts": [item.to_dict() for item in self.status_counts],
        }


@dataclass(frozen=True, slots=True)
class ArtifactPairReport:
    """Deterministic report that holds no raw artifact values."""

    state: PairState
    summary: ArtifactPairSummary | None
    issues: tuple[ArtifactPairIssue, ...]

    def __post_init__(self) -> None:
        """Keep the state/summary/issue cardinality internally consistent."""
        if self.state is PairState.VALID and (self.summary is None or self.issues):
            raise ValueError("PAIR_VALID requires one summary and zero issues")
        if self.state is PairState.INVALID and (self.summary is not None or not self.issues):
            raise ValueError("PAIR_INVALID requires issues and no summary")

    @property
    def primary_issue(self) -> ArtifactPairIssue | None:
        """Return the first issue under the frozen precedence order."""
        return self.issues[0] if self.issues else None

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the versioned machine contract without evidence fragments."""
        primary = self.primary_issue
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "pair_state": self.state.value,
            "summary": self.summary.to_dict() if self.summary is not None else None,
            "primary_issue": primary.to_dict() if primary is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
        }
