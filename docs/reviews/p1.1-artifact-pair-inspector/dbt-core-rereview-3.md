# Focused dbt Core and artifact-contract closure re-review: P1.1

- Commit/diff: `75b7d41316216a3b18a3c56ff0c98f133f7aab89`
- Date: 2026-07-15
- Reviewer: Independent dbt Core and artifact-contract reviewer
- Verdict: `PASS_WITH_FOLLOW_UP`
- Prior review: [`dbt-core-rereview-2.md`](dbt-core-rereview-2.md), commit `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`
- Cloud activity: None. This re-review made no Databricks authentication, warehouse, compute, dbt runtime, or cloud mutation.

## Sources checked

- [dbt documentation LLM index](https://docs.getdbt.com/llms.txt), then the indexed [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), [run-results](https://docs.getdbt.com/reference/artifacts/run-results-json), and [`dbt build`](https://docs.getdbt.com/reference/commands/build) references.
- dbt Core `v1.11.12` first-party source: [`BuildTask.RUNNER_MAP`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py#L35-L48), [`RunStatus` and `TestStatus`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/artifacts/schemas/results.py#L51-L84), [manifest v12 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json), and [run-results v6 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json).
- The immutable [initial review](dbt-core-review.md), [first re-review](dbt-core-rereview.md), and [mixed-invalid integration re-review](dbt-core-rereview-2.md).

## Acceptance criteria reviewed

- `_invalid()` deduplicates every detected code, orders all unique codes through shared `ISSUE_PRECEDENCE`, truncates only after ordering, and constructs a closed report without raising.
- The mixed parse case returns canonical `PAIR_INVALID`: run-results invalid JSON precedes manifest duplicate-key evidence.
- The full-schema-valid mixed semantic case returns canonical `PAIR_INVALID`: duplicate result ID precedes invalid timing.
- The installed CLI returns exit 10, valid JSON on stdout, empty stderr, and canonical issues for both cases rather than exit 4/internal error.
- Systematic coverage proves canonicalization for every pair of the 26 closed issue codes, including duplicate input codes.
- Direct constructor and generated-JSON-schema closure from commit `bedfaa9…` remains intact.
- Fixture provenance, nesting safety, FIFO/device safety, exact Core collection/status semantics, installed schema-resource access, and validity/outcome/capture separation do not regress.

## Closure result

The sole remaining present defect is resolved.

`capture/src/dbtobsb_capture/inspector.py` now derives `_ISSUE_RANK` from the immutable shared `ISSUE_PRECEDENCE`. `_invalid()` performs these operations in the required order:

1. deduplicate the supplied codes;
2. sort every unique code by the shared rank;
3. apply `MAX_REPORT_ISSUES` only after sorting; and
4. construct the strict `ArtifactPairReport`.

An independent stress probe supplied all 26 issue codes in reverse order, then supplied them all again. The returned report contained exactly the first 20 registry codes in canonical order, proving that truncation does not preserve an arbitrary detection prefix.

### Mixed parse evidence

Input:

- manifest with a duplicate JSON key;
- run-results containing invalid JSON.

Observed Python result:

```text
PAIR_INVALID
DBT_RUN_RESULTS_JSON_INVALID
DBT_MANIFEST_JSON_DUPLICATE_KEY
```

The returned dictionary validates against the bundled report schema. No exception escaped.

Observed installed-CLI result:

```text
exit: 10
pair_state: PAIR_INVALID
issues: DBT_RUN_RESULTS_JSON_INVALID, DBT_MANIFEST_JSON_DUPLICATE_KEY
stderr: empty
```

### Mixed semantic evidence

Input:

- the valid-success full-schema artifact pair;
- `elapsed_time` changed to `-1`;
- the existing result duplicated.

Observed Python result:

```text
PAIR_INVALID
DBT_RESULTS_DUPLICATE_ID
DBT_TIMING_INVALID
```

The returned dictionary validates against the bundled report schema. No exception escaped.

Observed installed-CLI result:

```text
exit: 10
pair_state: PAIR_INVALID
issues: DBT_RESULTS_DUPLICATE_ID, DBT_TIMING_INVALID
stderr: empty
```

### Systematic ordering evidence

The checked-in test iterates all `26 choose 2 = 325` issue pairs. For every pair it supplies `[later, earlier, later]` to the report factory and requires exactly `[earlier, later]`. The independent re-review probe repeated the matrix and observed zero failures.

## Contract and prior-finding regression check

- Public constructors still reject invented state, wrong summary/issue/container/status-count types, 21 distinct issues, duplicates, and noncanonical Python issue order.
- The generated JSON Schema still freezes all 26 exact issue variants, caps issues at 20, requires uniqueness, and rejects reversed primary precedence. Canonical mixed inspector reports validate against it.
- Fixture-source authentication, adversarial source rejection, byte-identical regeneration, and explicitly non-attesting provenance pass unchanged.
- Deep JSON remains a bounded `PAIR_INVALID`; it does not raise or become an internal CLI error.
- Installed FIFO/device/sparse-file and symlink controls pass unchanged.
- The exact `BuildTask` collection/status matrices and unsupported/collision cases pass unchanged. The supported Core contract remains model, snapshot, seed, test, unit test, saved query, exposure, and function; run/test statuses remain identical to the tagged `v1.11.12` enums.
- Fresh validation still reads only the two installed checksum-pinned schema resources. Their hashes remain:

| Schema | SHA-256 |
| --- | --- |
| Core 1.11.12 manifest v12 | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` |
| run-results v6 | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` |

- Valid-success and valid-error fixtures both remain `PAIR_VALID`, with native outcome represented separately. No P1.1 result claims a future capture state or live Databricks qualification.

## Local and read-only checks

```text
git rev-parse HEAD
75b7d41316216a3b18a3c56ff0c98f133f7aab89

scripts/check_capture.sh
90 passed in 3.24s
Ruff check: passed
Ruff format: passed
ty: passed
fixture authentication/regeneration/byte comparison: passed
runtime-only install and API example: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

independent focused probes
mixed parse Python: canonical PAIR_INVALID
mixed semantic Python: canonical PAIR_INVALID
mixed parse installed CLI: exit 10, empty stderr
mixed semantic installed CLI: exit 10, empty stderr
all 325 issue pairs: 0 canonicalization failures
all 26 reversed and duplicated: sorted before 20-code truncation
both mixed reports: bundled-schema valid

shellcheck scripts/check_capture.sh
passed

bash -n scripts/check_capture.sh
passed

git diff --check bedfaa9d9e803c168c2481d5e4f18264a1f40e01 75b7d41316216a3b18a3c56ff0c98f133f7aab89
passed
```

No reviewed implementation, documentation, evidence, fixture, or prior review file was changed by this re-review.

## Non-blocking later qualification gates

These follow-ups belong to later product parts and are not defects in the portable P1.1 inspector:

1. P2 runtime owner: qualify real Azure Databricks archive retrieval/layout and native `dbt build` success, failure, cancellation, timeout, retry, and repair cases.
2. Runtime compatibility owner before declaring a qualified support row: validate the complete Python 3.12.3/Linux dependency lock in the actual Databricks execution image.
3. P2 and later owners: implement and independently review structured logs, AttemptKey correlation, archive completeness, and capture-state classification without changing P1.1 pair-validity meaning.
4. Compatibility owner for each future support row: re-qualify schema bytes, `BuildTask` collections, and status families before accepting another Core or adapter version.

## Findings

No present P1.1 dbt Core or artifact-contract defect was found in commit `75b7d41316216a3b18a3c56ff0c98f133f7aab89` within this focused closure scope.

## Resolution and re-review

- Resolution: Commit `75b7d41316216a3b18a3c56ff0c98f133f7aab89` canonicalizes all unique issue codes before the shared maximum and strict report construction. It resolves the mixed-invalid Python and CLI failure from `dbt-core-rereview-2.md`.
- Validation: The complete 90-test gate, independent Python and installed-CLI probes, all-pair matrix, sort-before-truncation probe, schema validation, and prior-finding regression checks pass.
- Re-review verdict: `PASS_WITH_FOLLOW_UP`. P1.1 is acceptable from the dbt Core/artifact-contract perspective; only the explicitly later runtime and compatibility qualification gates above remain.
