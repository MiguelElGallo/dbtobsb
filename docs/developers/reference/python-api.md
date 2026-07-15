# Python API

P1.1 exposes one deterministic function and immutable report types from `dbtobsb_capture`.

## Run a first inspection

After completing the runtime-only sync in the [tutorial](../tutorials/inspect-an-artifact-pair.md), run this copy-ready example from the repository root:

```bash
uv run --project capture --no-sync python capture/examples/inspect_valid_fixture.py
```

The checked-in script contains the complete API example: it reads the sanitized fixture into bytes, calls `inspect_artifact_pair`, prints `PairState`, and serializes the safe dictionary with deterministic JSON settings.

The exact output is:

```text
PAIR_VALID
{"issues":[],"pair_state":"PAIR_VALID","schema_version":"dbtobsb.artifact-pair-report.v1","summary":{"adapter_type":"databricks","command":"build","dbt_version":"1.11.12","manifest_schema":"https://schemas.getdbt.com/dbt/manifest/v12.json","run_results_schema":"https://schemas.getdbt.com/dbt/run-results/v6.json","status_counts":{"success":1}}}
```

The example reads files before calling the API. The API itself never opens a caller path.

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

Both arguments are keyword-only `bytes`. The function opens no caller-supplied path and reads only its installed checksum-pinned schema resources. It performs no network, environment, clock, subprocess, dbt, or Databricks access. Expected evidence failures—including over-deep JSON—return `PAIR_INVALID`; they do not raise. Non-`bytes` inputs raise `TypeError`, and internal invariant failures may raise an exception without including artifact content.

## Public types

| Type | Purpose |
| --- | --- |
| `PairState` | `PAIR_VALID` or `PAIR_INVALID`. |
| `ArtifactPairReport` | Frozen, slotted top-level result with `state`, optional `summary`, `issues`, `primary_issue`, and `to_dict()`. |
| `ArtifactPairSummary` | Allowlisted facts emitted only for a valid pair; `result_count` is computed from the status counts. |
| `NativeStatusCount` | One allowlisted native dbt status and its count. |
| `ArtifactPairIssue` | Static code, category, impact, and recovery text; no observed value. |

`ArtifactPairReport.to_dict()` returns the versioned JSON shape `dbtobsb.artifact-pair-report.v1`. It omits redundant `primary_issue` and `result_count` fields: `issues[0]` is primary, and the result total is the sum of the integer values in the closed `summary.status_counts` object. This makes inconsistent duplicates impossible in the machine contract. The report never retains raw input bytes. Its ordinary representation and dictionary exclude SQL, result messages, adapter responses, variables, environment values, relation names, paths, resource IDs, project names, and invocation IDs.

## Supported P1.1 pair

- manifest schema URL: `https://schemas.getdbt.com/dbt/manifest/v12.json`
- run-results schema URL: `https://schemas.getdbt.com/dbt/run-results/v6.json`
- dbt Core metadata: `1.11.12`
- manifest adapter type: `databricks`
- run-results command: `build`
- at least one uniquely resolved result

The schemas are vendored and checksum-pinned. The manifest bytes come from the exact Core 1.11.12 tag because the generic v12 endpoint is mutable; artifact metadata still uses the standard v12 URL.

## Result interpretation

A valid report always has one summary and no issues. An invalid report has no summary and at least one issue, bounded to 20 under a frozen precedence order. Every public constructor rejects invented status, code, category, impact, or action values. A dbt result such as `error`, `fail`, or `warn` can appear in a valid summary because evidence validity is not job success. For invalid evidence, use the first item in `issues` or the Python `primary_issue` convenience property, then follow its static next action.
