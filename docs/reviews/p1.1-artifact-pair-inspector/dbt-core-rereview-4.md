# Final dbt Core product-contract re-review: P1.1

- Commit: `cff8bbcd808ff7e13a7ead182543a2564cd04ff6`
- Tree: `a3802ab9b14a1dc3b7f18f90255eee349fdeecbb`
- Parent: `8711aa803016b5d732553756c5e71542e0a928bf`
- Date reviewed: 2026-07-15
- Reviewer role: Independent dbt Core and artifact-contract reviewer
- Verdict: `PASS_WITH_FOLLOW_UP`
- Prior implementation closure: [`dbt-core-rereview-3.md`](dbt-core-rereview-3.md), commit `75b7d41316216a3b18a3c56ff0c98f133f7aab89`
- Cloud activity: None. This review did not authenticate to Databricks, start compute, run dbt in a workspace, or mutate cloud state.

## Executive verdict

Commit `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` still satisfies the accepted P1.1 dbt Core product contract. No original dbt finding, constructor/schema finding, or mixed-invalid integration blocker regressed.

The post-`75b7d41` correction to `DBT_INVOCATION_ID_INVALID` and `DBT_INVOCATION_ID_MISMATCH` is internally complete. The exact impact and recovery action are synchronized across the static registry, generated report schema, generated mismatch fixture, fixture generator, CLI registry rows, tutorial output, and executable CLI/API/documentation tests. The action now reflects dbt's overwrite behavior: collect both closed artifacts from one completed pinned `dbt build` invocation before another dbt command runs.

Decision 0002 is acceptable as a pre-release correction that retains `dbtobsb.artifact-pair-report.v1`. It explicitly limits that treatment to the unreleased candidate, requires regeneration and independent re-review, and requires a new version decision and migration analysis for an equivalent post-release change.

No present P1.1 dbt Core or artifact-contract defect was found. The follow-ups in this report are later runtime, compatibility, and release gates rather than P1.1 blockers.

## Exact review snapshot and scope

The review was pinned to the commit and tree above, not to a moving worktree. The 46-file scope below covers the inspector's implementation, public Python and CLI contracts, vendored dbt schemas, generated report schema and fixtures, generator/tests, user and developer documentation, evidence, decision record, prior immutable reviews, and the full local gate.

Each line is `SHA-256  path`, calculated from that file's blob at the reviewed commit. The SHA-256 of the complete newline-delimited record stream, in the order shown, is `727f40cf24b421b495085796af5fa78766a07beaa37e8be63d6680c13947e8b9`.

