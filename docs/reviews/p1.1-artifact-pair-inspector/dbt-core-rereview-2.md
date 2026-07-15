# Final dbt Core and artifact-contract re-review: P1.1 artifact-pair inspector

- Commit/diff: `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`
- Date: 2026-07-15
- Reviewer: Independent dbt Core and artifact-contract reviewer
- Verdict: `CHANGES_REQUIRED`
- Prior review: [`dbt-core-rereview.md`](dbt-core-rereview.md), commit `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
- Cloud activity: None. This re-review made no Databricks authentication, compute, warehouse, dbt execution against a warehouse, or cloud mutation.

## Sources checked

- [dbt documentation LLM index](https://docs.getdbt.com/llms.txt), then the indexed [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), [run-results](https://docs.getdbt.com/reference/artifacts/run-results-json), and [`dbt build`](https://docs.getdbt.com/reference/commands/build) references.
- dbt Core `v1.11.12` first-party source: [`BuildTask.RUNNER_MAP`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py#L35-L48), [`RunStatus` and `TestStatus`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/artifacts/schemas/results.py#L51-L84), [manifest v12 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json), and [run-results v6 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json).
- The immutable prior [initial review](dbt-core-review.md) and [first re-review](dbt-core-rereview.md), including the six finding acceptance conditions.

## Acceptance criteria reviewed

- One immutable `ISSUE_PRECEDENCE` and `MAX_REPORT_ISSUES` definition is shared by the inspector, public constructors, schema generator, and tests.
- `ArtifactPairSummary` rejects wrong containers/objects and noncanonical native status sets.
- `ArtifactPairReport` rejects invented state, wrong summary/issue/container types, invalid state cardinality, more than 20 distinct issues, duplicates, and noncanonical Python issue order before an instance exists.
- The generated Draft 2020-12 schema freezes exact issue variants and status fields, limits issues to 20, rejects duplicates, and rejects a primary issue when an earlier-precedence issue is also present.
- Every constructible public report serializes and validates against the bundled schema.
- The inspector remains a valid producer of that closed public report contract for all combinations of expected evidence failures, not only one issue at a time.
- The five previously resolved findings and the exact Core 1.11.12 collection/status semantics do not regress.
- Pair validity, native dbt outcome, and future capture state remain separate facts.

## DBT-P1.1-004 resolution assessment

### Controls that now pass

Commit `bedfaa9d9e803c168c2481d5e4f18264a1f40e01` correctly introduces shared immutable registry values:

- `ISSUE_PRECEDENCE` is a 26-code tuple in `capture/src/dbtobsb_capture/registry.py`.
- `MAX_REPORT_ISSUES` is defined once as 20; the inspector's compatibility alias points to it.
- Import-time validation proves that the static issue-template registry has exactly the shared code order.

The public constructors now reject the requested bad values:

| Probe | Result |
| --- | --- |
| Invented string state | Rejected with `ValueError` |
| Wrong non-null summary object | Rejected with `ValueError` |
| List instead of issue tuple | Rejected with `ValueError` |
| Non-`ArtifactPairIssue` tuple item | Rejected with `ValueError` |
| List instead of status-count tuple | Rejected with `ValueError` |
| Non-`NativeStatusCount` tuple item | Rejected with `ValueError` |
| 21 distinct closed issues | Rejected with `ValueError` |
| Duplicate closed issue | Rejected with `ValueError` |
| Reversed Python issue tuple | Rejected with `ValueError` |

The generated JSON Schema also behaves as intended. It contains exact closed variants for all 26 issues, `maxItems: 20`, `uniqueItems: true`, and conditional primary-precedence rules derived from the same tuple. Independent exhaustive pair probes checked all 325 earlier/later code pairs: every reversed-primary pair was rejected and every canonical pair was accepted. Raw JSON with 21 distinct issues, duplicate issues, or a later primary followed by an earlier issue was rejected. Every constructible canonical prefix from one through 20 issues validated against the bundled schema, as did the checked-in valid summaries and every single closed issue variant.

These changes close the direct constructor and raw-schema examples from the first re-review. They do not yet close the integration between the inspector and the strict constructor.

### DBT-P1.1-004 remains open: mixed invalid evidence can escape as an exception

- Severity: Medium
- Affected behavior: `capture/src/dbtobsb_capture/inspector.py`, `_invalid()` and every Python/CLI inspection path that detects more than one issue whose detection order differs from `ISSUE_PRECEDENCE`.
- Evidence: `_invalid()` deduplicates `codes` in encounter order and truncates them, then constructs `ArtifactPairReport`. It does not canonicalize those codes through the shared registry. `ArtifactPairReport.__post_init__()` now correctly rejects a noncanonical tuple. Two independent, schema-relevant probes therefore raised `ValueError: issues must follow the closed v1 precedence` instead of returning `PAIR_INVALID`:

  1. A manifest with a duplicate JSON key plus run-results containing invalid JSON. Parsing detects `DBT_MANIFEST_JSON_DUPLICATE_KEY` before `DBT_RUN_RESULTS_JSON_INVALID`, while the registry places the run-results invalid-JSON code first.
  2. A full-schema-valid pair mutated to have negative `elapsed_time` and a duplicate result ID. Semantic inspection detects `DBT_TIMING_INVALID` before `DBT_RESULTS_DUPLICATE_ID`, while the registry places the duplicate-ID code first.

- Why the existing gate misses it: The 85 tests exercise the requested constructor mutants and individual inspector failures, but they do not combine failure categories whose detection order crosses registry order. The property-based byte test overwhelmingly stops at parsing or schema validation and does not generate full-schema-valid multi-semantic mutants.
- User/system impact: The public API promises that expected evidence failures return a bounded `PAIR_INVALID` report. These ordinary invalid artifact combinations instead raise. The CLI catches the exception as `DBTOBSB_INTERNAL_ERROR`/exit 4 rather than emitting the deterministic invalid report/exit 10. A regulated consumer loses the documented issue code and recovery path for validly classifiable bad evidence.
- Required change: Canonicalize deduplicated issue codes through the shared precedence registry before truncation and construction. Prefer one shared helper that maps each closed code to its rank, sorts all unique codes, applies the 20-code bound after sorting, and is used by the inspector and any other report factory. Add Python and installed-CLI regressions for both mixed probes above, asserting deterministic canonical issue order, `PAIR_INVALID`, exit 10 for the CLI, static text, and no evidence leakage. Add a systematic mixed-issue test over stage/category pairs so constructor strictness cannot again turn expected invalid evidence into an internal error.
- Re-review outcome: `OPEN — CHANGES_REQUIRED`.

## Prior-finding regression check

### DBT-P1.1-001: Fixture source, sanitization, and provenance

- Outcome: No regression detected.
- Evidence: Fixture-generation code and the approved source are unchanged from the passing re-review. The full gate authenticated the source hash, regenerated every fixture in a temporary directory, and required a byte-identical comparison. The approved source still hashes to `14d1b3c6f54831fcc004bfad548578c0b955e03f41db786bba7f484391be419c`; provenance remains explicitly non-attesting and `runtime_evidence=false`.

### DBT-P1.1-002: JSON nesting safety

- Outcome: No nesting regression detected.
- Evidence: The depth bound and recursion catches are unchanged, and both Python and CLI deep-nesting tests pass. The new mixed-order defect is a report-production integration failure, not a return of the old recursion escape.

### DBT-P1.1-003: FIFO and device safety

- Outcome: No regression detected.
- Evidence: CLI code is unchanged. Timeout-bounded installed-command FIFO/device tests and sparse-file/symlink tests pass in the full gate.

### DBT-P1.1-005: Exact `BuildTask` collections and statuses

- Outcome: No regression detected.
- Evidence: The tagged source still lists model, snapshot, seed, test, unit test, saved query, exposure, and function. Run statuses remain `success`, `error`, `skipped`, `partial success`, and `no-op`; test statuses remain `pass`, `error`, `fail`, `warn`, and `skipped`. The collection, status, freshness-only rejection, unsupported-collection, and collision matrices all pass.

### DBT-P1.1-006: Installed schema-resource access

- Outcome: No regression detected.
- Evidence: Schema loading and its documentation are unchanged. The fresh-cache test still observes only the two checksum-pinned installed package-resource reads.

The vendored schema digests remain exact:

| Schema | SHA-256 |
| --- | --- |
| Core 1.11.12 manifest v12 | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` |
| run-results v6 | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` |

Valid-success and valid-error fixtures remain separately `PAIR_VALID`, native outcomes remain status counts rather than validity labels, and no local fixture or report claims a future capture state.

## Local and read-only checks

```text
git rev-parse HEAD
bedfaa9d9e803c168c2481d5e4f18264a1f40e01

