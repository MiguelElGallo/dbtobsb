# Python API

P1.1 exposes one pure function and immutable report types from `dbtobsb_capture`.

## Function

```python
from dbtobsb_capture import inspect_artifact_pair

report = inspect_artifact_pair(
    manifest=manifest_bytes,
    run_results=run_results_bytes,
)
```

```text
inspect_artifact_pair(*, manifest: bytes, run_results: bytes) -> ArtifactPairReport
```

Both arguments are keyword-only `bytes`. The function performs no filesystem, network, environment, clock, subprocess, dbt, or Databricks access. Expected evidence failures return `PAIR_INVALID`; they do not raise. Non-`bytes` inputs raise `TypeError`, and internal invariant failures may raise an exception without including artifact content.

## Public types

| Type | Purpose |
| --- | --- |
| `PairState` | `PAIR_VALID` or `PAIR_INVALID`. |
| `ArtifactPairReport` | Frozen, slotted top-level result with `state`, optional `summary`, `issues`, `primary_issue`, and `to_dict()`. |
| `ArtifactPairSummary` | Allowlisted facts emitted only for a valid pair. |
| `NativeStatusCount` | One allowlisted native dbt status and its count. |
| `ArtifactPairIssue` | Static code, category, impact, and recovery text; no observed value. |

`ArtifactPairReport.to_dict()` returns the versioned JSON shape `dbtobsb.artifact-pair-report.v1`. The report never retains raw input bytes. Its ordinary representation and dictionary exclude SQL, result messages, adapter responses, variables, environment values, relation names, paths, resource IDs, project names, and invocation IDs.

## Supported P1.1 pair

- manifest schema URL: `https://schemas.getdbt.com/dbt/manifest/v12.json`
- run-results schema URL: `https://schemas.getdbt.com/dbt/run-results/v6.json`
- dbt Core metadata: `1.11.12`
- manifest adapter type: `databricks`
- run-results command: `build`
- at least one uniquely resolved result

The schemas are vendored and checksum-pinned. The manifest bytes come from the exact Core 1.11.12 tag because the generic v12 endpoint is mutable; artifact metadata still uses the standard v12 URL.

## Result interpretation

A valid report always has one summary and no issues. An invalid report has no summary and at least one issue, bounded to 20 under a frozen precedence order. A dbt result such as `error`, `fail`, or `warn` can appear in a valid summary because evidence validity is not job success.
