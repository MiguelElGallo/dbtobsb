# dbt Core review: P0 planning baseline

- Reviewed input: pre-commit working tree
- Frozen input SHA-256: `3a637dae8ac48cf7cea7c84ebbec5c9d39cd63a8cd75105f689f5478a7023d98`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `CHANGES_REQUIRED`
- Blockers: none

## Executive verdict

The product direction is sound. The baseline correctly makes capture deterministic, keeps AI outside the trusted execution path, treats `manifest.json` and `run_results.json` as sensitive primary evidence, separates the Lakeflow attempt outcome from the dbt capture outcome, and anticipates failures before dbt artifacts exist.

P0 is not ready to accept because five parts of the dbt contract are not yet precise enough to implement or test consistently:

1. A zero-node selector is not required to fail, even though dbt normally treats it as a warning.
2. The existing-job scanner has no normative allowlist of supported dbt command/artifact classes.
3. The artifact-pair consistency and capture-state precedence rules are not defined.
4. `Python 3.10 or later` is an unbounded compatibility claim, and the runtime dependency lock is not an explicit exit artifact.
5. The normalized data semantics do not yet distinguish manifest inventory from nodes that actually have invocation results.

These are bounded planning changes. I found no architectural blocker to continuing with a private Databricks App plus Bundle after they are resolved.

## Reviewed files

| File | dbt review | Evidence |
|---|---|---|
| `README.md` | `PASS` | Lines 7-15 establish artifact-first evidence, restricted logs, deterministic validation, and three-specialist review. |
| `AGENTS.md` | `PASS` | Lines 5-20 prohibit arbitrary dbt input, active log writes to a Volume, unsafe evidence exposure, and floating runtime support. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | The App does not execute dbt and Lakeflow owns execution and collection (Decision, lines 17-23); AI is not an execution boundary (lines 56-58). |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | The overall model is correct, but the capture contract and several P0-P5 exit conditions need the exact acceptance rules in findings DBT-P0-001 through DBT-P0-005. |
| `docs/plans/review-process.md` | `PASS` | The dbt reviewer remit covers pins, schemas, identity, early failures, retries, overwrite prevention, sensitive fields, and fixtures (lines 25-34); verdict and re-review rules are testable. |
| `docs/plans/documentation-plan.md` | `PASS_WITH_FOLLOW_UP` | The planned `capture-contract`, `artifact-and-log-fields`, `capture-states`, and support-matrix references are the right homes (lines 48-64). Their D2 acceptance criteria must include the resolved P0 invariants. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | The register is current and mostly complete, but it needs the dbt warnings source for zero-node enforcement, a source-freshness/sources-artifact source for command classification, and an explicit Python support/fixture note. |

## Product-plan section review

