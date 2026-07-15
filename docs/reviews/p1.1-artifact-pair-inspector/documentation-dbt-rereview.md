# dbt Core documentation accuracy closure re-review: P1.1

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `2367a05d4e9ddb763cc52a3b7090c4099a639631` |
| Commit tree | `a3ef222f0300903f6cee4bef57db64d9a3d5b49d` |
| Commit parent | `08de2ddb3429bb675b6587de4c225bbf93102a1f` |
| Commit subject | `fix: make p1.1 invocation recovery overwrite-safe` |
| Review date | 2026-07-15 |
| Review role | Independent dbt Core artifact and documentation subject-matter reviewer |
| Prior review | [`documentation-dbt.md`](documentation-dbt.md), verdict `CHANGES_REQUIRED` at commit `2b76abbd565271b30f37fdb1e3f00d76185e8dc4` |
| Verdict | **PASS** |
| Open findings | 0 |
| Cloud activity | None. No Databricks, Azure, authentication, warehouse, compute, SQL, dbt runtime, or paid-resource path was used. |

Both prior findings are closed at the exact commit above. The public reference now publishes the exact Core 1.11.12 `BuildTask` collection/resource/run-versus-test status matrix, unsupported collections, freshness exclusion, ambiguity behavior, and the executed-result scope of `status_counts`. Invocation recovery now requires two closed artifacts from one completed pinned `dbt build` invocation before another command can overwrite them; it explicitly rejects directory co-location as a pairing key and preserves equality of parseable `metadata.invocation_id` values as the inspector invariant.

The corrected invocation text is aligned across implementation, generated report schema, generated fixture, tutorial output, CLI issue registry, diagnosis route, and executable tests. “Trusted pair” has been narrowed to contract-valid internal consistency with explicit origin, authenticity, modification, custody, archive, and capture-completeness non-claims. Decision 0002 provides an acceptable pre-release basis for retaining `dbtobsb.artifact-pair-report.v1`; no public release surface or contrary repository evidence was found.

## Exact scope and hashes

This focused closure review covered the prior finding record, corrected reader route, Decision 0002, static report contract, fixture generation, exact schemas, executable tests, and repository-owned gates. All SHA-256 values below were calculated from path-sorted blobs at the immutable reviewed commit, not from mutable working-tree content.

