"""Typed collector contracts shared by acquisition, custody, and persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from dbtobsb_capture import ArchiveCapture
from dbtobsb_contracts import AttemptIdentity


class RetrievalState(StrEnum):
    """Whether the native Databricks archive was retrieved."""

    RETRIEVED = "RETRIEVED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class AttemptContext:
    """Installed dynamic-reference context for one observed dbt task attempt."""

    workspace_id: int
    observed_job_id: int
    observed_job_run_id: int
    dbt_task_run_id: int
    observed_task_key: str
    repair_count: int
    execution_count: int

    def __post_init__(self) -> None:
        positive = (
            self.workspace_id,
            self.observed_job_id,
            self.observed_job_run_id,
            self.dbt_task_run_id,
            self.execution_count,
        )
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in positive
        ):
            raise ValueError("attempt identifiers must be positive integers")
        if (
            not isinstance(self.repair_count, int)
            or isinstance(self.repair_count, bool)
            or self.repair_count < 0
        ):
            raise ValueError("repair_count must be a nonnegative integer")
        if (
            not self.observed_task_key
            or len(self.observed_task_key) > 100
            or not self.observed_task_key.replace("_", "").isalnum()
        ):
            raise ValueError("observed_task_key must be a bounded alphanumeric key")

    def as_dbt_attempt_identity(self) -> AttemptIdentity:
        """Map native dynamic references to the shared immutable path identity."""
        return AttemptIdentity(
            workspace_id=self.workspace_id,
            job_id=self.observed_job_id,
            job_run_id=self.observed_job_run_id,
            task_run_id=self.dbt_task_run_id,
            repair_count=self.repair_count,
            execution_count=self.execution_count,
        )


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Ephemeral signed download material; never safe for logs or persistence."""

    url: str = field(repr=False)
    headers: dict[str, str] = field(repr=False)
    allow_internal_databricks_http: bool = field(default=False, repr=False)


@dataclass(frozen=True, slots=True)
class VolumeArtifactReference:
    """Closed customer-local attempt root used to assemble one bounded archive."""

    source_root: str = field(repr=False)
    archive_root: str = field(repr=False)
    include_deps: bool


type ArtifactSource = ArtifactReference | VolumeArtifactReference


@dataclass(frozen=True, slots=True)
class ObservedTaskEvidence:
    """Allowlisted Jobs facts plus an optional ephemeral artifact reference."""

    task_start_time: datetime | None
    task_end_time: datetime | None
    lakeflow_result_state: str
    attempt_number: int
    logs_truncated: bool | None
    artifact_reference: ArtifactSource | None


@dataclass(frozen=True, slots=True)
class CollectionRecord:
    """One normalized attempt ready for idempotent Delta publication."""

    context: AttemptContext
    observed: ObservedTaskEvidence
    retrieval_state: RetrievalState
    capture: ArchiveCapture
    raw_archive_locator: str | None
    collected_at: datetime
    normalized_digest: str


class JobsEvidenceReader(Protocol):
    """Fetch and correlate one installed dbt task from Jobs APIs."""

    def read(self, context: AttemptContext) -> ObservedTaskEvidence: ...


class ArchiveDownloader(Protocol):
    """Consume one ephemeral artifact reference into bounded closed bytes."""

    def download(self, reference: ArtifactSource) -> bytes: ...


class RawArchiveStore(Protocol):
    """Persist exact closed bytes and verify readback."""

    def preserve(self, *, context: AttemptContext, archive: bytes) -> str: ...


class EvidenceSink(Protocol):
    """Idempotently publish one normalized record."""

    def publish(self, record: CollectionRecord) -> None: ...
