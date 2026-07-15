# dbt Core re-review: P0 planning baseline 0.2

- Reviewed input: frozen pre-commit author file set
- Re-review input SHA-256: `483a3a4e1ccfe063a8af07a15483ac48abf5d090c44f1817a4cee8e810483965`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `CHANGES_REQUIRED`
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.2 is substantially stronger than the initial input. The revised plan now has the correct Core 1.11.12 warning names, a closed v1 command matrix, exact manifest v12 and run-results v6 contracts, the correct BuildTask result-collection union, explicit ancillary-output handling, a separate source-freshness contract, a bounded Python candidate, and manifest-inventory semantics that do not invent execution results. The private Databricks App plus Bundle architecture remains viable.

P0 is not ready to accept because three previously required acceptance conditions remain incomplete:

1. `DBT-P0-002` defines the command matrix and warning flags but does not define or scan the complete resolved flag contract that guarantees JSON artifacts, JSON file logs, task-local paths, and disabled dbt usage statistics.
2. `DBT-P0-003` gives capture-state precedence, but `ARCHIVE_UNAVAILABLE` still overlaps with early `NOT_PRODUCED`, while the outcome summary assigns every artifact-free dbt failure to `NOT_PRODUCED` even when a dbt-start event would require `PARTIAL`.
3. `DBT-P0-004` now pins Core, adapter, Python, and dependency graphs, but it dropped the original acceptance requirement to persist and fixture-test the actual structured-log `log_version`.

These are bounded contract edits. I found no new architecture blocker and no need to change the selected Core/adapter/Python candidate.

## Immutable input verification

The reviewed scope is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. Hashing each file and then hashing the sorted digest list reproduces the resolution ledger:

```text
483a3a4e1ccfe063a8af07a15483ac48abf5d090c44f1817a4cee8e810483965
```

The repository has no commit yet. This file-set digest is therefore the immutable review identity. This re-review report and the resolution ledger are outside the author-input hash. No author-owned planning file was edited during this re-review.

## Current primary sources checked

As of 2026-07-15, dbt Core 1.11.12 remains the latest stable Core release; 1.12.0 is still a release candidate. `dbt-databricks` 1.12.2 remains the latest stable adapter release.

- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12)
- [dbt Core 1.11.12 Python and dependency metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml)
- [`dbt-databricks` 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2)
- [`dbt-databricks` 1.12.2 Python, Core, adapter, and common constraints](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml)
- [dbt warning configuration](https://docs.getdbt.com/reference/global-configs/warnings)
- [Core 1.11.12 warning/flag parameters](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py)
- [Core 1.11.12 flag precedence and mutual exclusion](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py)
- [Core 1.11.12 selector warning behavior](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/graph/selector.py)
- [Core 1.11.12 `NothingToDo`, artifact writing, and ephemeral-result behavior](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/runnable.py)
- [dbt build](https://docs.getdbt.com/reference/commands/build)
- [Core 1.11.12 BuildTask runner collections](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py)
- [dbt artifact production](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [manifest JSON](https://docs.getdbt.com/reference/artifacts/manifest-json)
- [manifest v12 schema](https://schemas.getdbt.com/dbt/manifest/v12.json)
- [run-results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [run-results v6 schema](https://schemas.getdbt.com/dbt/run-results/v6.json)
- [sources JSON](https://docs.getdbt.com/reference/artifacts/sources-json)
- [sources v3 schema](https://schemas.getdbt.com/dbt/sources/v3.json)
- [Core 1.11.12 source-freshness task](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/freshness.py)
- [JSON artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts)
- [other dbt artifacts](https://docs.getdbt.com/reference/artifacts/other-artifacts)
- [Core 1.11.12 manifest and semantic-manifest writing](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/parser/manifest.py)
- [events and structured logs](https://docs.getdbt.com/reference/events-logging)
- [log configuration](https://docs.getdbt.com/reference/global-configs/logs)
- [Core 1.11.12 emission of `MainReportVersion.log_version`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py)
- [dbt retry](https://docs.getdbt.com/reference/commands/retry)
- [dbt environment variables](https://docs.getdbt.com/reference/dbt-jinja-functions/env_var)
- [dbt anonymous usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats)

## Exact pinned-contract verification

| Contract area | Re-review result | Evidence and conclusion |
|---|---|---|
| Core/adapter pair | `PASS` | Product plan lines 124-138 pin Core 1.11.12 and adapter 1.12.2. The adapter declares `dbt-core>=1.11.2,<1.11.13`, so the exact pair is compatible. |
| Python | `PASS` | Both packages require Python `>=3.10`, publish 3.10-3.13 classifiers, and the adapter tests 3.10-3.13. The plan correctly limits the candidate to serverless environment 5/Python 3.12.3 and rejects 3.14 until requalification. |
| Zero-execution warnings | `PASS` | Lines 142-168 use exactly `NoNodesForSelectionCriteria` and `NothingToDo`, reject explicitly set `warn_error` even when false, inspect current and legacy aliases, and reject empty run-results from ephemeral-only selection. This matches the tagged selector, runnable task, and flag tests. |
| Command/artifact matrix | `PASS_WITH_REQUIRED_FLAG_FIX` | Lines 153-166 correctly make optional `deps` plus one named-selector `build` the only ready sequence and classify all documented primary alternatives. The non-warning resolved flag contract is still incomplete; see reopened `DBT-P0-002`. |
| Primary schemas | `PASS` | Lines 195-205 correctly require manifest v12 and run-results v6. They correctly avoid requiring `adapter_type` in run-results v6, where the field does not exist. |
| Invocation pair | `PASS` | The non-null parseable and equal `invocation_id`, exact Core version, `args.which=build`, manifest adapter type, AttemptKey/ordinal, cardinality, hash, and duplicate-result rules are appropriately stricter than the schemas. The plan correctly does not compare `generated_at`, `invocation_started_at`, or `env`. |
| Build result crosswalk | `PASS` | Line 199 correctly resolves each result exactly once across `nodes`, `unit_tests`, `saved_queries`, `exposures`, or `functions`, matching Core 1.11.12 `BuildTask.RUNNER_MAP`. |
| Ancillary target output | `PASS` | Line 201 correctly treats semantic manifest, partial-parse data, graph output, and compiled/run trees as expected but untrusted ancillary entries. It correctly counts canonical archive entries rather than repeated `ArtifactWritten` events. |
| Source freshness | `PASS` | Lines 161 and 205 correctly keep it deferred and separate: manifest v12 plus sources v3, result IDs resolving to `manifest.sources`, with no run-results, `args`, or adapter-type contract. |
| Structured log contract | `CHANGES_REQUIRED` | The plan requires JSON info-level file logs, but neither lines 195-205 nor fixture lines 335-339 persist or qualify the actual `MainReportVersion.data.log_version`. See reopened `DBT-P0-004`. |

## Initial finding outcomes

| Initial finding | Re-review outcome | Current evidence | Remaining condition |
|---|---|---|---|
| `DBT-P0-001` | `RESOLVED` | Product plan lines 142-168 and 337-339 | Implement the three named zero-execution fixtures and prove none can become `Observable`. |
| `DBT-P0-002` | `PARTIALLY_RESOLVED — REOPENED` | Lines 153-166 provide the command/artifact matrix and semantic-change warning. | Define and fixture the full resolved flag/path contract, not only warning flags. |
| `DBT-P0-003` | `PARTIALLY_RESOLVED — REOPENED` | Lines 195-205 provide strong pair invariants; lines 207-217 provide ordered states. | Make absence versus retrieval-unavailability predicates exclusive and align the outcome summary with `PARTIAL`. |
| `DBT-P0-004` | `PARTIALLY_RESOLVED — REOPENED` | Lines 124-138, 201, 228-235, and 321 pin the runtime and complete locks. | Restore the required actual structured-log version to persisted compatibility evidence and fixtures. |
| `DBT-P0-005` | `RESOLVED` | Lines 203, 304, and 339 | P1/P4 fixtures must keep inventory-only resources as `NO_RESULT_RECORDED` and preserve explicit skipped results. |
| `DBT-P0-006` | `RESOLVED FOR P0; P2 FOLLOW-UP REMAINS` | Lines 147-150 and 337-339 define per-ordinal directories, closed files, five-by-20-MiB bounds, rotation/truncation/path fixtures, and pre-initialization absence. | P2 must emit explicit truncation/absence state and quarantine malformed JSONL without parsing `msg`. |
| `DBT-P0-007` | `RESOLVED FOR P0; P1/P7 FOLLOW-UP REMAINS` | Lines 219-235, 290-292, documentation plan line 62, and P7 exit evidence | Field-level source/type/nullability/classification/UI rules and adversarial user-controlled-string denial tests remain implementation gates. |
| `DBT-P0-008` | `RESOLVED` | `AGENTS.md` lines 7-10, ADR lines 35 and 50/66-68, product plan lines 45-51 and P9 | Run the complete core product suite with every AI feature disabled. |

No wholly new dbt finding was identified. The required changes below reopen incomplete acceptance conditions from `DBT-P0-002`, `DBT-P0-003`, and `DBT-P0-004`.

## File-set review

| File | Verdict | dbt re-review result |
|---|---|---|
| `README.md` | `PASS` | Product principles still put deterministic artifacts first and raw logs outside the ordinary UI. |
| `AGENTS.md` | `PASS` | The repository contract prohibits arbitrary dbt input, active Volume logging, unsafe artifact exposure, floating dependencies, and AI enforcement. |
| `docs/index.md` | `PASS` | It accurately routes readers to the contract, reviews, decisions, and source register. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | The App does not execute dbt; the selected exact candidate remains explicitly provisional until qualification. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | The exact artifact contract is strong, but the three reopened conditions below are normative contradictions or missing scanner/compatibility predicates. |
| `docs/plans/review-process.md` | `PASS` | Lines 25-34 and 124-140 give the dbt reviewer the correct scope for every P0-P10 part. |
| `docs/plans/documentation-plan.md` | `PASS_WITH_FOLLOW_UP` | The D2 references have the correct homes. They must inherit the final resolved-flag, state, and log-version rules. |
| `docs/research/source-register.md` | `PASS_WITH_FOLLOW_UP` | It now contains the previously missing warning, freshness, Python, BuildTask, and ancillary sources. Add the tagged flag-precedence and log-version sources when resolving the reopened findings. |
| `docs/reviews/p0-planning-baseline/resolution.md` | `CHANGES_REQUIRED` | Its DBT-P0-002 through DBT-P0-004 rows currently claim complete resolution beyond what the frozen product plan defines. Update only after the contract edits and this re-review are resolved. |

## P0-P10 dbt review matrix

| Part | Verdict | Current dbt-specific strength | Required gate or follow-up |
|---|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Exact candidate, schemas, warning policy, command matrix, crosswalk, and evidence boundary are now explicit. | Resolve the three reopened findings, obtain all re-review verdicts, then commit and push the reviewed baseline as required by product plan lines 402-411. |
| P1 — Capture library | `CHANGES_REQUIRED` | Lines 195-205 and 335-339 now define nearly all golden artifact cases without Databricks. | Add exact resolved-flag fixtures, exclusive archive-presence/retrieval predicates, and allowlisted structured-log versions. |
| P2 — Collector and reconciliation | `CHANGES_REQUIRED` | Per-ordinal paths, closed-log bounds, early absence, malformed archives, and exactly-once AttemptKey behavior are planned. | Implement the corrected capture-state distinction; expose truncation/absence; quarantine malformed JSONL; never parse `msg`; validate `log_version` when a structured log exists. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Exact Core/adapter/Python/CLI/environment candidates and full hash locks are required. | Generate or verify the complete resolved dbt flag/path contract and include the locked `dbt-common`/log-version qualification evidence. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | Lines 203 and 304 keep outer, capture, invocation, and node/test outcomes separate and curated-only. | Query/UI fixtures must distinguish unselected inventory, explicit skip, failure, warning, and successful independent results without using `msg`. |
| P5 — Job onboarding | `CHANGES_REQUIRED` | Five scanner states, a closed command matrix, semantic-change review, and no behavior-preserving claim are strong. | `READY` must depend on all resolved artifact/log/path/privacy flags, with override fixtures, not only command and warning configuration. |
| P6 — Controlled actions | `PASS` | Only a pre-bound Job can run; no selector, flag, command, variable, or path enters through the user or AI action. | Preserve the immutable approved command/selector and use the same validator on every run. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Allowlisted fields, failure-only raw evidence, defense-in-depth scrubbing, retention, and safe operation schemas are correctly planned. | Complete field classification, raw-access denial, deletion verification, and adversarial user-controlled value tests. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | A small real run, zero-execution cases, exact schemas, lifecycle inventory, and bounded cost are covered. | Persist and show actual Core, adapter, Python, schema, and structured-log versions; prove the three exclusive absence/partial/unavailable paths before cleanup. |
| P9 — Optional intelligence | `PASS` | AI remains advisory, receives no raw evidence, and cannot construct or authorize dbt execution. | Complete the AI-disabled core-suite gate. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Repeatable installs, upgrade, uninstall, and non-author journeys are required. | Classify every design-partner Job against the closed version/command/flag matrix; never expand support implicitly from a successful run. |

## Reopened findings

### DBT-P0-002: Enforce the complete resolved flag and path contract

- Re-review outcome: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/product-plan.md:140-168`, P1, P3, and P5
- Evidence: The plan names JSON artifacts, JSON info-level file logs, disabled anonymous statistics, and task-local paths, but only warning flags have exact scanner predicates. Core 1.11.12 lets project and environment values set `write_json`, `log_format_file`, `log_level_file`, `send_anonymous_usage_stats`, `target_path`, and `log_path`. For example, an inherited `write_json=false` can remove the primary evidence unless the generated invocation overrides it or the scanner rejects it.
- User/system impact: A Job can be classified `READY` while writing no run-results, text rather than JSON logs, artifacts to a stale/shared directory, logs outside the bounded subtree, or anonymous dbt usage data contrary to the regulated contract.
- Required change:
  1. Add a normative resolved-value table for at least `which=build`, exactly one approved selector, no `vars`, approved `warn_error_options`, `write_json=true`, `log_format_file=json`, `log_level_file=info`, `send_anonymous_usage_stats=false`, and exact per-attempt/per-ordinal `target_path` and `log_path`.
  2. State whether the new-job template supplies each value through a CLI flag or another reviewed precedence source. The safest generated Core 1.11.12 flags are `--write-json`, `--log-format-file json`, `--log-level-file info`, `--no-send-anonymous-usage-stats`, `--target-path <product-path>`, and `--log-path <product-path>`, in addition to the existing selector and warning options.
  3. Require existing-job scanning to evaluate the resolved value after CLI/environment/project/deprecated-profile precedence, not merely search command text.
  4. Keep the collector byte/file cap authoritative. If `log_file_max_bytes` is unbounded or above policy, reject it or explicitly record truncation rather than relying on the dbt logger to enforce the product boundary.
- Acceptance test: Fixtures that set project/environment overrides for `write_json=false`, text file logs, a foreign log/target path, usage statistics enabled, and an unbounded log file must never return `READY` unless an approved higher-precedence value demonstrably produces the exact target/log output. Two scans return the same state, stable reason, and proposed patch.

### DBT-P0-003: Make absence, partial evidence, and retrieval unavailability exclusive

- Re-review outcome: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/product-plan.md:12-17` and `207-217`
- Evidence: Line 17 says any failed Job with no dbt artifact is `NOT_PRODUCED`. Line 214 correctly says dbt-start evidence without a complete result pair is `PARTIAL`. Separately, line 211 makes an archive that “cannot be retrieved” `ARCHIVE_UNAVAILABLE`, while line 215 makes an attempt with no artifact/start evidence `NOT_PRODUCED`. An early Git, library, compute, process-start, or CLI-argument failure can have no archive to retrieve and no dbt-start evidence, satisfying the latter two descriptions simultaneously; precedence would choose `ARCHIVE_UNAVAILABLE` even though lines 17 and 217 imply `NOT_PRODUCED`.
- User/system impact: Implementations can label the same early failure as unavailable or not produced. Operators then receive the wrong recovery action: retry archive retrieval versus repair the Job before dbt can start.
- Required change:
  1. Change line 17 to distinguish artifact-free invocations that have dbt-start evidence (`PARTIAL`) from attempts with neither artifact nor start evidence (`NOT_PRODUCED`).
  2. Define the archive retrieval input as distinct states such as confirmed absent/not created versus expected or known to exist but still inaccessible after bounded retries. Use `ARCHIVE_UNAVAILABLE` only for the latter.
  3. If the Databricks API cannot distinguish absence from unavailability in a supported environment, document the conservative mapping instead of promising both states.
  4. Keep a successfully retrieved but malformed or contradictory archive in `INVALID_CAPTURE_CONTRACT`, not `ARCHIVE_UNAVAILABLE` or `NOT_PRODUCED`.
- Acceptance test: Three fixtures must be exclusive: an outer Git/library failure with confirmed no dbt archive/start event becomes `NOT_PRODUCED`; an info-level dbt-start event or valid manifest without a complete pair becomes `PARTIAL`; and a known/expected archive whose retrieval remains denied, expired, or transport-failed after reconciliation becomes `ARCHIVE_UNAVAILABLE`. Each yields one state and one distinct next action.

### DBT-P0-004: Persist and qualify the structured-log version

- Re-review outcome: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/product-plan.md:124-138`, `195-205`, and `335-339`
- Evidence: The initial finding required actual Core, adapter, Python, artifact-schema, and log-version evidence. Baseline 0.2 persists the first four but omits log version. In Core 1.11.12, preflight emits the info-level `MainReportVersion` event with `data.log_version`, sourced from the locked `dbt-common` event library. The product already requires info-level JSON file logs, so this field is available whenever logging initializes.
- User/system impact: A change in the structured event contract can silently alter diagnostic parsing while the Core/adapter versions appear unchanged, particularly if a different allowed `dbt-common` resolution enters the environment.
- Required change:
  1. Add actual `log_version` to the compatibility evidence persisted for every invocation that emitted structured logs; use an explicit absent/not-initialized state for pre-log failures.
  2. Include `dbt-common` in the full hash lock and associate each supported log version with golden JSONL fixtures and an allowlisted parser contract.
  3. Reject or quarantine an unknown log version for structured-event normalization without invalidating an otherwise valid primary artifact pair solely because optional diagnostics are absent.
  4. Add wrong/unknown/missing-after-start log-version cases to P1/P2/P8 fixtures and to `reference/artifact-and-log-fields.md` and `reference/support-matrix.md`.
- Acceptance test: Changing the locked event library or a fixture’s `MainReportVersion.data.log_version` blocks structured-event normalization until qualified; a failure before logger initialization records an explicit absence reason and still uses outer Lakeflow evidence.

## Resolution and re-review

- Resolution: pending for the three reopened conditions above
- Required validation before another dbt re-review:
  - Frozen product plan with the complete resolved flag/path table and override fixtures.
  - Exclusive and testable archive-absence/retrieval-unavailability predicates, plus a corrected outcome summary.
  - Persisted structured-log version contract and fixture list tied to the locked event dependency.
  - Updated source-register and resolution-ledger rows.
  - New immutable author-input hash.
- Re-review verdict: `CHANGES_REQUIRED`