```text
9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099  capture/examples/inspect_valid_fixture.py
69f1367bf81be14cf166626251e734854655871c95dd1624015c11a10e2a8935  capture/pyproject.toml
3a55f3869616f8db19b8771081efe0b329d88bc080f648f471da3ac908a59de3  capture/scripts/generate_artifact_pair_fixtures.py
a3b0a877110617e10d27d11893b34e65633279b77fd1cd7b547c10c396e44ad9  capture/scripts/generate_report_schema.py
6f312022cfbf58b4a11232963e06e406e81da9c8ba42f55c331529f5a257b5f9  capture/src/dbtobsb_capture/contracts.py
d80955b8575ff12d5daf2d6d26bf3e4b49f79a2d0beb910ef5aed961db7ffdaf  capture/src/dbtobsb_capture/inspector.py
561f7a81bcb0fe7a9d1d2a8364228d39f88f758a83c34889c7e4480f60d5c1a6  capture/src/dbtobsb_capture/registry.py
d9a03b0c53e3346031520abef9b22094733402d64bbed1337665623621965029  capture/src/dbtobsb_capture/schemas.py
a57bd0c63cfb846ea4282e686ff859892465b501eff6ae132b8650503d2eddc0  capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json
b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3  capture/src/dbtobsb_capture/schemas/manifest-v12.json
1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf  capture/src/dbtobsb_capture/schemas/run-results-v6.json
05cadb8737782e4eb35af90bfff48dfd41db86de12bca95cc7702651c677ee9c  capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/expected-report.json
14d1b3c6f54831fcc004bfad548578c0b955e03f41db786bba7f484391be419c  capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/manifest.json
61b1d1fcdca3ac007a201cef0a94491cafbbfd67837504498a7cbdd8129d3a72  capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/provenance.json
3898f1870fdce4d877be7a1893d65f3a7724bcdda6609361d8bdd3c8582ec2bc  capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/run_results.json
203f4a7ba9f445330c9a9807fc19b15cec125a7d4241b80fe4d9380005cd795b  capture/tests/test_artifact_pair.py
34a514f751fd83df0afd045ae73b6bbc0af151dcb27523fb22a9f08f534a9683  capture/tests/test_documentation.py
6441b939e20c7578a8900daa452d47483e7932369f3ae32dbef0e88af5acde07  capture/tests/test_fixture_generator.py
946d6ca04d362d5a25606f0306114b2776d2479376ab300899ca4bc0019614d1  docs/decisions/0002-correct-p1.1-invocation-recovery-text.md
0ce8f5dc9fe7e426fbcd65b2b09b8bdf30b5230f29cb288c14836d423c88fda1  docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md
653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990  docs/developers/explanation/raw-artifact-custody.md
e2befb7ad8648db1cfd71ec9e4f9eba4a44a78a2c67fb2cb7233fece097c4531  docs/developers/how-to/diagnose-an-invalid-artifact-pair.md
539ac1e3e1c208b52d6e486a1c87b788e73b92f1f4b7d4e5d30724022908e920  docs/developers/how-to/handle-raw-dbt-artifacts-safely.md
bb4c28a5c50988e4ddc17e90c462b3d86de145ecec8d1c06e78f19ed97c30323  docs/developers/reference/cli-report-and-exit-codes.md
14f83e19b7520a80287a1c728a76ee04fdb103df084b9fe1b705e71b5a0d02aa  docs/developers/reference/python-api.md
35b778b40eda2880b837a2d5c5d517c55ac9593e41d6aacf3815f76ba5c6a12d  docs/developers/tutorials/inspect-an-artifact-pair.md
84fcc96227afab551e07c0ed7194d13e8fa299e7210bebb132ef5b875b076eab  docs/evidence/p1.1-local-artifact-pair-2026-07-15.md
555ea21e8de979ad539024e0856275b9741cd377253a5285fa2779ee12288849  docs/index.md
ec7e73009e88274a38c140add8eb49e81b74be23c5350a39578a70a784d8780c  docs/reviews/README.md
4639c495d4ebc0c219850b2da4f4b595220246402c9e7d6a7bca6477a4cb5e95  docs/reviews/p1.1-artifact-pair-inspector/documentation-dbt.md
92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911  scripts/check_capture.sh
aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0  scripts/check_markdown_links.py
```

The SHA-256 of that exact 32-record stream, including two spaces between digest and path and one trailing newline per record, is:

```text
0882e7bd6daeb31688e442f6aba173d3732b905706d294792f1280e78c061ff9
```

This re-review report is outside every reviewed input and aggregate. No reviewed source, fixture, schema, test, decision, evidence, or prior review file was edited by this review.

## Current primary sources checked