| Section | Verdict | Exact evidence and review result |
|---|---|---|
| Outcome | `PASS` | `docs/plans/product-plan.md:8-17` correctly refuses to equate job success with observable capture and preserves an outer record for `NOT_PRODUCED`. |
| Fixed constraints | `PASS` | Lines 19-27 are compatible with dbt Core operation and regulated evidence handling. |
| Product boundary | `CHANGES_REQUIRED` | Lines 31-59 correctly reject arbitrary execution, but they do not state which dbt commands and artifact sets qualify as `READY`; see DBT-P0-002. |
| Target architecture | `PASS` | Lines 61-78 keep dbt in a native task and collection out of the App process. |
| Identity model | `PASS` | Lines 80-92 keep the dbt run-as principal separate from collection and read-only App access. |
| Candidate compatibility baseline | `CHANGES_REQUIRED` | Lines 96-104 correctly pair adapter 1.12.2 with Core 1.11.12, but `Python 3.10 or later` is not bounded; see DBT-P0-004. |
| Invocation rules | `CHANGES_REQUIRED` | Lines 106-115 contain the correct principles but no canonical flag template, zero-node enforcement, or supported command table; see DBT-P0-001 and DBT-P0-002. |
| Correlation model | `PASS_WITH_FOLLOW_UP` | Lines 117-133 correctly distinguish the Lakeflow AttemptKey, command ordinal, dbt `invocation_id`, and adapter corroboration. P1 must define artifact-pair equality and duplicate handling; see DBT-P0-003. |
| Evidence priority | `PASS_WITH_FOLLOW_UP` | Lines 135-140 correctly prioritize outer state, artifacts, and structured events. Clarify that structured events exist only after dbt logging initializes and cannot cover Git/library/compute failures before dbt starts. |
| Capture states | `CHANGES_REQUIRED` | Lines 142-150 name the right high-level states but do not define mutually exclusive predicates or precedence; see DBT-P0-003. |
| Regulated data model | `PASS_WITH_FOLLOW_UP` | Lines 152-159 exclude the highest-risk fields and constrain custom environment metadata. P1/P7 still need a field-level classification and the defense-in-depth limits of secret scrubbing; see DBT-P0-007. |
| Installation experience | `PASS_WITH_FOLLOW_UP` | Lines 161-188 prove value with a real row and avoid direct mutation. `Observable` must additionally require the artifact invariants and zero-node rule from DBT-P0-001 and DBT-P0-003. |
| Delivery parts and review gates | `CHANGES_REQUIRED` | Lines 190-206 form a good sequence, but P1, P3, P4, and P5 need the acceptance conditions identified below. |
| Test strategy | `PASS_WITH_FOLLOW_UP` | Lines 208-228 have unusually strong failure coverage, including pre-dbt failures, zero-node selection, rotations, contract violations, and Python models. Add named assertions from DBT-P0-001 through DBT-P0-005 so a fixture cannot pass merely because ingestion did not crash. |
| Cost discipline | `PASS` | Lines 230-238 do not weaken dbt correctness and keep live validation bounded. |
| Marketplace path | `PASS` | Lines 240-249 do not make distribution part of the dbt runtime contract. |
| Decisions still open | `PASS_WITH_FOLLOW_UP` | Lines 251-261 correctly leave the exact dbt matrix open until P1. Add the exact initial Python minor and dependency-lock format to this decision or to P3 acceptance. |
| Definition of planning baseline | `PASS` | Lines 263-272 require all reviews, resolution, an immutable reviewed baseline, and no cloud resource use. P0 remains open while this report is `CHANGES_REQUIRED`. |

## P0-P10 dbt review matrix

| Part | Verdict | dbt-specific evidence | Required acceptance condition or follow-up |
|---|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Product plan lines 94-159 and 263-272 | Resolve DBT-P0-001 through DBT-P0-005 and refresh the source register before accepting the baseline. |
| P1 — Capture library | `CHANGES_REQUIRED` | Line 197 promises schemas, allowlists, hashes, crosswalks, and fixtures. | Add explicit artifact-pair, duplicate-entry, schema/version, command/artifact, capture-state-precedence, and inventory-versus-result invariants. Unit tests must assert each outcome, not only successful parsing. |
| P2 — Collector job | `PASS_WITH_FOLLOW_UP` | Line 198 plus test strategy lines 212-228 cover malformed/missing archives, rotations, retries, repairs, and pre-dbt failures. | Target P2: ingest only closed allowlisted `dbt.log*` files within byte/file limits, group JSONL by `invocation_id`, make writes idempotent by AttemptKey plus artifact hash, and record absence without inventing dbt evidence. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Line 199; review-process line 29 requires exact pins. | Make one tested Python minor and a reproducible dependency lock/constraints artifact part of P3 exit evidence. The generated dbt command must exactly implement the P0 contract and record actual runtime versions. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | Line 200 and regulated data model lines 152-159 | Target P4: display manifest inventory separately from invocation result rows; never infer success, skip, or selection from absence in `run_results.json`; never classify using human `msg`. |
| P5 — Job onboarding | `CHANGES_REQUIRED` | Lines 182-188 and 201 define scanner states but not their dbt predicates. | Define the supported command/artifact matrix and resolved-flag checks so `READY`, `NEEDS_CHANGES`, and `UNSUPPORTED` are deterministic. Include exact reasons and a golden scanner fixture for each row. |
| P6 — Controlled actions | `PASS` | Line 202; fixed boundaries lines 51-59 and invocation rule line 110 | The plan already prohibits arbitrary dbt input and limits execution to a pre-bound job. Acceptance must preserve the approved immutable selector and command contract. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Line 203 and regulated data model lines 152-159 | Target P7: verify raw-evidence deletion, classify identifiers/paths as potentially sensitive, document that `DBT_ENV_SECRET_*` scrubbing is not complete DLP, and test denial of raw-field/UI access. |
| P8 — Bounded live proof | `PASS_WITH_FOLLOW_UP` | Line 204 and staging plan lines 218-228 | Target P8: capture actual Core, adapter, Python, artifact schema, and log-version values; prove a zero-node selector cannot produce `Observable`; retain sanitized query evidence before cleanup. |
| P9 — Optional intelligence | `PASS` | Lines 43-49 and 205; ADR lines 31 and 56-58 | AI remains optional and outside execution. A Genie skill may explain or propose a patch, but must call the same deterministic validator and must not synthesize or execute raw dbt commands. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Line 206 | Target P10: each design-partner project must be classified against the support matrix before onboarding; unsupported versions/commands must fail closed rather than expand support implicitly. |

