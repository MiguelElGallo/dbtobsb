"""Restricted allowlisted projection from one strictly accepted artifact pair.

Unlike :mod:`dbtobsb_capture.contracts`, these values contain dbt resource identifiers
and belong only in the restricted evidence tables.  They deliberately exclude SQL,
messages, relation names, arbitrary adapter responses, environment values, and dbt vars.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dbtobsb_capture.contracts import ArtifactPairReport, PairState
from dbtobsb_capture.inspector import (
    _mapping,
    _parse_json,
    _resource_match,
    inspect_artifact_pair,
)


@dataclass(frozen=True, slots=True)
class InvocationProjection:
    """Allowlisted invocation facts from a valid run-results document."""

    invocation_id: str
    generated_at: str
    elapsed_time: float
    dbt_version: str
    adapter_type: str
    command: str
    result_count: int
    status_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class NodeResultProjection:
    """Allowlisted result facts for one executed dbt resource."""

    unique_id: str
    resource_type: str
    status: str
    execution_time: float
    failures: int | None


@dataclass(frozen=True, slots=True)
class ArtifactPairProjection:
    """Restricted normalized facts projected from one accepted pair."""

    invocation: InvocationProjection
    node_results: tuple[NodeResultProjection, ...]


@dataclass(frozen=True, slots=True)
class ArtifactPairInspection:
    """Public safe report plus an optional restricted projection."""

    report: ArtifactPairReport
    projection: ArtifactPairProjection | None


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise RuntimeError("accepted artifact projection invariant failed")
    return value


def _required_number(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise RuntimeError("accepted artifact projection invariant failed")
    return float(value)


def inspect_and_project_artifact_pair(
    *, manifest: bytes, run_results: bytes
) -> ArtifactPairInspection:
    """Strictly validate then project only the closed restricted-field allowlist.

    Projection reparses the same immutable byte strings with the inspector's exact
    duplicate-rejecting UTF-8 JSON decoder.  Spark and SQL never reinterpret rejected
    evidence; they receive only these typed values after ``PAIR_VALID``.
    """
    report = inspect_artifact_pair(manifest=manifest, run_results=run_results)
    if report.state is PairState.INVALID:
        return ArtifactPairInspection(report=report, projection=None)

    manifest_document, manifest_error = _parse_json(manifest, component="manifest")
    run_document, run_error = _parse_json(run_results, component="run_results")
    if (
        manifest_error is not None
        or run_error is not None
        or manifest_document is None
        or run_document is None
        or report.summary is None
    ):
        raise RuntimeError("accepted artifact parse invariant failed")

    run_metadata = _mapping(run_document.get("metadata"))
    results = run_document.get("results")
    if not isinstance(results, list):
        raise RuntimeError("accepted run-results projection invariant failed")

    projected_nodes: list[NodeResultProjection] = []
    for value in results:
        if not isinstance(value, dict):
            raise RuntimeError("accepted dbt result projection invariant failed")
        unique_id = _required_string(value, "unique_id")
        _, _, _, _, resource_type = _resource_match(manifest_document, unique_id)
        if resource_type is None:
            raise RuntimeError("accepted resource projection invariant failed")
        failures = value.get("failures")
        projected_nodes.append(
            NodeResultProjection(
                unique_id=unique_id,
                resource_type=resource_type,
                status=_required_string(value, "status"),
                execution_time=_required_number(value, "execution_time"),
                failures=failures
                if isinstance(failures, int) and not isinstance(failures, bool)
                else None,
            )
        )

    summary = report.summary
    invocation = InvocationProjection(
        invocation_id=_required_string(run_metadata, "invocation_id"),
        generated_at=_required_string(run_metadata, "generated_at"),
        elapsed_time=_required_number(run_document, "elapsed_time"),
        dbt_version=summary.dbt_version,
        adapter_type=summary.adapter_type,
        command=summary.command,
        result_count=summary.result_count,
        status_counts=tuple((item.status, item.count) for item in summary.status_counts),
    )
    return ArtifactPairInspection(
        report=report,
        projection=ArtifactPairProjection(
            invocation=invocation,
            node_results=tuple(projected_nodes),
        ),
    )