The current official dbt documentation was refreshed through the [dbt documentation LLM index](https://docs.getdbt.com/llms.txt) and its LLM-friendly Markdown pages:

- [manifest.json](https://docs.getdbt.com/reference/artifacts/manifest-json) says the manifest contains the full enabled-project resource inventory even when only some resources execute;
- [run_results.json](https://docs.getdbt.com/reference/artifacts/run-results-json) says it represents one completed invocation and contains only executed nodes, their native statuses, and `args.which`;
- [JSON artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) says the default target is shared, supports an invocation-specific target-path override, and explicitly warns that a later operation can overwrite earlier artifacts; and
- [`dbt build`](https://docs.getdbt.com/reference/commands/build) confirms the primary command and its combined manifest/run-results behavior.

Exact Core behavior was rechecked against first-party dbt Core `v1.11.12` source:

- [`BuildTask.RUNNER_MAP`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py#L35-L48) contains model, snapshot, seed, test, unit test, saved query, exposure, and function;
- [`RunStatus`, `TestStatus`, and `FreshnessStatus`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/artifacts/schemas/results.py#L51-L84) provide the exact two accepted families and separate freshness-only `runtime error`; and
- the exact [manifest v12](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json) and [run-results v6](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json) schemas remain the pinned validation inputs.

The remote `v1.11.12` tag resolved to `fa444c13bb5cd46a55656d553b1cd57c8ec19f01`. Independent byte checks matched both vendored schemas to the tag:

| Schema | Vendored and tagged SHA-256 |
| --- | --- |
| manifest v12 | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` |
| run-results v6 | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` |

## Finding closure

### DOCDBT-P1.1-001 — Closed

The prior finding required an exact, self-contained `BuildTask` compatibility contract, its unsupported/freshness/ambiguity boundary, precise `status_counts` meaning, direct recovery navigation, and implementation-derived documentation tests.

The [Python API reference](../../developers/reference/python-api.md#buildtask-result-compatibility) now publishes this exact matrix:

| Manifest collection | Accepted resource type | Native family |
| --- | --- | --- |
| `nodes` | `model`, `seed`, `snapshot` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `nodes` | `test` | Test: `error`, `fail`, `pass`, `skipped`, `warn` |
| `unit_tests` | `unit_test` | Test: `error`, `fail`, `pass`, `skipped`, `warn` |
| `saved_queries` | `saved_query` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `exposures` | `exposure` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |
| `functions` | `function` | Run: `error`, `no-op`, `partial success`, `skipped`, `success` |

The adjacent closed boundary names `sources`, `macros`, `metrics`, and `semantic_models` as unsupported, rejects freshness-only `runtime error`, and describes supported/supported and supported/unsupported collisions as ambiguous rather than manually selectable. This matches the inspector's exact collection dictionaries, resource check, and run-versus-test family choice.

The reference now defines `summary.status_counts` as the count of every accepted entry in that pair's `run_results.results`, grouped by preserved native status. It explicitly excludes the manifest's complete inventory, an overall dbt success label, outer Databricks/Lakeflow state, and future capture completeness. This matches the inspector's `Counter` over accepted result entries and the official manifest-versus-run-results distinction.

Navigation and anti-drift coverage are direct:

- the [CLI issue registry](../../developers/reference/cli-report-and-exit-codes.md#issue-registry) links every issue to a real diagnosis fragment and links compatibility issues to the exact matrix;
- [Recover result evidence](../../developers/how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) links directly to the same matrix; and
- `test_buildtask_matrix_and_status_counts_match_implementation` derives the matrix from `_SUPPORTED_RESULT_COLLECTIONS`, `RUN_STATUSES`, and `TEST_STATUSES`, derives the unsupported sequence from `_UNSUPPORTED_RESULT_COLLECTIONS`, and binds every count-scope exclusion.

Focused execution passed every run status, every test status, all eight `BuildTask` resource types, all four unsupported collections, freshness rejection, supported/supported ambiguity, supported/unsupported ambiguity, and report-schema variants.

**Disposition: CLOSED.**

### DOCDBT-P1.1-002 — Closed

The prior finding required overwrite-safe same-invocation recovery, directory non-reliance, narrowed `PAIR_VALID` language, and exact alignment across the static contract.

Both invocation issue templates now say:

```text
Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs.
```

`DBT_INVOCATION_ID_MISMATCH` now reports that the files do not have the same dbt invocation identity; it does not call them an untrusted pair. The [recovery guide](../../developers/how-to/diagnose-an-invalid-artifact-pair.md#recover-pair-metadata) makes the operational rule explicit:

1. give one approved pinned `dbt build` an empty attempt-specific target path;
2. let that invocation close both artifacts;
3. collect them before another command can reuse or overwrite the target;
4. require equal parseable `metadata.invocation_id` values; and
5. never treat co-location as the pairing key.

That guidance directly addresses the official dbt overwrite behavior while preserving the implemented equality invariant. It neither edits evidence nor infers identity from a path.

The [pair-validity explanation](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md) now asks whether the files form a “contract-valid, internally consistent pair.” It explicitly says `PAIR_VALID` does not prove origin, authenticity, absence of post-generation modification, custody, archive completeness, or capture completeness, and names the missing provenance signature, customer-evidence hash, AttemptKey, and archive correlation. The evidence record likewise says mismatched invocations are not internally consistent.

Static alignment is complete:

| Layer | Closure evidence |
| --- | --- |
| Inspector | Both invocation templates contain the corrected action; mismatch impact uses identity rather than trust. |
| Generated JSON Schema | Both exact issue variants contain the corrected constant strings; generated schema SHA-256 is `a57bd0c63cfb846ea4282e686ff859892465b501eff6ae132b8650503d2eddc0`. |
| Fixture generator | `_mismatch_report()` emits the corrected impact and action. |
| Reviewed fixture | `invalid_invocation_mismatch/expected-report.json` contains the corrected values. |
| CLI reference | Both invocation rows reproduce the exact templates and link directly to `recover-pair-metadata`. |
| Tutorial | Its marked invalid-invocation fence reproduces the exact installed CLI output. |
| Tests | Issue rows are bound to `_ISSUES`; every schema variant validates; the fixture snapshot matches; the tutorial command is executed and its complete stdout compared byte-for-byte. |
| Full gate | Report schema and fixtures regenerate in temporary storage and compare byte-for-byte before the runtime-only wheel/CLI checks pass. |

**Disposition: CLOSED.**

## Decision 0002 and pre-release version treatment

[Decision 0002](../../decisions/0002-correct-p1.1-invocation-recovery-text.md) records why changing exact static issue text while retaining `dbtobsb.artifact-pair-report.v1` is acceptable before the first release:

- the candidate had not been distributed, released, or accepted by an external consumer;
- fixtures, generated schema, CLI/Python output, and documentation contracts remained repository-controlled;
- every affected generated and executable surface had to be regenerated and tested;
- dbt, usability, and security re-review are required before release; and
- an equivalent post-release change requires a new contract-version decision and consumer migration analysis.

Current read-only checks found no conflict with that premise:

| Check | Observed result |
| --- | --- |
| Repository visibility | Private GitHub repository `MiguelElGallo/dbtobsb`. |
| Local and remote Git tags | None. |
| GitHub releases | None. |
| Public PyPI JSON endpoint for `dbtobsb-capture` | HTTP `404`. |
| Package version | `0.1.0`. |
| Publishing workflow | No release/publish workflow; only the capture validation workflow is present. |

Those checks establish absence of the normal public release surfaces; Decision 0002 is the accountable repository record for the stronger no-accepted-external-consumer statement. No contrary evidence was found. The unchanged v1 identifier is therefore acceptable for this pre-release correction. This dbt re-review satisfies only the decision's dbt-review requirement; it does not claim that separate usability and security re-reviews have completed.

## Checks run

```text
git rev-parse HEAD
2367a05d4e9ddb763cc52a3b7090c4099a639631

focused documentation contract
6 passed in 2.00s

focused artifact/schema compatibility
32 passed, 43 deselected in 0.92s

scripts/check_capture.sh
96 passed in 5.26s
tracked_markdown_files=124
local_links=200
fragments=55
errors=0
Ruff check: passed
Ruff format: passed
ty: passed
fixture and report-schema regeneration/byte comparison: passed
runtime-only installation and API example: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

shellcheck scripts/check_capture.sh
passed

bash -n scripts/check_capture.sh
passed

git diff --check 2b76abbd565271b30f37fdb1e3f00d76185e8dc4 2367a05d4e9ddb763cc52a3b7090c4099a639631
passed

git diff --check
passed before this report was added

exact upstream checks
dbt Core v1.11.12 tag resolved
vendored manifest v12 matched the exact tag
vendored run-results v6 matched the exact tag

pre-release surface checks
private repository
zero local/remote tags
zero GitHub releases
PyPI project API HTTP 404
package version 0.1.0
```

The focused tests were deliberately redundant with the full gate so that each closure claim has a named result while the repository-owned gate still proves regeneration, links, lint, typing, packaging, and installed-runtime behavior together. The worktree was clean and `HEAD` matched the reviewed commit before checks began.

## Non-blocking later qualification gates

The following remain later product or release gates, not defects in these P1.1 documentation corrections:

1. qualify real Azure Databricks native archives for success, dbt failure, early failure, cancellation, timeout, retry, and repair;
2. freeze native archive retrieval/layout, attempt-specific target/log paths, and complete Python 3.12/Linux dependency behavior in the actual execution image;
3. implement structured-log, AttemptKey, archive-hash, retrieval, and capture-state parts without expanding `PAIR_VALID`; and
4. complete the separate usability and security re-reviews required by Decision 0002 before release.

No paid compute or cloud resource was started, changed, or deleted for this re-review.

## Verdict

**PASS**

`DOCDBT-P1.1-001` and `DOCDBT-P1.1-002` are closed at commit `2367a05d4e9ddb763cc52a3b7090c4099a639631`. The exact compatibility/count contract is now reader-visible and implementation-bound; invocation recovery is overwrite-safe and same-invocation-based; `PAIR_VALID` is properly limited to internal contract consistency; all affected static/generated/executable surfaces agree; and Decision 0002 adequately governs the pre-release v1 text correction. No new dbt Core documentation accuracy finding was identified in this closure scope.
