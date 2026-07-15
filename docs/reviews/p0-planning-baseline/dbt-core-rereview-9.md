# Ninth dbt Core re-review: P0 planning baseline 0.10

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `2fa25d8bef4e2499de9feb0541b405430599400059172e206b1ec7bf89f9a8a1`
- Date: 2026-07-15
- Reviewer: independent dbt Core and `dbt-databricks` product/security specialist
- Verdict: `PASS`
- Open dbt P0 findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.10 passes the ninth independent dbt review. The new account-administrator service-principal-roster attestation, whole-group-root policy, point-in-time runtime-trust snapshot, 24-hour expiry, and direct-versus-effective warehouse-authority disclosure do not weaken or overwrite the canonical dbt evidence contract.

The author set continues to keep these domains separate:

1. A native, explicitly onboarded Lakeflow dbt task is the only supported producer of dbt evidence. Its closed sequence is optional `dbt deps` followed by exactly one named-selector `dbt build`.
2. One trusted AttemptKey and command ordinal bind immutable task-local log and target boundaries, the native task archive, a dbt `invocation_id`, and artifact hashes.
3. Only a fully qualified manifest-v12/run-results-v6 pair can create trusted node or test rows. A migration row, Query History record, runtime-trust snapshot, service-principal-role attestation, group-root declaration, App record, or system snapshot cannot satisfy that contract.
4. Structured JSON logs are diagnostic evidence with their own ordered state. They cannot replace a valid primary artifact pair, and malformed, truncated, missing, or unknown-version logs do not invalidate an independently valid pair.
5. Runtime trust is an overlay on provenance. When the observation is stale or unavailable, collection may continue and the App must label affected output unverified; it must not alter the underlying Lakeflow attempt, dbt invocation, artifact, result, or capture state.

This is approval of the P0 planning contract, not a claim that P1 parsers, P2 collection, P3 dependency locks and generated Jobs, P8 live archives, or P10 real-project qualification already exist.

## Immutable input verification and exact scope

I independently hashed every scoped author file by path, sorted the per-file SHA-256 records, and hashed that stream before reviewing and again before writing this report. Both calculations produced exactly:

```text
2fa25d8bef4e2499de9feb0541b405430599400059172e206b1ec7bf89f9a8a1
```

The exact scope was:

- `AGENTS.md`
- `README.md`
- `docs/index.md`
- `docs/decisions/0001-private-app-bundle.md`
- `docs/plans/documentation-plan.md`
- `docs/plans/product-plan.md`
- `docs/plans/review-process.md`
- `docs/research/source-register.md`

Review reports and the resolution ledger are outside this digest. I read the complete author scope and the prior review/finding chain, with focused comparison to `dbt-core-rereview-8.md` and `databricks-rereview-8.md`. I edited no author file or earlier report.

## Current primary evidence checked

As of 2026-07-15, the selected tagged versions remain the latest stable releases. The candidate dependency intersection remains coherent:

- [dbt Core 1.11.12](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) is stable and requires Python `>=3.10`; its published classifiers cover Python 3.10 through 3.13.
- [`dbt-databricks` 1.12.2](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) is stable and declares `dbt-core>=1.11.2,<1.11.13`, `dbt-common>=1.37.0,<1.38.0`, and Python `>=3.10`, with classifiers for 3.10 through 3.13. Its release includes the Python-model failure-state fix relevant to trustworthy failure capture.
- The tagged [`dbt-databricks` dependency metadata](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml) admits Core 1.11.12 and common 1.37.5; the tagged [Core dependency metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml) admits that common version.
- The published `dbt_common-1.37.5-py3-none-any.whl` SHA-256 remains `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077` in the [official package index](https://pypi.org/project/dbt-common/1.37.5/).
- Current [dbt artifact documentation](https://docs.getdbt.com/reference/artifacts/dbt-artifacts) still defines versioned JSON artifacts and a per-invocation identifier. [Manifest documentation](https://docs.getdbt.com/reference/artifacts/manifest-json) still describes full project inventory, while [run-results documentation](https://docs.getdbt.com/reference/artifacts/run-results-json) still describes executed results joined back by `unique_id`.
- Core 1.11 maps to [manifest schema v12](https://schemas.getdbt.com/dbt/manifest/v12.json), and current run results use [schema v6](https://schemas.getdbt.com/dbt/run-results/v6.json).
- Current [JSON-artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) continues to warn, by behavior, that commands sharing a target path overwrite prior output; the baseline's attempt- and ordinal-local boundaries are therefore the correct integrity practice.
- Current [log configuration](https://docs.getdbt.com/reference/global-configs/logs) continues to expose structured `log_version`, event name/code, level, timestamp, thread, and invocation identity separately from human message text.
- Current [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings) continues to support targeted warning promotion, including `NoNodesForSelectionCriteria`; the pinned-source qualification of `NothingToDo` remains part of the fixture contract.
- Azure Databricks continues to archive dbt task output and requires the individual dbt task run ID, not the parent multi-task run ID, for [artifact retrieval](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows).

The current trend boundary is also represented honestly. [Core 1.12.0rc3](https://github.com/dbt-labs/dbt-core/releases/tag/v1.12.0rc3) is a release candidate and Core 2.0 remains pre-release; neither is silently admitted. Newer surfaces such as state reuse and additional parse artifacts/statuses are portability inputs for a future matrix, not production evidence for this exact candidate.

## Baseline 0.10 regression review

| Baseline 0.10 change | Result | dbt conclusion |
|---|---|---|
| Account-admin native Service Principal User/Manager roster review | `PASS` | This is a separately labeled runtime-authority attestation. It has no dbt command, task archive, schema URL, invocation UUID, result ID, event envelope, or artifact hash and cannot create or validate dbt evidence. |
| Whole-group principals treated as customer-governed trusted roots | `PASS` | Group governance affects runtime authority classification only. It does not change which Job/task is onboarded, the AttemptKey, command ordinal, artifact paths, or result resolver. |
| GA `SHOW GROUPS` limited to named migration actors/groups | `PASS` | Migration current-DML classification remains outside the observed dbt-task namespace. No migration identity or membership result can become build-start evidence. |
| Point-in-time runtime observation plus 24-hour expiry | `PASS` | Observation ID, time, age, and qualifier are provenance overlays. `RUNTIME_TRUST_STALE` or `RUNTIME_TRUST_UNVERIFIED` changes presentation/action eligibility, never the immutable native attempt or dbt capture classification. |
| Low-privilege writers stamp, but do not re-observe, the accepted snapshot | `PASS` | The collector may stamp snapshot identity and age on its rows, but it must still independently satisfy every exact artifact/log/correlation invariant. A local snapshot check cannot manufacture a manifest, run results, invocation, or node result. |
| Direct warehouse `CAN_MONITOR` versus workspace-admin effective `CAN_MANAGE` | `PASS` | This corrects platform truth without changing dbt execution. Installer Query History and fixed migration SQL remain non-dbt evidence classes. |
| Combined personal route now requires account-administrator authority | `PASS` | Human bootstrap eligibility changes; the generated dbt command, version lock, observed Job run-as, archive, and evidence rules do not. |

## Exact dbt contract verification

| Contract area | Verdict | Ninth-review conclusion |
|---|---|---|
| Version and dependency boundary | `PASS` | Core 1.11.12, adapter 1.12.2, common 1.37.5, and Python 3.12.3 are a coherent exact candidate. The complete Python/Linux and Node lock remains mandatory before support is claimed. |
| Supported commands | `PASS` | Only optional `deps` plus one required `build` is ready. Every other primary command or evidence type is explicitly unsupported, deferred, validation-only, or non-observable. |
| Selector and empty-work prevention | `PASS` | A version-controlled named selector is required; neither a user, App parameter, Job parameter, migration input, nor AI supplies it. Both zero-execution warning paths and the independent non-empty-results postcondition prevent false observability. |
| Resolved flags | `PASS` | The scanner evaluates CLI, current/legacy environment aliases, one allowed project-or-profile mapping, `DO_NOT_TRACK`, and defaults. Project/profile and current/legacy alias conflicts fail deterministically instead of being masked by CLI precedence. |
| Privacy and egress flags | `PASS` | Both ordinals explicitly disable anonymous usage and artifact-ingest upload. Raw SQL, vars, messages, adapter messages, arbitrary metadata/events, and custom-environment content stay out of ordinary tables. |
| Path and overwrite isolation | `PASS` | Every Lakeflow attempt, retry, repair, and execution has a distinct AttemptKey root; each command has an ordinal-local log directory and reserved target boundary. `build` receives its own target path, while `deps` correctly receives no unsupported `--target-path`. |
| Partial parsing | `PASS` | `partial_parse.msgpack` is ancillary and never normalized as primary evidence. Pair equality deliberately excludes metadata fields that partial parsing can retain, while full schema, invocation, command, version, adapter, result cardinality, and result-ID resolution remain mandatory. A cache cannot satisfy or override those gates. |
| Concurrency | `PASS` | The signed runtime-trust manifest binds Job/task concurrency. Parallel or repaired task attempts remain isolated by job/task run coordinates, repair/execution counters, command ordinal, and unique target/log roots; collector idempotency is keyed to AttemptKey plus trusted hashes. No shared target directory is allowed. |
| Manifest/run-results pair | `PASS` | The exact v12/v6 pair requires one common non-null parseable UUID, Core 1.11.12, `args.which=build`, manifest `adapter_type=databricks`, trusted AttemptKey/ordinal, non-empty unique results, and exact BuildTask collection resolution. |
| Incomplete and early failure | `PASS` | Manifest-only may be `PARTIAL`; run-results-only is invalid; neither-file with same-build start evidence is partial; neither-file without it is not produced; unavailable retrieval wins. Pre-dbt failures remain outer Lakeflow facts only. |
| Structured logs | `PASS` | Per-ordinal states remain ordered as unavailable, not initialized, truncated, malformed, missing, unknown version, or valid. A `deps` event cannot prove the primary build started, and human `msg` is never a parsing contract. |
| Retry, repair, and reconciliation | `PASS` | Lakeflow repeats the full build in a new attempt rather than using `dbt retry` as the normal path. Reconciliation uses the same idempotent collector and never merges artifacts from distinct attempts. |
| Runtime-trust separation | `PASS` | Migration, attestation, group, roster, runtime-observation, App, role, enrichment, and Query History records remain separate from canonical dbt facts and cannot alter capture-state precedence. |
| Optional AI and future engines | `PASS` | The product remains complete with AI disabled. Genie/MCP cannot synthesize or execute arbitrary dbt commands. Core 1.12, Core 2.0/Fusion, state reuse, and future schemas/statuses require a separately frozen compatibility qualification. |

## Numbered finding disposition

No new numbered dbt finding is opened. No critical, high, medium, or low P0 correctness issue was found.

| Prior finding | Ninth re-review disposition |
|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION`; both zero-execution warnings plus the empty-result invariant prevent false success. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION`; the closed command matrix, per-command argv, conflict handling, privacy flags, and selector boundary remain exact. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION`; artifact standalone/pair validation and total retrieval/capture precedence remain deterministic. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION`; exact dependency, schema, wheel, and structured-log-version qualification remains intact. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION`; manifest inventory and invocation results remain distinct, including `NO_RESULT_RECORDED`. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION`; command-local closed-log handling, rotation bounds, and pre-logger states remain explicit. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION`; allowlisting, restricted diagnostics, and defense-in-depth redaction remain separate controls. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION`; optional intelligence remains advisory and cannot bypass deterministic validation or authorization. |

Because there is no new finding, there is no P0 acceptance correction. The later-gate evidence below remains mandatory and is not waived by this verdict.

## P0-P10 dbt review matrix

| Part | Planning verdict | Required dbt evidence at the part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record the ninth immutable-hash verdict with the other specialist outcomes and complete repository acceptance. |
| P1 — Capture library | `PASS` | Implement vendored exact schemas, standalone/pair validation, BuildTask resolution, path/size/hash/field allowlists, total capture/log precedence, and every adversarial fixture. |
| P2 — Collector and reconciliation | `PASS` | Prove individual-task archive retrieval, closed per-ordinal bounds, exactly-once AttemptKey writes, snapshot-stamp provenance, and hard rejection of migration/product/non-onboarded contexts as dbt evidence. |
| P3 — Bundle installer | `PASS` | Produce complete reproducible locks and exact argv fixtures; bind concurrency and immutable paths; prove runtime-trust and migration inputs cannot enter a dbt command, selector, path, artifact, or result. |
| P4 — App read-only MVP | `PASS` | Present Lakeflow, dbt invocation, node/test, collector, capture, migration, runtime-trust, and optional-enrichment outcomes separately; show observation age without rewriting dbt status. |
| P5 — Job onboarding | `PASS` | Deterministically inspect task shape, command sequence, selector, flags/aliases, vars, paths, privacy/egress, versions, connection/target feature compatibility, concurrency, and access/check failures. |
| P6 — Controlled actions | `PASS` | Start only a pre-approved bound observed Job. No request, user, App, role Job, migration input, AI, or roster/group evidence may supply dbt command material. |
| P7 — Security and operations | `PASS` | Prove normalized-field classification, restricted diagnostics, retention/export/delete, egress denial, and runtime-trust overlay behavior without broadening canonical dbt data. |
| P8 — Bounded live proof | `PASS` | Capture real success/failure/partial/early/cancel/retry/repair paths; prove target/log archival and AttemptKey correlation; exercise overlap if concurrency greater than one is supported, otherwise prove the bound; expire/refresh trust without changing capture facts; finish with no compute running. |
| P9 — Optional intelligence | `PASS` | Pass the whole install/capture/investigation/lifecycle suite with AI disabled; accepted tools use only deterministic validators and curated evidence. |
| P10 — Private alpha | `PASS` | Qualify representative projects against the exact version/command/adapter-feature matrix without silently admitting Core 1.12/2.0, state-reuse statuses, new artifacts, or untested adapter options. |

## Non-blocking portability watch

Current releases are moving toward Core 1.12, Core 2.0/Fusion, state reuse, additional parse artifacts, and adapter options such as the connector kernel. None belongs in the current exact matrix merely because it is present in current documentation or a newer release. Before any is supported, its exact stable Core/adapter/Python/dependency pair, command and flag surface, artifact schemas, result statuses, partial-parse behavior, structured-log version, authentication compatibility, and native Databricks archive behavior must pass a new frozen fixture and live qualification. This is a P1/P3/P5/P8 portability gate, not a P0 defect in the exact 1.11.12/1.12.2 baseline.

## Cloud-mutation statement

This review used local repository reads, current official documentation, first-party tagged GitHub release/source metadata, the official schema registry, and the official Python package index. It did not authenticate to or call Azure Databricks, start or stop compute, execute dbt, run SQL, or create, modify, or delete any cloud resource. No paid resource was started.

## Final disposition

- Frozen baseline 0.10 dbt verdict: `PASS`.
- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- P0 blockers: none.
- Future version, feature, concurrency, and archive evidence remains gated at the named implementation parts.
