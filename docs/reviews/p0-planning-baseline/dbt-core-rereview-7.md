# Seventh dbt Core re-review: P0 planning baseline 0.8

- Reviewed input: frozen author file set defined in `resolution.md`
- Re-review input SHA-256: `185113f8218872fc934f40ecce588b255507fdfd400bdbde6f0c7755e48ebe3f`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `PASS`
- Open dbt findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.8 passes the seventh dbt specialist review. The change from a privileged migration Job and Jobs-output receipt to an attended Statement Execution data plane and durable Delta receipt does not weaken, overlap, or imitate the dbt evidence contract.

The execution classes are now unambiguous:

1. The **observed customer Job** is the only dbt execution surface. Its immutable, version-controlled native dbt task may run optional `deps` followed by exactly one supported `build`; its task attempt owns the dbt command ordinals, native archive, artifacts, logs, and invocation ID.
2. The **collector Job** is a separate DML-only consumer. It has `CAN_VIEW` only on explicitly onboarded observed Jobs, validates the canonical archive in the trusted AttemptKey and command-ordinal context, and writes only the three normalized evidence tables. It cannot run dbt, read customer project data, perform DDL, or read the migration ledger.
3. The **product data plane** is no longer a Job. Signed code sends fixed, parameter-bound statements through the Statement Execution API as the attended UC operator. It has no Lakeflow Job or task run, native dbt task, dbt argv, target/log path, archive, `manifest.json`, `run_results.json`, `MainReportVersion`, dbt invocation ID, or collector AttemptKey.
4. The **authoritative receipt** is a closed row in `dbtobsb_migration_ledger`, read through `dbtobsb_installation_receipts`. It is not Jobs output, is outside the normalized-evidence tables, and is unreadable by the collector. No Jobs-visible receipt carrier exists in v1.

Consequently, the removed migration Job and removed Jobs-output receipt cannot be classified as dbt evidence: there is no product Job run to onboard or correlate, no native archive to retrieve, and no compatible artifact pair to validate. A copied row or local receipt would also fail every evidence gate because canonical capture requires an explicitly onboarded observed task attempt, primary-build ordinal, exact v12/v6 pair, shared non-null invocation UUID, Core 1.11.12, `args.which=build`, Databricks adapter type, and non-empty uniquely resolved results.

This is approval of the P0 planning contract. It is not a claim that P1 golden captures, P2 collector code, P3 reproducible locks and policy tests, P8 live isolation proof, or P10 real-project qualification already exist.

## Immutable input verification

The author scope is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently calculated SHA-256 for each file, sorted those per-file records by path, and hashed that stream. Before review and again before writing this report, the result was exactly:

```text
185113f8218872fc934f40ecce588b255507fdfd400bdbde6f0c7755e48ebe3f
```

Review reports and `resolution.md` are outside that digest. I changed no author-owned file or earlier review.

## Method and current primary sources

I traced the complete P0-P10 contract across compatibility, command construction, configured flag resolution, artifact/log production, archive retrieval, AttemptKey correlation, normalization, privacy, UI semantics, product-Job exclusion, optional enrichment, AI optionality, tests, and documentation. Current first-party evidence checked on 2026-07-15 includes:

- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) and [Core Python metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml)
- [`dbt-databricks` 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) and [exact dependency constraints](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml)
- [`dbt-databricks` 1.12.1 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.1), which added the optional Job/task correlation fields in `adapter_response`
- [Core command decorators](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/main.py), [parameter and environment aliases](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py), [resolved flags](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py), and [project/profile flag loading](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/config/project.py)
- [Core 1.11.12 BuildTask collections](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py) and [`MainReportVersion` emission](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py)
- [dbt build](https://docs.getdbt.com/reference/commands/build), [warnings](https://docs.getdbt.com/reference/global-configs/warnings), [JSON artifact paths](https://docs.getdbt.com/reference/global-configs/json-artifacts), [logs](https://docs.getdbt.com/reference/global-configs/logs), [events](https://docs.getdbt.com/reference/events-logging), and [usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats)
- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), and [run results](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [manifest v12 schema](https://schemas.getdbt.com/dbt/manifest/v12.json), [run-results v6 schema](https://schemas.getdbt.com/dbt/run-results/v6.json), and [`dbt-common` 1.37.5](https://pypi.org/project/dbt-common/1.37.5/)
- [dbt Core 1.12.0rc3](https://github.com/dbt-labs/dbt-core/releases/tag/v1.12.0rc3) and [Core 2.0 alpha](https://github.com/dbt-labs/dbt-core/releases/tag/v2.0.0-alpha.1) as trend evidence only

The candidate remains internally coherent: adapter 1.12.2 permits Core `>=1.11.2,<1.11.13` and `dbt-common>=1.37.0,<1.38.0`; both Core and adapter require Python `>=3.10`, and their declared/tested candidate intersection includes CPython 3.10-3.13. The exact selected inputs remain `dbt-core==1.11.12`, `dbt-databricks==1.12.2`, `dbt-common==1.37.5`, and Python 3.12.3. The `dbt-common` 1.37.5 wheel digest remains `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077`; its source sets `LOG_VERSION=3` and its rotating file handler retains five backups. Core 1.12 and 2.0 are pre-releases and correctly remain outside the MVP support matrix.

## Ranked findings

| Rank | Result |
|---|---|
| Blocker | None |
| High | None |
| Medium | None |
| Low | None |

No new dbt finding is opened. Baseline 0.8 changes installer custody and receipt transport, not the canonical dbt process, command templates, task-attempt namespace, artifact parser, log parser, or capture-state precedence.

## Prior dbt finding dispositions

| Finding | Seventh re-review disposition | Baseline 0.8 conclusion |
|---|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION` | Both zero-selection warnings are promoted. No-match, filtered-to-nothing, ephemeral-only, and every other empty-result path remain non-observable. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION` | Only optional `deps` followed by one named-selector `build` is ready. Project/profile and current/legacy alias conflicts fail deterministically; both ordinals disable anonymous usage and artifact-ingest upload; no App, migration, Job parameter, AI, or capsule supplies command input. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION` | Standalone validation precedes pair validation. Manifest-only may be `PARTIAL`; run-results-only is invalid; neither-file needs same-build start evidence; unavailable retrieval wins; `deps` and product-data operations cannot prove build start. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION` | Exact Core/adapter/common/Python/schema/log inputs and seven ordered log states remain intact. Unknown or damaged diagnostic logs never invalidate a valid primary artifact pair. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION` | Manifest resources remain inventory; unmatched resources are `NO_RESULT_RECORDED`; Lakeflow, dbt invocation, node/test, collector, and capture outcomes remain separate. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION` | Ordinal-local immutable paths, no `deps --target-path`, and closed-file size/rotation/truncation rules remain exact. The attended product data plane has no dbt ordinal or file path. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION` | Curated evidence remains allowlisted. Raw/compiled code, vars, messages, adapter messages, arbitrary metadata, raw events, environment values, and `msg` remain excluded; receipts cannot carry these fields. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION` | Genie and MCP remain optional and advisory. Neither participates in dbt command construction, authorization, capture, validation, migration, or receipt verification. |

## Exact contract verification

| Contract area | Verdict | Seventh re-review conclusion |
|---|---|---|
| Exact pins and schemas | `PASS` | Core 1.11.12, adapter 1.12.2, common 1.37.5/log version 3, manifest v12, run-results v6, Python 3.12.3, and the common wheel digest remain exact candidate inputs. |
| Reproducible environment | `PASS` | The common wheel digest is not misrepresented as a full lock; complete Python 3.12/Linux and Node hash locks remain mandatory before runtime support. |
| Resolved argv/env/flags | `PASS` | Scanner resolution covers CLI, configured current/legacy aliases, exactly one project-or-profile mapping, `DO_NOT_TRACK`, and defaults. Explicit `warn_error`, conflicting sources, non-empty CLI vars, and unclassified output/egress/path overrides fail before Apply. |
| Commands and ordinals | `PASS` | A supported observed task has build-only or deps-then-build, one approved selector, one build target root, separate ordinal log roots, and no dynamic command fragments. Tagged Core confirms `deps` has governed global flags but no selector or target-path option. |
| Warning and empty execution | `PASS` | `NoNodesForSelectionCriteria` plus `NothingToDo` are promoted, while an empty result array—including an ephemeral-only selection—is independently invalid with `DBT_EMPTY_EXECUTION`. |
| Privacy and egress | `PASS` | Both dbt ordinals explicitly disable anonymous usage and artifact-ingest upload. Field allowlisting, rather than scrubbing or human messages, is the primary evidence boundary. |
| Artifact pair | `PASS` | Exact schemas, Core version, manifest adapter type, `args.which=build`, shared non-null UUID, AttemptKey/ordinal, non-empty unique results, and exact BuildTask collection resolution are mandatory. |
| Partial and early failure | `PASS` | Manifest-only, run-results-only, neither-file, inaccessible archive, pre-logger failure, same-build start, and outer Lakeflow existence remain mutually distinguishable. Every observed outer attempt is represented. |
| Structured logs | `PASS` | `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID` remain a total ordered set per ordinal. `MainReportVersion.data.log_version` and the six-file/120-MiB bound match the pinned sources. |
| Reconciliation | `PASS` | The normal collector and bounded reconciler use the same idempotent AttemptKey path for explicitly onboarded observed attempts, including cancellation, retry, repair, and failures before dbt starts. |
| Field allowlisting | `PASS` | Ordinary tables/views exclude raw code, SQL, messages, vars, arbitrary metadata/events, environment data, and signed archive links. Restricted evidence is optional, closed, bounded, separately permissioned, and retained under policy. |
| Observed versus collector | `PASS` | Only the observed native dbt task has a canonical dbt ordinal/archive. The collector is a separate fixed Job/run-as with no dbt project data or DDL and cannot treat its own invocation as observed execution. |
| Product Jobs versus dbt | `PASS` | Collector, role-administration, and optional enrichment Jobs have fixed non-dbt tasks and distinct grants. They do not satisfy the canonical native `deps`/`build` scanner contract and remain outside the observed-Job allowlist and artifact namespace. |
| Migration data plane | `PASS` | Migration is attended Statement Execution, not a Job or dbt process. No plan, capsule, user, App, AI, or Job parameter can inject dbt commands, selectors, flags, vars, paths, artifacts, logs, or arbitrary SQL. |
| Durable receipt isolation | `PASS` | The receipt is a Delta ledger row/view with no Jobs output or dbt artifact. The collector has no ledger access; receipt fields cannot satisfy the native archive, AttemptKey/ordinal, schema, invocation, command, adapter, or result gates. |
| Optional enrichment | `PASS` | Fixed scope updates and optional system snapshots remain product operational context. They neither modify canonical artifact parsing nor become dbt invocation/node/test evidence. |
| AI-disabled path | `PASS` | Installation, observed execution, capture, investigation, retention, and removal remain complete when every optional AI capability is disabled. |

## P0-P10 dbt review matrix

These verdicts approve the planning contract and named future gate; they do not claim that later implementation evidence already exists.

| Part | Verdict | Required dbt evidence at the part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record all seventh reviews against this frozen hash and complete repository acceptance. |
| P1 — Capture library | `PASS` | Implement vendored exact schemas, standalone/pair validation, BuildTask result-ID resolution, field allowlists, hashes, and every adversarial golden artifact/log/capture fixture. |
| P2 — Collector and reconciliation | `PASS` | Prove per-ordinal closed-path bounds, quarantine, total precedence, exactly-once AttemptKey writes, and hard denial of collector, role, enrichment, migration-ledger, and every other non-onboarded product context as dbt evidence. |
| P3 — Bundle installer | `PASS` | Produce complete dependency locks and exact argv fixtures; statically prove no migration Job/receipt carrier exists; prove Statement Execution has no dbt command/file/archive surface and runtime resources cannot enter the observed namespace. |
| P4 — App read-only MVP | `PASS` | Keep Job, dbt invocation, node/test, collector, capture, migration, receipt, and optional-enrichment outcomes distinct; never display a receipt or product operation as a dbt run. |
| P5 — Job onboarding | `PASS` | Deterministically classify commands, native task structure, selectors, aliases, flags, vars, paths, privacy, and unavailable checks; reject collector/role/enrichment product Jobs and every unsupported command as observed dbt Jobs. |
| P6 — Controlled actions | `PASS` | Run only a pre-approved observed Job. No user, App, role Job, migration envelope, or AI supplies dbt command, selector, vars, path, artifact, log, or SQL input. |
| P7 — Security and operations | `PASS` | Complete field classification, evidence retention/export/delete, adversarial string, egress, receipt isolation, and lifecycle tests without broadening normalized fields. |
| P8 — Bounded live proof | `PASS` | Capture supported success/failure/partial paths; prove attended migration and receipt generations create zero dbt AttemptKey/invocation/node rows; prove every product Job is excluded; finish with no running compute. |
| P9 — Optional intelligence | `PASS` | Pass the full core suite with AI disabled; optional tools call deterministic validators over curated data only. |
| P10 — Private alpha | `PASS` | Qualify representative real projects against the exact version/command matrix without silently expanding supported commands, flags, schemas, adapters, or versions. |

## Author file-set result

| Author file | Verdict | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | Artifact-first capture and the absence of a migration Job/Jobs receipt are explicit. |
| `AGENTS.md` | `PASS` | Prohibits dynamic dbt input, unsafe evidence, collector DDL, migration Jobs, Jobs-visible receipts, floating dependencies, and AI enforcement. |
| `docs/index.md` | `PASS` | Makes no unsupported runtime claim and routes to the normative plans, decision, sources, and reviews. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Separates observed dbt execution, collection, attended migration, durable receipt, App, role, and enrichment trust paths. |
| `docs/plans/product-plan.md` | `PASS` | Preserves the exact command/artifact/log/capture contract and removes the former product Job/output collision surface. |
| `docs/plans/review-process.md` | `PASS` | Retains dbt review responsibility for all P0-P10 parts and explicitly requires that no migration input can become a dbt command. |
| `docs/plans/documentation-plan.md` | `PASS` | Plans distinct dbt command/evidence pages and requires Job, invocation, node/test, collector, capture, migration, and receipt terminology to remain separate. |
| `docs/research/source-register.md` | `PASS` | Current first-party version, source, schema, wheel, command, flag, artifact, log, and trend evidence is sufficient for P0. |

## Bounded future gates

No P0 author change is required. Before later parts claim support, they must still prove:

- P1 exact schema/parser behavior and adversarial artifact/log fixtures.
- P2/P5 hard exclusion of collector, role, enrichment, and every non-native/non-onboarded product Job from observed capture.
- P3 complete reproducible dependency locks, parser-verified argv, and static/runtime proof that no migration Job or Jobs receipt carrier has re-entered the graph.
- P8 bounded live success, failure, cancellation, repair, partial/invalid/missing evidence, attended-migration isolation, durable-receipt isolation, and stopped inventory.
- P10 representative real-project lifecycle qualification.

Any Core, adapter, common, Python, serverless environment, artifact schema, log version, command surface, adapter feature, or product execution-class change reopens qualification.

## Cloud-mutation statement

This review used repository reads, current official web documentation, first-party GitHub release/source reads, schema reads, and PyPI metadata/source reads. It did not authenticate to, query, create, start, stop, modify, or delete any Azure, Databricks, dbt Cloud, or other cloud resource. No paid compute was started.

## Final disposition

- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- Blocking or high findings: none.
- Seventh dbt specialist verdict for frozen baseline 0.8: `PASS`.
