# Python API

P1.1 exposes one deterministic function and immutable report types from `dbtobsb_capture`. For installation and a guided first result, use [Inspect an artifact pair](../tutorials/inspect-an-artifact-pair.md#4-use-the-python-api).

<a id="run-a-first-inspection"></a>

## Function

```text
inspect_artifact_pair(*, manifest: bytes, run_results: bytes) -> ArtifactPairReport
```

<!-- BEGIN: python-public-contract -->

| Contract item | Exact P1.1 value |
| --- | --- |
| `manifest` | Keyword-only `bytes`; at most 134,217,728 bytes (128 MiB); JSON nesting at most 256 structural levels. |
| `run_results` | Keyword-only `bytes`; at most 134,217,728 bytes (128 MiB); JSON nesting at most 256 structural levels. |
| Return | `ArtifactPairReport`; expected evidence failures, including size and nesting failures, return `PAIR_INVALID` instead of raising. |
| Non-byte input | Raises static `TypeError`. |
| Internal invariant failure | May raise a static exception without artifact content. |
| External access | Opens no caller path; reads only installed checksum-pinned schemas; no network, environment, clock, subprocess, dbt, or Databricks access. |
| Raw-input classification | Potentially sensitive and Personal Data-bearing; caller-owned lifecycle and custody apply. |
| Native status vocabulary | Exactly `error`, `fail`, `no-op`, `partial success`, `pass`, `skipped`, `success`, and `warn`. |
| Invalid issue cardinality | One to 20 unique issues in canonical precedence order. |

<!-- END: python-public-contract -->

Size and depth failures use the static `*_SIZE_LIMIT_EXCEEDED` and `*_JSON_NESTING_LIMIT_EXCEEDED` issues. Follow [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs).

## Example

This complete example is also checked in as [inspect_valid_fixture.py](../../../capture/examples/inspect_valid_fixture.py). It uses only the sanitized repository fixture.

<!-- BEGIN: inspect-valid-fixture.py -->

```python
"""Copy-ready Python API first-success example used by the documentation gate."""

from __future__ import annotations

import json
from pathlib import Path

from dbtobsb_capture import inspect_artifact_pair

fixture = Path("capture/tests/fixtures/artifact_pair/valid_success")
report = inspect_artifact_pair(
    manifest=(fixture / "manifest.json").read_bytes(),
    run_results=(fixture / "run_results.json").read_bytes(),
)
print(report.state.value)
print(json.dumps(report.to_dict(), ensure_ascii=True, separators=(",", ":"), sort_keys=True))
```

<!-- END: inspect-valid-fixture.py -->

The exact output is:

<!-- BEGIN: inspect-valid-fixture-output -->

```text
PAIR_VALID
{"issues":[],"pair_state":"PAIR_VALID","schema_version":"dbtobsb.artifact-pair-report.v1","summary":{"adapter_type":"databricks","command":"build","dbt_version":"1.11.12","manifest_schema":"https://schemas.getdbt.com/dbt/manifest/v12.json","run_results_schema":"https://schemas.getdbt.com/dbt/run-results/v6.json","status_counts":{"success":1}}}
```

<!-- END: inspect-valid-fixture-output -->

The example reads files before calling the API. The API itself never opens a caller path.

## Public types

<!-- BEGIN: python-public-types -->

| Type | Public fields and invariant |
| --- | --- |
| `PairState` | `PAIR_VALID` or `PAIR_INVALID`. |
| `ArtifactPairReport` | Frozen and slotted. `state: PairState`; `summary: ArtifactPairSummary &#124; None`; `issues: tuple[ArtifactPairIssue, ...]`; `primary_issue: ArtifactPairIssue &#124; None`; `to_dict()`. Valid means one summary and zero issues; invalid means no summary and 1–20 unique canonical issues. |
| `ArtifactPairSummary` | Frozen and slotted. `manifest_schema: str`; `run_results_schema: str`; `dbt_version: str`; `adapter_type: str`; `command: str`; `status_counts: tuple[NativeStatusCount, ...]`; computed positive `result_count: int`. |
| `NativeStatusCount` | `status: str` from the closed vocabulary below; `count: int` greater than zero. Status entries are unique and canonically ordered. |
| `ArtifactPairIssue` | Static `code: str`; `component: str`; `field: str`; `observed_category: str`; `impact: str`; and `next_action: str`; never an observed value. |

<!-- END: python-public-types -->

The closed native-status vocabulary is `error`, `fail`, `no-op`, `partial success`, `pass`, `skipped`, `success`, and `warn`. The matrix below determines which family applies to a resolved result.

## BuildTask result compatibility

<!-- BEGIN: buildtask-compatibility -->

| Manifest collection | Accepted resource type | Accepted native status family |
| --- | --- | --- |
| `nodes` | `model`, `seed`, `snapshot` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `nodes` | `test` | Test: `error`, `fail`, `pass`, `skipped`, `warn` |
| `unit_tests` | `unit_test` | Test: `error`, `fail`, `pass`, `skipped`, `warn` |
| `saved_queries` | `saved_query` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `exposures` | `exposure` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `functions` | `function` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |

<!-- END: buildtask-compatibility -->

<!-- BEGIN: buildtask-unsupported -->

Results that resolve only through `sources`, `macros`, `metrics`, or `semantic_models` are unsupported. Freshness-only `runtime error` is not an accepted `build` result status. A result that collides across supported collections, or across supported and unsupported collections, is ambiguous; P1.1 never chooses a resource manually.

<!-- END: buildtask-unsupported -->

<!-- BEGIN: status-counts-semantics -->

`summary.status_counts` counts every accepted entry in this pair's `run_results.results`, grouped by its preserved native status. It does not count the manifest's complete enabled-project inventory. It is not an overall dbt success label, an outer Databricks or Lakeflow task state, or a future capture-completeness state.

<!-- END: status-counts-semantics -->

`ArtifactPairReport.to_dict()` returns the versioned JSON shape `dbtobsb.artifact-pair-report.v1`. It omits redundant `primary_issue` and `result_count` fields: `issues[0]` is primary under the shared v1 precedence registry, and the result total is the sum of the integer values in the closed `summary.status_counts` object. The JSON Schema conditionally rejects a first issue when an earlier-precedence issue is also present. This makes inconsistent duplicates impossible in the machine contract. The report never retains raw input bytes. Its ordinary representation and dictionary exclude SQL, result messages, adapter responses, variables, environment values, relation names, paths, resource IDs, project names, and invocation IDs.

## Sensitive input boundary

The safe report does not make its raw inputs safe to retain or share. `manifest.json` and `run_results.json` can contain Personal Data, secrets, SQL, messages, paths, topology, and identities. The API receives caller-owned bytes and does not persist, copy, upload, delete, or govern the caller's originals or other copies. Use policy-approved storage and follow [Handle raw dbt artifacts safely](../how-to/handle-raw-dbt-artifacts-safely.md).

## Supported P1.1 pair

- manifest schema URL: `https://schemas.getdbt.com/dbt/manifest/v12.json`
- run-results schema URL: `https://schemas.getdbt.com/dbt/run-results/v6.json`
- dbt Core metadata: `1.11.12`
- manifest adapter type: `databricks`
- run-results command: `build`
- at least one uniquely resolved result

The schemas are vendored and checksum-pinned. The manifest bytes come from the exact Core 1.11.12 tag because the generic v12 endpoint is mutable; artifact metadata still uses the standard v12 URL.

## Result interpretation

A valid report always has one summary and no issues. An invalid report has no summary and between one and 20 unique, canonically ordered issues. Public constructors reject wrong object types, invented state/status/code/text values, duplicates, over-limit issue sets, and noncanonical precedence before an instance exists. A dbt result such as `error`, `fail`, or `warn` can appear in a valid summary because evidence validity is not job success. For invalid evidence, use the first item in `issues` or the Python `primary_issue` convenience property, then follow its static next action.
