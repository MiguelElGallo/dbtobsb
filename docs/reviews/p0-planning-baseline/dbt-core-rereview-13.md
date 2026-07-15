# Thirteenth dbt Core re-review: P0 planning baseline 0.14

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `3402e6cb5c96844be04a4d259fb8ca00d6fd60903e0f801fe2559c048334507a`
- Date: 2026-07-15
- Reviewer: independent dbt Core and dbt-databricks product/security specialist
- Verdict: `PASS`
- Open dbt P0 findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.14 passes the thirteenth independent dbt Core and dbt-databricks review. The new singleton authorization-fence protocol and unsigned-decimal-string canonicalization repair Databricks control-plane concerns without contaminating the native dbt command, AttemptKey, artifact, structured-log, capture, or result domains.

The collector contract is also sufficiently closed at planning level. One `dbt_artifact_registry` row is the immutable root for one native AttemptKey. Its first successful insert stamps the runtime-trust view as observed by that statement; it does not claim trust at the later evidence-table commit. Re-entry for that same AttemptKey reuses the stored tuple. A new native dbt retry, repair, or execution has different native attempt coordinates and therefore a different AttemptKey/root and its own first observation. This per-root interpretation follows the correlation model, unique attempt-directory rule, and P2 requirement of exactly one immutable tuple per attempt; implementation tests must preserve it explicitly.

P6 remains outside dbt execution. Its action, fence, generation, snapshot, actor, Job ID, native run ID, drain identity, lease, and Jobs idempotency token are product control values. Run Now carries only the approved Job ID and the deterministic API idempotency token, with no Job parameters or task override. None of those values can enter dbt argv, environment, selector, vars, target/log paths, artifacts, structured events, AttemptKey, or normalized results.

The decimal-string change is similarly confined. It governs canonical product-control JSON used for runtime-trust/fence digests and the Jobs token. Delta control columns stay numeric. Native `manifest.json`, `run_results.json`, and structured dbt events remain byte-preserved inputs validated against their published schemas; their numbers are neither converted to strings nor re-canonicalized as trust objects.

This is approval of a frozen planning contract. It is not evidence that P1 schemas/parsers, P2 concurrent merge SQL, P3 generated commands and full dependency locks, P6 parameterless dispatch, P8 native archives/races, or P10 representative-project qualification have been implemented.

## Immutable input verification and scope

I used the requested eight-file author scope and globally sorted the paths before hashing each file and the resulting record stream:

```sh
{
printf '%s\n' README.md AGENTS.md docs/index.md
find docs/decisions docs/plans docs/research -type f -name '*.md'
} | LC_ALL=C sort | while IFS= read -r file; do shasum -a 256 "$file"; done | shasum -a 256
```

The result before review was:

```text
3402e6cb5c96844be04a4d259fb8ca00d6fd60903e0f801fe2559c048334507a  -
```

The exact author scope was:

- `AGENTS.md`
- `README.md`
- `docs/decisions/0001-private-app-bundle.md`
- `docs/index.md`
- `docs/plans/documentation-plan.md`
- `docs/plans/product-plan.md`
- `docs/plans/review-process.md`
- `docs/research/source-register.md`

I read all eight files, the prior dbt findings and re-reviews, and the baseline-0.13 cross-review disposition. Review records are outside the author-input digest. I edited no author file and no prior report; this report is the only file written.

## Current primary evidence checked

The following official evidence was checked on 2026-07-15:

