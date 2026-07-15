# Twelfth dbt Core re-review: P0 planning baseline 0.13

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: 2bde12f3f3eef01efecef33f483015cbcf2588234281666ba192a6d7534c81c7
- Date: 2026-07-15
- Reviewer: independent dbt Core and dbt-databricks product/security specialist
- Verdict: PASS
- Open dbt P0 findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.13 passes the twelfth independent dbt Core and dbt-databricks product/security review. The exhaustive runtime-trust DDL, two phase-specific machine observations, original-roster source-chain validation, literal canonical digest objects, accurate query-evaluation time semantics, exact latest-generation view, and conditional P6 gate resolve the eleventh Databricks findings without weakening the canonical dbt execution or evidence contract.

The result depends on six boundaries that are now closed at planning level:

1. Runtime-deployment inventories, App artifact/configuration digests, Direct state, runtime-trust events, component observations, roster attestations, machine observations, and accepted snapshots are control-plane provenance. None is a dbt artifact, structured dbt event, invocation identifier, command result, or proof that dbt started.
2. The observed task remains optional dbt deps followed by one version-controlled named-selector dbt build. No deployment, migration, trust, component, actor, action, user, AI, or request value may supply or override its command, selector, flags, vars, environment, target path, log path, or artifact location.
3. AttemptKey plus command ordinal remains the dbt task-local correlation and namespace boundary. Runtime-trust generation, event, snapshot, component, deployment, roster, phase-observation, state, or evaluation-time values are excluded from attempt identity and idempotency.
4. Only an allowlisted, standalone-valid, same-invocation manifest-v12/run-results-v6 pair can create trusted dbt node or test results. A control-plane field named manifest_digest or artifact_digest has a different typed domain and cannot satisfy any primary dbt-file predicate.
5. Structured JSON logs remain an independent diagnostic evidence class. App or runtime-trust events cannot become MainReportVersion, log version 3, a dbt invocation ID, same-build start evidence, or a reason to upgrade a missing, malformed, truncated, or unknown-version log.
6. The collector may stamp the separately typed collection-time trust snapshot/state only as provenance after independently validating native archives and dbt evidence. Neither that immutable stamp nor current trust state may rewrite native Lakeflow/dbt outcomes, capture precedence, hashes, result resolution, or exactly-once identity.

This is approval of the frozen planning contract. It is not evidence that the P1 parser, P2 merge SQL, P3 generated Job and lockfiles, P6 parameterless Job start, P8 live archives, or P10 representative-project qualification have been implemented.

## Immutable input verification and scope

Before review, I globally sorted the requested author paths, hashed each file with SHA-256, sorted the per-file records by path, and hashed that stream. The result exactly matched the assigned digest:

    2bde12f3f3eef01efecef33f483015cbcf2588234281666ba192a6d7534c81c7

The exact author scope was:

- AGENTS.md
- README.md
- docs/decisions/0001-private-app-bundle.md
- docs/index.md
- docs/plans/documentation-plan.md
- docs/plans/product-plan.md
- docs/plans/review-process.md
- docs/research/source-register.md

I read every author file and all three eleventh specialist reports in full. I traced the baseline 0.13 response to DBX-P0-025, DBX-P0-026, and DBX-P0-027; the eleventh dbt isolation requirements; all prior DBT-P0-001 through DBT-P0-008 findings; and the usability report's remaining P3 implementation gate. Review reports are outside the frozen digest. I edited no author file and no prior report; this report is the only file written.

The same author-scope procedure was repeated after this report was written. It again produced the exact assigned digest, proving that the frozen input did not change during review.

## Current primary evidence checked

The following current first-party evidence was rechecked on 2026-07-15:

