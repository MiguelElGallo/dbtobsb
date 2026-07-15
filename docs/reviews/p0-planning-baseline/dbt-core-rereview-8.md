# Eighth dbt Core re-review: P0 planning baseline 0.9

- Reviewed input: frozen author file set defined in `resolution.md`
- Re-review input SHA-256: `ca6df928ba9353ffa240f7a5c21ab9a7cccf68bf682145d58ad18f83de536d1a`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `PASS`
- Open dbt findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.9 passes the eighth dbt specialist review. The new Query History recovery contract, pre-revoke Delta attestation, composite seal, enumerated runtime DML, and runtime-trust states do not weaken or conflate the canonical dbt capture contract.

The author set preserves five distinct evidence classes:

1. The explicitly onboarded **observed Lakeflow Job** has the native dbt task, task attempt, optional `deps` ordinal, required `build` ordinal, immutable task-local paths, native archive, artifacts, structured logs, and dbt invocation identity.
2. The separate **collector Job** consumes that one allowlisted archive and writes the three normalized evidence tables under a trusted AttemptKey. It has no dbt project-data privilege, command surface, schema DDL, or migration-ledger access.
3. The attended **migration data plane** is fixed Statement Execution SQL on an installer-only warehouse. Query History supplies bounded recovery state for those SQL operations, not a dbt task, dbt command, archive, command ordinal, invocation, node result, or build-start signal.
4. `DATA_APPLIED_PENDING_REVOKE` plus the later **composite seal** proves a point-in-time data-contract and authority state. Statement Execution IDs, ledger rows, grant observations, and seal digests cannot satisfy any dbt artifact, AttemptKey, command, invocation, or result invariant.
5. The **runtime-trust manifest** classifies whether collector/App/Job code and authority still match the approved graph. It is separate from both migration state and dbt capture state: drift can make affected evidence untrusted or unverified, but it cannot manufacture a dbt attempt, artifact pair, invocation, node row, or successful capture.

Only a canonical archive from an explicitly onboarded observed dbt task can enter the dbt parser. A candidate still has to pass the exact manifest-v12/run-results-v6 pair, common non-null invocation UUID, Core 1.11.12, `args.which=build`, manifest adapter type, AttemptKey/ordinal, non-empty unique result, and BuildTask collection-resolution gates. Query History, Delta migration data, optional system snapshots, App/action records, and product runtime-integrity records satisfy none of those gates.

This is approval of the P0 planning contract. It does not claim that P1 fixtures and parsers, P2 collector code, P3 dependency locks and generated policy, P8 live archives, or P10 representative-project qualification already exist.

## Immutable input verification

The author scope is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently calculated SHA-256 for each file, sorted those per-file records by path, and hashed that stream before reviewing and again immediately before writing this report. The result was exactly:

```text
ca6df928ba9353ffa240f7a5c21ab9a7cccf68bf682145d58ad18f83de536d1a
```

Review reports and `resolution.md` are outside that digest. I changed no author file or earlier review.

## Method and current primary sources

I traced every P0-P10 planning part across exact dependency candidates, command construction, resolved flags, selector restrictions, artifact/log paths, artifact schemas, invocation and task correlation, early failures, retries/repairs, capture-state precedence, field allowlisting, migration isolation, runtime DML, runtime trust, optional enrichment, AI optionality, tests, and planned documentation.

Current official and first-party evidence checked on 2026-07-15 includes:

- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) and [Core 1.11.12 Python metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml)
- [`dbt-databricks` 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) and [exact dependency constraints](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml)
- [`dbt-databricks` 1.12.1 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.1), which introduced `job_id`, `job_run_id`, and `task_run_id` in `adapter_response`, and [`dbt-databricks` 1.11.8](https://github.com/databricks/dbt-databricks/releases/tag/v1.11.8), which added `invocation_id` to default query comments
- [Core command decorators](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/main.py), [global parameters and current/legacy aliases](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py), [resolved flags](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py), and [project/profile flag loading](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/config/project.py)
- [Core 1.11.12 BuildTask collections](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py) and [`MainReportVersion` emission](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py)
- [dbt build](https://docs.getdbt.com/reference/commands/build), [dbt retry](https://docs.getdbt.com/reference/commands/retry), [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings), [JSON artifact configuration](https://docs.getdbt.com/reference/global-configs/json-artifacts), [log configuration](https://docs.getdbt.com/reference/global-configs/logs), [events and logging](https://docs.getdbt.com/reference/events-logging), and [anonymous usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats)
- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), [run results](https://docs.getdbt.com/reference/artifacts/run-results-json), [other artifacts](https://docs.getdbt.com/reference/artifacts/other-artifacts), and [source-freshness results](https://docs.getdbt.com/reference/artifacts/sources-json)
- [manifest v12 schema](https://schemas.getdbt.com/dbt/manifest/v12.json), [run-results v6 schema](https://schemas.getdbt.com/dbt/run-results/v6.json), [sources v3 schema](https://schemas.getdbt.com/dbt/sources/v3.json), and the [dbt schema registry](https://schemas.getdbt.com/)
- [`dbt-common` 1.37.5 distribution](https://pypi.org/project/dbt-common/1.37.5/), whose published wheel digest I independently matched before inspecting `LOG_VERSION=3` and `backupCount=5` in that exact wheel
- [Azure Databricks native dbt task and archived output](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows), including the requirement to retrieve output with the individual dbt task run ID rather than the parent multi-task run ID
- [dbt Core 1.12.0rc3](https://github.com/dbt-labs/dbt-core/releases/tag/v1.12.0rc3) and [dbt Core 2.0.0 alpha.1](https://github.com/dbt-labs/dbt-core/releases/tag/v2.0.0-alpha.1) as pre-release trend evidence only

The candidate is coherent. Adapter 1.12.2 allows `dbt-core>=1.11.2,<1.11.13` and `dbt-common>=1.37.0,<1.38.0`; Core and adapter require Python `>=3.10`, and the published candidate classifiers intersect at CPython 3.10-3.13. The selected exact inputs remain Core 1.11.12, adapter 1.12.2, common 1.37.5, and Python 3.12.3. The published `dbt-common` wheel digest remains `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077`. The plan correctly treats this as a candidate until the complete Python/Node lock and every golden/staging test pass. Core 1.12 RC and Core 2.0 alpha remain outside the support matrix.

## Ranked findings

| Rank | Result |
|---|---|
| Blocker | None |
| High | None |
| Medium | None |
| Low | None |

No new dbt finding is opened. Baseline 0.9 changes Databricks migration recovery, receipt ordering, and later runtime-integrity classification; it does not change the native observed-task requirement, dbt argv, path namespace, artifact schemas, result resolver, log parser, AttemptKey, or capture-state precedence.

## Baseline 0.9 regression focus

| Baseline 0.9 change | Verdict | dbt-isolation conclusion |
|---|---|---|
| Cross-user recovery through GA Query History | `PASS` | Query History is scoped to fixed installer SQL recovery. It is not read by the canonical dbt artifact parser, is not a native task archive, and cannot prove a dbt build started or ended. A query marker UUID or Statement Execution ID is never a dbt invocation ID. |
| `DATA_APPLIED_PENDING_REVOKE` followed by exact revoke and composite observation | `PASS` | The ledger/view is outside all three normalized evidence tables and inaccessible to the collector. A pending row or seal has no manifest/run-results schema URL, dbt version, `args.which`, adapter type, AttemptKey, command ordinal, or result IDs. |
| Enumerated runtime DML and named runtime trusted roots | `PASS` | The collector's intentional write set remains exactly the three evidence tables, while every runtime principal is denied migration-ledger DML and DDL. Job/App/SP managers are honestly trusted roots; drift changes the separate runtime-integrity classification before affected output is trusted, not the parsed dbt facts. |
| Product Jobs after removal of the migration Job | `PASS` | Collector, role-administration, and optional enrichment Jobs are fixed non-dbt jobs and remain outside the explicitly onboarded observed-job/task namespace. The only supported dbt producer is a native task whose resolved sequence is optional `deps` plus one named-selector `build`. |
| Optional system snapshots | `PASS` | Lakeflow and billing snapshots are operational enrichment only. They can corroborate outer platform context but cannot create a dbt invocation, artifact-pair result, or normalized node/test fact. |

## Prior dbt finding dispositions

| Finding | Eighth re-review disposition | Baseline 0.9 conclusion |
|---|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION` | Both zero-execution warnings remain promoted; no-match, filtered-to-nothing, ephemeral-only, and every empty-result path remain non-observable. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION` | Only optional `deps` plus one named-selector `build` is ready. Project/profile and current/legacy alias conflicts fail deterministically; both ordinals disable anonymous usage and artifact-ingest upload; no migration, App, Job parameter, user, or AI input supplies command fragments. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION` | Standalone validation still precedes pair validation. Manifest-only may be `PARTIAL`; run-results-only is invalid; neither-file requires same-build start evidence; unavailable retrieval wins; no `deps` or migration event proves build start. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION` | Exact Core/adapter/common/Python/schema/log inputs and the seven ordered log states remain intact. Unknown or damaged diagnostic logs do not invalidate a valid primary pair. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION` | Manifest resources remain inventory; unmatched resources are `NO_RESULT_RECORDED`; Job, invocation, node/test, collector, capture, migration, and runtime-integrity outcomes remain distinct. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION` | Ordinal-local immutable paths, no `deps --target-path`, and closed-file size/rotation/truncation rules remain exact. Migration SQL has no dbt path or command ordinal. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION` | Curated evidence remains allowlisted. Raw/compiled code, vars, messages, adapter messages, arbitrary metadata/events, custom environment content, and `msg` remain excluded from ordinary tables and receipts. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION` | Genie and MCP remain optional and advisory; they cannot construct commands, authorize runs, validate evidence, execute migration SQL, or unlock runtime. |

## Exact dbt contract verification

| Contract area | Verdict | Eighth re-review conclusion |
|---|---|---|
| Exact candidate pins | `PASS` | Core 1.11.12 and adapter 1.12.2 are current tagged releases; the adapter's exact Core/common ranges admit the selected versions. Common 1.37.5/log version 3, Python 3.12.3, and the wheel digest remain candidate inputs, not a substitute for a full lock. |
| Artifact schemas | `PASS` | Core 1.11 maps to manifest v12; current run-results is v6. The plan validates full schemas first and fails closed on unqualified schema versions. |
| Invocation identity | `PASS` | Both primary artifacts require the same non-null parseable UUID in the same AttemptKey and primary-build ordinal. Platform/query IDs and the adapter's optional correlation fields never replace it. |
| Commands and selectors | `PASS` | The ready sequence is build-only or deps-then-build. The selector is a version-controlled named selector, not App/parameter/AI input; every unsupported primary command is classified explicitly. |
| Resolved flags | `PASS` | Scanner evaluation covers CLI, configured current and legacy environment aliases, exactly one project-or-profile mapping, `DO_NOT_TRACK`, and defaults. It does not infer readiness from command text alone. |
| Warning and empty execution | `PASS` | `NoNodesForSelectionCriteria` and `NothingToDo` are targeted errors, and an independent non-empty-result invariant rejects ephemeral-only or any other empty execution. |
| Paths and overwrite prevention | `PASS` | Attempt and ordinal paths are unique across runs, retries, repairs, and commands. `build` receives its own target path; `deps` receives no target path; structured logs use ordinal-local paths. |
| Structured logs | `PASS` | JSON file logs are parsed by qualified event/version fields, never human `msg`. `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID` remain ordered per ordinal. |
| Rotation bounds | `PASS` | The exact common wheel uses five backups; the plan's active-plus-five cap and 20 MiB per-file setting produce the explicit six-file/120-MiB collector ceiling. Saturation without the initial version event is truncated, not silently missing. |
| Artifact pair | `PASS` | The exact v12/v6 pair requires Core 1.11.12, `args.which=build`, manifest `adapter_type=databricks`, one shared invocation UUID, non-empty unique results, and exact resolution across BuildTask's node/unit-test/saved-query/exposure/function collections. |
| Partial and early failure | `PASS` | Manifest-only, run-results-only, neither-file, inaccessible archive, pre-logger failure, and same-build start remain distinguishable. Outer Lakeflow state records failures before dbt or the collector starts. |
| Retry and repair | `PASS` | `dbt retry` remains unsupported as the normal path because it depends on prior run-results and can do nothing after zero-node early failure. Lakeflow retries/repairs create new attempt coordinates and run the complete supported build, with idempotent reconciliation. |
| Task/platform correlation | `PASS` | The trusted crosswalk includes job run, repair, dbt task run, execution count, command ordinal, invocation ID, and hashes. Adapter `job_id`/`job_run_id`/`task_run_id` fields are corroboration only, matching the first-party release evidence. |
| Native archive retrieval | `PASS` | The plan uses the individual dbt task run ID, preserves retrieval state separately, never stores the signed archive link, and keeps inline/truncated output below primary artifact priority. P8 still must prove custom target/log-path capture in the real archive. |
| Field allowlisting | `PASS` | Ordinary data excludes raw code, compiled SQL, vars, messages, adapter messages, raw events, signed links, and arbitrary/custom environment metadata. Restricted closed diagnostics are optional, bounded, separately permissioned, and retained under policy. |
| Migration and seal isolation | `PASS` | Statement Execution, Query History, the Delta pending row, exact revoke, and composite seal have no entry into the observed-task archive or normalized dbt evidence namespace. |
| Runtime-integrity isolation | `PASS` | Runtime drift is a separate trust overlay. The author set never converts a verified migration seal or product runtime record into a valid dbt artifact, and never lets runtime integrity erase the underlying native dbt facts. |
| Optional enrichment and AI | `PASS` | System snapshots are operational context, and AI remains optional. The deterministic capture/parser path is complete with both disabled. |

## P0-P10 dbt review matrix

These verdicts approve the planning contract and its named future gates. They do not claim that later implementation evidence already exists.

| Part | Verdict | Required dbt evidence at that part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record all eighth specialist outcomes against this frozen hash and complete the repository acceptance sequence. |
| P1 — Capture library | `PASS` | Implement vendored exact schemas, standalone/pair validation, BuildTask result resolution, path/size/hash and field allowlists, total capture/log precedence, and every adversarial golden fixture. |
| P2 — Collector and reconciliation | `PASS` | Prove canonical individual-task archive retrieval, per-ordinal closed-path bounds, exactly-once AttemptKey writes, and hard denial of migration, ledger, runtime-integrity, collector, role, enrichment, and non-onboarded contexts as dbt evidence. |
| P3 — Bundle installer | `PASS` | Produce full dependency locks and exact argv fixtures; prove Direct/migration/Query History/attestation/seal records have no observed dbt namespace; prove runtime identity and trust checks cannot inject command, path, or evidence input. |
| P4 — App read-only MVP | `PASS` | Present outer Job, dbt invocation, node/test, collector, capture, migration, seal, optional enrichment, and runtime-integrity outcomes as distinct states and views. |
| P5 — Job onboarding | `PASS` | Deterministically inspect native task shape, command sequence, selector, flags, aliases, vars, paths, privacy/egress, versions, and access/check failures; reject product jobs and unsupported commands as observed dbt jobs. |
| P6 — Controlled actions | `PASS` | Start only a pre-approved bound observed Job. No user, App, role Job, migration envelope, Query History marker, AI, or request parameter supplies a dbt command, selector, vars, path, artifact, log, or SQL fragment. |
| P7 — Security and operations | `PASS` | Prove field classification, restricted diagnostics, retention/export/delete, egress denial, product-ledger isolation, trust-state separation, and lifecycle cleanup without broadening normalized fields. |
| P8 — Bounded live proof | `PASS` | Capture real success/failure/partial/early/cancel/retry/repair paths, prove archive and AttemptKey correlation, prove every migration/seal/product-Job operation creates zero dbt invocation/node rows, exercise runtime drift, and finish with no running compute. |
| P9 — Optional intelligence | `PASS` | Pass install, capture, validation, investigation, and lifecycle suites with AI disabled; any accepted tool uses deterministic validators and curated data only. |
| P10 — Private alpha | `PASS` | Qualify representative real projects against the exact candidate matrix without silently expanding commands, flags, adapters, schemas, versions, or evidence types. |

## Author file-set result

| Author file | Verdict | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | Artifact-first capture, attended non-Job migration, pending-row/composite distinction, enumerated runtime DML, and separate runtime-integrity trust are explicit. |
| `AGENTS.md` | `PASS` | Prohibits dynamic dbt input, unsafe path/log handling, collector DDL, migration-ledger access, Jobs receipts, floating dependencies, and AI enforcement; it names exact runtime writes without turning them into dbt evidence. |
| `docs/index.md` | `PASS` | Contains no unsupported dbt claim and routes to the normative decision, plans, sources, and reviews. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Separates observed native dbt execution, collection, Statement Execution migration, pending attestation/composite seal, App/action state, optional enrichment, and runtime-trust boundaries. |
| `docs/plans/product-plan.md` | `PASS` | Preserves the exact version/command/path/artifact/log/AttemptKey/capture contract while making Query History, Delta migration state, intentional runtime DML, and integrity drift non-canonical context. |
| `docs/plans/review-process.md` | `PASS` | Requires dbt review for every P0-P10 part and explicitly checks that migration input cannot become a dbt command or evidence. |
| `docs/plans/documentation-plan.md` | `PASS` | Plans distinct command, artifact, flag, AttemptKey, capture, migration, seal, runtime-integrity, and operational-enrichment pages and terminology, with real sanitized evidence at later stages. |
| `docs/research/source-register.md` | `PASS` | Current tagged Core/adapter constraints, schemas, commands, flags, artifacts, logs, correlation additions, wheel evidence, and pre-release trends are sufficient for P0. |

## Bounded future gates

No P0 author change is required. Before support is claimed, later parts must still prove:

- P1 exact schema and parser behavior against adversarial artifact, log, path, size, duplication, early-failure, and precedence fixtures.
- P2/P5 hard exclusion of migration, ledger, runtime-integrity, collector, role, enrichment, and every non-native/non-onboarded product context from observed capture.
- P3 complete reproducible Python/Node locks, parser-verified argv and effective-flag resolution, and static policy proving no migration/Query History/attestation/seal input can enter a dbt command or evidence record.
- P8 real native archives with the generated target/log paths; task/job/invocation correlation; success, failure, cancellation, timeout, retry and repair; migration/product-Job isolation; runtime drift; and a stopped inventory.
- P10 representative real-project and adapter-feature qualification.

Any Core, adapter, common, Python, serverless environment, artifact schema, log version, command surface, adapter feature, native archive behavior, or product execution-class change reopens qualification.

## Cloud-mutation statement

This review used local repository reads, current official web documentation, tagged first-party GitHub release/source reads, JSON-schema reads, and an ephemeral local inspection of the checksum-verified published `dbt-common` wheel. It did not authenticate to, query, create, start, stop, modify, or delete any Azure, Databricks, dbt Cloud, GitHub repository, or other cloud resource. No paid compute was started.

## Final disposition

- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- Blocking or high findings: none.
- Eighth dbt specialist verdict for frozen baseline 0.9: `PASS`.