```text
9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099  capture/examples/inspect_valid_fixture.py
69f1367bf81be14cf166626251e734854655871c95dd1624015c11a10e2a8935  capture/pyproject.toml
3a55f3869616f8db19b8771081efe0b329d88bc080f648f471da3ac908a59de3  capture/scripts/generate_artifact_pair_fixtures.py
a3b0a877110617e10d27d11893b34e65633279b77fd1cd7b547c10c396e44ad9  capture/scripts/generate_report_schema.py
a7ac1c6de1c5cbac2053b2321b9da37375e0be46f861ebf050180f108218e096  capture/src/dbtobsb_capture/__init__.py
d05d272ead702943221a4e337c4708af21db7c07607b734c8ed30b18f70bc4f1  capture/src/dbtobsb_capture/cli.py
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
f28ede076d444298bbd4ea2ccb7a4459a58765e61737e319ee19bfc34dc23b3b  capture/tests/fixtures/artifact_pair/valid_dbt_failure/expected-report.json
14d1b3c6f54831fcc004bfad548578c0b955e03f41db786bba7f484391be419c  capture/tests/fixtures/artifact_pair/valid_dbt_failure/manifest.json
1fa0e4f6e72451831ec0f5bf7015e5f7c7e06e0164aed1d737c77009767b0554  capture/tests/fixtures/artifact_pair/valid_dbt_failure/provenance.json
5c73625525e88efbc6a302f2c2cab9f9ef1c0e8083c7a383290a5dc329a70691  capture/tests/fixtures/artifact_pair/valid_dbt_failure/run_results.json
c201e6cebad768948fc11b2c1a14cc0075754c80ccc5e631d8a8c170e8bd044d  capture/tests/fixtures/artifact_pair/valid_success/expected-report.json
14d1b3c6f54831fcc004bfad548578c0b955e03f41db786bba7f484391be419c  capture/tests/fixtures/artifact_pair/valid_success/manifest.json
60fdc39b4fb082677ca7c339a1987588774bba338b3c14e9c0c9024975dafcd8  capture/tests/fixtures/artifact_pair/valid_success/provenance.json
4465791113cec78b9267697585952c4cfc4a1ef60c71ea07456c6766cb5e3f70  capture/tests/fixtures/artifact_pair/valid_success/run_results.json
203f4a7ba9f445330c9a9807fc19b15cec125a7d4241b80fe4d9380005cd795b  capture/tests/test_artifact_pair.py
b8f620560cc16ec77935c306ac4ef10b40a29ed16bb6864ba94c9ad2e4bcb29d  capture/tests/test_cli.py
8dab5bf14843fef5ae4bc86a2335ae3912fe18c9ba88175302fdff0b7e160b99  capture/tests/test_documentation.py
6441b939e20c7578a8900daa452d47483e7932369f3ae32dbef0e88af5acde07  capture/tests/test_fixture_generator.py
946d6ca04d362d5a25606f0306114b2776d2479376ab300899ca4bc0019614d1  docs/decisions/0002-correct-p1.1-invocation-recovery-text.md
0ce8f5dc9fe7e426fbcd65b2b09b8bdf30b5230f29cb288c14836d423c88fda1  docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md
653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990  docs/developers/explanation/raw-artifact-custody.md
e2befb7ad8648db1cfd71ec9e4f9eba4a44a78a2c67fb2cb7233fece097c4531  docs/developers/how-to/diagnose-an-invalid-artifact-pair.md
539ac1e3e1c208b52d6e486a1c87b788e73b92f1f4b7d4e5d30724022908e920  docs/developers/how-to/handle-raw-dbt-artifacts-safely.md
bb4c28a5c50988e4ddc17e90c462b3d86de145ecec8d1c06e78f19ed97c30323  docs/developers/reference/cli-report-and-exit-codes.md
7c5e2ca891124cfb9b60f6184983fb97a963ec26339c1decce4e40dba14e9c82  docs/developers/reference/python-api.md
35b778b40eda2880b837a2d5c5d517c55ac9593e41d6aacf3815f76ba5c6a12d  docs/developers/tutorials/inspect-an-artifact-pair.md
84fcc96227afab551e07c0ed7194d13e8fa299e7210bebb132ef5b875b076eab  docs/evidence/p1.1-local-artifact-pair-2026-07-15.md
85afa735b82c694413181b931eb8033fa6f8257704983daeb1ce808ec0012cc9  docs/reviews/p1.1-artifact-pair-inspector/dbt-core-rereview-2.md
5bb97bbf6a08207fb4462c1de590e4fa7c9e0fd40bcdda7f28e9926f3f2ac0180  docs/reviews/p1.1-artifact-pair-inspector/dbt-core-rereview-3.md
1e62186125273ccedd66518c6c49c801ce242f59d5726a206bd816b3de6d722a  docs/reviews/p1.1-artifact-pair-inspector/dbt-core-rereview.md
5bf3e1f794301f4614f00607c6ca1c69ae8d272aa746bf1870cd3e8398a155fe  docs/reviews/p1.1-artifact-pair-inspector/dbt-core-review.md
b824d7721e442678b9843832cb87bdbd6c3e186fec1a976310a76678a9480745  docs/reviews/p1.1-artifact-pair-inspector/documentation-dbt-rereview.md
4639c495d4ebc0c219850b2da4f4b595220246402c9e7d6a7bca6477a4cb5e95  docs/reviews/p1.1-artifact-pair-inspector/documentation-dbt.md
92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911  scripts/check_capture.sh
aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0  scripts/check_markdown_links.py
```

## Change-boundary review

### Since the accepted implementation closure

The diff from `75b7d41316216a3b18a3c56ff0c98f133f7aab89` to the reviewed commit contains the intended static invocation-language correction, regenerated contract artifacts, tests, Decision 0002, documentation, evidence, and immutable peer-review records.

The product-significant change is deliberately narrow:

| Code | Exact impact | Exact next action |
| --- | --- | --- |
| `DBT_INVOCATION_ID_INVALID` | `The files cannot be bound to one parseable dbt invocation.` | `Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs.` |
| `DBT_INVOCATION_ID_MISMATCH` | `The files do not have the same dbt invocation identity.` | `Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs.` |

These strings match exactly in the inspector registry, generated schema variants, mismatch fixture and generator, CLI reference, tutorial output, and executable tests. An independent CLI run against the checked-in mismatch fixture returned exit 10 and exactly:

```text
PAIR_INVALID
code: DBT_INVOCATION_ID_MISMATCH
impact: The files do not have the same dbt invocation identity.
next_action: Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs.
```

### Since the prior dbt documentation closure

The diff from `2367a05d4e9ddb763cc52a3b7090c4099a639631` to the reviewed commit does not change the inspector, registry, public report model, generated schema, fixtures, or generator. It hardens GitHub-Flavored Markdown handling by escaping Python union pipes as `\|`, updates the documentation test to parse backslash-escaped table cells, and adds immutable review records. This does not alter the dbt product contract.

