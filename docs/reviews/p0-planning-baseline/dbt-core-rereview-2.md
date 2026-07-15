# Second dbt Core re-review: P0 planning baseline 0.3

- Reviewed input: frozen pre-commit author file set defined in `resolution.md`
- Re-review input SHA-256: `3e81a74f338000c7441bcb0a643991e958b34f469d71112d81e18b555a5561ae`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `CHANGES_REQUIRED`
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.3 resolves the structured-log version finding and most of the invocation and capture-state findings. It now has the correct Core 1.11.12 flags, current and legacy environment aliases, schema pair, BuildTask collections, separate archive-retrieval state, ordered capture-state evaluation, actual `MainReportVersion.data.log_version`, exact locked `dbt-common` evidence, and quarantine semantics that do not invalidate a valid primary artifact pair.

P0 is not ready to accept because two implementation-significant ambiguities remain in the frozen contract:

1. `DBT-P0-002` treats `dbt_project.yml:flags` and deprecated `profiles.yml:config` as a precedence chain. Tagged Core 1.11.12 instead raises `DbtProjectError` whenever both mappings are non-empty, before project flag resolution, even when an approved CLI override exists. The scanner fixtures do not cover this error. The contract also needs to say which shared observability/privacy flags apply to optional `deps`, because the resolved table's command row can only describe `build` and `deps` does not accept `--target-path`.
2. `DBT-P0-003` permits a valid manifest without a complete pair to become `PARTIAL`, but the prior `INVALID_CAPTURE_CONTRACT` predicate says cardinality failures win first. It does not say whether a single valid primary file is an incomplete partial capture or an invalid pair, and a run-results-only archive can otherwise match no terminal predicate. The missing-file fixture is not split into manifest-only and run-results-only outcomes.

`DBT-P0-004` is resolved. These remaining issues are bounded contract edits; I found no architecture blocker or reason to change the selected Core, adapter, or Python candidate.

## Immutable input verification

The hash scope in `resolution.md` is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently hashed each scoped file with SHA-256 and then hashed the sorted digest list. The result is:

```text
3e81a74f338000c7441bcb0a643991e958b34f469d71112d81e18b555a5561ae
```

The repository still has no commit. This file-set digest is therefore the immutable review identity. Review reports and `resolution.md` are outside the author-input hash. No author-owned file was edited during this review.

## Current primary sources checked

As of 2026-07-15, Core 1.11.12 is the latest stable dbt Core release; 1.12.0rc3 is a prerelease. `dbt-databricks` 1.12.2 is the latest stable adapter release.

- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12)
- [dbt Core 1.11.12 Python and dependency metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml)
- [`dbt-databricks` 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2)
- [`dbt-databricks` 1.12.2 Python/Core/common constraints](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml)
- [dbt global flags and available environment aliases](https://docs.getdbt.com/reference/global-configs/about-global-configs)
- [dbt command-line option precedence](https://docs.getdbt.com/reference/global-configs/command-line-options)
- [Core 1.11.12 option declarations and current/legacy aliases](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py)
- [Core 1.11.12 flag resolution](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py)
- [Core 1.11.12 project/profile flag loading](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/config/project.py)
- [Core 1.11.12 command-specific option decorators](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/main.py)
- [dbt warning configuration](https://docs.getdbt.com/reference/global-configs/warnings)
- [dbt JSON artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts)
- [dbt log configuration](https://docs.getdbt.com/reference/global-configs/logs)
- [dbt anonymous usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats)
- [dbt build](https://docs.getdbt.com/reference/commands/build)
- [Core 1.11.12 BuildTask runner collections](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py)
- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [manifest JSON](https://docs.getdbt.com/reference/artifacts/manifest-json)
- [manifest v12 schema](https://schemas.getdbt.com/dbt/manifest/v12.json)
- [run-results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [run-results v6 schema](https://schemas.getdbt.com/dbt/run-results/v6.json)
- [Core 1.11.12 `MainReportVersion` emission](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py)
- [`dbt-common` 1.37.5 package release](https://pypi.org/project/dbt-common/1.37.5/)
- [dbt events and structured logs](https://docs.getdbt.com/reference/events-logging)

The tagged package constraints yield `dbt-common>=1.37.3,<1.38.0`. The currently published eligible versions are 1.37.3, 1.37.4, and 1.37.5. I verified the published wheel SHA-256 values against the package index before inspecting them; all three contain `LOG_VERSION = 3` and a rotating-file `backupCount=5`. This observation does not replace the product's required exact dependency lock: the selected locked wheel and hash, not the floating range or moving source branch, are the qualification input.

## Exact contract verification

| Contract area | Re-review result | Exact conclusion |
|---|---|---|
| Core/adapter/Python candidate | `PASS` | Core 1.11.12 and adapter 1.12.2 are the current stable candidate. The adapter constrains Core to `>=1.11.2,<1.11.13` and `dbt-common` to `>=1.37,<1.38`; Core requires Python `>=3.10` and `dbt-common>=1.37.3`. Python 3.12.3 is inside the published/tested 3.10-3.13 intersection. |
| Current and legacy environment aliases | `PASS` | Core 1.11.12 registers `DBT_ENGINE_*` first and the corresponding legacy `DBT_*` alias second for the reviewed options. A CLI value wins over either environment value; the current alias wins when both aliases are set. |
| CLI/environment/project resolution | `PASS` | The generated `build` CLI flags in lines 170-181 win over environment and project values. The required values for JSON artifacts, JSON/info file logs, usage opt-out, task-local paths, and rotation match tagged option names and types. |
| Project/profile interaction | `CHANGES_REQUIRED` | Lines 168 and 380 describe project/profile/environment precedence, but Core's `read_project_flags` raises when both `dbt_project.yml:flags` and `profiles.yml:config` are non-empty. This is a validation error, not a lower-priority value. It occurs before CLI values can make the invocation safe. |
| Optional `deps` | `CHANGES_REQUIRED` | `deps` accepts the global log, warning, usage, and write-json flags but has no `target_path` command option. The plan requires separate ordinal paths and a closed structured log, yet the resolved table has only one command row, `build`. A per-command template is required so `deps` cannot run with default text/debug logs or anonymous usage enabled and so an unsupported `--target-path` is not generated for it. |
| Warning contract | `PASS` | `NoNodesForSelectionCriteria` and `NothingToDo` are exact Core 1.11.12 warning names. The plan correctly rejects any explicitly supplied `warn_error`, including false, when approved `warn_error_options` is used. |
| Primary schemas and metadata | `PASS` | Manifest v12 plus run-results v6 is the correct build pair. The plan correctly requires matching parseable non-null invocation IDs, exact Core version, `args.which=build`, manifest adapter type, AttemptKey/ordinal binding, hashes, non-empty unique results, and full schema validation. It correctly does not require run-results adapter type or compare `generated_at`, `invocation_started_at`, or `env`. |
| Result-ID collections | `PASS` | Core 1.11.12 `BuildTask.RUNNER_MAP` covers models, snapshots, seeds, tests, unit tests, saved queries, exposures, and functions. These serialize into exactly the five manifest dictionaries listed by the plan: `nodes`, `unit_tests`, `saved_queries`, `exposures`, and `functions`. Sources, macros, metrics, and semantic models are correctly rejected as build-result owners. |
| Complete pair | `PASS` | Exactly one manifest and one run-results candidate satisfying all invariants becomes `COMPLETE`; duplicate, ambiguous, unknown-schema, mismatched, empty, duplicate-result, or unresolved-ID input fails closed. |
| Incomplete pair | `CHANGES_REQUIRED` | The ordered predicates do not define whether one valid primary file fails pair cardinality at step 2 or can reach a later state. Step 4 expressly allows a valid manifest to prove `PARTIAL`, while an otherwise valid run-results-only archive has no stated terminal outcome. |
| Retrieval versus capture state | `PASS` | `RETRIEVED`, `CONFIRMED_ABSENT`, and `UNAVAILABLE` are exclusive inputs. Indeterminate existence maps conservatively to `UNAVAILABLE`; malformed retrieved content stays in `INVALID_CAPTURE_CONTRACT`; confirmed absence plus no start evidence reaches `NOT_PRODUCED`. This resolves the prior overlap. |
| Structured-log version | `PASS` | The plan now persists `MainReportVersion.data.log_version` and the exact locked `dbt-common` version whenever JSON logging starts. `VALID`, `NOT_INITIALIZED`, `UNKNOWN_VERSION`, `MALFORMED`, and `TRUNCATED` stay separate from primary capture; unknown/malformed/truncated diagnostics are quarantined without parsing `msg` or invalidating a valid pair. |
| Fixtures and documentation plan | `PASS_WITH_REQUIRED_PAIR/PRECEDENCE_FIX` | Lines 376-380 and the D2 reference set cover override, path, rotation, schema, collection, capture, and log-version behavior. Add the exact conflict and incomplete-pair cases below; the planned reference homes are otherwise correct. |

## Reopened finding dispositions

| Finding | Focused re-review disposition | Evidence in baseline 0.3 | Remaining acceptance condition |
|---|---|---|---|
| `DBT-P0-002` | `PARTIALLY_RESOLVED — REOPENED` | Product plan lines 153-200 and 376-380 now define the supported sequence, exact build flags, aliases, caps, deterministic scanner result, and override fixtures. | Model simultaneous project/profile maps as Core's configuration error and define the exact shared versus command-specific `deps`/`build` argv contract. |
| `DBT-P0-003` | `PARTIALLY_RESOLVED — REOPENED` | Lines 227-257 now define exact schemas, pair equality, BuildTask collections, retrieval input, conservative indeterminate mapping, and ordered states. | Make primary-file absence/cardinality total: explicitly classify manifest-only and run-results-only archives and fixture both. |
| `DBT-P0-004` | `RESOLVED` | Lines 137-151, 233-235, 362, and 376-380 require a complete exact dependency lock, actual runtime/schema/log versions, an allowlisted parser pair, independent structured-log states, quarantine, and qualification reopening on dependency change. | P1/P3/P8 must produce the already-required lock, known-version fixture, missing/unknown/malformed/truncated cases, and actual evidence; this is implementation evidence at those parts, not a deferred P0 contract correction. |

The previously resolved `DBT-P0-001`, `DBT-P0-005`, `DBT-P0-006`, `DBT-P0-007`, and `DBT-P0-008` contracts did not regress.

## Required corrections and exact acceptance criteria

### DBT-P0-002: Represent Core's configuration error and split per-command enforcement

- Severity: high
- Affected contract: `docs/plans/product-plan.md:153-200`, compatibility fixtures, scanner, P3, and P5
- Evidence: Core 1.11.12 `read_project_flags` loads both mappings and raises `DbtProjectError` if both are non-empty. `Flags` calls this loader after CLI/environment assignment; therefore an approved CLI override does not turn that invalid configuration into a runnable resolved value. Separately, `deps` receives the global flag decorators but not the `target_path` decorator in tagged `cli/main.py`.
- User/system impact: A scanner can return `READY` for an invocation that Core rejects before execution, or a generated optional `deps` command can send anonymous dbt telemetry or produce text/debug logs outside the qualified diagnostic contract. An attempted `--target-path` on `deps` would itself be unsupported.
- Required correction:
  1. State that non-empty `dbt_project.yml:flags` plus non-empty deprecated `profiles.yml:config` is a deterministic configuration conflict and therefore `NEEDS_CHANGES`, regardless of CLI overrides. Do not describe the two mappings as ordered precedence inputs.
  2. Define two exact command templates. The optional `deps` ordinal has no selector and no required execution artifact; it must still enforce empty CLI vars, JSON/info file logging, anonymous-usage opt-out, ordinal-local `log_path`, and the 20-MiB rotation value. It must not generate an unsupported `--target-path`; any task-local target directory for the ordinal is only a reserved collector boundary. The primary `build` ordinal receives every row in the resolved table, including its ordinal-local target and log paths.
  3. State the result for conflicting current and legacy environment aliases, and include `DO_NOT_TRACK` in the computed usage-statistics result. The implementation may accept the tagged Core precedence or deliberately require cleanup, but it must return one stable state and reason.
  4. Preserve two-scan determinism and the rule that only `NEEDS_CHANGES` can produce the reviewed patch.
- Acceptance tests:
  - A fixture with any non-empty project `flags` and any non-empty deprecated profile `config` returns `NEEDS_CHANGES` with a stable Core-configuration-conflict reason even when every required CLI override is present.
  - Golden generated argv for zero-command-prerequisite and `deps`-plus-`build` paths contain only options accepted by each tagged command and prove the resolved values, exact ordinal paths, and no anonymous usage.
  - Current/legacy alias conflicts and `DO_NOT_TRACK` fixtures reproduce Core 1.11.12 behavior or a documented stricter scanner policy twice with the same state/code/patch.

### DBT-P0-003: Make incomplete primary-file cardinality total

- Severity: high
- Affected contract: `docs/plans/product-plan.md:227-257`, compatibility fixtures, P1, P2, and P8
- Evidence: Step 2 gives invalid pair cardinality precedence, but step 4 expressly permits a valid manifest without a complete pair to establish `PARTIAL`. The contract does not define “invalid candidate” narrowly enough to reconcile those statements. A run-results-only archive is neither a complete pair nor a valid-manifest/start case and cannot reach `NOT_PRODUCED` because an artifact exists.
- User/system impact: Two collectors can classify the same incomplete archive differently, or fail to emit any capture state. A run-results file without its manifest must never create node rows because there is no trusted inventory against which to resolve IDs.
- Required correction:
  1. Define missing-counterpart behavior explicitly. The safest asymmetric rule is: one valid manifest plus allowlisted start evidence is `PARTIAL`; a run-results candidate without its matching manifest is `INVALID_CAPTURE_CONTRACT`. If a different rule is selected, it must still yield exactly one state and zero trusted node-result rows.
  2. Define “invalid candidate” so malformed/unknown/duplicate/contradictory primary files take step 2, while the narrowly allowed manifest-only partial case can reach step 4.
  3. Keep a retrieved archive with neither primary candidate separate: allowlisted dbt-start evidence makes it `PARTIAL`; no artifact/start evidence makes it `NOT_PRODUCED`.
- Acceptance tests:
  - Fixture manifest-only, run-results-only, neither-file-with-start, and neither-file-without-start archives separately.
  - Each fixture yields exactly one retrieval state, one capture state, one stable next action, and no trusted node-result row unless a complete valid pair exists.
  - Reconciliation and repeated collection preserve that classification for the same AttemptKey and artifact hashes.

### DBT-P0-004: Resolved acceptance contract

- Disposition: resolved
- Exact acceptance retained for later implementation gates:
  1. The full hash lock selects one exact eligible `dbt-common` distribution and records its package hash; any dependency change reopens qualification.
  2. A JSON log with the allowlisted `MainReportVersion.data.log_version` and matching locked `dbt-common` can become `VALID` only after its golden parser fixture passes.
  3. An unknown version becomes `UNKNOWN_VERSION`. Missing or malformed version evidence after other logger-start evidence becomes `MALFORMED` or demonstrably `TRUNCATED`; it never becomes `VALID`. A true pre-logger failure becomes `NOT_INITIALIZED` with an explicit reason.
  4. Unknown, malformed, or truncated diagnostics are quarantined from structured-event normalization and never parsed via `msg`; a separately valid manifest/run-results pair remains valid.

## P0-P10 regression matrix

| Part | Focused dbt verdict | Regression result or required gate |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Correct the project/profile error and incomplete-pair totality before accepting the baseline. |
| P1 — Capture library | `CHANGES_REQUIRED` | Add exact project/profile conflict and manifest-only/run-results-only fixtures; retain every schema, collection, structured-log, and capture-state fixture already listed. |
| P2 — Collector and reconciliation | `CHANGES_REQUIRED` | Implement the total incomplete-pair state machine and independent structured-log quarantine; preserve one AttemptKey under reconciliation. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Generate command-specific accepted argv and the complete exact hash lock. Do not claim the unsupported `deps --target-path` form. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | No regression: inventory, invocation, node/test, collector, and capture outcomes remain separate and curated-only. P4 fixtures must consume the final state contract. |
| P5 — Job onboarding | `CHANGES_REQUIRED` | The scanner must model Core configuration failure, not only value precedence, before returning `READY`. |
| P6 — Controlled actions | `PASS` | No regression: no user or AI input can construct command, selector, vars, flags, or paths. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | No regression: field allowlisting remains primary and secret scrubbing defense in depth. Complete the already-owned field and denial tests. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | Prove command-specific argv, all incomplete/retrieval states, exact runtime/schema/log versions, and final cleanup within the approved cost envelope. |
| P9 — Optional intelligence | `PASS` | No regression: deterministic capture and validation work with AI disabled. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | No regression: every partner Job must remain inside the closed version/command/flag matrix; do not expand support from one successful run. |

## File-set result

| File | Verdict | dbt result |
|---|---|---|
| `README.md` | `PASS` | Artifact-first, customer-local, deterministic, and restricted-log principles remain correct. |
| `AGENTS.md` | `PASS` | Arbitrary dbt input, floating dependencies, unsafe evidence, and AI enforcement remain prohibited. |
| `docs/index.md` | `PASS` | Routes readers to the normative plan, decision, reviews, and sources. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Execution remains in the observed Job and deterministic collection stays outside the App. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | Two bounded normative corrections above are required; the structured-log and remaining dbt contract is sound. |
| `docs/plans/review-process.md` | `PASS` | Immutable independent review, verdict, re-review, and P0-P10 responsibilities remain adequate. |
| `docs/plans/documentation-plan.md` | `PASS_WITH_FOLLOW_UP` | The D2 reference homes cover resolved flags/paths, supported commands, capture states, support matrix, and artifact/log fields. They must inherit the final two corrected predicates. |
| `docs/research/source-register.md` | `PASS_WITH_FOLLOW_UP` | The tagged Core flag, log event, BuildTask, schema, and adapter sources are present. When P3 selects the lock, replace moving-branch logger evidence with the exact locked package/hash evidence. |
| `docs/reviews/p0-planning-baseline/resolution.md` | `CHANGES_REQUIRED` | `DBT-P0-002` and `DBT-P0-003` currently claim complete resolution beyond the frozen predicates. Update them only after the contract corrections and another focused re-review. |

## Resolution and re-review

- `DBT-P0-002`: partially resolved; reopened for the exact Core project/profile error and per-command `deps`/`build` contract.
- `DBT-P0-003`: partially resolved; reopened for total manifest-only/run-results-only classification.
- `DBT-P0-004`: resolved.
- New architecture blockers: none.
- Required next evidence: corrected frozen plan, conflict and incomplete-pair fixtures in the test strategy, updated source/resolution rows, and a new immutable author-input hash.
- Final re-review verdict: `CHANGES_REQUIRED`
