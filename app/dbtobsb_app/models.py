"""Sanitized public models for the read-only observability surface."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

LakeflowResultState: TypeAlias = Literal[
    "BREAKING_CHANGE",
    "BUDGET_POLICY_LIMIT_EXCEEDED",
    "CANCELED",
    "CLOUD_FAILURE",
    "CLUSTER_ERROR",
    "CLUSTER_REQUEST_LIMIT_EXCEEDED",
    "DISABLED",
    "DRIVER_ERROR",
    "EXCLUDED",
    "FAILED",
    "FEATURE_DISABLED",
    "INTERNAL_ERROR",
    "INVALID_CLUSTER_REQUEST",
    "INVALID_RUN_CONFIGURATION",
    "LIBRARY_INSTALLATION_ERROR",
    "MAX_CONCURRENT_RUNS_EXCEEDED",
    "MAXIMUM_CONCURRENT_RUNS_REACHED",
    "MAX_JOB_QUEUE_SIZE_EXCEEDED",
    "MAX_SPARK_CONTEXTS_EXCEEDED",
    "REPOSITORY_CHECKOUT_FAILED",
    "RESOURCE_NOT_FOUND",
    "RUN_EXECUTION_ERROR",
    "SKIPPED",
    "STORAGE_ACCESS_ERROR",
    "SUCCESS",
    "SUCCESS_WITH_FAILURES",
    "TIMEDOUT",
    "UNAUTHORIZED_ERROR",
    "UNKNOWN",
    "UPSTREAM_CANCELED",
    "UPSTREAM_FAILED",
    "USER_CANCELED",
    "WORKSPACE_RUN_LIMIT_EXCEEDED",
]
RetrievalState: TypeAlias = Literal["RETRIEVED", "UNAVAILABLE"]
CaptureState: TypeAlias = Literal[
    "COMPLETE",
    "PARTIAL",
    "NOT_PRODUCED",
    "ARCHIVE_UNAVAILABLE",
    "INVALID_CAPTURE_CONTRACT",
]
PairState: TypeAlias = Literal["PAIR_VALID", "PAIR_INVALID"]
StructuredLogState: TypeAlias = Literal[
    "UNAVAILABLE",
    "NOT_INITIALIZED",
    "TRUNCATED",
    "MALFORMED",
    "MISSING",
    "UNKNOWN_VERSION",
    "ARTIFACT_INVOCATION_MISMATCH",
    "VALID",
]
CollectionState: TypeAlias = Literal[
    "DISCOVERED",
    "COLLECTING",
    "RETRYABLE",
    "TERMINAL_FAILURE",
    "PUBLISHED",
]
ErrorCode: TypeAlias = Literal[
    "DBTOBSB_CONFIGURATION_INVALID",
    "DBTOBSB_APP_AUTH_INVALID",
    "DBTOBSB_APP_QUERY_FAILED",
    "DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH",
    "DBTOBSB_APP_NODE_VIEW_CONTRACT_MISMATCH",
    "DBTOBSB_APP_COLLECTION_VIEW_CONTRACT_MISMATCH",
]
ResponsibleActor: TypeAlias = Literal["deployment/seal verifier", "data operator"]
DbtResourceType: TypeAlias = Literal[
    "model",
    "seed",
    "snapshot",
    "test",
    "unit_test",
    "saved_query",
    "exposure",
    "function",
]
DbtNativeStatus: TypeAlias = Literal[
    "error",
    "fail",
    "no-op",
    "partial success",
    "pass",
    "skipped",
    "success",
    "warn",
]

_RUN_STATUSES = frozenset({"error", "no-op", "partial success", "skipped", "success"})
_TEST_STATUSES = frozenset({"error", "fail", "pass", "skipped", "warn"})


class PublicModel(BaseModel):
    """Strict model that rejects accidental new fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class RunHealth(PublicModel):
    """Allowlisted run-level fields from the sanitized health view."""

    workspace_id: int = Field(ge=1)
    dbt_task_run_id: int = Field(ge=1)
    observed_job_id: int = Field(ge=1)
    observed_job_run_id: int = Field(ge=1)
    observed_task_key: Literal["dbt_build"]
    repair_count: int = Field(ge=0)
    execution_count: int = Field(ge=1)
    attempt_number: int = Field(ge=0)
    task_start_time: datetime | None
    task_end_time: datetime | None
    lakeflow_result_state: LakeflowResultState
    retrieval_state: RetrievalState
    capture_state: CaptureState
    pair_state: PairState | None = None
    dbt_include_deps: bool
    issue_code: str | None = Field(default=None, max_length=128)
    logs_truncated: bool | None
    structured_log_state: StructuredLogState
    deps_structured_log_state: StructuredLogState | None
    structured_log_expected_dbt_common_version: Literal["1.37.5"]
    invocation_id: str | None = Field(default=None, max_length=128)
    expected_node_count: int = Field(ge=0)
    collected_at: datetime
    published_at: datetime | None
    generated_at: datetime | None
    elapsed_time: float | None = Field(default=None, ge=0)
    dbt_version: Literal["1.11.12"] | None = None
    adapter_type: Literal["databricks"] | None = None
    result_count: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_evidence_axes(self) -> RunHealth:
        """Reject combinations that the closed collector contract cannot publish."""
        if self.dbt_include_deps != (self.deps_structured_log_state is not None):
            raise ValueError("deps log state must match dbt_include_deps")

        invocation_values = (
            self.invocation_id,
            self.generated_at,
            self.elapsed_time,
            self.dbt_version,
            self.adapter_type,
            self.result_count,
        )
        if self.pair_state == "PAIR_VALID":
            if (
                self.capture_state != "COMPLETE"
                or self.issue_code is not None
                or any(value is None for value in invocation_values)
                or self.result_count != self.expected_node_count
                or self.expected_node_count < 1
            ):
                raise ValueError("PAIR_VALID requires one complete accepted invocation")
        elif (
            self.capture_state == "COMPLETE"
            or self.issue_code is None
            or (
                self.pair_state == "PAIR_INVALID"
                and self.capture_state != "INVALID_CAPTURE_CONTRACT"
            )
            or any(value is not None for value in invocation_values)
        ):
            raise ValueError("non-valid pairs cannot carry accepted invocation metadata")
        return self


