# dbt Core and artifact-contract re-review: P1.1 artifact-pair inspector

- Commit/diff: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
- Date: 2026-07-15
- Reviewer: Independent dbt Core and artifact-contract reviewer
- Verdict: `CHANGES_REQUIRED`
- Prior review: [`dbt-core-review.md`](dbt-core-review.md), commit `054527a6721c36af6a9e99218120b39920bd0fed`
- Cloud activity: None. This re-review did not authenticate to Databricks, start compute, run dbt against a warehouse, or mutate a cloud resource.

## Sources checked

- [dbt documentation LLM index](https://docs.getdbt.com/llms.txt), then its indexed [artifact overview](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest reference](https://docs.getdbt.com/reference/artifacts/manifest-json), [run-results reference](https://docs.getdbt.com/reference/artifacts/run-results-json), and [`dbt build` reference](https://docs.getdbt.com/reference/commands/build).
- dbt Core `v1.11.12` first-party source: [`BuildTask.RUNNER_MAP`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py#L35-L44), [`RunStatus` and `TestStatus`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/artifacts/schemas/results.py#L51-L71), [manifest v12 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json), and [run-results v6 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json).
- dbt public schema registry: [manifest v12](https://schemas.getdbt.com/dbt/manifest/v12/index.html) and [run-results v6](https://schemas.getdbt.com/dbt/run-results/v6/index.html).
- First-party adapter/release evidence: [dbt-databricks `v1.12.2`](https://github.com/databricks/dbt-databricks/tree/v1.12.2) and exact PyPI release metadata for [dbt-core 1.11.12](https://pypi.org/project/dbt-core/1.11.12/), [dbt-databricks 1.12.2](https://pypi.org/project/dbt-databricks/1.12.2/), [dbt-common 1.37.5](https://pypi.org/project/dbt-common/1.37.5/), [dbt-adapters 1.23.0](https://pypi.org/project/dbt-adapters/1.23.0/), [dbt-protos 1.0.541](https://pypi.org/project/dbt-protos/1.0.541/), and [dbt-spark 1.10.3](https://pypi.org/project/dbt-spark/1.10.3/).

## Acceptance criteria reviewed

- Resolve `DBT-P1.1-001` through `DBT-P1.1-006` against the actual immutable commit, not the author's resolution claims alone.
- Authenticate the reviewed synthetic fixture source before projection, regenerate byte-identical fixtures, reject altered origins/free text, and describe package versions and digests as compatibility context rather than runtime attestation.
- Bound JSON nesting before recursive decoding and convert decoder/schema recursion exhaustion into deterministic invalid evidence through both Python and CLI surfaces.
- Reject FIFOs, devices, links, and over-limit inputs without blocking or exposing paths and exception text.
- Make the exported Python types and the published report schema one closed v1 protocol: exact states, compatibility fields, native statuses, issue variants, cardinality, uniqueness, and primary-issue precedence.
- Cover all eight resource types in the pinned `BuildTask`, all five run statuses, all five test statuses, the freshness-only status rejection, every unsupported collection, and supported/supported plus supported/unsupported ambiguity.
- State the installed checksum-pinned schema-resource reads honestly while preserving the stronger no-caller-path, no-network, no-dbt, and no-Databricks boundary.
- Preserve the distinction among pair validity, native dbt outcome, and future capture state.

## Authoritative contract check

The tagged Core source still has exactly these `BuildTask` resource types: model, snapshot, seed, test, unit test, saved query, exposure, and function. The accepted run statuses remain `success`, `error`, `skipped`, `partial success`, and `no-op`; test statuses remain `pass`, `error`, `fail`, `warn`, and `skipped`. `runtime error` remains freshness-only and is correctly rejected for this `build` contract.

The vendored schemas are byte-identical to the Core `v1.11.12` tag:

| Schema | Recomputed SHA-256 |
| --- | --- |
| manifest v12 | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` |
| run-results v6 | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` |

The current generic manifest-v12 registry bytes still hash to `f29ac66b0ea66b46575da0a5da66b2716f06f25295044234304e16631773ea4c`, while current generic run-results-v6 bytes match the tagged digest. The implementation is therefore right to validate the checksum-pinned Core tag bytes while requiring the standard v12/v6 metadata URLs.

All six wheel digests in fixture provenance still match the exact PyPI releases. A fresh temporary Python 3.12.13 environment with the six exact package versions ran `dbt parse` against the synthetic fixture project without a Databricks connection. It produced manifest v12, Core `1.11.12`, adapter `databricks`, 761 macros, all required supported and unsupported resource inventories, and zero errors against the vendored tagged manifest schema. This remains local compatibility evidence, not Python 3.12.3/Linux or Azure Databricks runtime attestation.

## Finding-by-finding resolution

### DBT-P1.1-001: Fixture provenance and sanitization

- Re-review outcome: `RESOLVED`
- Evidence: `generate_artifact_pair_fixtures.py` now requires the exact SHA-256 of `capture/tests/fixture_source/approved-manifest.json`, validates that document against the full pinned schema, checks exact Core/schema/adapter metadata, and checks the expected supported and deliberately unsupported inventory before creating any output. The altered-origin/free-text adversarial test is rejected before an output directory exists. The quality gate regenerates all three fixtures in a temporary directory and requires a byte-identical tree comparison. The approved source, generated manifest, and recorded `source_manifest_sha256` all equal `14d1b3c6f54831fcc004bfad548578c0b955e03f41db786bba7f484391be419c`.
- Truthfulness: Provenance now says `runtime_evidence=false`, `runtime_attestation=false`, and explicitly says the source manifest does not attest the listed transitive versions or wheel digests. Generator-host fields are fixed rather than silently varying. The evidence record separately identifies the actual fixture-preparation interpreter as 3.12.13 and the planned candidate as 3.12.3.
- Preserve: Keep the reviewed-source hash update, full-schema check, inventory check, adversarial rejection, and byte-identical regeneration in the same reviewed change whenever fixture source changes.

### DBT-P1.1-002: Bounded JSON nesting

- Re-review outcome: `RESOLVED`
- Evidence: The inspector scans structural depth outside JSON strings and rejects depth over 256 before recursive decoding. It also catches `RecursionError` at decoding and schema-validation boundaries. The checked-in Python and CLI regressions pass. An independent 10,000-level, roughly 20 KiB probe returned `DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED` rather than raising or entering the CLI internal-error path.
- Preserve: Retain both the explicit work bound and the defensive recursion catches; neither alone expresses the complete bounded-input contract.

### DBT-P1.1-003: Nonblocking FIFO and device handling

- Re-review outcome: `RESOLVED`
- Evidence: `_read_regular_file()` opens with `O_NONBLOCK`, `O_NOFOLLOW` where available, and `O_CLOEXEC`, then performs `fstat()` before any read. The installed-command tests reject a FIFO and `/dev/null` within a two-second subprocess bound, reject a sparse file over 128 MiB, and preserve static exit-3 output without paths or exceptions. Symlink rejection remains covered.
- Preserve: Keep the installed-entry-point subprocess tests; an in-process mock would not prove that opening a FIFO cannot block.

### DBT-P1.1-004: Closed public Python and JSON contract

- Re-review outcome: `OPEN — CHANGES_REQUIRED`
- Severity: Medium
- Resolution present: The generated JSON schema is materially improved. It closes compatibility fields and status keys, uses exact issue variants with static text, rejects legacy redundant `primary_issue` and `result_count`, enforces state/summary/issue cardinality, and caps issues at 20. `ArtifactPairIssue`, `NativeStatusCount`, and `ArtifactPairSummary` now reject invented issue text/statuses and invalid summary values.
- Remaining evidence: The exported `ArtifactPairReport` constructor still does not enforce that `state` is a `PairState`, that issues are unique and bounded, or that their order follows the documented frozen precedence. Independent probes produced these results:

  - `ArtifactPairReport("INVENTED", None, ())` constructed successfully; `to_dict()` then raised `AttributeError` instead of rejecting construction with a static contract error.
  - A report containing 21 copies of one valid issue constructed and serialized even though its own v1 JSON schema rejects the result for both `maxItems` and uniqueness.
  - Two distinct closed issues in reverse stage order constructed, serialized, and validated against the JSON schema, even though `issues[0]` defines the primary issue and the reference says precedence is frozen.

- User/system impact: The inspector itself emits canonical reports, but the package explicitly exports and documents `ArtifactPairReport` as a public type. A typed or plugin caller can construct a value that is not in the published v1 protocol, receive a late non-contract exception, or serialize JSON rejected by the package's own schema. The Python and JSON boundaries are therefore not yet equivalent or closed.
- Required change: In `ArtifactPairReport.__post_init__`, reject non-`PairState` state values, noncontract summary/issue objects, more than 20 issues, duplicates, and noncanonical issue precedence before an instance exists. Define precedence from one shared immutable registry used by the inspector, constructors, schema generator/tests, and reference. Add negative public-constructor tests for invented state, wrong object types, 21 issues, duplicate issues, and reversed known issues; require every constructible report to serialize successfully and validate against the bundled v1 schema. If arbitrary public construction is not supported, stop exporting/documenting the constructors and provide a validated parsing/factory boundary instead.

### DBT-P1.1-005: Pinned `BuildTask` collection and status coverage

- Re-review outcome: `RESOLVED`
- Evidence: The test matrix now exercises model, seed, snapshot, data test, unit test, saved query, exposure, and function resolution. It covers every tagged run and test status, rejects freshness-only `runtime error`, rejects sources/macros/metrics/semantic models individually, and exercises supported/supported plus supported/unsupported identifier collisions. Duplicate IDs, inner-ID disagreement, resource-aware status rejection, timing, failure counts, and issue bounding also remain covered. The implementation map and status registries match the exact tagged Core source.
- Preserve: New Core or adapter versions must receive a new reviewed collection/status contract rather than silently extending this v1 map.

### DBT-P1.1-006: Installed schema-resource access

- Re-review outcome: `RESOLVED`
- Evidence: The docstring, product plan, README, and Python reference now state the actual boundary: the function does not open caller-supplied paths or external services, while validation reads only installed checksum-pinned package schema resources. A fresh-validator-state test observes exactly those two package-resource reads and still returns `PAIR_VALID`.
- Preserve: Do not regress the narrower guarantee into an absolute “no filesystem access” claim.

## Positive controls preserved

- Full tagged schemas are applied before semantic interpretation, and their installed bytes are checksum-verified.
- Strict JSON rejects duplicate keys and non-finite constants; ordinary issue text remains static and evidence-safe.
- Valid-success and valid-error fixtures are both `PAIR_VALID`; native dbt status is a separate bounded summary.
- Invalid pairs have no native-outcome summary, and no fixture or local parse claims a future capture state.
- Reports retain neither raw bytes nor SQL, messages, paths, environment values, relation/resource/project identity, or invocation identity.
- Synthetic provenance remains `runtime_evidence=false`; candidate dependency evidence remains explicitly non-attesting.
- CLI output remains noninteractive, deterministic, no-color, and stable across normal invalid-evidence paths.

## Local and read-only checks

```text
git rev-parse HEAD
e5969edd822ea5ccb31171f6c74e0ba690fd2294

scripts/check_capture.sh
81 passed in 2.41s
Ruff check: passed
Ruff format: passed
ty: passed
fixture regeneration and byte-identical comparison: passed
runtime-only install and API example: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

shellcheck scripts/check_capture.sh
passed

bash -n scripts/check_capture.sh
passed

git diff --check 054527a6721c36af6a9e99218120b39920bd0fed e5969edd822ea5ccb31171f6c74e0ba690fd2294
passed

fresh exact-package dbt parse
Python 3.12.13; dbt-core 1.11.12; dbt-databricks 1.12.2
dbt-common 1.37.5; dbt-adapters 1.23.0
dbt-protos 1.0.541; dbt-spark 1.10.3
manifest v12; adapter databricks; 761 macros; 0 tagged-schema errors

independent adversarial probes
10,000-level nesting: stable invalid report
invented ArtifactPairReport state: constructed, then AttributeError on serialization
21 duplicate issues: constructed and serialized, rejected by bundled schema
reversed distinct issues: constructed, serialized, accepted by bundled schema
```

The worktree contained another reviewer's untracked `databricks-rereview.md`; this reviewer did not alter it or any implementation, documentation, evidence, fixture, or initial review file.

## Later qualification gates

These are genuinely later product gates and do not weaken the current `CHANGES_REQUIRED` result:

1. Qualify the complete Python 3.12.3/Linux dependency lock in the actual Azure Databricks execution image.
2. Execute real native `dbt build` cases and qualify archive retrieval/layout for success, dbt failure, early failure, cancellation, timeout, retry, and repair.
3. Keep structured logs, archive completeness, AttemptKey correlation, and capture-state classification outside this local pair-validity result until their own reviewed parts exist.
4. Re-qualify schema bytes, collection maps, and status families for every future dbt Core or adapter support row.

## Resolution and re-review

- Resolution: Commit `e5969edd822ea5ccb31171f6c74e0ba690fd2294` fully resolves `DBT-P1.1-001`, `DBT-P1.1-002`, `DBT-P1.1-003`, `DBT-P1.1-005`, and `DBT-P1.1-006`. It partially resolves `DBT-P1.1-004`, but the exported top-level report type can still represent values outside the closed v1 JSON protocol.
- Validation: The complete local gate, exact schema/source comparisons, exact package parse, PyPI digest checks, and targeted adversarial probes are recorded above.
- Re-review verdict: `CHANGES_REQUIRED`. Re-review a new immutable commit after the public report construction boundary is made equivalent to the closed JSON contract and the new constructor-level negative tests pass with the full gate.
