# Independent dbt Core documentation accuracy review: P1.1

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `2b76abbd565271b30f37fdb1e3f00d76185e8dc4` |
| Commit tree | `24d4fb122ee6a167bf2ae529034ee17013b30024` |
| Commit parent | `7ce722cddfed42f1e96741bb07b6cd8762127f22` |
| Commit subject | `docs: record p1.1 documentation closure reviews` |
| Review date | 2026-07-15 |
| Review role | Independent dbt Core artifact and documentation subject-matter reviewer |
| Verdict | **CHANGES_REQUIRED** |
| Blocking findings | 2 |
| Cloud activity | None. No Databricks, Azure, authentication, warehouse, compute, or paid-resource path was used. |

The pinned inspector implementation is consistent with dbt Core 1.11.12 for the artifact schemas, `BuildTask` resource set, native run/test status families, and invocation-ID equality. The reader-facing documentation also correctly separates pair validity from dbt success and future capture completeness, and it treats raw artifacts as potentially sensitive.

The documentation is not yet acceptable as the dbt compatibility contract, however. It does not publish the exact supported resource/collection-to-status matrix or the precise scope of `status_counts`, even though its issue actions refer readers to that missing contract. Its invocation-mismatch recovery also treats a shared target directory as sufficient pairing evidence, while dbt can overwrite artifacts in that directory across invocations. That same route uses “trusted pair” language for checks that establish internal contract validity, not provenance or authenticity.

## Exact review scope and hashes

The report reviews the path-sorted 16-file P1.1 reader route and its planning/source claims at the immutable commit above. SHA-256 values were calculated from the commit blobs, not from mutable working-tree content.

```text
0be609fbbb0239d7dbb1142dcd630fa94f0a7b13ba9af7940b65f08d9d48c5cf  README.md
d664454aa140415fc822398a217d62bb57cffc41c647fee46da98213fa0e6e19  capture/README.md
3221cd5c38a3b5d9fdace49cb19a07efdc945fec9d3a0af1bfebbe0c5911e48e  docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md
653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990  docs/developers/explanation/raw-artifact-custody.md
196ae6032b6ea8e2fe19b84cdb6ae9e2bdb15f90af41e0202e02ed033ca2eae8  docs/developers/how-to/diagnose-an-invalid-artifact-pair.md
59f10d13d45d85a13eb4d903bfc76e245621f09d13348b2c8b1676af46fedd46  docs/developers/how-to/handle-raw-dbt-artifacts-safely.md
8867bd6d28b38d7c22bfe1bb2c2affead9b737f64311b8c7d2c519544d6c0ceb  docs/developers/index.md
462117759f5eb09588f843e91c603a1e7ef8ef405d99d71423fe3229582a8aab  docs/developers/reference/cli-report-and-exit-codes.md
d6163c7b4ae07db5bb6b033f20c527a48f9912b7a4b382b80ad39807cdac1dc2  docs/developers/reference/python-api.md
4a005dacbbdb3d89f1c97d21b1ad9e5f98eb148f622fa7e0dfa53d52f2d79296  docs/developers/tutorials/inspect-an-artifact-pair.md
670dc2b74185492ea1de9e06fc0d64ee7c1fb3bef3b402ceeee3e4496e1125e9  docs/evidence/p1.1-local-artifact-pair-2026-07-15.md
2b6fece0e8ca96e2407e14f1bd8e5df90dbad39495feaefbd74914541bbc7fe2  docs/index.md
b753b2d568e246bceefefe806d1ebd5bb47eadf8e7a32d95a557f03471e0623e  docs/plans/documentation-plan.md
00e410370497edc3b55bfb2ee9491eeb91512dca64b81d44543c0f04c72076eb  docs/plans/product-plan.md
4189c82644fdbc93dc11faf1f652831ffab5e54ffd320e2c28af1b788283f95b  docs/research/source-register.md
af0f8b9cc8b717689f9b9c2ba2217db6df56c7f355508e1e2198b3b9cb3cb382  docs/reviews/README.md
```

The SHA-256 of that exact record stream, including two spaces between digest and path and one trailing newline per record, is:

```text
4bd4ae3e459fba0e6694042d20b73bc17a1a23abe558e3e9e885c3ef6f2828f8
```

These implementation and executable-contract files were used only as corroborating inputs. Their hashes also come from the reviewed commit:

```text
6f312022cfbf58b4a11232963e06e406e81da9c8ba42f55c331529f5a257b5f9  capture/src/dbtobsb_capture/contracts.py
eccae1da909abeba0638f78a5001e6fb059481b74fe8fff8e4e2f1aac37208be  capture/src/dbtobsb_capture/inspector.py
561f7a81bcb0fe7a9d1d2a8364228d39f88f758a83c34889c7e4480f60d5c1a6  capture/src/dbtobsb_capture/registry.py
d9a03b0c53e3346031520abef9b22094733402d64bbed1337665623621965029  capture/src/dbtobsb_capture/schemas.py
9eca896c07ec7b228f777dfaa1f8046169acf728ea68a7686b9d916327e06f80  capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json
b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3  capture/src/dbtobsb_capture/schemas/manifest-v12.json
1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf  capture/src/dbtobsb_capture/schemas/run-results-v6.json
203f4a7ba9f445330c9a9807fc19b15cec125a7d4241b80fe4d9380005cd795b  capture/tests/test_artifact_pair.py
3653fe330b9dd660f959803c98337053980c9ea24cd30be904025f01ff90b8f9  capture/tests/test_documentation.py
92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911  scripts/check_capture.sh
aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0  scripts/check_markdown_links.py
```

Their path-sorted record-stream SHA-256 is `3c7b132dffe948181803b23e3aa2c5e250513df5efa1568fe55ebab872f704f9`. The nine valid-success, valid-dbt-failure, and invalid-invocation fixture/report blobs have aggregate record-stream SHA-256 `5a7499e3fad054b2d0e8fc4fd3a2025d3cdfb7695c93f53e49c8103469ebee3e`.

This new report is outside every reviewed input and aggregate. No reviewed source file was edited by this review.

## Official dbt sources checked

