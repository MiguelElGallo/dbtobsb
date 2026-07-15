# Tenth dbt Core re-review: P0 planning baseline 0.11

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `4c033d3a47ebd9c11b695177d1e166986af5c74d404ded76cfed828c088d8073`
- Date: 2026-07-15
- Reviewer: independent dbt Core and `dbt-databricks` product/security specialist
- Verdict: `PASS`
- Open dbt P0 findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.11 passes the tenth independent dbt review. The durable runtime-trust ledger/view, staged App lifecycle, candidate-versus-accepted distinction, stale-collection rule, additional control fields, and P6 conditional gate repair platform and human-flow defects without changing the canonical dbt capture contract.

The decisive separation is now explicit and implementable:

1. Only an explicitly onboarded native Lakeflow dbt task can produce a dbt attempt. Its supported sequence remains optional `dbt deps` followed by exactly one version-controlled named-selector `dbt build`.
2. AttemptKey plus command ordinal still owns the immutable task-local target/log namespace and archive correlation. A trust generation, snapshot ID, action ID, App deployment ID, migration operation, user identity, or trust-event ID is not part of AttemptKey.
3. Only a fully qualified manifest-v12/run-results-v6 pair can create trusted node/test results. Runtime-trust rows, status-view rows, candidates, accepted events, migration attestations, App records, Query History, action records, and system snapshots satisfy none of the artifact-pair gates.
4. Structured JSON logs remain independent diagnostic evidence. Runtime-trust state cannot become a log event, `MainReportVersion`, invocation ID, start event, or substitute for missing/malformed/truncated/unknown-version log evidence.
5. The collector may copy a typed accepted-snapshot reference and server-evaluated trust state into its own product row as provenance. That stamp is not dbt evidence and cannot participate in argv construction, artifact validation, result resolution, capture-state precedence, or idempotency identity.
6. `TRUST_CANDIDATE`, `SNAPSHOT_ACCEPTED`, stale, drift, and unverified states control product presentation and authorization. They never rewrite the outer Lakeflow attempt, dbt invocation, native result status, artifact hash, structured-log state, or capture state.

This is approval of the P0 planning contract. It is not evidence that P1 parsers, P2 writes, P3 locks/generated Jobs, P6 actions, P8 native archives, or P10 representative-project qualification already exist.

## Immutable input verification and scope

I independently hashed the requested author files by path, sorted their per-file SHA-256 records, and hashed that stream before review and again immediately before writing this report. Both calculations produced exactly:

```text
4c033d3a47ebd9c11b695177d1e166986af5c74d404ded76cfed828c088d8073
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

Review reports and the resolution ledger are outside the digest. I read the complete author scope and all three ninth reports. I specifically traced the baseline 0.11 resolutions of `DBX-P0-020`, `DBX-P0-021`, `UX-P0-011`, `UX-P0-012`, and `UX-P0-013` through every dbt boundary. I edited no author file or earlier report; this report is the only file written.

## Current primary evidence checked

As of 2026-07-15, the candidate remains a coherent exact stable intersection:

- [dbt Core 1.11.12](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) is the latest stable tagged Core release and is classified Production/Stable with Python 3.10-3.13 in its [tagged dependency metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml).
- [`dbt-databricks` 1.12.2](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) is the latest stable tagged adapter release. Its [tagged metadata](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml) declares `dbt-core>=1.11.2,<1.11.13`, `dbt-common>=1.37.0,<1.38.0`, Python `>=3.10`, and classifiers through Python 3.13. The release explicitly raises the Core upper bound to admit 1.11.12 and includes the Python-model non-success-state fix.
- The official package index still publishes `dbt_common-1.37.5-py3-none-any.whl` with SHA-256 `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077` on the [dbt-common 1.37.5 release](https://pypi.org/project/dbt-common/1.37.5/). The wheel contains `LOG_VERSION = 3` and a rotating file handler with five backups, matching the six-file bound.
- Current [artifact documentation](https://docs.getdbt.com/reference/artifacts/dbt-artifacts) defines versioned artifacts and common per-invocation metadata. [Manifest documentation](https://docs.getdbt.com/reference/artifacts/manifest-json) continues to define project inventory, while [run-results documentation](https://docs.getdbt.com/reference/artifacts/run-results-json) continues to define executed results joined through `unique_id` and lists schema v6.
- The exact initial schema contracts remain [manifest v12](https://schemas.getdbt.com/dbt/manifest/v12.json) and [run-results v6](https://schemas.getdbt.com/dbt/run-results/v6.json). Tagged [Core 1.11.12 `BuildTask`](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py) still owns the exact supported result resource collections.
- Current [JSON-artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts) continues to state that output is written to `target/` and that disabling JSON writes avoids overwriting prior artifacts. This supports immutable attempt- and ordinal-local paths.
- Current [log configuration](https://docs.getdbt.com/reference/global-configs/logs) continues to expose structured `log_version`, event name/code, level, timestamp, thread, and invocation identity separately from human `msg`, and independently configurable log/target paths.
- Current [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings) still supports targeted promotion of `NoNodesForSelectionCriteria`; tagged Core 1.11.12 contains both that warning and `NothingToDo`.
- Current [`dbt build` documentation](https://docs.getdbt.com/reference/commands/build) still defines one combined manifest/run-results output and DAG/test skip semantics. Current [`dbt retry` documentation](https://docs.getdbt.com/reference/commands/retry) still depends on the prior `run_results.json`, which supports retaining full Lakeflow-attempt retry as the normal product path.
- Current [project-parsing documentation](https://docs.getdbt.com/reference/parsing) states that `partial_parse.msgpack` is an internal cached manifest and documents stale parse-time-context limitations. It remains ancillary, never a primary execution artifact.
- Azure Databricks continues to require the individual dbt task run ID, not the parent multi-task run ID, for native [dbt task artifact retrieval](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows).

[Core 1.12.0rc3](https://github.com/dbt-labs/dbt-core/releases/tag/v1.12.0rc3) remains a pre-release. The 1.12 prerelease line has introduced parser/status/command changes, so baseline 0.11 correctly excludes it, Core 2.0/Fusion, state reuse, new artifacts, and new result states from the exact candidate.

## Baseline 0.11 regression review

| Baseline 0.11 change | Verdict | dbt conclusion |
|---|---|---|
| `runtime_trust_ledger` and `runtime_trust_status_v` | `PASS` | These are separately owned control objects. The collector has status-view `SELECT` only and no ledger write. Neither object is in the native archive or primary artifact allowlist, and neither can create an AttemptKey, invocation, result, log event, or capture state. |
| `MANIFEST_REGISTERED` / `TRUST_CANDIDATE` / `SNAPSHOT_ACCEPTED` / `SNAPSHOT_INVALIDATED` | `PASS` | These are product trust-event states, not dbt manifest or run-result states. A candidate unlocks neither collection nor actions; acceptance only labels/authorizes product use after the same App deployment is observed. |
| Stage, deploy, stop, bind, candidate, direct start, reobserve, accept | `PASS` | Every command in this sequence targets the Databricks App/resource plane. It neither invokes the observed native dbt task nor changes the closed dbt argv, selector, target/log paths, artifact schemas, or AttemptKey. |
| Read-only trust-view stamping | `PASS` | The stamp is provenance attached after the collector independently satisfies the canonical archive/artifact/log contract. It must remain excluded from artifact hashes, invocation identity, result resolution, capture predicates, and the collector's exactly-once key. |
| Expired-snapshot continuation | `PASS` | Base collection may continue only for an expired matching contract and stamps `STALE`; this changes trust presentation, not the already observed dbt facts. Absent/mismatched contract fails the write. Existing output is labeled from the current view without rewriting native dbt status. |
| Candidate/unverified interval | `PASS` | The App remains setup-only and exposes no trusted evidence/action. A dbt attempt that exists during this interval remains an outer platform fact; trust state cannot manufacture or delete its canonical artifact evidence. |
| P6 conditional accepted-row gate | `PASS` | The conditional DML is an action-authorization gate outside the observed dbt task. It may authorize starting only the pre-approved bound Job; no user/action/roster/trust/migration field may supply or override task parameters, dbt command material, selector, vars, paths, environment, or evidence. |
| Added deployment, authority, roster, signature, and timing fields | `PASS` | They live in the control ledger/view and have no dbt artifact schema URL, invocation UUID, command ordinal, AttemptKey, node `unique_id`, event envelope, or native archive path. Generic deployment `artifact_digest` terminology must remain type/name-separated from dbt artifact hashes in P1/P3 schemas. |
| Two-person topology and one recovery-actor table | `PASS` | Human choreography and migration cleanup do not create a dbt invocation. Query History and Statement Execution records remain non-dbt evidence classes. |

## Exact dbt contract revalidation

| Contract area | Verdict | Tenth-review conclusion |
|---|---|---|
| Version/dependency boundary | `PASS` | Core 1.11.12, adapter 1.12.2, common 1.37.5, Python 3.12.3, schema v12/v6, and log version 3 remain a coherent candidate. Complete Linux/Python and Node hash locks remain P3 evidence. |
| Supported commands | `PASS` | Only optional `deps` plus one required `build` is ready. All other commands remain unsupported, deferred, validation-only, or non-observable. App lifecycle and trust-event commands are not dbt commands. |
| Selector/empty work | `PASS` | The approved selector remains version controlled. Both zero-execution warnings and the independent non-empty-results postcondition prevent false observability. Trust/action/user input cannot select work. |
| Resolved flags | `PASS` | CLI, current/legacy aliases, one allowed project-or-profile mapping, `DO_NOT_TRACK`, and defaults remain independently scanned. Project/profile and alias conflicts still fail deterministically. |
| Exact argv | `PASS` | `deps` and `build` retain separate templates. Both ordinals disable anonymous usage and artifact-ingest upload; `deps` receives no selector or unsupported `--target-path`; `build` receives the approved selector and ordinal-local target path. |
| AttemptKey and paths | `PASS` | Job/task run coordinates, repair/execution counters, and command ordinal remain the correlation/path namespace. Trust generation/snapshot/action fields are overlays and cannot enter AttemptKey or target/log path construction. |
| Concurrency | `PASS` | Signed task concurrency remains an observed configuration input, but it does not become an artifact invariant. Overlapping attempts remain isolated by AttemptKey/ordinal roots. A trust refresh cannot create a second attempt row or change idempotency identity. |
| Partial parsing | `PASS` | `partial_parse.msgpack` remains path/size-checked ancillary output only. Runtime trust neither seeds nor validates it. Pair equality still excludes metadata fields partial parsing may retain while requiring complete schema/invocation/command/version/adapter/result invariants. |
| Manifest/run-results pair | `PASS` | One same-invocation v12/v6 pair, exact Core version, `args.which=build`, manifest adapter type, trusted AttemptKey/ordinal, non-empty unique results, and exact BuildTask resolution remain mandatory. No control object can satisfy one of these fields. |
| Incomplete/early failure | `PASS` | Manifest-only may be `PARTIAL`; run-results-only is invalid; neither-file plus same-build start may be partial; neither-file without it is not produced; unavailable retrieval wins. Trust events never count as build-start evidence. |
| Structured logs | `PASS` | The seven ordered states remain unavailable, not initialized, truncated, malformed, missing, unknown version, and valid. A trust event, App event, migration event, or `deps` event cannot prove primary-build start. |
| Retry/repair/reconciliation | `PASS` | Lakeflow repeats a complete build in a new attempt; the same collector handles reconciliation. Snapshot changes may alter only provenance/presentation and never merge or duplicate artifacts across attempts. |
| Field/privacy boundary | `PASS` | Raw/compiled code, vars, messages, adapter messages, arbitrary metadata/events, custom environment content, and human `msg` stay out of ordinary tables. Trust control rows add no permission to persist raw dbt evidence. |
| Optional AI/future engines | `PASS` | Core operation remains complete with AI disabled. No model can create dbt command material or satisfy deterministic validation. Future Core/adapter/parser/status surfaces require a new frozen matrix. |

## Numbered finding disposition

No new numbered dbt finding is opened. I found no critical, high, medium, or low P0 correctness defect in baseline 0.11.

The following implementation rules are mandatory later-part evidence, not deferred corrections to P0:

1. P1/P2 must type the trust snapshot as provenance only and prove that removing or forging it cannot make an invalid archive valid, create node rows, or change capture/log precedence.
2. P2 exactly-once identity must remain AttemptKey plus trusted canonical hashes; a refresh, expiry transition, or different accepted snapshot cannot duplicate one attempt. Tests must distinguish an immutable collection-time stamp from current UI trust labeling.
3. P3 must generate observed dbt tasks without any runtime-trust, migration, actor, action, roster, or App-deployment value in dbt argv, Job/task parameter overrides, dbt environment, target/log paths, artifacts, or logs. Runtime-trust manifests may hash the approved task configuration but never supply it at run time.
4. P6 must invoke only the pre-approved bound Job with no dbt-task/job-parameter override. The conditional accepted-row DML controls action authorization only; its snapshot/action fields cannot cross into the observed task.

## Prior dbt finding disposition

| Prior finding | Tenth re-review disposition |
|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION`; both zero-execution warnings plus the non-empty-results invariant prevent false observability. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION`; the command matrix, command-specific argv, configuration conflicts, privacy flags, selector boundary, and no-runtime-trust-input rule remain closed. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION`; standalone/pair validation and total retrieval/capture precedence remain deterministic, and trust events cannot become primary candidates or start evidence. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION`; exact dependency/schema/wheel/log-version qualification remains intact. The durable trust schema does not expand the dbt compatibility matrix. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION`; manifest inventory, invocation results, Lakeflow state, collector state, capture state, and runtime trust remain distinct. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION`; ordinal-local paths, rotation bounds, pre-logger states, and closed-file rules remain exact. Trust ledger/view data is not a log source. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION`; allowlisting remains primary and secret scrubbing remains defense in depth. Added control fields are separately typed and contain no raw dbt artifact/log payload. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION`; Genie/MCP/LLM capability remains optional and outside execution, capture, validation, authorization, and trust promotion. |

## P0-P10 dbt outcomes

| Part | Planning outcome | Required dbt evidence at the part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record this immutable-hash verdict with the other specialist outcomes; no dbt P0 finding remains. |
| P1 — Capture library | `PASS` | Implement vendored exact schemas, pair/result validation, total capture/log precedence, field allowlists, and typed trust-provenance separation with adversarial fixtures. |
| P2 — Collector and reconciliation | `PASS` | Prove canonical individual-task archive retrieval, exact three-table DML, read-only status lookup, stale matching continuation, absent/mismatch denial, exactly-once AttemptKey writes across trust refreshes, and zero trust-to-dbt evidence promotion. |
| P3 — Bundle installer | `PASS` | Produce complete locks and exact argv fixtures; bind concurrency and paths; prove App stages/trust events do not invoke dbt and that no migration/trust/action/user input reaches observed Job/task parameters, dbt environment, commands, paths, artifacts, or logs. |
| P4 — App read-only MVP | `PASS` | Present Lakeflow, dbt invocation, node/test, collector, capture, migration, App lifecycle, runtime trust, and optional enrichment separately. Trust age/state must not rewrite dbt facts. |
| P5 — Job onboarding | `PASS` | Deterministically inspect task shape, exact command sequence, selector, resolved flags/aliases, vars, paths, versions, target/connection features, concurrency, and access/check failures independently of runtime trust. |
| P6 — Controlled actions | `PASS` | The accepted-row condition authorizes only a parameterless start of an already approved bound Job. No request, actor, action, migration, trust, roster, group, App, role Job, or AI value may become dbt command/evidence material. |
| P7 — Security and operations | `PASS` | Prove field classification, diagnostics, retention/export/delete, zero runtime egress, and trust-overlay behavior without broadening or rewriting canonical dbt data. |
| P8 — Bounded live proof | `PASS` | Capture real success/failure/partial/early/cancel/retry/repair paths; prove archive/AttemptKey correlation; exercise overlapping collection/reconciliation across candidate/accept/expiry/refresh; prove no trust generation creates or duplicates a dbt attempt; finish with no compute running. |
| P9 — Optional intelligence | `PASS` | Pass installation, capture, investigation, and lifecycle with AI disabled; accepted tools use only deterministic validators and curated evidence. |
| P10 — Private alpha | `PASS` | Qualify representative projects against the exact matrix without silently admitting Core 1.12/2.0, state reuse, new artifacts/statuses, untested adapter options, or trust-derived command input. |

## Author-file outcome

| Author file or set | Outcome | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | Artifact-first evidence and durable-but-separate point-in-time runtime trust are stated without conflation. |
| `AGENTS.md` | `PASS` | Arbitrary execution remains prohibited; trust writers are view-only and cannot promote trust or broaden canonical evidence. |
| `docs/index.md` | `PASS` | The planning index introduces no dbt contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Observed dbt execution, collection, migration, App lifecycle, trust events, and optional capabilities are separate planes. |
| `docs/plans/product-plan.md` | `PASS` | The exact argv/artifact/log/AttemptKey/capture contract is unchanged; baseline 0.11 adds a typed provenance/authorization overlay and an implementable App deployment order. |
| `docs/plans/review-process.md` | `PASS` | P0-P10 dbt gates explicitly prohibit migration or trust input from becoming dbt command/evidence and require re-review after material change. |
| `docs/plans/documentation-plan.md` | `PASS` | Planned pages keep Job, dbt invocation, artifact, diagnostic log, capture, migration, App deployment, and runtime trust distinct. |
| `docs/research/source-register.md` | `PASS` | Current stable pins, schemas, flags, logs, archive behavior, and pre-release boundary are represented with primary sources and appropriate cautions. |

## Non-blocking portability watch

Core 1.12 is now at release-candidate status and continues to change parsing, commands, statuses, and artifact surfaces. Adapter 1.12.2 intentionally admits only Core `<1.11.13`. Do not infer that matching minor numbers make adapter 1.12.2 compatible with Core 1.12, and do not admit `Reused`, new parser/state behavior, OSI/new artifacts, connector-kernel options, or `catalogs.yml` v2 merely because current release notes mention them. Each exact future pair needs its own dependency lock, schemas, flags, result states, partial-parse behavior, structured-log version/parser, native archive qualification, and trust-input isolation fixtures.

## Cloud-mutation statement

This review used local repository reads, current official dbt documentation, first-party tagged GitHub releases/source, the official schema registry, the official Python package index, and the official Databricks native dbt-task documentation. It did not authenticate to Azure or Databricks, execute dbt or SQL, start/stop compute, or create, modify, or delete any cloud resource. No paid resource was started.

## Final disposition

- Frozen baseline 0.11 dbt verdict: `PASS`.
- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- P0 dbt blockers: none.
- P1/P2/P3/P6/P8 must produce the explicit trust-input-isolation, parameterless-start, exactly-once, concurrency, and live-archive evidence above.
