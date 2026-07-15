# Fifth dbt Core re-review: P0 planning baseline 0.6

- Reviewed input: frozen author file set defined in `resolution.md`
- Re-review input SHA-256: `96257d1f55152d92d303852a9f057a419c0d77bdc5a553cb4d92cea0cf4b173e`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `PASS`
- Open dbt findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.6 passes the fifth dbt specialist review. The customer-owned-schema and targeted migration-plane revision does not regress the dbt capture contract:

1. Customer dbt execution remains in the observed Lakeflow Job under its existing run-as principal. The product migration Job is a separate, fixed DDL/data-contract mechanism and cannot receive or execute a dbt command, selector, flag, variable, path, artifact, log, or user/AI-supplied SQL.
2. The collector remains a separate DML-only Job. It consumes the observed task's archived evidence, validates one exact Core/adapter/common contract, and cannot create or replace product objects.
3. Optional `deps` and required `build` ordinals retain deterministic governed argv, resolved configuration, separate immutable paths, explicit telemetry/upload opt-outs, and exact evidence expectations.
4. Artifact, log, empty/partial/failure, security, reconciliation, and AI-disabled outcomes remain total and fail closed.

This verdict approves the P0 planning contract. It does not claim that the candidate runtime has passed P1 golden fixtures, P3 dependency locking, P8 live capture, or P10 customer-project qualification; those bounded gates remain mandatory.

## Immutable input verification

The reviewed author scope is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently hashed each scoped file and then hashed the sorted digest list:

```text
96257d1f55152d92d303852a9f057a419c0d77bdc5a553cb4d92cea0cf4b173e
```

Review reports and `resolution.md` are outside that author-input digest. I changed no author-owned file and performed no Azure, Databricks, dbt Cloud, or other remote mutation.

## Method and current primary sources

The review traced each P0-P10 dbt responsibility from product boundary through invocation, collection, persistence, UI semantics, security, tests, documentation, optional intelligence, and private-alpha gates. Current official documentation, exact tagged source, release metadata, schemas, and package metadata were refreshed on 2026-07-15.

Primary evidence checked:

- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) and [Python/dependency metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml)
- [`dbt-databricks` 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) and [exact dependency constraints](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml)
- [Core command decorators](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/main.py), [option and environment aliases](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py), [resolved flag behavior](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py), and [project/profile flag loading](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/config/project.py)
- [dbt build](https://docs.getdbt.com/reference/commands/build), [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings), [JSON artifact paths](https://docs.getdbt.com/reference/global-configs/json-artifacts), [logs](https://docs.getdbt.com/reference/global-configs/logs), and [usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats)
- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), and [run results](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [manifest v12 schema](https://schemas.getdbt.com/dbt/manifest/v12.json), [run-results v6 schema](https://schemas.getdbt.com/dbt/run-results/v6.json), and [Core 1.11.12 BuildTask collections](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py)
- [`MainReportVersion` emission](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py) and [`dbt-common` 1.37.5 wheel metadata](https://pypi.org/project/dbt-common/1.37.5/)

The refreshed release state supports the selected conservative baseline: Core 1.11.12 and adapter 1.12.2 are the current stable releases, while Core 1.12.0rc3 and Core 2.0 builds remain prerelease. Adapter 1.12.2 explicitly permits Core `>=1.11.2,<1.11.13` and common `>=1.37.0,<1.38.0`; the exact selected pins fit those bounds. The newer adapter kernel backend and Core 1.12/2.0 command changes are not silently adopted and require separate qualification.

Read-only checks also corroborated that:

- `deps` accepts the governed global warning, logging, usage, artifact-upload, and JSON flags but not selector or target-path options.
- `build` accepts the one approved selector and ordinal-specific target path.
- The selected `dbt-common` wheel digest is `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077` and declares log version `3`.
- Run-results v6 has no adapter-type field, while manifest v12 has `metadata.adapter_type`; the plan correctly obtains the adapter version from trusted locked runtime evidence rather than an artifact assertion.

## Ranked findings

| Rank | Result |
|---|---|
| Blocker | None |
| High | None |
| Medium | None |
| Low | None |

No new dbt finding was opened. Future implementation evidence already assigned to P1-P10 is not reclassified as a P0 defect.

## Prior dbt finding dispositions

| Finding | Fifth re-review disposition | Baseline 0.6 evidence and conclusion |
|---|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION` | Both zero-selection warnings are promoted; a no-match, filtered-to-nothing, ephemeral-only, or otherwise empty result set cannot become observable. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION` | Only optional `deps` followed by one named-selector `build` is ready. Project/profile and current/legacy alias conflicts are deterministic; both ordinals explicitly disable anonymous usage and artifact upload; no dynamic command, selector, flag, CLI vars, or path enters from App, Job parameters, or AI. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION` | Standalone validation precedes pair validation. Manifest-only may be `PARTIAL`; run-results-only is invalid; neither-file uses same-build start evidence; unavailable retrieval wins; `deps` cannot prove `build` start. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION` | Core, adapter, common, Python, environment, schemas, wheel digest, and log version are exact candidate inputs. The seven ordered log states are total, and damaged diagnostics do not invalidate an otherwise valid artifact pair. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION` | Manifest resources remain inventory. Unmatched resources are `NO_RESULT_RECORDED`; Lakeflow, invocation, node/test, collector, and capture outcomes remain distinct. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION` | Every command ordinal has a task-local immutable log path; `build` has its own target path; `deps` is never given target-path; closed-file rotation and size caps have explicit truncation states. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION` | Curated persistence is field-allowlisted. Raw/compiled code, vars, arbitrary metadata, messages, adapter messages, raw events, environment values, and `msg` stay outside ordinary views; scrubbing is defense in depth only. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION` | Genie and MCP remain optional advisory surfaces. Neither constructs commands nor participates in authorization, capture, validation, state precedence, or support qualification. |

## Exact contract verification

| Contract area | Verdict | Fifth re-review conclusion |
|---|---|---|
| Core/adapter/common pins | `PASS` | `dbt-core==1.11.12`, `dbt-databricks==1.12.2`, and `dbt-common==1.37.5` are exact, mutually compatible candidate pins; Python 3.12.3 is within the declared 3.10-3.13 intersection. |
| Reproducibility boundary | `PASS` | The common wheel hash is exact and is not misrepresented as the whole environment lock. Full Python 3.12/Linux and Node hash locks remain a P3 release gate. |
| Governed configuration | `PASS` | The scanner resolves CLI, configured current/legacy environment aliases, one allowed project-or-profile mapping, `DO_NOT_TRACK`, and defaults. Ambiguous project/profile or alias ownership fails deterministically before mutation. |
| Command ordinals | `PASS` | Only build-only or deps-then-build is supported. Each ordinal is separately identified, logged, capped, correlated, and tested; a deps event cannot stand in for primary-build evidence. |
| Dynamic-input exclusion | `PASS` | Users and models cannot supply a command fragment, selector, flag, vars, target/log path, Git reference, or compute setting. Controlled actions run an already approved observed Job rather than constructing dbt input. |
| Warning and empty semantics | `PASS` | `NoNodesForSelectionCriteria` and `NothingToDo` are promoted without enabling all future warnings. Empty execution fails with a stable capture-contract code. |
| Privacy and egress flags | `PASS` | Both ordinals explicitly use `--no-send-anonymous-usage-stats` and `--no-upload-to-artifacts-ingest-api`; conflicting sources are rejected. |
| Artifact pair | `PASS` | Exact v12/v6 schemas, Core version, manifest adapter type, build command, non-null shared invocation UUID, AttemptKey/ordinal, unique non-empty results, and exact BuildTask collection resolution are required. |
| Partial and early failure | `PASS` | Manifest-only, invalid run-results-only, neither-file with/without build start, unavailable archive, pre-logger failure, and outer Lakeflow-only outcomes have exclusive conservative states. |
| Structured logs | `PASS` | `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID` are ordered; unknown/damaged JSONL is quarantined and never parsed through human `msg`. |
| Reconciliation | `PASS` | Every outer attempt persists once through the same idempotent AttemptKey path, including pre-dbt failures and cancellation paths missed by `ALL_DONE`. |
| Regulated persistence | `PASS` | Ordinary views expose allowlisted operational facts only. Restricted closed diagnostics are optional, bounded, separately permissioned, and retained under policy. |
| Schema-migration separation | `PASS` | The migration Job receives only a migration ID and digest and renders fixed product data operations. It cannot execute customer dbt, inspect dbt project data, parse artifacts, or accept App/user/AI SQL. The collector has no DDL. |
| Optional enrichment separation | `PASS` | System snapshots remain optional operational context and do not replace or alter canonical dbt artifact parsing or capture precedence. |
| AI-disabled operation | `PASS` | The entire required install, execution, capture, investigation, and lifecycle contract remains valid with every AI feature disabled. |

## P0-P10 dbt review matrix

The verdicts below assess whether each part has a sufficient dbt contract and future acceptance gate; they do not claim later implementation evidence already exists.

| Part | Verdict | Required dbt evidence at its gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record this review with the other independent verdicts and complete the repository acceptance gate. |
| P1 — Capture library | `PASS` | Implement vendored exact schemas, standalone/pair validation, result-ID resolution, field allowlists, hashing, and every golden artifact/log/capture fixture. |
| P2 — Collector and reconciliation | `PASS` | Prove closed-path/size/rotation bounds, per-ordinal logs, quarantine, total precedence, idempotent AttemptKey writes, retries, repairs, and pre-dbt outer attempts. |
| P3 — Bundle installer | `PASS` | Produce full hash locks and exact build-only/deps-plus-build argv fixtures; prove scanner conflict/path/privacy/egress denials before mutation. Keep the migration Job separate from dbt execution. |
| P4 — App read-only MVP | `PASS` | Views and UI must preserve Job, invocation, node/test, collector, and capture distinctions without exposing raw fields; system enrichment must remain non-canonical and optional. |
| P5 — Job onboarding | `PASS` | Scanner/source-patch fixtures must deterministically classify commands, selector, aliases, flags, vars, paths, privacy, unavailable checks, and semantic changes. |
| P6 — Controlled actions | `PASS` | Run only a pre-approved observed Job. No user or AI can supply dbt or migration SQL/command input; the immutable summary binds the approved selector and Job. |
| P7 — Security and operations | `PASS` | Complete field-classification, restricted-evidence, retention/export/delete, adversarial string, dependency, and egress tests. |
| P8 — Bounded live proof | `PASS` | Within the approved cost window, capture a real supported build plus early failure, warning, test failure/skip, cancellation, timeout, retry/repair, malformed/missing evidence, and final stopped inventory. |
| P9 — Optional intelligence | `PASS` | Run the entire core suite with AI disabled; any Genie/MCP path may only call the deterministic validator over curated data. |
| P10 — Private alpha | `PASS` | Qualify real projects against the exact version/command matrix through repeatable install, upgrade, observation, and uninstall without silently expanding support. |

## File-set result

| Author file | Verdict | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | Correctly presents artifact-first, customer-local, deterministic evidence and the collector/migration split. |
| `AGENTS.md` | `PASS` | Prohibits dynamic dbt input, active Volume logging, unsafe fields, floating dependencies, collector DDL, and AI enforcement. |
| `docs/index.md` | `PASS` | Routes to the normative plan, ADR, research, and review records without making a runtime claim. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Keeps observed dbt execution, fixed migration, collection, App query, and optional enrichment as separate trust paths. |
| `docs/plans/product-plan.md` | `PASS` | Defines exact candidate pins, deterministic invocation/evidence contracts, total failure states, security boundaries, and P0-P10 gates. |
| `docs/plans/review-process.md` | `PASS` | Gives the dbt reviewer explicit responsibility for all parts and blocks completion on a required change. |
| `docs/plans/documentation-plan.md` | `PASS` | Provides dedicated command, flag, path, artifact, log, capture-state, recovery, support, and optionality documentation routes. |
| `docs/research/source-register.md` | `PASS` | Records current first-party docs, tagged source, release, schema, wheel, and trend evidence with refresh triggers. |

## Bounded future gates

No P0 change is required, but later parts must not claim support before all of these existing gates pass:

- P1: exact schema/parser and adversarial golden fixtures.
- P3: complete reproducible dependency locks and parser-verified exact command templates.
- P8: bounded real capture across success, partial, invalid, missing, cancellation, timeout, retry, repair, and Python-model failure, followed by stopped/clean inventory.
- P10: representative non-author projects and exact-pair lifecycle qualification.

Any Core, adapter, `dbt-common`, Python, serverless environment, artifact schema, log version, command surface, or adapter feature change reopens qualification.

## Final disposition

- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- Blocking or high findings: none.
- Fifth dbt specialist verdict for frozen baseline 0.6: `PASS`.