Current official documentation was refreshed through the [dbt documentation LLM index](https://docs.getdbt.com/llms.txt) and the first-party pages it lists:

- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts) for common metadata, including schema version, dbt version, adapter type, environment, and invocation identity;
- [manifest.json](https://docs.getdbt.com/reference/artifacts/manifest-json) for full enabled-project inventory and the Core-to-manifest-schema mapping;
- [run_results.json](https://docs.getdbt.com/reference/artifacts/run-results-json) for completed-invocation results, `args.which`, result fields, and the rule that only executed nodes appear;
- [`dbt build`](https://docs.getdbt.com/reference/commands/build) for its single manifest/run-results pair and failure/skip behavior; and
- [JSON artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) for the shared default `target/` directory, invocation-specific target-path override, and explicit warning that another operation can overwrite earlier artifacts.

Exact pinned behavior was checked against dbt Core `v1.11.12` first-party source:

- [`BuildTask.RUNNER_MAP`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py#L35-L48);
- [`RunStatus`, `TestStatus`, and `FreshnessStatus`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/artifacts/schemas/results.py#L51-L84);
- the [tagged manifest v12 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json); and
- the [tagged run-results v6 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json).

The remote tag resolved to `fa444c13bb5cd46a55656d553b1cd57c8ec19f01`. Independent byte checks produced:

| Source | SHA-256 | Result |
| --- | --- | --- |
| Vendored manifest v12 | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` | Matches the exact `v1.11.12` tag. |
| Exact `v1.11.12` manifest v12 | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` | Match. |
| Current generic manifest v12 endpoint | `f29ac66b0ea66b46575da0a5da66b2716f06f25295044234304e16631773ea4c` | Differs from the pinned tag, as the project documentation warns. |
| Vendored run-results v6 | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` | Matches the exact tag and current generic endpoint. |

## Contract assessment

| Review area | Result | Evidence-based assessment |
| --- | --- | --- |
| Artifact schemas and dbt version | **PASS** | Manifest v12, run-results v6, and dbt Core `1.11.12` are exact; the tagged manifest bytes are correctly pinned instead of treating the mutable generic URL as supply-chain identity. |
| `BuildTask` resources and statuses | **FAIL** | Implementation is correct, but the public reference supplies only the union of eight statuses and does not publish which resources or status family P1.1 accepts. |
| Invocation pairing | **FAIL** | Equality of parseable `metadata.invocation_id` values is implemented, but the primary recovery action incorrectly presents directory co-location as sufficient. |
| `status_counts` meaning | **FAIL** | Examples are numerically correct and preserve native values, but the reference does not define the counts as accepted `run_results.results` entries only, distinct from the full manifest inventory and outer job/capture state. |
| Valid evidence versus dbt failure | **PASS** | Both the valid-success and valid-error fixtures remain `PAIR_VALID`; `error=1` is explicitly not described as dbt success. |
| Sensitive raw fields | **PASS** | The raw-input pages correctly warn about SQL, messages, paths, topology, environment/context, identities, Personal Data, and possible secrets while keeping the report allowlisted. |
| Supported and unsupported claims | **FAIL** | Version/adapter/command are explicit; exact supported collections/resource types, unsupported collections, and freshness-only status exclusion are absent from reader-facing reference. |
| Recovery instructions | **FAIL** | Most instructions correctly say to recollect unmodified evidence, but invocation mismatch recovery is not safe against normal target-directory reuse. |
| Capture completeness | **PASS** | The tutorial, explanation, API/CLI references, and product plan consistently state that P1.1 does not prove archive retrieval, Databricks attempt evidence, structured-log coverage, or `COMPLETE`. |

## Findings

### DOCDBT-P1.1-001 — Medium — The exact `BuildTask` compatibility and `status_counts` contract is absent

The [Python API reference](../../developers/reference/python-api.md) publishes the union vocabulary—`error`, `fail`, `no-op`, `partial success`, `pass`, `skipped`, `success`, and `warn`—and says only that a resource type determines whether run or test statuses are valid. Its “Supported P1.1 pair” section lists schemas, Core version, adapter, command, and non-empty resolution, but no collection/resource/status mapping. The [CLI issue registry](../../developers/reference/cli-report-and-exit-codes.md) then directs readers to “the supported dbt build contract,” “BuildTask,” and “the matched resource type” without defining those terms anywhere in the implemented developer route. An immutable `git grep` over `docs/developers` found no `saved_query`, `unit_test`, `semantic_models`, `FreshnessStatus`, `runtime error`, `RUN_STATUSES`, or `TEST_STATUSES` entry.

The pinned implementation and exact Core tag require this matrix:

| Manifest collection | Accepted resource type | Accepted status family |
| --- | --- | --- |
| `nodes` | `model`, `seed`, `snapshot` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `nodes` | `test` | Test: `error`, `fail`, `pass`, `skipped`, `warn` |
| `unit_tests` | `unit_test` | Test: `error`, `fail`, `pass`, `skipped`, `warn` |
| `saved_queries` | `saved_query` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `exposures` | `exposure` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `functions` | `function` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |

Results that resolve only through `sources`, `macros`, `metrics`, or `semantic_models` are unsupported. Freshness-only `runtime error` is not a valid `build` result status. A result that collides across supported or supported/unsupported collections is ambiguous rather than manually selected.

The reference must also state that `summary.status_counts` counts every accepted entry in this pair's `run_results.results`, grouped by its preserved native status. It is not a count of all manifest resources: official dbt documentation says the manifest is full enabled-project inventory while run results contain only executed nodes. It is also not the Lakeflow task state, an overall dbt success label, or a future capture-completeness state.

**Impact:** A dbt owner cannot determine from the public contract whether a saved query, exposure, function, unit test, source, or freshness result is supported; nor can an integrator interpret a count against the manifest inventory without inspecting source code. The issue and recovery text is therefore not self-contained at the exact compatibility boundary it claims to document.

**Required resolution:**

1. Add the exact table above, unsupported collections, ambiguity behavior, and freshness exclusion to the Python or a dedicated compatibility reference; link the CLI issue rows and diagnosis route to that stable anchor.
2. Define `status_counts` as counts over accepted executed-result records and explicitly distinguish it from manifest inventory, overall dbt success, outer Databricks state, and capture state.
3. Extend the documentation contract test to derive and verify the collection/resource-to-status matrix, unsupported collections, and count scope. The current test freezes only the union vocabulary, so it can pass while this compatibility contract is missing.

### DOCDBT-P1.1-002 — Medium — Target-directory recovery and “trusted pair” wording overstate pairing evidence

The tutorial's exact invalid-pair output and the CLI issue registry prescribe:

```text
next_action: Collect both artifacts from the same build target directory.
```

The diagnosis table similarly says to recollect from “the same completed build target directory.” The inspector does not validate directory identity. It validates that both artifacts contain equal, parseable `metadata.invocation_id` values. The official dbt JSON-artifact configuration explicitly notes that another operation can overwrite artifacts from a previous step in the target directory, and official run-results documentation says different invocations produce different run results. A manifest from invocation A and run-results from invocation B can therefore occupy or be copied from the same directory at different times.

The checked-in mismatch fixture demonstrates the contract boundary: its two co-located files contain `11111111-1111-4111-8111-111111111111` and `22222222-2222-4222-8222-222222222222`. The CLI correctly returns exit `10` and `DBT_INVOCATION_ID_MISMATCH`, then emits the insufficient same-directory action.

The [pair-validity explanation](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md) also asks whether the files form a “trusted pair.” P1.1 proves full-schema validity and a bounded set of internal cross-file invariants. It performs no provenance authentication, signature verification, customer-evidence hashing, custody attestation, AttemptKey correlation, or archive-completeness check. The tutorial's more precise “internally valid” and “satisfy the pinned artifact-pair contract” language accurately describes the implemented guarantee.

**Impact:** An operator can repeatedly recollect a mixed pair from a reused target path, and a regulated reader can interpret `PAIR_VALID` as authenticity or provenance evidence that P1.1 does not possess. The first problem makes the primary recovery action operationally unreliable; the second expands the evidence claim beyond the implementation.

**Required resolution:**

1. Replace same-directory recovery with “collect both closed artifacts from the same completed pinned `dbt build` invocation,” preserving the inspector's invocation-ID equality check.
2. In the future job/capture procedure, give each invocation an isolated target path or atomically close/copy the pair before any later dbt command can reuse its target. Directory location may be custody context; it is not the pairing key.
3. Replace the unqualified “trusted pair” question with “contract-valid, internally consistent pair,” and state that P1.1 does not prove origin, authenticity, absence of post-generation modification, custody, archive completeness, or capture completeness.
4. Update the static issue template, exact tutorial/CLI output, diagnosis text, and their binding tests together. The current green documentation test intentionally freezes the same misleading primary action; it does not validate recovery against dbt target-overwrite semantics. Apply the repository's contract-version decision rule if changing this versioned issue text requires one.

## Accurate boundaries retained

The required changes do not weaken the substantial accurate material already present:

- A valid pair with native `error`, `fail`, or `warn` results remains valid evidence; it is not reclassified as dbt success.
- `status_counts` preserves native dbt values rather than inventing a product success state.
- Schema URLs, exact Core version, Databricks adapter path, and `build` command are explicit.
- The exact Core 1.11.12 manifest schema bytes are vendored and checksum-pinned, and the generic mutable endpoint is not misrepresented as immutable.
- Raw artifact fields are treated as potentially Personal Data-bearing and sensitive, while the ordinary report omits SQL, messages, adapter response, variables, environment values, relations, paths, project/resource identity, and invocation identity.
- P1.1 is consistently described as local inspection. It does not claim live Databricks runtime qualification, artifact retrieval, log coverage, capture completeness, or a future Databricks-local custody boundary.
- Recovery generally says to recollect unmodified output and never tells the reader to edit evidence until it passes.

## Checks run

```text
git rev-parse HEAD
2b76abbd565271b30f37fdb1e3f00d76185e8dc4

scripts/check_capture.sh
94 passed in 3.77s
tracked_markdown_files=120
local_links=188
fragments=53
errors=0
Ruff check and format: passed
ty: passed
fixture authentication/regeneration/byte comparison: passed
runtime-only installation and API example: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

focused BuildTask collection/status test
8 passed

focused documentation contract tests
4 passed

shellcheck scripts/check_capture.sh
passed

bash -n scripts/check_capture.sh
passed

git diff --check
passed before this report was added

exact tag and endpoint checks
v1.11.12 tag resolved
tagged manifest and run-results hashes matched vendored resources
current generic manifest-v12 hash differed from the pinned tag as documented
```

The green gates establish implementation behavior, deterministic examples, link integrity, and the contracts they currently encode. They do not close either finding: the documentation test does not encode the missing matrix/count semantics, and it deliberately binds the unsafe same-directory action to the implementation template.

## Verdict and re-review conditions

**CHANGES_REQUIRED**

Commit `2b76abbd565271b30f37fdb1e3f00d76185e8dc4` is not documentation-complete from the dbt Core subject-matter perspective. Re-review requires both findings to be resolved in source and tests:

1. publish and test the exact supported/unsupported collection, resource, status, and `status_counts` contract; and
2. make invocation recovery depend on one completed invocation rather than one directory, while narrowing `PAIR_VALID` language to internal contract validity.

Later real Azure Databricks archive, retry/repair, cancellation, and complete Python/Linux dependency qualification remain later product gates. They are not substitutes for these source-document corrections and were not exercised by this review.