- [dbt Core 1.11.12](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) is the latest non-prerelease Core release. Its [tagged package metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml) requires Python 3.10 or newer, advertises CPython 3.10 through 3.13, and admits `dbt-common>=1.37.3,<2.0` and `dbt-adapters>=1.15.5,<2.0`.
- [dbt-databricks 1.12.2](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) is the latest non-prerelease adapter release. Its [tagged package metadata](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml) requires Python 3.10 or newer, `dbt-core>=1.11.2,<1.11.13`, and `dbt-common>=1.37.0,<1.38.0`. The release explicitly raises the Core cap to include 1.11.12 and fixes propagation of failed Python-model result state.
- The official [dbt-common 1.37.5 distribution](https://pypi.org/project/dbt-common/1.37.5/) publishes `dbt_common-1.37.5-py3-none-any.whl` with SHA-256 `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077`. I downloaded and re-hashed the wheel. It contains `LOG_VERSION = 3` and a rotating file handler with five backups, supporting the active-file-plus-five-backups bound.
- Official [dbt artifact documentation](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest documentation](https://docs.getdbt.com/reference/artifacts/manifest-json), and [run-results documentation](https://docs.getdbt.com/reference/artifacts/run-results-json) continue to distinguish project inventory from executed results and use invocation metadata for correlation.
- The exact initial schemas remain [manifest v12](https://schemas.getdbt.com/dbt/manifest/v12.json) and [run-results v6](https://schemas.getdbt.com/dbt/run-results/v6.json). Run-results v6 metadata has no adapter-type property, so the baseline correctly requires adapter type from the manifest and locked runtime inventory rather than inventing a run-results field.
- Tagged [Core 1.11.12 BuildTask](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py) maps executable build results to model, snapshot, seed, test, unit-test, saved-query, exposure, and function runners. The plan's exact result-resolution collections match that source.
- Official [`dbt build` documentation](https://docs.getdbt.com/reference/commands/build) states that one build writes one manifest and one combined run-results artifact and documents downstream skip behavior.
- Official [JSON-artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) keeps target output invocation-configurable and makes overwrite risk explicit. The AttemptKey/ordinal-local target boundary remains necessary.
- Official [events and logging documentation](https://docs.getdbt.com/reference/events-logging) and [log configuration](https://docs.getdbt.com/reference/global-configs/logs) keep event envelope fields and `log_version` distinct from human `msg`, and support independently configured JSON file format, level, log path, and rotation size.
- Tagged Core 1.11.12 [CLI parameters](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py), [flag resolution](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py), [command decorators](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/main.py), and [logger initialization](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py) support the closed warning, privacy/upload, JSON, log, and per-command path contract. In particular, `deps` accepts the governed global flags but not selector or target path.
- Official [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings) supports event-name targeting; tagged Core contains both `NoNodesForSelectionCriteria` and `NothingToDo`. The separate non-empty-results postcondition still handles empty ephemeral-only execution.
- Official [environment-variable documentation](https://docs.getdbt.com/reference/dbt-jinja-functions/env_var) confirms that `DBT_ENV_CUSTOM_ENV_*` values are copied into artifact metadata and structured-log extras, so the plan correctly limits them to opaque nonsensitive identifiers.
- Official [dbt retry documentation](https://docs.getdbt.com/reference/commands/retry) continues to depend on the previous `run_results.json` and can have nothing to retry after an early failure. A complete new Lakeflow attempt remains the supported scheduled retry policy.
- Official [usage-statistics documentation](https://docs.getdbt.com/reference/global-configs/usage-stats) continues to document `DO_NOT_TRACK`; the generated command still disables anonymous telemetry and artifact-ingest upload explicitly.

[Core 1.12.0rc3](https://github.com/dbt-labs/dbt-core/releases/tag/v1.12.0rc3) and [Core 2.0.0-alpha.4](https://github.com/dbt-labs/dbt-core/releases/tag/v2.0.0-alpha.4) are prereleases. Core 1.12 introduces additional parser, status, command, environment, and artifact behavior, and adapter 1.12.2 deliberately caps Core below 1.11.13. The baseline correctly keeps both future lines outside the candidate matrix.

## Baseline 0.14 focused regression

| Baseline 0.14 change | Verdict | dbt conclusion |
|---|---|---|
| Immutable AttemptKey-root trust tuple | `PASS` | The tuple is payload provenance on exactly one `dbt_artifact_registry` root. It is not part of AttemptKey, merge identity, artifact/log hashes, pair validity, event validity, result resolution, capture precedence, or a native outcome. |
| Trust-read versus evidence-commit race | `PASS` | The frozen timestamp is the status view's statement query-evaluation time. A trust generation may change before the evidence write commits; the earlier observation remains immutable and is displayed separately from current runtime trust. No commit-current claim remains. |
| Same-AttemptKey re-entry versus new native attempt | `PASS` | Collector retry, reconciliation, and partial-write repair for an existing root reuse its tuple. A native dbt task retry/repair/execution changes the native AttemptKey coordinates and receives a new root/observation. P2 must fixture both cases. |
| Serializable singleton action fence | `PASS` | Fence claim/drain/phase/release/reopen transitions authorize product actions and lifecycle only. They cannot become a dbt invocation, build-start event, archive state, or artifact predicate. |
| Journal-before-dispatch and same-token recovery | `PASS` | The action ledger and Jobs idempotency token coordinate the external Run Now request. The request body has no workload parameters or dbt override; retrying the same token cannot change dbt correlation. |
| Closed-before-trust/lifecycle ordering | `PASS` | Drain/quiescence affects whether product maintenance may proceed. It cannot reinterpret a completed attempt or mutate an existing dbt artifact/result row. |
| Unsigned decimal-string canonical control fields | `PASS` | The rule is scoped to product-control canonical JSON and Jobs-token input. Native dbt artifact/event JSON is validated as published and retains native numeric representation. |
| Cross-language boundary vectors | `PASS` | Python/generated SQL/JavaScript vectors cover values above JavaScript's safe-integer range without parsing through `Number`. Those fixtures exercise trust/fence digests, not dbt schemas or evidence hashes. |
| Explicit no-Preview/no-multi-table-transaction boundary | `PASS` | The control fence has no effect on dbt's fixed task configuration. Per-table trust/evidence races remain observational and are tested as such rather than represented as one dbt transaction. |

## AttemptKey-root and race interpretation

The planning contract implies this exact sequence for one native attempt:

1. Native Lakeflow coordinates determine AttemptKey before trust lookup. Trust state cannot create, merge, or split that identity.
2. The first successful root insert reads exactly one acceptable `BASE_OBSERVABILITY` status summary and stores its snapshot, generation, state, and view query-evaluation timestamp.
3. If trust changes after that read but before the root commits, the stored tuple remains the earlier observation. The App separately queries current trust and may show N versus N+1, stale, or invalidated.
4. An indeterminate root insert is resolved by exact readback. An existing single root and its tuple win; proven absence permits one new observation. Duplicate/conflicting roots fail closed rather than selecting the most favorable trust value.
5. Invocation/artifact/node rows copy or join the root tuple. They cannot refresh it, and their partial-write recovery cannot promote trust.
6. Collector re-entry for the same native AttemptKey reuses the root. A later native retry, repair, or task execution changes repair/task/execution coordinates, so it creates a different AttemptKey and performs its own first root observation.

This sequence preserves both facts users need: what native dbt evidence says happened, and which runtime-trust summary the collector observed. It intentionally does not prove that trust was current when dbt executed or when the evidence commit became visible.

## Explicit non-contamination review

| dbt boundary | Thirteenth-review result |
|---|---|
| Command and argv | `PASS` — the supported sequence remains optional `deps` followed by one named-selector `build`. Migration, deployment, trust, fence, action, token, drain, actor, user, or AI values have no construction path. |
| Resolved flags and aliases | `PASS` — CLI, current/legacy configured environment aliases, one project-or-profile source, `DO_NOT_TRACK`, and defaults remain the complete resolved inputs. Trust/fence state is not a flag source. |
| Selector, vars, and workload parameters | `PASS` — the selector is version controlled, CLI vars are empty, and P6 Run Now carries no `job_parameters`, selector, vars, or task override. |
| Target and log paths | `PASS` — paths derive only from AttemptKey plus command ordinal. `deps` still receives no target path; `build` has an ordinal-local target boundary. No control value enters either path. |
| AttemptKey | `PASS` — workspace/job/run/repair/task-run/execution coordinates define native attempt identity. Trust snapshot/generation/state/evaluation time and P6 action/fence/token values are excluded. |
| Artifact bytes and hashes | `PASS` — one allowlisted manifest-v12/run-results-v6 pair is validated and hashed in its native form. Product canonicalization cannot rewrite either file or substitute a control-plane `manifest_digest`/`artifact_digest`. |
| Artifact pair | `PASS` — exact schemas, Core version, non-null equal invocation UUID, command ordinal, `args.which=build`, manifest adapter type, non-empty unique results, and exact BuildTask resolution remain mandatory. |
| Structured logs | `PASS` — `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID` remain ordered and command-ordinal scoped. Product control events cannot satisfy `MainReportVersion`, log version, invocation, or primary-build start evidence. |
| Capture precedence | `PASS` — archive unavailable, invalid primary input, complete pair, allowed partial evidence, and not produced remain the only ordered predicates. Neither current nor observed trust is a capture predicate. |
| Node/test outcomes | `PASS` — only valid non-empty run-results entries resolving exactly once through the tagged BuildTask collections create native rows. Fence/action/trust state cannot create, suppress, or alter a dbt result status. |
| Retry, repair, and reconciliation | `PASS` — a new native attempt gets a new AttemptKey/root; collection re-entry for one root is idempotent. Trust changes never merge two attempts or duplicate one. |
| Sensitive fields | `PASS` — raw/compiled code, vars, result/adapter messages, arbitrary metadata/events, custom environment content, and `msg` remain outside ordinary tables. Control fields do not widen that allowlist. |
| Decimal representation | `PASS` — only typed control canonical JSON uses quoted decimal strings. Native artifact numbers and event data remain governed by dbt schemas and parser fixtures. |

## Numbered finding disposition

No new numbered dbt finding is opened. I found no critical, high, medium, or low P0 dbt correctness defect in baseline 0.14.

The following are mandatory later-part acceptance rules, not deferred P0 corrections:

1. P1 schemas and generated interfaces must keep `runtime_trust_manifest_digest`, App deployment digests, `dbt_manifest_sha256`, and `dbt_run_results_sha256` fully qualified and non-substitutable.
2. P2 must implement one compare-protected root per AttemptKey and fail closed on duplicate/conflicting root rows. Concurrent collectors, response loss, and partial commits must not select a later or more favorable trust tuple.
3. P2 tests must distinguish collection retry/reconciliation/partial-write repair for the same AttemptKey from a new Lakeflow dbt retry/repair/execution with different native coordinates. Only the former reuses a tuple.
4. P2 barrier tests must pause before the trust read, after the trust read but before root commit, after an indeterminate root response, and before downstream evidence writes. Native dbt/capture outcomes and AttemptKey must remain invariant through registration, invalidation, expiry, and refresh at each barrier.
5. P1/P2 adversarial fixtures must prove that absent, stale, forged, duplicate, unreadable, component-mismatched, refreshed, or invalidated trust summaries cannot create node rows, validate artifacts/logs, change capture precedence, or duplicate an attempt.
6. P3 must prove that generated observed tasks contain no migration/deployment/trust/component/fence/action/token/actor/user value in Job parameters, environment, dbt argv, selector, vars, target/log paths, artifacts, or logs.
7. P6 must capture the exact Run Now request and prove that the only dynamic API field is the deterministic idempotency token; no workload parameter or task override is present. Identical-token recovery must preserve one native run and normal AttemptKey correlation.
8. P1/P3/P6 fixtures must prove that decimal-string canonicalization is applied only to typed control domains and never transforms native artifact/event JSON or its hashes.
9. P4/P7 must visibly distinguish **Trust observed by collector**, **Current runtime trust**, and native Lakeflow/dbt/capture outcomes, including the read-change-commit timeline.
10. P8 must exercise real success, failure, partial, early failure, cancellation, retry, and repair while racing trust and fence transitions, proving one root/tuple per native AttemptKey and no control-to-dbt evidence promotion.

## Prior finding disposition

| Prior finding | Thirteenth re-review disposition |
|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION`; both zero-execution warnings plus the non-empty-results invariant prevent false observability. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION`; the closed command matrix, per-command flags, configuration-conflict checks, privacy controls, selector boundary, and control-input prohibition remain exact. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION`; standalone/pair validation and total retrieval/capture precedence remain deterministic. Trust/fence/action rows cannot become primary candidates or start evidence. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION`; exact Core/adapter/common/Python/schema/wheel/log-version qualification remains coherent. Control canonicalization does not expand the dbt matrix. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION`; manifest inventory, invocation results, Lakeflow state, collector state, capture state, App deployment state, and current/observed runtime trust remain separate. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION`; ordinal-local paths, six-file/120-MiB bound, pre-logger states, and closed-file rules remain exact. Fence/action records are not log sources. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION`; field allowlisting remains primary and secret scrubbing remains defense in depth. Added control fields contain no native dbt payload. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION`; Genie/MCP/LLM features remain optional and outside dbt execution, capture, validation, action authorization, and trust promotion. |
| `DBX-P0-028` control-fence requirement | `RESOLVED FOR DBT ISOLATION`; the same-row fence now serializes product admission/drain while remaining explicitly non-atomic with Jobs and completely outside dbt command/evidence identity. |
| `DBX-P0-029` integer canonicalization requirement | `RESOLVED FOR DBT ISOLATION`; quoted decimal strings are confined to versioned control canonicalization and do not alter native dbt JSON. |

## P0-P10 dbt outcomes

These are planning outcomes, not claims that later implementation evidence already exists.

| Part | Planning outcome | Required dbt evidence at the part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Preserve this immutable-hash verdict with the other specialist outcomes; no dbt P0 finding remains. |
| P1 — Capture library | `PASS` | Implement vendored schemas, exact pair/result/log validation, allowlists, qualified digest types, native-JSON preservation, and adversarial trust/fence isolation fixtures. |
| P2 — Collector and reconciliation | `PASS` | Prove one immutable root/tuple per native AttemptKey, same-root re-entry versus new-attempt behavior, read/commit races, exact three-table DML, and zero control-to-dbt evidence promotion. |
| P3 — Bundle installer | `PASS` | Produce complete locks and exact argv fixtures; prove generated tasks accept no deployment/trust/fence/action/token/user input and that control operations never invoke dbt. |
| P4 — App read-only MVP | `PASS` | Present Lakeflow, dbt invocation, node/test, collector, capture, immutable collector-observed trust, and current trust separately. |
| P5 — Job onboarding | `PASS` | Deterministically inspect task shape, command sequence, selector, aliases/flags, vars, paths, target/connection features, versions, concurrency, and archive access independently of trust/fence state. |
| P6 — Controlled actions | `PASS` | Authorize only parameterless start of the already approved Job; prove one same-token native run and no action/fence/token value in dbt input or evidence. |
| P7 — Security and operations | `PASS` | Prove field classification, diagnostics, retention/export/delete, zero runtime egress, native-JSON preservation, and control lifecycle without rewriting dbt facts. |
| P8 — Bounded live proof | `PASS` | Exercise real archives and every native outcome across trust-read/commit and claim/drain barriers; prove one root/tuple per native AttemptKey and finish with no compute running. |
| P9 — Optional intelligence | `PASS` | Pass install, capture, investigation, and lifecycle with AI disabled; deterministic validators remain canonical. |
| P10 — Private alpha | `PASS` | Qualify representative projects without admitting Core 1.12/2.0, untested adapter options, new artifacts/statuses, unsupported commands, or control-derived dbt input. |

## Author-file outcome

| Author file or set | Outcome | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | Artifact-first evidence, collector-observed trust, current trust, and the optional fence are stated as separate domains. |
| `AGENTS.md` | `PASS` | Arbitrary execution and control-value interpolation are prohibited; per-root trust provenance and parameterless P6 dispatch remain binding implementation rules. |
| `docs/index.md` | `PASS` | The planning index introduces no dbt contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Observed dbt execution, collector DML, runtime trust, deployment lifecycle, and P6 fence/Jobs dispatch remain separate planes. |
| `docs/plans/product-plan.md` | `PASS` | Baseline 0.14 preserves the exact compatibility/argv/artifact/log/capture contract and adds honest per-root observation-time provenance plus a non-contaminating action fence. |
| `docs/plans/review-process.md` | `PASS` | Every P0-P10 gate requires control-input isolation, per-attempt provenance, and unchanged native outcomes through races. |
| `docs/plans/documentation-plan.md` | `PASS` | Planned pages distinguish native dbt files/events/results from control canonicalization and show collector-observed versus current trust separately. |
| `docs/research/source-register.md` | `PASS` | Current stable pins, schemas, tagged flags/log behavior, prerelease trends, decimal rationale, and Jobs parameter boundary are grounded in primary sources. |

## Non-blocking portability watch

Core 1.12 is at release-candidate status and Core 2.0 is alpha. Adapter 1.12.2 also introduces optional connector-kernel and catalogs-v2 surfaces that are not admitted merely because they ship in the pinned wheel. Every future candidate needs its own full dependency lock, exact Python/Core/adapter/common versions, target/profile options, artifact schemas, flags/aliases, result states and BuildTask collections, partial-parsing behavior, structured-log version/parser, native archive qualification, retry/repair semantics, and the same control-input/native-JSON isolation fixtures.

## Cloud-mutation statement

This review used local repository reads, current official dbt documentation, first-party tagged GitHub releases/source and release APIs, the official dbt schema registry, and the official Python package distribution. It did not authenticate to Azure or Databricks, execute dbt or SQL, start or stop compute, or create, modify, or delete any cloud resource. No paid resource was started.

## Final disposition

- Frozen baseline 0.14 dbt verdict: `PASS`.
- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- `DBX-P0-028` and `DBX-P0-029`: resolved with no dbt regression.
- New dbt findings: none.
- P0 dbt blockers: none.
- P1/P2/P3/P4/P6/P8 must produce the explicit per-AttemptKey, read/commit-race, native-JSON, decimal-domain, command-input, same-token, and live-archive evidence above.
