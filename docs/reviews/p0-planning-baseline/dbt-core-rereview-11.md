# Eleventh dbt Core re-review: P0 planning baseline 0.12

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `93343ae870073dbe4518765b8949edc29d0a992255b36854b0e62c631f78392b`
- Date: 2026-07-15
- Reviewer: independent dbt Core and `dbt-databricks` product/security specialist
- Verdict: `PASS`
- Open dbt P0 findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.12 passes the eleventh independent dbt Core review. The sequential Direct-plan lifecycle and executable one-row-per-event/latest-generation trust summary resolve the tenth Databricks findings without weakening or extending the canonical dbt capture contract.

The decisive boundaries are explicit:

1. Stage planning, `bundle run <app-resource-key>`, App deployment reconciliation, App stop/start, final-binding planning, and trust-event commits are App/resource/control-plane operations. None invokes the observed native dbt task.
2. The only supported dbt sequence remains optional `dbt deps` followed by one version-controlled named-selector `dbt build`. No deployment, trust, migration, component, action, actor, or user value can supply its command, selector, flags, vars, environment, target path, or log path.
3. AttemptKey plus command ordinal remains the task-local correlation and namespace boundary. Direct lineage/serial, deployment IDs, deployment-set digests, trust generation, event IDs, snapshot ID, component keys, trust state, and server trust times are excluded.
4. Only the allowlisted same-invocation manifest-v12/run-results-v6 pair can create trusted node or test results. App artifacts, runtime-trust manifests, trust rows/views, migration attestations, Query History, deployment inventories, action rows, and system snapshots satisfy none of those predicates.
5. Structured JSON logs remain an independent diagnostic evidence class. A trust event or App lifecycle event cannot become `MainReportVersion`, a dbt invocation ID, a same-build start event, or evidence that a missing/malformed/truncated/unknown-version log is valid.
6. The collector may copy a separately typed trust snapshot/state into its own normalized row only as provenance. That overlay cannot change native dbt status, hashes, node resolution, capture-state precedence, or exactly-once identity.

This is approval of the planning contract. It is not evidence that the P1 parser, P2 collector SQL, P3 generated Jobs and dependency locks, P6 action call, P8 live archives, or P10 representative-project qualification already exist.

## Immutable input verification and scope

I globally sorted the requested author paths, hashed each file with SHA-256, sorted the resulting per-file records by path, and hashed that stream before review. The result exactly matched the assigned digest:

```text
93343ae870073dbe4518765b8949edc29d0a992255b36854b0e62c631f78392b
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

I read every author file and all three tenth reports in full. I traced the baseline 0.12 response to `DBX-P0-022`, `DBX-P0-023`, and `DBX-P0-024`, the tenth dbt isolation requirements, all prior `DBT-P0-001` through `DBT-P0-008` findings, and the usability report's lifecycle interpretation. Review reports are outside the digest. I edited no author file or earlier report; this report is the only file written.

## Current primary evidence checked

As of 2026-07-15, the frozen candidate remains a coherent exact stable intersection:

- [dbt Core 1.11.12](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) remains the latest non-prerelease Core tag. Its [tagged metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml) requires Python `>=3.10` and publishes classifiers for Python 3.10 through 3.13.
- [`dbt-databricks` 1.12.2](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) remains the latest non-prerelease adapter tag. Its [tagged metadata](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml) requires `dbt-core>=1.11.2,<1.11.13`, `dbt-common>=1.37.0,<1.38.0`, Python `>=3.10`, and classifiers through Python 3.13.
- The official [dbt-common 1.37.5 distribution](https://pypi.org/project/dbt-common/1.37.5/) still publishes `dbt_common-1.37.5-py3-none-any.whl` with SHA-256 `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077`. I re-hashed the wheel and re-read its package source: `LOG_VERSION = 3` and the rotating file handler has `backupCount=5`.
- Current [artifact documentation](https://docs.getdbt.com/reference/artifacts/dbt-artifacts) continues to define common per-invocation metadata, including schema URL, dbt version, environment metadata, and `invocation_id`. [Manifest documentation](https://docs.getdbt.com/reference/artifacts/manifest-json) remains project inventory; [run-results documentation](https://docs.getdbt.com/reference/artifacts/run-results-json) remains executed-result evidence joined to the manifest through `unique_id`.
- The exact initial schemas remain [manifest v12](https://schemas.getdbt.com/dbt/manifest/v12.json) and [run-results v6](https://schemas.getdbt.com/dbt/run-results/v6.json). Tagged [Core 1.11.12 `BuildTask`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py) still limits supported build result resolution to its model/snapshot/seed/test/unit-test/saved-query/exposure/function runner collections.
- Current [`dbt build` documentation](https://docs.getdbt.com/reference/commands/build) still says one build writes one manifest and one combined run-results artifact and preserves downstream skip semantics.
- Current [JSON-artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) still writes artifacts to `target/`, permits an invocation-local target path, and warns that another operation can overwrite existing output. This continues to support immutable AttemptKey/ordinal-local paths.
- Current [events/logging](https://docs.getdbt.com/reference/events-logging) and [log configuration](https://docs.getdbt.com/reference/global-configs/logs) keep structured event fields, `log_version`, event name/code, level, timestamp, thread, and invocation identity separate from human `msg`, and retain separately configurable log and target paths.
- Current [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings) still supports warning-name targeting, including `NoNodesForSelectionCriteria`; tagged Core 1.11.12 still defines both that warning and `NothingToDo`.
- Current [partial-parsing documentation](https://docs.getdbt.com/reference/parsing) still describes `partial_parse.msgpack` as an internal cached manifest and warns that volatile parse-time context such as invocation ID or flags can become stale. It remains ancillary rather than execution evidence.
- Current [`dbt retry` documentation](https://docs.getdbt.com/reference/commands/retry) still depends on prior `run_results.json`, including the limitation that an early failure with no recorded nodes gives retry nothing to run. Full Lakeflow-attempt retry remains the safer ordinary product contract.

[Core 1.12.0rc3](https://github.com/dbt-labs/dbt-core/releases/tag/v1.12.0rc3) and Core `2.0.0-alpha.4` remain prereleases. Current multi-engine docs already contain conditional 1.12/Fusion behaviors, which reinforces rather than weakens the need to qualify tagged Core 1.11.12 instead of silently accepting current-doc additions.

## Baseline 0.12 change regression

| Baseline 0.12 change | Verdict | dbt conclusion |
|---|---|---|
| Sequential stage plan then fresh final-binding plan | `PASS` | Both plans manage App/Job resources and bindings. The final plan is generated after App deployment reconciliation and stop, but neither plan executes the observed dbt task or supplies its argv. The final diff is constrained to reviewed bindings/ACLs with source, build, App code/configuration, and selected deployment unchanged. |
| Fully paginated before/after App deployment inventory | `PASS` | Deployment records, active/pending pointers, `SNAPSHOT` mode, Direct lineage/serial, and App artifact/configuration digests are platform deployment facts. They cannot satisfy a dbt schema URL, invocation UUID, command ordinal, native archive path, `run_results.args.which`, result `unique_id`, or structured-log event. |
| Pinned runner's prior-code start and internal POST reissue | `PASS` | The repair bounds App compute and deployment identity. It does not introduce a dbt retry, repair, command retry, or second dbt AttemptKey. Wrapper retry remains prohibited; reconciliation is over App deployment records only. |
| One physical trust-ledger row per logical event | `PASS` | `ledger_row_id`, `event_id`, generation, operation, component arrays, and server commit time belong only to `runtime_trust_ledger`. The observed Job cannot write this table, and the collector reads only the sanitized summary view. No row is a dbt artifact or event. |
| Event-specific registration/candidate/acceptance/invalidation fields | `PASS` | The nullability and predecessor rules define product trust transitions. Candidate, acceptance, invalidation, or replay cannot create or remove an outer Lakeflow attempt, dbt invocation, primary file, log event, or node result. |
| One-row-per-installation latest-generation summary | `PASS` | `runtime_trust_status_v` is a control-state reduction, not a normalized dbt view. Absence, unreadability, duplicate/conflict, invalidation, or supersession fails the product gate; none changes canonical artifact validity or capture precedence. |
| Server-only roster/machine clocks and `valid_until` | `PASS` | These timestamps age the trust overlay. They never replace or become pair-equality keys for dbt `generated_at`, `invocation_started_at`, log event time, node timing, or Lakeflow task time. |
| Read-only `BASE_OBSERVABILITY` component check and stamp | `PASS` | The collector must independently evaluate the archive, artifact, log, AttemptKey, and capture contracts before its DML; a non-valid diagnostic-log state can still remain separate from a valid primary pair. The component check authorizes/stamps the applicable write but cannot make invalid evidence valid. |
| Stale base-collection continuation | `PASS` | An expired otherwise-matching summary permits a `STALE` provenance stamp only. It does not rewrite native dbt/Lakeflow outcomes, merge attempts, alter hashes, or infer node results. A missing or mismatched component fails the write. |
| P6 same-statement fresh-summary/component gate | `PASS` | This is an action-authorization predicate outside dbt. It may authorize only the already approved bound Job; no trust/event/component/action/user field may become a task parameter override, selector, vars, dbt environment value, path, artifact, or log field. |
| Refresh, upgrade, rollback, restart, and uninstall | `PASS` | A new trust generation can lock presentation/actions and trigger App lifecycle work, but it cannot mutate an existing AttemptKey, reclassify canonical capture evidence, or manufacture another dbt attempt. Code/task changes require their own stopped lifecycle and requalification. |

## Explicit non-contamination review

| dbt boundary | Eleventh-review result |
|---|---|
| argv and command | `PASS` — only separate exact `deps` and `build` templates exist. App commands and trust-event SQL are different command domains. |
| Resolved flags and aliases | `PASS` — CLI, configured current/legacy environment aliases, one allowed project-or-profile mapping, `DO_NOT_TRACK`, and defaults remain the complete resolution inputs. Trust-view fields are not a flag source. |
| Selector and vars | `PASS` — the selector is version controlled, CLI vars are empty, and App/Job-parameter/AI input cannot select work. Deployment component arrays do not map to dbt selection. |
| Target/log paths | `PASS` — paths derive only from AttemptKey and command ordinal. `deps` still receives no `--target-path`; `build` receives its own target boundary. No generation/event/snapshot/deployment value enters either path. |
| AttemptKey and idempotency | `PASS` — workspace/job/run/repair/task-run/execution coordinates plus ordinal remain canonical. A trust refresh or accepted-snapshot change is provenance only and cannot create a second attempt row. |
| Artifact validation | `PASS` — standalone path/size/schema/metadata validation and same-invocation v12/v6 pair validation remain mandatory. Runtime-trust `manifest_digest` and App deployment artifact digests are separately qualified control-plane values, not dbt file hashes. |
| Structured logs | `PASS` — the seven ordered states remain `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID`. Trust/App/migration events never count as a dbt event or primary-build start. |
| Node/test results | `PASS` — only non-empty, unique run-results IDs that resolve exactly once through tagged BuildTask collections can create rows. Trust components and App deployment components cannot resolve a dbt `unique_id`. |
| Partial parsing | `PASS` — `partial_parse.msgpack` remains path/size-checked ancillary output only. Trust state neither seeds nor validates it, and volatile artifact metadata remains excluded from pair equality. |
| Capture precedence | `PASS` — archive availability, invalid primary input, complete pair, allowed incomplete evidence, and not-produced remain the only ordered predicates. Trust state is not a capture predicate or same-build start signal. |
| Evidence provenance | `PASS` — collection-time snapshot/state and current UI trust state must remain separately typed overlays. Neither may overwrite native status, invocation identity, dbt timing, file hashes, log state, node status, or capture state. |

## Numbered finding disposition

No new numbered dbt finding is opened. I found no critical, high, medium, or low P0 dbt correctness defect in baseline 0.12.

The following are mandatory later-part acceptance rules, not deferred P0 corrections:

1. P1/P3 schemas must name- and type-separate `runtime_trust_manifest_digest`, App deployment artifact/configuration digests, `dbt_manifest_sha256`, and `dbt_run_results_sha256`; an unqualified generic digest must never be accepted across those domains.
2. P2's merge/idempotency key must remain AttemptKey plus canonical dbt file/result hashes as appropriate. Trust generation, component, snapshot, state, and evaluation time may be stored as provenance but may not participate in attempt identity or artifact validity.
3. P2 adversarial fixtures must prove that missing, forged, duplicate, stale, refreshed, or changed trust summaries cannot create node rows, change log/capture precedence, or duplicate one attempt.
4. P3 must prove generated observed dbt tasks contain no migration/deployment/trust/component/actor/action/user value in Job/task parameters, environment, dbt argv, selector, vars, target/log paths, artifacts, or logs. Runtime-trust manifests may hash approved task configuration but never supply it at run time.
5. P6 must make a parameterless start of the already approved bound Job with no parameter override. The same-statement trust check authorizes the action only; request and ledger fields cannot cross into the observed task.
6. P4/P7 must distinguish immutable collection-time trust provenance from the current summary-derived UI label and from every native Lakeflow/dbt/capture fact.

## Tenth cross-review finding disposition

| Tenth finding or requirement | Eleventh dbt disposition |
|---|---|
| `DBX-P0-022` — precomputed final Direct plan | `RESOLVED IN BASELINE 0.12; NO DBT REGRESSION`. Final planning now occurs only after stage Apply, deployment reconciliation, and stop. No final-plan input becomes dbt command/evidence. |
| `DBX-P0-023` — one runner invocation can yield ambiguous deployments | `RESOLVED IN BASELINE 0.12; NO DBT REGRESSION`. Complete deployment-set reconciliation and exactly-one-new-`SNAPSHOT` acceptance concern App code deployment only; they do not change dbt attempt/retry semantics. |
| `DBX-P0-024` — under-specified ledger/view cardinality | `RESOLVED IN BASELINE 0.12; NO DBT REGRESSION`. The typed single-row events, component arrays, deterministic reduction, server clocks, and non-authoritative signatures are executable control-state semantics, not dbt artifact semantics. |
| Tenth dbt trust-input isolation rules | `PRESERVED`. Baseline 0.12 adds explicit P3 prohibition on migration/deployment/trust/component/user input becoming a dbt command or evidence and retains the closed command/path/artifact contract. |
| Tenth usability lifecycle interpretation | `NO DBT REGRESSION`. Automatic deployment reconciliation and one latest summary remove human ID choice; they add no user-controlled dbt input. `UX-P0-F03` remains a future installer-platform gate with no effect on P0 artifact correctness. |

## Prior dbt finding disposition

| Prior finding | Eleventh re-review disposition |
|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION`; both zero-execution warnings plus the non-empty-results postcondition prevent false observability. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION`; the command matrix, per-command argv, configuration conflicts, privacy flags, selector boundary, and trust-input prohibition remain closed. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION`; standalone/pair validation and total archive/capture precedence remain deterministic. Trust rows, components, and App deployment records cannot become primary candidates or build-start evidence. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION`; exact Core/adapter/common/Python/schema/wheel/log-version qualification remains intact. The control-ledger schema does not expand the dbt compatibility matrix. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION`; manifest inventory, invocation results, Lakeflow state, collector state, capture state, App deployment state, and runtime trust remain distinct. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION`; ordinal-local paths, six-file/120-MiB bound, pre-logger states, and closed-file rules remain exact. Trust ledger/view data is not a log source. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION`; allowlisting remains primary and secret scrubbing remains defense in depth. New control fields contain no raw dbt artifact/log payload. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION`; Genie/MCP/LLM capability remains optional and outside execution, capture, validation, authorization, and trust promotion. |

## P0-P10 dbt outcomes

These are planning outcomes, not claims that later implementation evidence already exists.

| Part | Planning outcome | Required dbt evidence at the part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record this immutable-hash verdict with the other specialist outcomes; no dbt P0 finding remains. |
| P1 — Capture library | `PASS` | Implement exact vendored schemas, pair/result validation, total capture/log precedence, field allowlists, domain-separated digest types, and adversarial trust-provenance isolation fixtures. |
| P2 — Collector and reconciliation | `PASS` | Prove individual-task archive retrieval, exact three-table DML, read-only latest-summary lookup, stale matching continuation, absent/mismatch denial, exactly-once AttemptKey behavior across refreshes, and zero trust-to-dbt evidence promotion. |
| P3 — Bundle installer | `PASS` | Produce complete dependency locks and exact argv fixtures; prove sequential App plans/events do not invoke dbt and that no migration/deployment/trust/component/action/user value enters the observed task or native evidence. |
| P4 — App read-only MVP | `PASS` | Present Lakeflow, dbt invocation, node/test, collector, capture, App deployment, migration, trust provenance/current state, and optional enrichment separately. Trust age/state must not rewrite dbt facts. |
| P5 — Job onboarding | `PASS` | Deterministically inspect task shape, command sequence, selector, flags/aliases, vars, paths, target/connection features, versions, concurrency, and access/check outcomes independently of trust state. |
| P6 — Controlled actions | `PASS` | Authorize only a parameterless start of the approved bound Job. Candidate/stale/conflict/cardinality denial and action/user/trust inputs may not alter dbt configuration or evidence. |
| P7 — Security and operations | `PASS` | Prove field classification, diagnostics, retention/export/delete, zero runtime egress, digest-domain separation, and trust overlay lifecycle without broadening or rewriting canonical dbt data. |
| P8 — Bounded live proof | `PASS` | Capture success/failure/partial/early/cancel/retry/repair paths; exercise collection across candidate/accept/expiry/refresh and App lifecycle interruptions; prove no trust/deployment generation creates or duplicates a dbt attempt; end with no compute running. |
| P9 — Optional intelligence | `PASS` | Pass install, capture, investigation, and lifecycle with AI disabled; accepted tools use only deterministic validators and curated evidence. |
| P10 — Private alpha | `PASS` | Qualify representative projects against the exact matrix without admitting Core 1.12/2.0, new parser/state/artifact/status behavior, untested adapter options, or trust-derived command input. |

## Author-file outcome

| Author file or set | Outcome | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | Artifact-first evidence and the repaired deployment/trust lifecycle remain explicitly separate. |
| `AGENTS.md` | `PASS` | Arbitrary dbt inputs remain prohibited; the latest summary is read-only provenance/authorization and cannot promote trust or canonical evidence. |
| `docs/index.md` | `PASS` | The planning index introduces no dbt contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Observed dbt execution, collector DML, App deployment reconciliation, trust events, migration, and optional capabilities remain separate planes. |
| `docs/plans/product-plan.md` | `PASS` | Baseline 0.12 repairs Direct/deployment/trust semantics while preserving the exact argv, AttemptKey, artifact, log, result, partial-parse, and capture contract. |
| `docs/plans/review-process.md` | `PASS` | P0-P10 gates expressly prohibit migration/deployment/trust/component/user input from becoming dbt command/evidence and require later implementation proof. |
| `docs/plans/documentation-plan.md` | `PASS` | Planned pages keep App deployment artifact, runtime-trust manifest, dbt manifest, run-results, logs, capture, and current trust state distinct. |
| `docs/research/source-register.md` | `PASS` | Stable pins, exact tagged behavior, schemas, warning/log/path rules, and prerelease boundaries remain represented with primary sources. |

## Non-blocking portability watch

Core 1.12 is at release-candidate status and Core 2.0 is at alpha status. Current docs include conditional OSI artifacts, v2 parser/state behavior, new statuses, and Fusion-specific command semantics that are outside this candidate. Adapter 1.12.2 explicitly caps Core below 1.11.13. Do not infer compatibility from matching version numbers or current unqualified docs. Every future pair needs a complete dependency lock, exact schemas, flags, command decorators, result states/collections, partial-parsing behavior, structured-log version/parser, native archive qualification, and the same trust/deployment-input isolation tests.

## Cloud-mutation statement

This review used local repository reads, current official dbt documentation, first-party GitHub release/source/API data, the dbt schema registry, and the official Python package distribution. It did not authenticate to Azure or Databricks, execute dbt or SQL, start/stop compute, or create, modify, or delete any cloud resource. No paid resource was started.

## Final disposition

- Frozen baseline 0.12 dbt verdict: `PASS`.
- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- `DBX-P0-022` through `DBX-P0-024`: resolved in baseline 0.12 with no dbt regression.
- New dbt findings: none.
- P0 dbt blockers: none.
- P1/P2/P3/P4/P6/P8 must produce the explicit digest-domain, provenance-isolation, parameterless-start, exactly-once, and live-archive evidence above.