- [dbt Core 1.11.12](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) is the latest non-prerelease Core release. Its [tagged package metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml) requires Python 3.10 or newer, advertises Python 3.10 through 3.13, and constrains dbt-common and dbt-adapters below their next major versions.
- [dbt-databricks 1.12.2](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) is the latest non-prerelease adapter release. Its [tagged package metadata](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml) requires dbt-core at least 1.11.2 and below 1.11.13, dbt-common at least 1.37.0 and below 1.38.0, and Python 3.10 or newer.
- Adapter 1.12.2 explicitly raises the Core upper compatibility cap to include Core 1.11.12 and fixes failed Python-model result state. Adapter 1.12.1 added Databricks job, job-run, and task-run identifiers to adapter_response; these remain corroborating evidence rather than the sole correlation source. Adapter 1.11.8 added invocation_id to the default query comment; query history remains optional enrichment, not canonical dbt evidence.
- The official [dbt-common 1.37.5 distribution](https://pypi.org/project/dbt-common/1.37.5/) publishes dbt_common-1.37.5-py3-none-any.whl with SHA-256 432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077. I downloaded and re-hashed that wheel, then rechecked its source: LOG_VERSION is 3 and the rotating file handler retains five backups.
- Official [artifact documentation](https://docs.getdbt.com/reference/artifacts/dbt-artifacts) defines per-invocation metadata, including schema URL, dbt version, environment metadata, and invocation_id. [Manifest documentation](https://docs.getdbt.com/reference/artifacts/manifest-json) describes project inventory, while [run-results documentation](https://docs.getdbt.com/reference/artifacts/run-results-json) describes executed results joined back to that inventory by unique_id.
- The frozen initial schemas remain [manifest v12](https://schemas.getdbt.com/dbt/manifest/v12.json) and [run-results v6](https://schemas.getdbt.com/dbt/run-results/v6.json). Tagged [Core 1.11.12 BuildTask](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py) resolves build results only through its model, snapshot, seed, test, unit-test, saved-query, exposure, and function runner collections.
- Official [dbt build documentation](https://docs.getdbt.com/reference/commands/build) continues to state that one build writes one manifest and one combined run-results artifact and applies downstream skip behavior.
- Official [JSON-artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) writes artifacts to target by default, supports an invocation-local target path, and warns that another invocation can overwrite existing output. That behavior continues to require immutable AttemptKey/ordinal-local directories.
- Official [events and logging documentation](https://docs.getdbt.com/reference/events-logging) and [log configuration](https://docs.getdbt.com/reference/global-configs/logs) keep structured event identity, code, level, timestamp, thread, invocation ID, and log version distinct from the human msg field, and expose a separately controlled log path.
- Official [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings) continues to support warning-name targeting, including NoNodesForSelectionCriteria. Tagged Core 1.11.12 defines both NoNodesForSelectionCriteria and NothingToDo.
- Official [partial-parsing documentation](https://docs.getdbt.com/reference/parsing) describes partial_parse.msgpack as an internal cache and warns that volatile parse-time context can become stale. It is ancillary output, never primary execution evidence.
- Official [dbt retry documentation](https://docs.getdbt.com/reference/commands/retry) continues to depend on the previous run_results.json and explains that an early failure can leave nothing to retry. A complete new Lakeflow attempt remains the safer normal product policy.
- Official [environment-variable documentation](https://docs.getdbt.com/reference/dbt-jinja-functions/env_var) documents secret scrubbing but also that DBT_ENV_CUSTOM_ENV values are copied into artifacts and logs. The baseline correctly keeps arbitrary sensitive values out of this channel.
- Official [usage-statistics documentation](https://docs.getdbt.com/reference/global-configs/usage-stats) continues to document DO_NOT_TRACK. The frozen generated commands explicitly disable anonymous usage and artifact-ingest upload rather than relying on an ambient default.

[Core 1.12.0rc3](https://github.com/dbt-labs/dbt-core/releases/tag/v1.12.0rc3) and [Core 2.0.0-alpha.4](https://github.com/dbt-labs/dbt-core/releases/tag/v2.0.0-alpha.4) are prereleases. Current docs contain version- and engine-conditional behavior, so tagged-source qualification remains necessary; current unqualified documentation does not expand this candidate.

## Baseline 0.13 focused regression

| Baseline 0.13 change | Verdict | dbt conclusion |
|---|---|---|
| Exhaustive runtime_trust_ledger DDL and exact four-event required/null matrix | PASS | Every column and event is confined to the runtime-trust control domain. Registration, candidate, acceptance, and invalidation rows cannot satisfy a dbt path, schema, invocation, command, result, or log predicate. |
| Separate pre_start_machine_observation_digest and post_start_machine_observation_digest | PASS | The STOPPED and ACTIVE phases prove App deployment lifecycle, not dbt execution. Neither phase observation is accepted as primary-build start evidence, a dbt invocation, or an archive-retrieval state. |
| Stable graph separated from lifecycle pointers | PASS | The stable projection binds deployment/configuration facts while phase observations carry lifecycle facts. Neither projection enters generated dbt argv, AttemptKey, target/log paths, or artifact-pair equality. |
| Original self-anchored roster source and complete accepted-source validation | PASS | Roster reuse is a control-custody assertion. Orphan, intermediate, transitive, invalidated, deleted, conflicted, or tampered sources make runtime trust unverified; they cannot invalidate or repair already collected native dbt facts. |
| Literal RFC 8785/SHA-256 domains and acyclic ID order | PASS | Domain-separated deployment, component, roster, graph, observation, event, candidate, acceptance, payload, snapshot, server-record, and ledger-row values cannot be substituted for dbt manifest/run-results file hashes. |
| statement_evaluated_at from one server current_timestamp at query-evaluation start | PASS | The corrected name avoids claiming Delta commit time. It remains control-evidence time and is never a substitute for dbt generated_at, invocation_started_at, event time, result timing, or Lakeflow task time. |
| Exact latest-generation runtime_trust_status_v reduction | PASS | The sanitized view exposes one derived control summary rather than raw trust rows. It exposes no client signature and no primary dbt payload. Current state is an overlay, not a capture or result classifier. |
| Base collection stale continuation | PASS | An expired otherwise-matching summary can only stamp STALE provenance. It cannot change archive availability, validate an artifact, infer build start, create node results, or duplicate an AttemptKey. |
| Same-statement P6 summary/component conditional DML | PASS | Fresh accepted trust and exactly one CONTROLLED_ACTIONS component authorize only the configured action. They cannot supply Job parameters or mutate the fixed dbt command contract. |
| Refresh, upgrade, rollback, restart, and invalidation | PASS | A new trust generation can lock UI/actions or alter provenance. It cannot create another dbt attempt, modify an existing AttemptKey, repair a malformed archive, or reinterpret native statuses. |

## Explicit non-contamination review

| dbt boundary | Twelfth-review result |
|---|---|
| Command and argv | PASS — the only supported sequence remains optional deps followed by one build. Runtime-deployment, trust, migration, component, roster, action, actor, user, or AI data has no command-construction path. |
| Resolved flags and aliases | PASS — CLI, current/legacy configured environment aliases, one allowed project-or-profile mapping, DO_NOT_TRACK, and defaults remain the complete inputs. A runtime-trust summary field is not a dbt flag source. |
| Selector, vars, and Job parameters | PASS — the named selector is version controlled, CLI vars are empty, and the App cannot accept free-form selection. “Approved selector” denotes the frozen configured Job selector; P6 may not send a selector or any other task override. |
| Target and log paths | PASS — paths derive only from AttemptKey and command ordinal. deps still has no target-path option; build has its own target boundary. Trust generation, event, snapshot, component, deployment, actor, and action values cannot enter either path. |
| AttemptKey and idempotency | PASS — workspace/job/run/repair/task-run/execution coordinates plus command ordinal remain canonical. Trust refreshes and accepted-snapshot changes are provenance only and cannot produce a second attempt row. |
| Artifact validation | PASS — standalone path/size/schema/metadata checks and same-invocation v12/v6 pair checks remain mandatory. The runtime-trust field manifest_digest is the digest of a versioned control manifest in its explicit runtime-trust domain, not dbt_manifest_sha256. App deployment artifact_digest is likewise not a dbt file hash. |
| Structured logs | PASS — UNAVAILABLE, NOT_INITIALIZED, TRUNCATED, MALFORMED, MISSING, UNKNOWN_VERSION, and VALID remain ordered and independent. Trust/App/migration events never count as a dbt event, MainReportVersion, or same-build start. |
| Node and test results | PASS — only non-empty unique run-results IDs resolving exactly once through tagged BuildTask collections can create rows. Trust components and deployment components cannot resolve a dbt unique_id. |
| Partial parsing | PASS — partial_parse.msgpack remains path/size-checked ancillary output. Trust state neither seeds nor validates it, and volatile artifact metadata remains excluded from pair equality. |
| Retry and repair | PASS — dbt retry is not the normal scheduled path. A Lakeflow retry/repair produces a new AttemptKey; trust refresh or App reconciliation does not. Wrapper retries remain prohibited where they could duplicate dbt execution. |
| Capture precedence | PASS — archive unavailable, invalid primary input, complete pair, allowed partial evidence, and not produced remain the only ordered predicates. Trust state is not a capture predicate and cannot be same-build start evidence. |
| Evidence provenance | PASS — immutable collection-time trust provenance, current trust state, native Lakeflow state, dbt invocation/result state, log state, and capture state remain distinct. No overlay may rewrite another domain. |

## Expanded runtime-trust and deployment isolation

The expanded trust model cannot become dbt evidence or command input for the following concrete reasons:

1. Its writers and tables are separately authorized. The observed dbt Job cannot write runtime_trust_ledger, and the collector/App read only the sanitized status view needed for a control decision or provenance stamp.
2. Its canonical objects use explicit dbtobsb.runtime-trust domains and control-plane fields. A digest is meaningful only with its qualified domain and schema; equal-length lowercase hexadecimal text is not cross-domain substitutability.
3. The primary dbt evidence predicate is conjunctive: allowlisted command-ordinal path, safe archive entry, size bound, exact v12/v6 schema, exact Core/adapter command metadata, parseable equal invocation UUID, matching AttemptKey/ordinal context, non-empty unique results, and exact BuildTask result resolution. No trust or deployment record satisfies that predicate.
4. The structured-log predicate independently requires the qualified dbt JSON event envelope and one matching MainReportVersion/log-version event in the closed ordinal-local log set. A trust event cannot satisfy it.
5. The fixed generated dbt task is version controlled. Product input is denied at App, Job-parameter, AI, and wrapper boundaries; runtime-trust data is evaluated only after/beside that fixed configuration, never interpolated into it.
6. The collection merge key is defined by native attempt coordinates and canonical dbt evidence. Trust snapshot/state is a typed payload column only. Refresh, invalidation, expiry, or component change therefore updates control interpretation without cloning or merging dbt attempts.

Implementation must preserve the fully qualified names at every API, SQL, model, and UI boundary. A generic manifest_digest, artifact_digest, snapshot_id, state, or evaluated_at field without its runtime-trust type/context would fail the relevant later-part gate even though the frozen plan's canonical domain is unambiguous.

## Numbered finding disposition

No new numbered dbt finding is opened. I found no critical, high, medium, or low P0 dbt correctness defect in baseline 0.13.

The following are mandatory later-part acceptance rules, not deferred P0 corrections:

1. P1 and P3 schemas and generated interfaces must name- and type-separate runtime_trust_manifest_digest, App deployment source/artifact/configuration digests, dbt_manifest_sha256, and dbt_run_results_sha256. No generic digest value may be accepted across domains.
2. P2's merge/idempotency key must remain AttemptKey plus canonical dbt evidence hashes where appropriate. Trust generation, event, component, snapshot, state, phase-observation digest, roster anchor, and evaluation time may be stored only as provenance and may not participate in attempt identity or artifact validity.
3. P1/P2 adversarial fixtures must prove that absent, forged, duplicate, stale, refreshed, invalidated, source-tampered, or component-changed trust summaries cannot create node rows, upgrade log state, change capture precedence, or duplicate one attempt.
4. P3 must prove generated observed tasks contain no migration/deployment/trust/component/roster/actor/action/user value in task parameters, environment, dbt argv, selector, vars, target/log paths, artifacts, or logs. A runtime-trust manifest may hash approved task configuration but never supply it at run time.
5. P6 must issue a parameterless start of the already approved bound Job with no parameter override. The same-statement trust predicate authorizes the action only; request, identity, ledger, component, and trust fields cannot cross into the observed task.
6. P4/P7 must visibly distinguish immutable collection-time trust provenance, current summary-derived trust state, and every native Lakeflow/dbt/capture fact.
7. P8 must run refresh/expiry/invalidation/source-tamper and App lifecycle adversarial cases around real dbt success, early failure, retry, and repair, proving one AttemptKey per native task execution and zero trust-to-dbt evidence promotion.

## Eleventh cross-review finding disposition

| Eleventh finding or requirement | Twelfth dbt disposition |
|---|---|
| DBX-P0-025 — ambiguous retention/validation of both machine observations | RESOLVED IN BASELINE 0.13; NO DBT REGRESSION. Candidate retains the PRE_START/STOPPED observation, acceptance repeats it and adds POST_START/ACTIVE, the stable graph must match, and the view rejects missing, swapped, duplicate, wrong-state, or drifted phases. Neither observation is dbt start evidence. |
| DBX-P0-026 — roster-anchor reuse not closed over a valid source attestation | RESOLVED IN BASELINE 0.13; NO DBT REGRESSION. Reuse targets only the original self-anchored candidate in exactly one complete accepted source chain, and the view dynamically revalidates it. Roster status remains control provenance only. |
| DBX-P0-027 — physical schema, canonical IDs, and server-time semantics not frozen | RESOLVED IN BASELINE 0.13; NO DBT REGRESSION. Exhaustive DDL/matrix, literal domains, acyclic derived IDs, exact view output/reduction, statement_evaluated_at, and fixed P6 conditional DML are now executable planning contracts. |
| Eleventh dbt digest-domain and input-isolation rules | PRESERVED. Baseline 0.13 expands the trust object graph but creates no path from it to dbt argv, paths, AttemptKey, artifact validity, logs, result resolution, or capture state. |
| Eleventh usability finding UX-P0-F03 | NO DBT REGRESSION. The future P3 installer/platform gate remains necessary, but it does not alter P0 dbt evidence semantics. |

DBX-P0-022 through DBX-P0-024 also remain resolved with no dbt regression: sequential stage/final planning does not invoke dbt; complete deployment reconciliation changes no attempt/retry semantics; and the one-row-per-event/latest-generation contract remains separate from dbt evidence.

## Prior dbt finding disposition

| Prior finding | Twelfth re-review disposition |
|---|---|
| DBT-P0-001 | RESOLVED — NO REGRESSION. Both zero-execution warnings plus the non-empty-results postcondition prevent false observability. |
| DBT-P0-002 | RESOLVED — NO REGRESSION. The closed command matrix, per-command flags, configuration conflicts, privacy controls, selector boundary, and trust-input prohibition remain exact. |
| DBT-P0-003 | RESOLVED — NO REGRESSION. Standalone/pair validation and total archive/capture precedence remain deterministic. Trust rows, phase observations, and deployments cannot become primary candidates or build-start evidence. |
| DBT-P0-004 | RESOLVED — NO REGRESSION. Exact Core/adapter/common/Python/schema/wheel/log-version qualification remains intact. Runtime-trust schema expansion does not expand the dbt compatibility matrix. |
| DBT-P0-005 | RESOLVED — NO REGRESSION. Manifest inventory, invocation results, Lakeflow state, collector state, capture state, App deployment state, and runtime trust remain separate domains. |
| DBT-P0-006 | RESOLVED — NO REGRESSION. Ordinal-local paths, six-file/120-MiB bound, pre-logger states, and closed-file rules remain exact. Control-ledger/view data is not a log source. |
| DBT-P0-007 | RESOLVED — NO REGRESSION. Field allowlisting remains primary and secret scrubbing remains defense in depth. New control fields contain no raw dbt artifacts, logs, SQL, messages, or arbitrary metadata. |
| DBT-P0-008 | RESOLVED — NO REGRESSION. Genie/MCP/LLM functionality remains optional and outside execution, capture, validation, authorization, and trust promotion. |

## P0-P10 dbt outcomes

These are planning outcomes, not claims that later implementation evidence already exists.

| Part | Planning outcome | Required dbt evidence at the part gate |
|---|---|---|
| P0 — Product contract | PASS | Preserve this immutable-hash verdict with the other specialist outcomes; no dbt P0 finding remains. |
| P1 — Capture library | PASS | Implement vendored schemas, pair/result validation, total capture/log precedence, field allowlists, fully qualified digest types, and adversarial trust/deployment-isolation fixtures. |
| P2 — Collector and reconciliation | PASS | Prove task-local archive retrieval, exact normalized DML, independently evaluated evidence, exactly-once AttemptKey behavior across trust refresh/expiry/invalidation, and zero control-to-dbt evidence promotion. |
| P3 — Bundle installer | PASS | Produce complete dependency locks and exact argv fixtures; prove generated tasks take no deployment/trust/component/actor/action/user parameter and that runtime deployment/trust operations never invoke dbt. |
| P4 — App read-only MVP | PASS | Present Lakeflow, dbt invocation, node/test, collector, capture, deployment, immutable collection-time trust, and current trust state separately. |
| P5 — Job onboarding | PASS | Deterministically inspect task shape, command sequence, selector, flags/aliases, vars, paths, target/connection features, versions, concurrency, and archive access independently of trust state. |
| P6 — Controlled actions | PASS | Authorize only a parameterless start of the approved bound Job. Candidate/stale/conflict/cardinality/source-anchor denial and action/user/trust input may not alter dbt configuration or evidence. |
| P7 — Security and operations | PASS | Prove field classification, diagnostics, retention/export/delete, zero runtime egress, digest-domain separation, and control provenance lifecycle without rewriting native dbt data. |
| P8 — Bounded live proof | PASS | Exercise success/failure/partial/early/cancel/retry/repair alongside phase/source/expiry/refresh/invalidation cases; prove no trust/deployment generation creates or duplicates a dbt attempt; finish with no compute running. |
| P9 — Optional intelligence | PASS | Pass install, capture, investigation, and lifecycle with AI disabled; accepted tools consume only deterministic validators and curated evidence. |
| P10 — Private alpha | PASS | Qualify representative projects against the exact matrix without admitting prerelease Core behavior, untested parser/state/artifact statuses, unsupported commands, or trust-derived command input. |

## Author-file outcome

| Author file or set | Outcome | dbt conclusion |
|---|---|---|
| README.md | PASS | Artifact-first dbt evidence and deployment/runtime-trust lifecycle remain separate. |
| AGENTS.md | PASS | Arbitrary dbt input is prohibited; exhaustive trust controls authorize/stamp only and cannot promote canonical evidence. |
| docs/index.md | PASS | The planning index introduces no dbt contradiction. |
| docs/decisions/0001-private-app-bundle.md | PASS | Observed dbt execution, collector DML, deployment reconciliation, trust events, migration, and optional capabilities remain separate planes. |
| docs/plans/product-plan.md | PASS | Baseline 0.13 repairs dual-phase/source/schema/time semantics while preserving exact argv, AttemptKey, artifact, log, result, partial-parse, retry/repair, and capture contracts. |
| docs/plans/review-process.md | PASS | P0-P10 gates prohibit migration/deployment/trust/component/user input from becoming a dbt command or evidence and demand later implementation proof. |
| docs/plans/documentation-plan.md | PASS | Planned pages distinguish App deployment artifacts, runtime-trust manifest/events, dbt manifest/run-results, structured logs, capture state, and current trust state. |
| docs/research/source-register.md | PASS | Stable pins, exact tagged behavior, schemas, warning/log/path/privacy rules, and prerelease boundaries remain grounded in primary sources. |

## Non-blocking portability watch

Core 1.12 is at release-candidate status and Core 2.0 is at alpha status. Current documentation already contains engine- and version-conditional parsing, state, artifact, status, and command behavior outside this frozen candidate. Adapter 1.12.2 explicitly caps Core below 1.11.13. Matching major/minor numbers or current unqualified docs are not compatibility proof.

Every future candidate needs a complete dependency lock; exact Python/Core/adapter/common versions; artifact schemas; flags and aliases; command decorators; result states and BuildTask collections; partial-parsing behavior; structured-log version/parser; native archive qualification; retry/repair semantics; and the same trust/deployment-input isolation tests.

## Cloud-mutation statement

This review used local repository reads, current official dbt documentation, first-party GitHub release/source/API data, the dbt schema registry, and the official Python package distribution. It did not authenticate to Azure or Databricks, execute dbt or SQL, start or stop compute, or create, modify, or delete any cloud resource. No paid resource was started.

## Final disposition

- Frozen baseline 0.13 dbt verdict: PASS.
- DBT-P0-001 through DBT-P0-008: resolved with no regression.
- DBX-P0-025 through DBX-P0-027: resolved in baseline 0.13 with no dbt regression.
- DBX-P0-022 through DBX-P0-024: remain resolved with no dbt regression.
- New dbt findings: none.
- P0 dbt blockers: none.
- P1/P2/P3/P4/P6/P8 must produce the explicit digest-domain, command-input isolation, parameterless-start, provenance separation, exactly-once, and live-archive evidence above.
