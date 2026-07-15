"""Public, evidence-safe report contracts for artifact-pair inspection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from dbtobsb_capture.registry import ISSUE_PRECEDENCE, MAX_REPORT_ISSUES, NATIVE_STATUSES

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

    def __post_init__(self) -> None:
        """Reject invented codes or text at the public construction boundary."""
        from dbtobsb_capture.inspector import _ISSUES

        template = _ISSUES.get(self.code)
        actual = (
            self.component,
            self.field,
            self.observed_category,
            self.impact,
            self.next_action,
        )
        expected = (
            (
                template.component,
                template.field,
                template.observed_category,
                template.impact,
                template.next_action,
            )
            if template is not None
            else None
        )
        if actual != expected:
            raise ValueError("issue must match one closed v1 issue contract")

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

    def __post_init__(self) -> None:
        """Accept only the pinned native vocabulary and a positive count."""
        if self.status not in NATIVE_STATUSES:
            raise ValueError("status is not in the closed v1 native vocabulary")
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 1:
            raise ValueError("status count must be a positive integer")

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
    status_counts: tuple[NativeStatusCount, ...]

    def __post_init__(self) -> None:
        """Enforce the exact v1 summary rather than a loose data container."""
        actual_contract = (
            self.manifest_schema,
            self.run_results_schema,
            self.dbt_version,
            self.adapter_type,
            self.command,
        )
        expected_contract = (
            "https://schemas.getdbt.com/dbt/manifest/v12.json",
            "https://schemas.getdbt.com/dbt/run-results/v6.json",
            "1.11.12",
            "databricks",
            "build",
        )
        if actual_contract != expected_contract:
            raise ValueError("summary must match the closed v1 compatibility contract")
        if not isinstance(self.status_counts, tuple) or any(
            not isinstance(item, NativeStatusCount) for item in self.status_counts
        ):
            raise ValueError("status counts must be a tuple of NativeStatusCount values")
        statuses = tuple(item.status for item in self.status_counts)
        if (
            not statuses
            or statuses != tuple(sorted(statuses))
            or len(statuses) != len(set(statuses))
        ):
            raise ValueError("status counts must be nonempty, unique, and sorted")

    @property
    def result_count(self) -> int:
        """Derive the total so the machine contract carries no inconsistent duplicate."""
        return sum(item.count for item in self.status_counts)

    def to_dict(self) -> dict[str, JsonValue]:
        """Return the versioned JSON representation."""
        return {
            "manifest_schema": self.manifest_schema,
            "run_results_schema": self.run_results_schema,
            "dbt_version": self.dbt_version,
            "adapter_type": self.adapter_type,
            "command": self.command,
            "status_counts": {item.status: item.count for item in self.status_counts},
        }


@dataclass(frozen=True, slots=True)
class ArtifactPairReport:
    """Deterministic report that holds no raw artifact values."""

    state: PairState
    summary: ArtifactPairSummary | None
    issues: tuple[ArtifactPairIssue, ...]

    def __post_init__(self) -> None:
        """Keep the state/summary/issue cardinality internally consistent."""
        if not isinstance(self.state, PairState):
            raise ValueError("state must be one closed v1 PairState")
        if self.summary is not None and not isinstance(self.summary, ArtifactPairSummary):
            raise ValueError("summary must be an ArtifactPairSummary or None")
        if not isinstance(self.issues, tuple) or any(
            not isinstance(issue, ArtifactPairIssue) for issue in self.issues
        ):
            raise ValueError("issues must be a tuple of ArtifactPairIssue values")
        if len(self.issues) > MAX_REPORT_ISSUES:
            raise ValueError("issues exceed the closed v1 maximum")
        if len(self.issues) != len(set(self.issues)):
            raise ValueError("issues must be unique")
        issue_rank = {code: rank for rank, code in enumerate(ISSUE_PRECEDENCE)}
        canonical_issues = tuple(sorted(self.issues, key=lambda issue: issue_rank[issue.code]))
        if self.issues != canonical_issues:
            raise ValueError("issues must follow the closed v1 precedence")
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
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "pair_state": self.state.value,
            "summary": self.summary.to_dict() if self.summary is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
        }
