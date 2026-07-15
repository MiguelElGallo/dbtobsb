# Sixth dbt Core re-review: P0 planning baseline 0.7

- Reviewed input: frozen author file set defined in `resolution.md`
- Re-review input SHA-256: `85eab368552b9614eba555dd8f44feb1b8850d0eb66cdcc250cf98d6a502c893`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `PASS`
- Open dbt findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.7 passes the sixth dbt specialist review. The revised attended installer and post-seal receipt flow do not weaken or blur the dbt evidence contract.

The three Job classes remain distinct:

1. The **observed customer Job** is the only dbt execution surface. Its immutable, version-controlled native dbt task may run optional `deps` followed by exactly one supported `build`; its task attempt owns the dbt command ordinals, invocation ID, archive, artifacts, and logs.
2. The **collector Job** is a separate DML-only consumer with `CAN_VIEW` only on explicitly onboarded observed Jobs. It validates archived dbt evidence and writes the three normalized evidence tables; it cannot run dbt, read project data, perform DDL, or read the migration ledger.
3. The **product schema-migration Job** is a fixed installer resource. Its only parameters are a nonsecret `migration_id` and approved digest. Signed code renders fixed product data-contract operations; it accepts no dbt command, selector, vars, path, artifact, log, user/AI SQL, or plan-supplied SQL.

After the temporary DDL lease is revoked and complete effective absence is proved, the same migration Job may be invoked idempotently with the same two bound parameters only to publish a Databricks-anchored terminal seal receipt. That receipt invocation has no lease, performs no DDL, is not an onboarded dbt Job, produces no supported dbt ordinal or artifact pair, and cannot create dbt node evidence. The collector's Job allowlist, native-task scanner, AttemptKey/ordinal correlation, and exact artifact contract prevent the receipt run from being normalized as customer dbt execution.

This is approval of the P0 planning contract, not a claim that P1 golden captures, P3 reproducible locks and policy tests, P8 live proof, or P10 real-project qualification already exist.

## Immutable input verification

The author scope is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently hashed each file and then hashed the sorted digest list:

```text
85eab368552b9614eba555dd8f44feb1b8850d0eb66cdcc250cf98d6a502c893
```

Review reports and `resolution.md` are outside that digest. I changed no author-owned file and performed no Azure, Databricks, dbt Cloud, or other cloud mutation.

## Method and primary sources

The review traced every P0-P10 dbt responsibility across the product boundary, identity model, installer chronology, invocation resolution, collection, normalization, UI semantics, security, tests, documentation, optional intelligence, and private-alpha gates. It used the current first-party sources already refreshed and registered on 2026-07-15:

- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) and [Python/dependency metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml)
- [`dbt-databricks` 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) and [exact dependency constraints](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml)
- [Core command decorators](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/main.py), [option/environment aliases](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py), [resolved flags](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py), and [project/profile flag loading](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/config/project.py)
- [dbt build](https://docs.getdbt.com/reference/commands/build), [warnings](https://docs.getdbt.com/reference/global-configs/warnings), [JSON artifact paths](https://docs.getdbt.com/reference/global-configs/json-artifacts), [logs](https://docs.getdbt.com/reference/global-configs/logs), and [usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats)
- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), and [run results](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [manifest v12 schema](https://schemas.getdbt.com/dbt/manifest/v12.json), [run-results v6 schema](https://schemas.getdbt.com/dbt/run-results/v6.json), and [Core 1.11.12 BuildTask collections](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py)
- [`MainReportVersion` emission](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py) and [`dbt-common` 1.37.5](https://pypi.org/project/dbt-common/1.37.5/)

The exact candidate remains coherent: `dbt-core==1.11.12`, `dbt-databricks==1.12.2`, and `dbt-common==1.37.5`; adapter 1.12.2 permits Core `>=1.11.2,<1.11.13` and common `>=1.37.0,<1.38.0`. Python 3.12.3 is inside the declared 3.10-3.13 intersection. Core 1.12 and 2.0 remain outside the MVP support matrix until separately qualified.

## Ranked findings

| Rank | Result |
|---|---|
| Blocker | None |
| High | None |
| Medium | None |
| Low | None |

No new dbt finding was opened. The additional installer handoff, complete-authority seal, anchored receipt, system-enrichment scope table, and actor-return changes stay outside canonical dbt command construction and evidence parsing.

## Prior dbt finding dispositions

| Finding | Sixth re-review disposition | Baseline 0.7 conclusion |
|---|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION` | Both zero-selection warnings are promoted; no-match, filtered-to-nothing, ephemeral-only, and other empty result paths cannot become observable. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION` | Only optional `deps` then one named-selector `build` is ready. Project/profile and current/legacy alias conflicts are deterministic; both ordinals disable usage and artifact upload; no dynamic command, flag, selector, vars, or path enters from App, Job parameters, AI, capsules, or migration receipts. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION` | Standalone validation precedes pair validation. Manifest-only may be `PARTIAL`; run-results-only is invalid; neither-file depends on same-build start evidence; unavailable retrieval wins; `deps` and migration receipt runs cannot prove build start. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION` | Exact Core/adapter/common/Python/schema/log inputs and ordered log states remain intact; unknown or damaged diagnostics never invalidate a valid primary artifact pair. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION` | Manifest resources remain inventory; unmatched resources are `NO_RESULT_RECORDED`; Lakeflow, dbt invocation, node/test, collector, and capture states remain separate. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION` | Ordinal-local immutable paths, no `deps --target-path`, and closed-file size/rotation/truncation rules remain unchanged. Product migration/receipt Jobs have no dbt ordinal path. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION` | Curated fields remain allowlisted; raw/compiled code, vars, arbitrary metadata, messages, adapter messages, raw events, environment values, and `msg` remain excluded. Capsules and receipts also cannot carry artifacts/logs/SQL. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION` | Genie and MCP stay optional and advisory; neither participates in command construction, authorization, migration, capture, validation, or state precedence. |

## Exact contract verification

| Contract area | Verdict | Sixth re-review conclusion |
|---|---|---|
| Exact pins and schemas | `PASS` | Core 1.11.12, adapter 1.12.2, common 1.37.5/log version 3, manifest v12, run-results v6, Python 3.12.3, and the common wheel digest remain exact candidate inputs. |
| Reproducible environment | `PASS` | The common wheel pin is not presented as the full lock; complete Python 3.12/Linux and Node hash locks remain mandatory before support. |
| Resolved argv/env/flags | `PASS` | Scanner resolution covers CLI, current/legacy environment aliases, one project-or-profile mapping, `DO_NOT_TRACK`, and defaults. Conflicts fail before Apply. |
| Command ordinals and paths | `PASS` | Supported observed Jobs have either build-only or deps-then-build, separate ordinal log roots, one build target root, fixed selector, capped rotation, and no dynamic input. |
| Privacy and egress | `PASS` | Both dbt ordinals explicitly disable anonymous usage and artifact-ingest upload; field allowlisting, not scrubbing, is the primary evidence boundary. |
| Artifact pair | `PASS` | Exact schemas, Core version, manifest adapter type, `args.which=build`, shared non-null invocation UUID, AttemptKey/ordinal, non-empty unique results, and exact BuildTask collection resolution are mandatory. |
| Empty/partial/failure states | `PASS` | Archive retrieval and capture precedence are exclusive and conservative across unavailable, invalid, complete, partial, and not-produced outcomes; every outer observed attempt remains represented. |
| Structured logs | `PASS` | The seven ordered log states remain total; damaged or unknown JSONL is quarantined and never parsed through human `msg`. |
| Reconciliation | `PASS` | The collector/reconciler uses the same idempotent AttemptKey path for explicitly onboarded observed attempts, including cancellation and pre-dbt failure. |
| Field allowlisting | `PASS` | Ordinary tables/views exclude raw SQL/code/messages/vars/events/environment data; restricted closed evidence remains optional, bounded, separately permissioned, and retained under policy. |
| Migration versus dbt execution | `PASS` | Migration accepts only ID+digest and fixed signed operations. It cannot run customer dbt, access project data, accept arbitrary SQL, or produce a supported dbt artifact pair. |
| Post-seal receipt isolation | `PASS` | The second fixed migration invocation is receipt-only after verified lease removal, uses the same bound ID+digest, performs no DDL, and is outside the observed-Job allowlist and dbt AttemptKey/ordinal namespace. |
| Optional enrichment | `PASS` | Scope-table updates and system snapshots are fixed product DML/operational context; they neither modify canonical artifact parsing nor become dbt node evidence. |
| AI-disabled path | `PASS` | Installation, observed execution, capture, investigation, retention, and removal remain complete when all AI capabilities are disabled. |

## P0-P10 dbt review matrix

These verdicts assess the planning contract and named future gate; they do not claim later implementation evidence already exists.

| Part | Verdict | Required dbt evidence at the part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record all sixth reviews against the frozen hash and complete repository acceptance. |
| P1 — Capture library | `PASS` | Implement vendored exact schemas, standalone/pair validation, result-ID resolution, field allowlists, hashes, and all adversarial golden artifact/log/capture fixtures. |
| P2 — Collector and reconciliation | `PASS` | Prove per-ordinal closed-path bounds, quarantine, total precedence, exactly-once AttemptKey writes, and denial of every non-onboarded product Job, including migration receipt runs. |
| P3 — Bundle installer | `PASS` | Produce full dependency locks and exact command fixtures; prove the migration Job receives only ID+digest, its post-seal replay is receipt-only/no-DDL, and neither run can enter observed dbt capture. |
| P4 — App read-only MVP | `PASS` | Preserve Job/invocation/node/test/collector/capture distinctions without raw fields; never display migration or enrichment receipts as dbt runs. |
| P5 — Job onboarding | `PASS` | Deterministically classify commands, tasks, selectors, aliases, flags, vars, paths, privacy, and unavailable checks; reject fixed product Jobs as observed dbt Jobs. |
| P6 — Controlled actions | `PASS` | Run only a pre-approved observed Job; no user or AI supplies dbt or migration command/SQL input. |
| P7 — Security and operations | `PASS` | Complete field classification, evidence retention/export/delete, adversarial strings, egress, receipt isolation, and lifecycle tests. |
| P8 — Bounded live proof | `PASS` | Capture supported success/failure/partial paths and prove migration plus receipt runs create no dbt AttemptKey/node evidence; finish with no running compute. |
| P9 — Optional intelligence | `PASS` | Pass the full core suite with AI disabled; optional tools call only deterministic validators over curated data. |
| P10 — Private alpha | `PASS` | Qualify representative real projects against the exact version/command matrix without silently expanding supported commands, flags, or versions. |

## File-set result

| Author file | Verdict | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | Artifact-first capture and the migration/collector/observed-Job boundaries remain clear. |
| `AGENTS.md` | `PASS` | Prohibits dynamic dbt input, unsafe evidence, collector DDL, plan/user SQL, floating dependencies, and AI enforcement. |
| `docs/index.md` | `PASS` | Makes no unsupported runtime claim and routes to normative plans and reviews. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Keeps observed dbt execution, fixed migration/receipt, collection, App, and enrichment as separate trust paths. |
| `docs/plans/product-plan.md` | `PASS` | Exact capture semantics remain unchanged and the new receipt invocation is fixed, post-seal, no-DDL, and non-dbt. |
| `docs/plans/review-process.md` | `PASS` | Retains dbt review responsibility across every P0-P10 part and blocks unresolved required changes. |
| `docs/plans/documentation-plan.md` | `PASS` | Provides distinct dbt command/evidence documentation and prevents migration receipts from being taught as dbt runs. |
| `docs/research/source-register.md` | `PASS` | Current first-party version, source, schema, wheel, artifact, flag, and trend evidence remains sufficient. |

## Bounded future gates

No P0 author change is required. Before later parts claim support they must still prove:

- P1 exact schema/parser and adversarial artifact/log fixtures.
- P2/P3 hard exclusion of all product Jobs from observed-db capture, plus no-DDL/idempotent post-seal receipt behavior.
- P3 complete reproducible dependency locks and parser-verified command templates.
- P8 bounded live success, failure, cancellation, repair, partial/invalid/missing evidence, and migration-receipt isolation with stopped inventory.
- P10 representative real-project lifecycle qualification.

Any Core, adapter, common, Python, serverless environment, artifact schema, log version, command surface, or adapter feature change reopens qualification.

## Final disposition

- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- Blocking or high findings: none.
- Sixth dbt specialist verdict for frozen baseline 0.7: `PASS`.