scripts/check_capture.sh
85 passed in 2.46s
Ruff check: passed
Ruff format: passed
ty: passed
fixture authentication/regeneration/byte comparison: passed
runtime-only install and API example: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

shellcheck scripts/check_capture.sh
passed

bash -n scripts/check_capture.sh
passed

git diff --check e5969edd822ea5ccb31171f6c74e0ba690fd2294 bedfaa9d9e803c168c2481d5e4f18264a1f40e01
passed

closed-contract adversarial probes
invented state, wrong summary/issue/container/status objects: rejected
21 distinct issues: rejected by Python and JSON Schema
duplicate issue: rejected by Python and JSON Schema
reversed primary: rejected by Python and JSON Schema
canonical 20-issue report: schema-valid
all 325 canonical/reversed issue pairs: expected schema result

mixed inspector probes
duplicate-key manifest + invalid-JSON run-results:
  raised ValueError: issues must follow the closed v1 precedence
negative elapsed time + duplicate result ID:
  raised ValueError: issues must follow the closed v1 precedence
```

No reviewed implementation, documentation, evidence, fixture, or prior review file was changed by this re-review.

## Later qualification gates

The following remain genuinely later gates after the current defect is fixed:

1. Qualify the complete Python 3.12.3/Linux lock in the actual Azure Databricks execution image.
2. Execute and capture real Azure Databricks `dbt build` success, failure, cancellation, timeout, retry, and repair cases.
3. Qualify archive layout/retrieval, structured logs, AttemptKey correlation, and capture-state classification in their planned parts.
4. Re-qualify schemas, collections, and statuses before adding another dbt Core or adapter support row.

## Resolution and re-review

- Resolution: Commit `bedfaa9d9e803c168c2481d5e4f18264a1f40e01` closes the direct public-constructor and raw-JSON mutants from `DBT-P1.1-004`, and the five previously resolved findings remain intact. It does not canonicalize inspector-produced multi-issue reports before applying the strict constructor.
- Validation: The full 85-test gate and requested constructor/schema probes pass; two independent mixed-evidence probes reproduce the remaining present defect.
- Re-review verdict: `CHANGES_REQUIRED`. Re-review a new immutable commit after inspector/report-factory issue ordering is canonicalized and mixed Python plus installed-CLI regression tests pass with the complete gate.