class NodeHealth(PublicModel):
    """Allowlisted node-level fields from the sanitized health view."""

    workspace_id: int = Field(ge=1)
    dbt_task_run_id: int = Field(ge=1)
    observed_job_id: int = Field(ge=1)
    observed_job_run_id: int = Field(ge=1)
    observed_task_key: Literal["dbt_build"]
    capture_state: Literal["COMPLETE"]
    lakeflow_result_state: LakeflowResultState
    invocation_id: str = Field(max_length=128)
    unique_id: str = Field(max_length=512)
    resource_type: DbtResourceType
    status: DbtNativeStatus
    execution_time: float = Field(ge=0)
    failures: int | None = Field(ge=0)

    @model_validator(mode="after")
    def validate_native_status(self) -> NodeHealth:
        """Keep native dbt status vocabulary resource-aware."""
        allowed = _TEST_STATUSES if self.resource_type in {"test", "unit_test"} else _RUN_STATUSES
        if self.status not in allowed:
            raise ValueError("dbt status is invalid for the resource type")
        return self


class CollectionHealth(PublicModel):
    """Allowlisted reconciliation state from the sanitized collection-health view."""

    workspace_id: int = Field(ge=1)
    dbt_task_run_id: int = Field(ge=1)
    observed_job_id: int = Field(ge=1)
    observed_job_run_id: int = Field(ge=1)
    observed_task_key: Literal["dbt_build"]
    repair_count: int = Field(ge=0)
    execution_count: int = Field(ge=1)
    attempt_number: int | None = Field(default=None, ge=0)
    task_start_time: datetime | None
    task_end_time: datetime | None
    lakeflow_result_state: LakeflowResultState | None
    collector_state: CollectionState
    collection_issue_code: str | None = Field(default=None, max_length=96)
    first_discovered_at: datetime | None
    last_attempted_at: datetime | None
    collection_attempt_count: int = Field(ge=0, le=3)
    published_at: datetime | None
    last_reconciliation_run_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_collection_lifecycle(self) -> CollectionHealth:
        """Reject combinations that cannot be produced by the bounded state machine."""
        if self.collector_state == "PUBLISHED":
            if self.published_at is None or self.collection_issue_code is not None:
                raise ValueError("PUBLISHED requires publication without a collection issue")
            return self

        if (
            self.published_at is not None
            or self.first_discovered_at is None
            or self.last_reconciliation_run_id is None
        ):
            raise ValueError("non-published collection state requires discovery provenance")
        if self.collector_state == "DISCOVERED":
            if (
                self.collection_attempt_count != 0
                or self.last_attempted_at is not None
                or self.collection_issue_code is not None
            ):
                raise ValueError("DISCOVERED requires an unattempted clean state")
        elif self.collector_state == "COLLECTING":
            if (
                not 1 <= self.collection_attempt_count <= 3
                or self.last_attempted_at is None
                or self.collection_issue_code is not None
            ):
                raise ValueError("COLLECTING requires one claimed clean attempt")
        elif self.collector_state == "RETRYABLE":
            if (
                not 1 <= self.collection_attempt_count < 3
                or self.last_attempted_at is None
                or self.collection_issue_code is None
            ):
                raise ValueError("RETRYABLE requires a bounded failed attempt")
        elif (
            self.collection_attempt_count != 3
            or self.last_attempted_at is None
            or self.collection_issue_code is None
        ):
            raise ValueError("TERMINAL_FAILURE requires three failed attempts")
        return self


class RunList(PublicModel):
    """Recent run response, including the explicit setup-only state."""

    state: Literal["ready", "setup_required"]
    limit: int
    items: tuple[RunHealth, ...]
    required_bindings: tuple[str, ...] = ()


class NodeList(PublicModel):
    """Recent node response, including the explicit setup-only state."""

    state: Literal["ready", "setup_required"]
    limit: int
    items: tuple[NodeHealth, ...]
    required_bindings: tuple[str, ...] = ()


class CollectionList(PublicModel):
    """Recent collection/reconciliation states, including setup-only state."""

    state: Literal["ready", "setup_required"]
    limit: int
    items: tuple[CollectionHealth, ...]
    required_bindings: tuple[str, ...] = ()


class HealthResponse(PublicModel):
    """Process-liveness response that never starts a SQL warehouse."""

    status: Literal["alive"]
    check: Literal["process_liveness"]
    service: Literal["dbtobsb"]
    version: str


class ReadinessResponse(PublicModel):
    """Configuration-only readiness without a remote query side effect."""

    status: Literal["ready", "setup_required", "configuration_invalid"]
    check: Literal["resource_binding_configuration"]
    service: Literal["dbtobsb"]
    version: str
    required_bindings: tuple[str, ...] = ()


class ErrorDetail(PublicModel):
    """Static safe error detail."""

    code: ErrorCode
    message: str = Field(max_length=160)
    responsible_actor: ResponsibleActor
    action: str = Field(max_length=160)
    correlation_id: str = Field(pattern=r"^[0-9a-f]{16}$")


class ErrorResponse(PublicModel):
    """Static error envelope."""

    error: ErrorDetail