## Current primary-source check

The review refreshed the [dbt documentation index](https://docs.getdbt.com/llms.txt) and the current first-party references for [manifest artifacts](https://docs.getdbt.com/reference/artifacts/manifest-json), [run-results artifacts](https://docs.getdbt.com/reference/artifacts/run-results-json), [JSON artifact paths and overwrite behavior](https://docs.getdbt.com/reference/global-configs/json-artifacts), and [`dbt build`](https://docs.getdbt.com/reference/commands/build).

The fixed compatibility row was also checked against immutable dbt Core `v1.11.12` source: [`BuildTask.RUNNER_MAP`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py#L35-L48), [`RunStatus` and `TestStatus`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/artifacts/schemas/results.py#L51-L84), [manifest v12](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json), and [run-results v6](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json). The resolved tag commit is `fa444c13bb5cd46a55656d553b1cd57c8ec19f01`.

The checked-in schema resources remain byte-identical to that tag:

| Schema resource | SHA-256 |
| --- | --- |
| dbt Core 1.11.12 manifest v12 | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` |
| dbt Core 1.11.12 run-results v6 | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` |

The current generic manifest endpoint no longer has the tagged manifest's checksum, which reinforces the existing design choice: validation is pinned to immutable compatibility-row bytes rather than a mutable latest schema endpoint.

## Accepted P1.1 dbt contract

| Area | Accepted behavior at the reviewed commit |
| --- | --- |
| Compatibility row | Exactly dbt Core `1.11.12`, manifest v12, run-results v6, adapter `databricks`, command `build`. |
| Pair identity | Both `metadata.invocation_id` values must be parseable and equal. Equality establishes internal pair binding; it does not authenticate origin, custody, or lack of modification. |
| Manifest meaning | The manifest is the enabled project inventory. It is not treated as proof that every resource ran. |
| Run-results meaning | `results` contains the resources executed by that completed invocation. It is not treated as the complete manifest inventory. |
| Supported result types | `model`, `seed`, `snapshot`, `test`, `unit_test`, `saved_query`, `exposure`, and `function`, resolved from their exact `BuildTask` collections. |
| Deliberately unsupported result types | `source`, `macro`, `metric`, and `semantic_model`. Freshness output is not accepted as `dbt build` run-results. |
| Native run statuses | `error`, `no-op`, `partial success`, `skipped`, and `success`. |
| Native test statuses | `error`, `fail`, `pass`, `skipped`, and `warn`. Freshness-only `runtime error` is rejected. |
| Ambiguity protection | Supported/supported and supported/unsupported unique-ID collisions are rejected instead of guessed. |
| `status_counts` | A deterministically sorted count of statuses from accepted `run_results.results`; it is not manifest inventory, job state, capture state, or an observability roll-up. |
| Valid dbt failure | A schema-valid, internally consistent artifact pair with native error results remains `PAIR_VALID`; dbt outcome is reported separately from pair validity. |
| Invalid output | All detected issue codes are deduplicated, ordered by shared `ISSUE_PRECEDENCE`, then capped at 20 before strict report construction. |
| File handling | Inputs are bounded regular files opened without following symlinks; nonblocking open and post-open `fstat` prevent FIFO/device hangs and type substitution. |
| Public report contract | Python constructors and generated JSON Schema both enforce the closed state, summary, issue, ordering, uniqueness, cardinality, and status-count contract. |

## Original and later finding regression check

| Finding | Current result |
| --- | --- |
| `DBT-P1.1-001`: fixture generator could forge provenance or retain sensitive source content | Closed. Source authentication, adversarial-source rejection, synthetic output, sensitive canaries, provenance semantics, regeneration, and byte comparison pass. |
| `DBT-P1.1-002`: deeply nested JSON could escape as `RecursionError` | Closed. Bounded invalid reports and CLI behavior pass. |
| `DBT-P1.1-003`: FIFO input could block | Closed. FIFO, device, sparse-file, and symlink controls pass. |
| `DBT-P1.1-004`: JSON Schema and public Python constructors did not express one closed contract | Closed. Direct-constructor rejection and every generated issue variant pass. |
| `DBT-P1.1-005`: incomplete `BuildTask` resource/status matrix | Closed. Supported collections, both status families, unsupported resources, freshness-only status, and collision cases pass against the pinned source contract. |
| `DBT-P1.1-006`: public API documentation overstated no-filesystem behavior | Closed. Documentation accurately describes path reads and installed API behavior. |
| Strict-constructor integration blocker from the second re-review | Closed. Mixed parse and mixed semantic evidence returns canonical reports instead of raising. |
| Detection-prefix/truncation blocker from the third re-review | Closed. Canonical ordering precedes the 20-code cap; an independent reverse-and-duplicate probe over all 26 codes returned the canonical first 20. |

The all-pairs regression matrix continues to cover all `26 choose 2 = 325` issue-code pairs with duplicate input. The direct constructor tests, schema mutants, installed-resource reads, exact BuildTask matrix, status matrix, fixture controls, and mixed-invalid API/CLI paths all remain green.

## Decision 0002 assessment

Decision 0002 is an appropriate pre-release v1 treatment for this correction because it records all of the boundaries that make retaining the identifier defensible:

1. the prior instruction was a repository-controlled candidate, not a released compatibility promise;
2. the correction changes static impact/action text, not report shape, state semantics, issue code, or ordering;
3. schema and fixtures are regenerated and byte-checked from the same registry;
4. API, CLI, constructor, fixture, and documentation gates are rerun;
5. immutable review history records the correction; and
6. the decision requires a new version decision and consumer migration analysis after release.

Current repository and package-index checks corroborate the pre-release premise: `MiguelElGallo/dbtobsb` is private, the local and remote repositories expose no tags, GitHub exposes no releases, the PyPI JSON endpoint for `dbtobsb-capture` returns 404, and there is no publish/release workflow. The package version remains `0.1.0`. These observable checks support the decision record; they do not replace its accountable assertion that no candidate was distributed or accepted by an external consumer.

This report supplies the required dbt Core re-review only. Decision 0002's separate usability and security acceptance must also be present before release.

## Verification evidence

### Focused contract gates

```text
documentation contract
6 passed in 2.01s

fixture and artifact-contract historical regression selection
56 passed, 20 deselected in 2.21s

CLI historical regression selection
7 passed, 7 deselected in 1.51s

focused total
69 passed
```

The focused selection includes exact documentation output, adversarial fixture sources, golden fixtures, valid dbt failure, sensitive canaries, schema digests and installed reads, provenance, mixed parse/semantic evidence, deep nesting, result resolution, exact BuildTask resources and statuses, unsupported/freshness/collision cases, all 325 issue pairs, deduplication and bounds, public constructors, schema variants, and schema mutants.

### Complete repository gate

```text
scripts/check_capture.sh
96 passed in 5.12s
tracked Markdown files: 128
local links checked: 212
fragments checked: 59
documentation errors: 0
Ruff check: passed
Ruff format: passed
ty: passed
fixture/schema regeneration and byte comparison: passed
runtime-only install: passed
API example: passed
wheel build: passed
installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED
```

### Independent and hygiene checks

```text
mismatch fixture CLI: exit 10 with exact static output
all 26 issue codes reversed and duplicated: canonical first 20 returned
first returned code: DBT_MANIFEST_SIZE_LIMIT_EXCEEDED
last returned code: DBT_RESULT_ID_UNSUPPORTED_RESOURCE
shellcheck scripts/check_capture.sh: passed
bash -n scripts/check_capture.sh: passed
git diff --check 75b7d41316216a3b18a3c56ff0c98f133f7aab89 cff8bbcd808ff7e13a7ead182543a2564cd04ff6: passed
worktree before this report: clean
```

## Findings

No present P1.1 dbt Core or artifact-contract defect was found at `cff8bbcd808ff7e13a7ead182543a2564cd04ff6`.

## Non-blocking later gates

These are not defects in the portable P1.1 inspector:

1. **Real Databricks runtime qualification:** archive real Azure Databricks runs for native `dbt build` success, failure, cancellation, timeout, retry, and repair behavior without leaving compute running.
2. **Execution-image compatibility:** validate the complete Python 3.12/Linux dependency lock in the actual Databricks image before declaring the runtime support row qualified.
3. **Capture and correlation semantics:** independently review structured logs, AttemptKey correlation, archive completeness, and capture-state classification without overloading `PAIR_VALID` or `status_counts`.
4. **Future dbt rows:** for every additional Core or adapter version, re-pin and re-qualify schema bytes, `BuildTask` collections, result types, and status families before accepting support.
5. **Release readiness:** confirm Decision 0002's independent usability and security re-reviews and freeze the accepted generated contract before the first distribution.

## Resolution

The post-`75b7d41` invocation-language correction is dbt-accurate, generated from one static registry, and protected by exact CLI/API/schema/fixture/documentation tests. The complete P1.1 inspector continues to satisfy its fixed dbt Core 1.11.12 contract, and every earlier blocker remains closed.

Final dbt Core verdict: `PASS_WITH_FOLLOW_UP`. P1.1 is acceptable from the dbt Core and artifact-contract perspective; only the explicitly later runtime, compatibility, capture, and release gates above remain.
