# dbt Core and artifact-contract review: P1.1 artifact-pair inspector

- Commit/diff: `054527a6721c36af6a9e99218120b39920bd0fed`
- Date: 2026-07-15
- Reviewer: Independent dbt Core and artifact-contract reviewer
- Verdict: `CHANGES_REQUIRED`
- Cloud activity: None. The review used only local files, temporary local Python environments, dbt's public schema registry, official documentation, first-party source repositories, and package-index release metadata. It did not authenticate to or mutate Databricks.

## Sources checked

- [dbt documentation LLM index](https://docs.getdbt.com/llms.txt), followed by the indexed [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), [run results](https://docs.getdbt.com/reference/artifacts/run-results-json), and [`dbt build`](https://docs.getdbt.com/reference/commands/build) references.
- dbt Core `v1.11.12` first-party source: [`BuildTask.RUNNER_MAP`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py), [result status definitions](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/artifacts/schemas/results.py), [manifest v12 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json), and [run-results v6 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json).
- dbt public schema registry: [manifest v12](https://schemas.getdbt.com/dbt/manifest/v12/index.html) and [run-results v6](https://schemas.getdbt.com/dbt/run-results/v6/index.html).
- dbt Databricks `v1.12.2` first-party source and release metadata: [repository tag](https://github.com/databricks/dbt-databricks/tree/v1.12.2) and [PyPI release](https://pypi.org/project/dbt-databricks/1.12.2/).
- Exact PyPI release metadata for the proposed candidate set: [dbt-core 1.11.12](https://pypi.org/project/dbt-core/1.11.12/), [dbt-databricks 1.12.2](https://pypi.org/project/dbt-databricks/1.12.2/), [dbt-common 1.37.5](https://pypi.org/project/dbt-common/1.37.5/), [dbt-adapters 1.23.0](https://pypi.org/project/dbt-adapters/1.23.0/), [dbt-protos 1.0.541](https://pypi.org/project/dbt-protos/1.0.541/), and [dbt-spark 1.10.3](https://pypi.org/project/dbt-spark/1.10.3/).

## Acceptance criteria reviewed

- Both inputs are parsed as strict JSON, bounded in size, validated against the complete checksum-pinned dbt schemas, and reduced to evidence-safe static output.
- Pair semantics establish the exact supported dbt Core version, schema URLs, adapter, `build` command, shared invocation identity, nonempty results, unique result IDs, manifest resolution, status family, timing shape, and failure metadata without equating pair validity with dbt success.
- Result IDs resolve through every collection used by the pinned `BuildTask`: `nodes` for models, seeds, snapshots, and data tests; `unit_tests`; `saved_queries`; `exposures`; and `functions`. Unsupported manifest collections cannot silently satisfy a result.
- Accepted statuses match the pinned Core `RunStatus` and `TestStatus` definitions.
- Schema bytes and recorded hashes are exact, and the proposed dependency evidence is exact and explicitly candidate-only rather than a live Databricks qualification.
- Synthetic fixtures are deterministic, sanitized, provenance-bound, and incapable of importing arbitrary source evidence.
- The public Python and JSON contracts enforce the versioned state, status, issue-code, precedence, and static-text promises made by the documentation.
- CLI input handling is bounded, non-disclosing, and rejects links, pipes, devices, and other non-regular inputs without waiting indefinitely.
- Tests cover every semantic branch and the documented separation among pair validity, native dbt outcome, and later capture state.

## Contract assessment

The core pair logic is directionally sound. The vendored manifest schema is byte-identical to dbt Core `v1.11.12`'s manifest v12 schema and hashes to `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3`; the vendored run-results schema is byte-identical to the tagged and current v6 schema and hashes to `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf`. Pinning the manifest bytes to the reviewed Core tag is preferable to silently accepting later registry drift.

The implementation's collection map matches the eight resource types in `BuildTask.RUNNER_MAP`: model, snapshot, seed, test, unit test, saved query, exposure, and function. Its accepted run statuses (`success`, `error`, `skipped`, `partial success`, and `no-op`) and test statuses (`pass`, `error`, `fail`, `warn`, and `skipped`) match the exact tagged Core enums. The implemented pair checks cover the frozen schema URLs and versions, exact Core and adapter, `args.which=build`, invocation equality, nonempty results, duplicate IDs, cross-collection resolution and ambiguity, resource identity, status family, timing, and failure metadata.

A fresh Python 3.12.13 environment installed the six exact proposed versions and successfully parsed a minimal Databricks project into manifest v12 with adapter `databricks`; its 761 macros produced no tagged-schema errors. Every recorded wheel digest for those six releases matched current PyPI release metadata. This is useful candidate evidence only: it is not a complete Linux runtime lock, an executed `dbt build`, or Azure Databricks qualification, and the repository's evidence generally preserves that distinction.

The ordinary inspector output also keeps the three facts separate: `PAIR_VALID` describes compatibility of the artifact pair, a valid report can still summarize native dbt `error`, and no local fixture claims a complete future capture. Those semantics should be preserved.

The current part nevertheless has six present-tense contract defects. Under the repository review policy, they require changes rather than a follow-up-only verdict.

## Findings

### DBT-P1.1-001: The fixture generator can forge provenance and retain source-only sensitive content

- Severity: High
- Evidence: `capture/scripts/generate_fixtures.py` reconstructs top-level metadata and provenance with hard-coded candidate versions and hashes, but copies selected resource dictionaries wholesale from the supplied manifest. In an adversarial local probe, a source manifest changed to dbt `9.9.9` and adapter `snowflake` produced generated metadata claiming dbt `1.11.12` and `databricks`; a canary inserted into a source node's `description` and `meta` remained in the generated fixture. The generator does not prove that its source was produced by the recorded package set, validate the source against the exact tagged schemas before rewriting it, or field-allowlist copied resources. Its provenance also records the generator host's Python version, system, and machine dynamically, so the complete output is not deterministic across supported generation hosts.
- User/system impact: A maintainer can unintentionally publish a fixture that claims a reviewed dbt/adapter origin it did not have and that carries arbitrary project content from a real manifest. This defeats both the provenance and sanitization boundaries used to justify regulated, shareable evidence.
- Required change: Make fixture construction field-by-field from an allowlisted synthetic specification, or strictly authenticate and validate an approved synthetic source before use. Never rewrite contradictory source origin into asserted provenance. Derive package versions and wheel digests from a verified lock/environment or require an independently verified provenance input; reject any mismatch. Add an adversarial test that injects canaries into every copied free-text, config, metadata, and extension field and proves they cannot survive. Define which generator-host fields are intentionally variable or remove them from the deterministic artifact.

### DBT-P1.1-002: A small, deeply nested JSON input escapes the promised evidence-failure result

- Severity: Medium
- Evidence: Strict parsing rejects duplicate keys and non-finite constants, but the parser catches `UnicodeDecodeError`, `JSONDecodeError`, and `ValueError`, not `RecursionError`. A roughly 20 KiB document containing 10,000 nested arrays is below the 128 MiB input cap yet raises `RecursionError` from the public Python API. The CLI converts that to its internal-error path rather than a stable invalid-evidence result.
- User/system impact: Untrusted artifact bytes can violate the documented rule that expected evidence failures return an `ArtifactPairReport` rather than raise. They also produce the wrong CLI category and can consume disproportionate stack/CPU resources.
- Required change: Add an explicit nesting/work budget before or during decoding and convert decoder and schema-recursion exhaustion into a static, evidence-safe invalid report. Cover the Python API and installed CLI with below-size-limit deeply nested inputs, and prove bounded completion and the expected stable exit/category.

### DBT-P1.1-003: A FIFO can block the CLI before it is rejected as non-regular

- Severity: Medium
- Evidence: `capture/src/dbtobsb_capture/cli.py` opens an input with `O_RDONLY` before calling `fstat()` to enforce the regular-file rule. Opening a FIFO for reading without `O_NONBLOCK` waits for a writer. A subprocess probe supplying a FIFO as the manifest remained blocked beyond a one-second timeout instead of returning `DBTOBSB_INPUT_READ_ERROR`/exit 3. Symlink and post-open regular-file checks do not address this pre-check wait.
- User/system impact: An accidentally or deliberately supplied pipe can hang a job or application worker indefinitely, contradicting the advertised bounded local-file boundary.
- Required change: Open with a nonblocking, no-follow descriptor and reject non-regular modes before reading, while preserving race resistance and descriptor cleanup. Add timeout-bounded installed-CLI tests for FIFOs and representative devices in addition to links, missing files, and over-limit regular files.

### DBT-P1.1-004: The published JSON schema does not enforce the versioned report contract

- Severity: Medium
- Evidence: The public report schema accepts invented status keys, inconsistent `count`/`result_count` values, arbitrary `DBT_*` issue codes and arbitrary impact/action text, and a `primary_issue` unrelated to `issues[0]`. Local schema probes validated all of those mutants with zero errors. The public dataclasses are similarly constructible with values the inspector never emits, while the JSON reference says codes, text, precedence, and shape are versioned consumer contracts.
- User/system impact: A downstream regulated consumer can validate a semantically false or evidence-bearing report as P1.1-compliant. The current schema authenticates a loose container, not the documented v1 protocol.
- Required change: Freeze the exact state/status/code vocabulary in the v1 schema; express issue records as closed variants with static category, impact, and action for each code; and enforce or remove promises such as primary-first and aggregate consistency that the schema cannot validate. Apply equivalent validation at public Python construction/serialization boundaries. Add negative schema tests for invented codes/statuses/text, mismatched primary issues, and inconsistent aggregates, plus positive tests for every emitted issue and status.

### DBT-P1.1-005: Exit evidence does not exercise every pinned `BuildTask` collection and status branch

- Severity: Medium
- Evidence: The implementation map is correct, but the checked-in schema-valid semantic tests exercise models across run statuses, unit tests across test statuses, and an exposure path; they do not independently prove successful resolution and resource/status validation for seeds, snapshots, data tests in `nodes`, saved queries, and functions. Unsupported-collection and ambiguity coverage is also selective rather than exhaustive for sources, macros, metrics, and semantic models. Consequently, the claim that every pair invariant is covered is broader than the test evidence.
- User/system impact: A future refactor can break a less common but valid `dbt build` result type while all P1.1 gates remain green. Functions are especially relevant to Core 1.11, and saved-query/exposure behavior cannot safely be inferred from model coverage.
- Required change: Add minimal full-schema fixtures or generated cases for every exact `BuildTask.RUNNER_MAP` resource/collection path and every applicable tagged status family. Add schema-valid negative cases for each unsupported collection, supported/unsupported and supported/supported collisions, declared-resource mismatches, duplicate results, and malformed timing/failure branches. Keep the assertions on static output and absence of raw evidence.

### DBT-P1.1-006: The public no-filesystem API claim is literally false

- Severity: Low
- Evidence: `inspect_artifact_pair()` calls `validator_for()`, whose first call reads the packaged schema bytes through `importlib.resources`. The function does not open caller-supplied paths and has no dbt, Databricks, network, subprocess, environment, or clock dependency, but its docstring and public documentation state that it performs no filesystem access at all.
- User/system impact: The implementation remains customer-local, but callers can select a read-denied or unusual packaged runtime based on a stronger purity guarantee than the code provides and then receive an internal failure.
- Required change: Narrow all public and plan wording to the true boundary—no caller-artifact path access and no external/runtime-service access—or load/embed the checksum-pinned schemas in a way that makes the stronger promise true. Add a fresh-validator-state test for whichever boundary is selected.

## Positive controls to preserve

- Complete tagged schemas are validated before semantic checks, and their embedded bytes are checksum-verified.
- JSON decoding rejects duplicate object keys and `NaN`/`Infinity` constants; ordinary issue text is static and does not echo observed values.
- Valid-error and valid-success pairs remain equally `PAIR_VALID`; native dbt outcome is represented separately in bounded counts.
- Synthetic evidence is labeled `runtime_evidence=false`, and neither a local parse nor a candidate dependency set is described as live Azure Databricks qualification.
- Inspector reports retain neither raw bytes nor SQL, dbt messages, paths, invocation IDs, project/resource names, relation names, or environment values.
- The exact pinned collection and status maps agree with dbt Core `v1.11.12` source.

## Local and read-only validation

All implementation checks were run against commit `054527a6721c36af6a9e99218120b39920bd0fed` before this review record was added.

```text
scripts/check_capture.sh
55 passed
Ruff check: passed
Ruff format: passed
ty: passed
wheel build and isolated installed console-entry-point smoke: passed
DBTOBSB_CAPTURE_CHECK_PASSED

shellcheck scripts/check_capture.sh
passed

fresh Python 3.12.13 candidate parse
dbt-core 1.11.12
dbt-databricks 1.12.2
dbt-common 1.37.5
dbt-adapters 1.23.0
dbt-protos 1.0.541
dbt-spark 1.10.3
manifest schema v12; adapter databricks; 761 macros; 0 schema errors

tagged schema-byte checks
manifest v12: b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3
run-results v6: 1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf

candidate release checks
all six recorded wheel SHA-256 values matched current PyPI release metadata

adversarial probes
fixture source-origin contradiction was rewritten into asserted candidate provenance
source-only canary survived fixture generation
10,000-level nested JSON raised RecursionError
FIFO input remained blocked beyond the subprocess timeout
invented status/code/text/primary/aggregate report mutants passed the public JSON schema
```

Python 3.12.13 was the locally available interpreter; the review does not claim exact reproduction of the workflow's declared Python 3.12.3 runtime. No `dbt build` was executed against Databricks, so the candidate dependency parse remains compatibility evidence, not runtime qualification.

## Resolution and re-review

- Resolution: No resolution is present in commit `054527a6721c36af6a9e99218120b39920bd0fed`; findings `DBT-P1.1-001` through `DBT-P1.1-006` remain open.
- Validation: The existing 55-test quality gate, schema/hash checks, exact dependency parse, source comparison, and wheel-digest checks pass. The adversarial fixture, nesting, FIFO, and public-schema probes demonstrate current contract failures that the existing gate does not catch.
- Re-review verdict: `CHANGES_REQUIRED`. Re-review a new immutable commit after all six current defects are resolved and the full local gate plus the new adversarial and collection-completeness tests pass.