## Primary sources checked

- [dbt-databricks 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) — current adapter changes, Python-model failure propagation, and Core upper bound.
- [dbt-databricks 1.12.2 dependency declaration](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml) — Python requirement/classifiers and exact Core compatibility range.
- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) — candidate stable Core version.
- [dbt-databricks 1.12.1 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.1) — Databricks job/task IDs in `adapter_response`.
- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts) — common metadata, `invocation_id`, schema versioning, and artifact production.
- [Manifest JSON](https://docs.getdbt.com/reference/artifacts/manifest-json) and [run results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json) — project inventory versus executed-node results and the `unique_id` join.
- [dbt build](https://docs.getdbt.com/reference/commands/build) — one combined manifest/run-results output and downstream skip semantics.
- [sources JSON](https://docs.getdbt.com/reference/artifacts/sources-json) — `source freshness` produces a different primary artifact class.
- [dbt warnings](https://docs.getdbt.com/reference/global-configs/warnings) — a zero-node selector is normally a warning and can be targeted with `NoNodesForSelectionCriteria`.
- [JSON artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) — `--write-json`, unique target paths, and overwrite behavior.
- [Events and logs](https://docs.getdbt.com/reference/events-logging) and [log configuration](https://docs.getdbt.com/reference/global-configs/logs) — JSON event fields, unstable human messages, levels, paths, and formats.
- [dbt retry](https://docs.getdbt.com/reference/commands/retry) — dependency on prior `run_results.json` and inability to recover a failure before any node was recorded.
- [Environment variables](https://docs.getdbt.com/reference/dbt-jinja-functions/env_var) — secret-prefix behavior and deliberate copying of `DBT_ENV_CUSTOM_ENV_*` values into artifacts and logs.
- [Anonymous usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats) — Core telemetry default and opt-out behavior.
- [Databricks native dbt task output](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows) — native archive, individual task-run ID, inline-log truncation, and pre-dbt task boundaries.

## Findings

### DBT-P0-001: Make zero-node selection a deterministic failure

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md:106-115` requires a named selector but does not require targeted warning promotion. `docs/plans/product-plan.md:226-228` lists a zero-node fixture without the expected exit or capture result. dbt documents no matching nodes as a warning and provides `--warn-error-options '{"error":["NoNodesForSelectionCriteria"]}'` for targeted promotion.
- User/system impact: A misspelled or stale approved selector can produce no model work while the dbt task exits successfully. The installer could then mark a job `Observable` despite observing no intended resources.
- Required change:
  1. Add the exact targeted warning policy to the P0 invocation contract, preferably as a CLI override for the pinned Core version.
  2. Define how the scanner handles a conflicting project/profile/environment `warn_error` configuration, because `WARN_ERROR` and `WARN_ERROR_OPTIONS` are mutually exclusive.
  3. Add the warnings page to `docs/research/source-register.md`.
  4. Make the golden fixture assert a non-success dbt exit, zero normalized node results, the documented capture state for the resulting artifact set, and ineligibility for the product-level `Observable` label.
- Acceptance test: A version-controlled selector that matches zero enabled nodes must never cause the installation or job to be labeled `Observable`.

### DBT-P0-002: Define the supported command and artifact matrix

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md:108-115` says to prefer `dbt build`, while `docs/plans/product-plan.md:182-188` requires deterministic scanner outcomes. No normative table says whether `run`, `test`, `seed`, `snapshot`, `compile`, `run-operation`, or `source freshness` is `READY`, patchable, or unsupported. dbt documents that `source freshness` produces `sources.json`, not `run_results.json`.
- User/system impact: Two implementations could classify the same existing job differently or normalize the wrong artifact set. A `source freshness` task could be incorrectly reported as `NOT_PRODUCED`, while multiple artifact-producing commands could silently overwrite one another.
- Required change:
  1. Add a v1 command matrix with command, allowed position, expected artifacts, primary/non-primary role, selector policy, and scanner result.
  2. The simplest safe v1 contract is `dbt deps` as optional setup followed by exactly one named-selector `dbt build` as the primary invocation; explicitly classify every other command.
  3. If `source freshness` is supported, model it as a separate task/capture type with `sources.json`; otherwise mark it `UNSUPPORTED` for v1.
  4. Require the scanner to inspect resolved relevant flags, not just command text, and produce a golden `READY`, `NEEDS_CHANGES`, or `UNSUPPORTED` fixture for each matrix row.
- Acceptance test: Given a job command array and project flag fixture, two independent scanner runs return the same state, reason code, and exact patch.

### DBT-P0-003: Specify artifact-pair invariants and capture-state precedence

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md:117-150` names the crosswalk and capture states but does not define valid-pair predicates. `docs/plans/product-plan.md:197-198` promises schemas and malformed-archive tests without saying what constitutes a mixed or stale pair. dbt artifacts carry a schema URL, dbt version, adapter type, and `invocation_id` in common metadata.
- User/system impact: A leftover manifest and a newer run-results file, duplicate archive entries, an unsupported schema, or artifacts from different invocations could be accepted and joined into false evidence.
- Required change:
  1. Define the candidate artifact allowlist and schema allowlist; for the initial pair, record the fixture-proven manifest and run-results schema versions.
  2. Require the primary `manifest.json` and `run_results.json` to share `metadata.invocation_id`, compatible dbt/adapter identity, and one AttemptKey/command ordinal.
  3. Reject duplicate canonical artifact paths, ambiguous multiple candidates, schema mismatches, and unresolved result `unique_id` values as `INVALID_CAPTURE_CONTRACT` unless a narrowly documented exception is fixture-proven.
  4. Define mutually exclusive predicates and precedence for `COMPLETE`, `PARTIAL`, `NOT_PRODUCED`, `INVALID_CAPTURE_CONTRACT`, and `ARCHIVE_UNAVAILABLE`.
  5. State that no dbt log/artifact is expected when Git checkout, dependency installation, compute startup, or argument parsing fails before dbt logging initializes; only outer Lakeflow evidence is authoritative then.
- Acceptance test: Golden archives containing cross-invocation pairs, duplicate manifest paths, unsupported schema URLs, and missing files each produce one deterministic capture state and never create trusted node-result rows.

### DBT-P0-004: Bound Python support and make dependency resolution reproducible

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Evidence: `docs/plans/product-plan.md:98-104` says `Python 3.10 or later`. The adapter declares `requires-python >=3.10` but publishes classifiers and a test matrix for specific minor versions; an unbounded `or later` claim can include an untested future Python. `AGENTS.md:19` and `docs/plans/review-process.md:29` require exact runtime pins.
- User/system impact: A new Python or transitive dependency release can change parsing, event, or adapter behavior without any product change, invalidating golden evidence and making installation non-reproducible.
- Required change:
  1. Choose one exact initial Python minor supported by the selected Databricks compute environment, or enumerate and fixture-test every supported minor; remove `or later`.
  2. Make a reproducible dependency lock or constraints artifact an explicit P3 deliverable, not only exact top-level adapter/Core pins.
  3. Persist actual Core, adapter, Python, artifact-schema, and log-version values in validation evidence and reject unsupported combinations before capture is labeled valid.
  4. Add the Python/runtime decision and first-party adapter dependency evidence to the source-register caution text.
- Acceptance test: Changing the Python minor or any locked dbt runtime package causes compatibility validation to fail until the new environment has its own golden suite.

### DBT-P0-005: Separate manifest inventory from invocation results

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Evidence: `docs/plans/product-plan.md:37` promises node/test views, and lines 137-139 identify manifest plus run-results as primary evidence, but no semantic rule describes their different populations. dbt documents that the manifest represents the full parsed project while `run_results.json` contains results for executed nodes and joins back through `unique_id`.
- User/system impact: A resource present only in the manifest could be displayed as selected, skipped, successful, or failed even though the invocation produced no result for it. This would corrupt success rates, failure counts, and user investigations.
- Required change:
  1. Define separate project-inventory and invocation-result entities/tables.
  2. Create execution status only from a valid result row; absence means `NO_RESULT_RECORDED`, not success, skip, or failure.
  3. Preserve dbt statuses such as warning, error, fail, skip, and success without collapsing them into Lakeflow state.
  4. Require P4 views and UI fixtures to show job outcome, capture outcome, and dbt node/test outcome separately.
- Acceptance test: A fixture with unselected manifest nodes, a failing upstream test, a skipped descendant, and a successful independent model yields four distinguishable states and correct aggregate counts.

### DBT-P0-006: Close the rotated-log and pre-initialization evidence details in P2

- Verdict: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Evidence: `docs/plans/product-plan.md:112-115` keeps active logs local, and line 228 includes rotated logs and pre-dbt failure fixtures. The precise closed-file allowlist and grouping behavior are deferred.
- User/system impact: Reading only `dbt.log` can omit earlier rotated events; treating missing logs as an ingestion error can misclassify failures before dbt initialized.
- Follow-up owner/target: P2 collector design.
- Follow-up acceptance: Bound file count and total bytes; accept only closed `dbt.log*` files from the expected archive subtree; parse JSONL by `invocation_id` and command ordinal; quarantine malformed lines without parsing human `msg`; record `logs_truncated`/archive absence explicitly.

### DBT-P0-007: Treat secret scrubbing as defense in depth, not evidence classification

- Verdict: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Evidence: `docs/plans/product-plan.md:152-159` already excludes raw code/messages and constrains `DBT_ENV_CUSTOM_ENV_*`. dbt documents special scrubbing for `DBT_ENV_SECRET*`, but artifacts/logs can still contain SQL, relation identifiers, descriptions, variables, and database-provided text unrelated to that prefix.
- User/system impact: Assuming dbt secret masking makes artifacts safe could expose Personal Data or operational metadata through curated fields, screenshots, or diagnostics.
- Follow-up owner/target: P1 field schema and P7 security/operations.
- Follow-up acceptance: Every normalized field has a source path, type, nullability, security classification, and UI exposure rule; secret-prefixed values are never relied on as the sole redaction control; relation/node/path identifiers are treated as potentially sensitive; raw access and deletion paths have denial tests.

### DBT-P0-008: Keep Genie advisory and deterministic validation canonical

- Verdict: `PASS`
- Severity: low
- Evidence: `AGENTS.md:9-10`, ADR lines 31 and 56-58, and product-plan lines 43-49 and 205 keep AI optional and prohibit arbitrary dbt input.
- User/system impact: This prevents an LLM instruction from becoming an authorization or reproducibility boundary.
- Acceptance condition: Any future Genie skill may explain the fixed capture contract, select from approved actions, or generate a reviewable patch, but it must not synthesize raw dbt commands or bypass the scanner/validator.

## Resolution and re-review

- Resolution: pending
- Validation required before re-review:
  - Updated product plan with the exact invocation rule, supported command matrix, artifact invariants, capture-state predicates, bounded Python/runtime support, and inventory-versus-result semantics.
  - Updated source register with the missing primary sources and cautions.
  - Updated P1/P3/P4/P5 exit evidence reflecting the testable conditions above.
  - New frozen input hash or immutable commit identifier.
- Re-review verdict: pending
