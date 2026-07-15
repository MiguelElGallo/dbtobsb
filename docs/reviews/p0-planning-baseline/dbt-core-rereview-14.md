# Fourteenth dbt Core re-review: P0 planning baseline 0.16

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `3d463e4e578ac5c24b0f0723b9830448559494f765713ac3caba4c5d4f480b9a`
- Separate evidence input: `docs/evidence/p0-live-smoke-2026-07-15.md`
- Separate evidence SHA-256: `9d46184b907c15038ecec919a4707075ad59404a035bc7628b4be5166e747326`
- Date: 2026-07-15
- Reviewer: independent dbt Core and dbt-databricks product/security specialist
- Verdict: `PASS`
- Open dbt P0 findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.16 passes the fourteenth independent dbt Core and dbt-databricks review. It retains every resolved dbt contract from the prior accepted baseline: the exact candidate toolchain, closed command and flag surface, zero-execution defenses, exact artifact pair, ordered structured-log and capture states, native AttemptKey correlation, immutable observation-time trust provenance, strict data allowlist, control-to-dbt isolation, and deterministic behavior with optional AI disabled.

The new P0 implementation and its separate live-smoke record do not overclaim that any of those later dbt capabilities exist. They prove only that a packaged FastAPI process can run as a private Databricks App, serve the reviewed `/api/health` contract, and emit its own App stdout event. The response says `readiness: not_evaluated`; both the README and evidence explicitly say that the smoke does not run dbt, capture artifacts, read product data, or prove product readiness. The smoke creates no dbt Job and uses no App resource binding. The App `health_check` event is therefore not a dbt structured event and cannot satisfy any build-start, invocation, log-version, artifact, capture, or result predicate.

This is approval of the frozen planning contract and the accuracy of the stated P0 dbt boundary. It is not implementation evidence for the P1 parser, P2 collector, P3 generated dbt Job, P4 observability UI, P6 controlled start, P8 native archive qualification, or P10 representative-project matrix.

## Immutable input verification and scope

I reproduced the requested sorted path-plus-content digest with this exact eight-file scope:

```sh
{
  printf '%s\n' README.md AGENTS.md docs/index.md
  rg --files docs/decisions docs/plans docs/research -g '*.md'
} | LC_ALL=C sort -u > /tmp/dbtobsb-baseline-016-files.txt

while IFS= read -r file; do
  shasum -a 256 "$file"
done < /tmp/dbtobsb-baseline-016-files.txt | shasum -a 256
```

The result before review was:

```text
3d463e4e578ac5c24b0f0723b9830448559494f765713ac3caba4c5d4f480b9a  -
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

The P0 evidence file is intentionally outside that aggregate. I verified it independently:

```sh
shasum -a 256 docs/evidence/p0-live-smoke-2026-07-15.md
```

```text
9d46184b907c15038ecec919a4707075ad59404a035bc7628b4be5166e747326  docs/evidence/p0-live-smoke-2026-07-15.md
```

I read all eight author files and the complete separate evidence record. I edited no author, evidence, or implementation file; this report is the only file written by this review.

## Current primary evidence checked

The following official evidence was refreshed on 2026-07-15:

- [dbt Core 1.11.12](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) remains the latest non-prerelease Core release. Core 1.12.0rc3 and 2.0.0-alpha.4 remain prereleases and are correctly outside the support matrix.
- [dbt-databricks 1.12.2](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) remains the latest stable adapter release. Its [published package metadata](https://pypi.org/project/dbt-databricks/1.12.2/) requires `dbt-core>=1.11.2,<1.11.13` and `dbt-common>=1.37.0,<1.38.0`; the exact baseline pins are inside both bounds.
- [dbt-core 1.11.12 package metadata](https://pypi.org/project/dbt-core/1.11.12/) requires Python 3.10 or newer and `dbt-common>=1.37.3,<2.0`; Python 3.12.3 and `dbt-common==1.37.5` remain coherent candidate pins.
- The official [dbt-common 1.37.5 distribution](https://pypi.org/project/dbt-common/1.37.5/) publishes `dbt_common-1.37.5-py3-none-any.whl` with SHA-256 `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077`. I downloaded and re-hashed the wheel. It contains `LOG_VERSION = 3` and configures five rotating backups, matching the baseline's active-file-plus-five-backups bound.
- Official [artifact](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), and [run-results](https://docs.getdbt.com/reference/artifacts/run-results-json) documentation continues to distinguish the complete parsed project inventory from only the nodes executed by an invocation.
- The published [manifest v12](https://schemas.getdbt.com/dbt/manifest/v12.json) and [run-results v6](https://schemas.getdbt.com/dbt/run-results/v6.json) schemas remain the exact supported pair. Manifest metadata exposes adapter type; run-results metadata does not, so the plan correctly avoids inventing a run-results adapter field.
- Official [`dbt build` documentation](https://docs.getdbt.com/reference/commands/build) confirms that one build writes one manifest and one combined run-results artifact for selected models, tests, snapshots, seeds, and functions.
- Official [events and logs documentation](https://docs.getdbt.com/reference/events-logging) continues to define `info` plus `data`, invocation ID, event name, and log version, and explicitly says human `msg` is not intended for machine consumption. The plan correctly uses structured data rather than message parsing.
- Official [warning configuration](https://docs.getdbt.com/reference/global-configs/warnings) continues to support event-name targeting, identifies `NoNodesForSelectionCriteria`, and makes `WARN_ERROR` and `WARN_ERROR_OPTIONS` mutually exclusive. The pinned Core source also retains `NothingToDo`; the independent non-empty-results postcondition remains necessary.

## Baseline 0.16 resolved-contract regression

| Contract | Verdict | Conclusion |
|---|---|---|
| Candidate runtime | `PASS` | `dbt-databricks==1.12.2`, `dbt-core==1.11.12`, `dbt-common==1.37.5`, Python 3.12.3, structured-log version 3, and the exact common-wheel digest remain explicit candidate pins. Support is withheld until locks, fixtures, and staging pass. |
| Command surface | `PASS` | The only supported observed sequence is optional `dbt deps` followed by exactly one selector-scoped `dbt build`. Arbitrary commands, selector text, vars, paths, and workload overrides remain prohibited. |
| Zero execution | `PASS` | Both `NoNodesForSelectionCriteria` and `NothingToDo` are promoted. Any empty `run_results.results`, including an ephemeral-only edge case, fails with `DBT_EMPTY_EXECUTION`; it never becomes observable. |
| Resolved flags | `PASS` | The scanner evaluates CLI, environment, project, profile, aliases, conflicts, defaults, privacy, JSON/log, and artifact-upload settings. It rejects explicit `warn_error` even when false and does not pretend that simultaneous non-empty project/profile flag sources form a precedence chain. |
| Command-local paths | `PASS` | `deps` has no selector or target path. `build` owns the unique AttemptKey/ordinal target path, and each command has its own task-local log path. No control value enters either. |
| Primary artifact pair | `PASS` | Exactly manifest v12 plus run-results v6 is supported. Both must have matching parseable non-null invocation UUIDs, exact Core version, trusted ordinal context, `args.which=build`, manifest adapter type `databricks`, and non-empty unique results. |
| Result resolution | `PASS` | Each result ID resolves exactly once through the supported Core 1.11 BuildTask collections: nodes, unit tests, saved queries, exposures, or functions. Manifest inventory remains distinct from executed results. |
| Structured logs | `PASS` | Per ordinal, the ordered states remain `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID`. Human `msg` is excluded, and a `deps` event cannot prove build start. |
| Capture precedence | `PASS` | The total order remains `ARCHIVE_UNAVAILABLE`, `INVALID_CAPTURE_CONTRACT`, `COMPLETE`, `PARTIAL`, and `NOT_PRODUCED`. The outer Lakeflow attempt is always retained; no trust, App, fence, or action state can rewrite capture. |
| Attempt identity | `PASS` | AttemptKey derives only from native workspace/Job/run/repair/task-run/execution coordinates. Collector-observed trust and P6 action/fence/token values remain excluded. |
| Collector trust | `PASS` | The first successful root write freezes the observation-time tuple. Same-AttemptKey reconciliation reuses it; a new native retry/repair/execution receives a new AttemptKey. The tuple cannot affect hashes, pair validity, capture, or native outcomes. |
| Data minimization | `PASS` | Raw/compiled SQL, vars, messages, arbitrary metadata/events, and sensitive custom environment values remain outside normal tables. Only opaque nonsensitive custom environment identifiers are admissible. |
| Control isolation | `PASS` | Deployment, trust, migration, action, fence, actor, user, generation, and idempotency-token values remain outside dbt argv, environment, selector, vars, paths, artifacts, events, AttemptKey, and results. Run Now carries no workload parameters. |
| Canonicalization boundary | `PASS` | Decimal-string canonicalization remains confined to typed product-control JSON and cannot transform native artifact or event JSON or their hashes. |
| Optional intelligence | `PASS` | Genie, MCP, and LLM assistance remain optional and outside execution, capture, validation, trust promotion, and action authorization. |

## P0 live-smoke dbt boundary assessment

| Evidence statement | Verdict | dbt interpretation |
|---|---|---|
| Scope is one private Databricks App process-liveness smoke | `PASS` | The evidence never labels this as a dbt invocation or observability-product proof. |
| Health response includes `check: process_liveness` and `readiness: not_evaluated` | `PASS` | These values accurately prevent process liveness from being presented as dependency, data, artifact, collector, or product readiness. |
| One App stdout `health_check` event was observed | `PASS` | This is an application event only. It is not a dbt event envelope and cannot satisfy `MainReportVersion`, invocation correlation, same-build start, log state, capture, or result rules. |
| Zero App resource bindings | `PASS` | The smoke cannot read the future Unity Catalog observability tables or impersonate a working collector. |
| Zero warehouses and clusters before and after | `PASS` | No SQL/dbt execution compute was created for this test. The evidence correctly stops at App liveness. |
| README says the wrapper creates no dbt Job | `PASS` | No scheduler, observed task, dbt argv, selector, target/log directory, archive, manifest, or run-results file was exercised. |
| Evidence explicitly denies dbt execution, artifact capture, product-data access, dependency readiness, and product readiness | `PASS` | The disclaimer exactly matches what the observations can prove. |
| App object remains `STOPPED` with no non-stopped Apps | `PASS` | The cost/cleanup conclusion is bounded to the reported App lifecycle and makes no dbt assertion. |

The evidence record is sanitized and reproducible by reference to the README. This review checked its dbt boundary accuracy; it did not independently rerun the live smoke and does not broaden the record's stated proof.

## Explicit non-contamination review

| dbt boundary | Fourteenth-review result |
|---|---|
| App process and OpenAPI | `PASS` — P0 code/lifecycle proves packaging and HTTP process liveness only. It supplies no dbt command, artifact, log, capture, or result input. |
| App stdout | `PASS` — the App `health_check` event is never admitted into the dbt structured-log parser or treated as build-start evidence. |
| Command and argv | `PASS` — optional governed `deps` plus one governed `build` remains the only future path. P0 has no dbt argv. |
| Selector, vars, and parameters | `PASS` — selectors are version controlled, vars are empty, and controlled Run Now has no workload parameters or task override. P0 supplies none. |
| AttemptKey | `PASS` — only native Lakeflow coordinates can define it. App deployment/run state, health requests, stdout, trust, and control values cannot. |
| Artifact bytes and hashes | `PASS` — only native allowlisted manifest-v12/run-results-v6 files can become primary candidates. P0 produces neither. |
| Structured-log state | `PASS` — only the locked dbt JSON event/log contract can satisfy the seven-state parser. Generic App JSON is outside the domain. |
| Capture and outcomes | `PASS` — a valid primary pair or allowlisted same-build dbt start signal is required. App liveness can create no Lakeflow/dbt/node/test/capture outcome. |
| Sensitive fields | `PASS` — the normal allowlist remains narrow, and the sanitized P0 record adds no raw customer log, identity, host, token, SQL, or dbt payload. |

## Prior finding disposition

No new numbered dbt finding is opened.

| Prior finding | Fourteenth re-review disposition |
|---|---|
| `DBT-P0-001` | `RESOLVED — NO REGRESSION`; two named zero-execution warnings plus the non-empty-results invariant prevent false observability. |
| `DBT-P0-002` | `RESOLVED — NO REGRESSION`; the command matrix, per-command flags, source/alias conflict checks, privacy controls, selector boundary, and control-input prohibition remain exact. |
| `DBT-P0-003` | `RESOLVED — NO REGRESSION`; standalone/pair validation and total retrieval/capture precedence remain deterministic. App health cannot become a primary artifact or start signal. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION`; exact Core/adapter/common/Python/schema/wheel/log-version qualification remains coherent and explicitly candidate-only. |
| `DBT-P0-005` | `RESOLVED — NO REGRESSION`; project inventory, executed results, native Lakeflow state, collector state, capture state, App lifecycle, and current/observed trust remain separate. |
| `DBT-P0-006` | `RESOLVED — NO REGRESSION`; ordinal-local paths, bounded log rotation, pre-logger states, and closed-file rules remain exact. The P0 App event is not a dbt log file. |
| `DBT-P0-007` | `RESOLVED — NO REGRESSION`; allowlisting remains primary and secret scrubbing remains defense in depth. The sanitized smoke does not widen the product data contract. |
| `DBT-P0-008` | `RESOLVED — NO REGRESSION`; Genie/MCP/LLM features remain optional and outside dbt execution, capture, validation, action authorization, and trust promotion. |

## Mandatory later-part evidence

These are acceptance gates for later implementation, not open P0 planning defects:

1. P1 must implement vendored exact schemas, native-byte hashing, pair/result/log validation, exhaustive state precedence, and adversarial fixtures without re-canonicalizing dbt JSON.
2. P2 must prove one immutable root/tuple per native AttemptKey, same-root re-entry versus new native attempts, trust read/commit races, exact DML authority, and no control-to-dbt evidence promotion.
3. P3 must produce the complete hash-locked runtime and exact generated argv fixtures, including separate `deps` and `build` templates, resolved alias/config scanning, and no arbitrary user input.
4. P3/P8 must run the pinned dbt pair on bounded Databricks compute and collect real success, failure, empty, partial, early-failure, cancellation, retry, repair, and malformed/missing archive cases.
5. P4 must display Lakeflow, dbt invocation, node/test, collector, capture, collector-observed trust, and current trust as separate outcomes. Process liveness must remain separately labeled.
6. P6 must capture the exact Run Now request and prove that its only dynamic API value is the deterministic idempotency token, with no dbt parameter or task override.
7. P7 must prove field classification, diagnostics, retention/export/delete, zero runtime egress, and native dbt JSON preservation.
8. P10 must qualify representative projects before admitting Core 1.12/2.0, additional adapter features, new statuses/artifacts, or any unsupported command.

## Author-file outcome

| Author file or set | Outcome | dbt conclusion |
|---|---|---|
| `README.md` | `PASS` | It labels P0 as FastAPI process liveness and explicitly denies dbt execution, artifact ingestion, product-data access, and readiness. It also says no dbt Job is created. |
| `AGENTS.md` | `PASS` | It preserves fixed runtime pins, closed execution, artifact-first validation, AttemptKey/trust isolation, and strict data minimization as implementation rules. |
| `docs/index.md` | `PASS` | It states that the P0 endpoint proves only App process liveness and that dbt execution/artifact ingestion begin later. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | The App does not run dbt; the future observed Lakeflow Job and separate DML collector remain distinct planes. |
| `docs/plans/product-plan.md` | `PASS` | It retains the exact compatibility, command, artifact, log, capture, AttemptKey, trust, data, action, and AI boundaries. |
| `docs/plans/review-process.md` | `PASS` | Later gates require native dbt evidence and control-input isolation rather than allowing P0 App liveness to stand in for product proof. |
| `docs/plans/documentation-plan.md` | `PASS` | Planned documentation distinguishes process, native dbt evidence, capture, collector-observed trust, and current trust and requires real sanitized examples later. |
| `docs/research/source-register.md` | `PASS` | Stable candidate pins, dependency caps, exact schemas, tagged Core behavior, structured logs, and prerelease watch items remain grounded in primary sources. |

## Non-blocking watch

Core 1.12 remains at release-candidate status and Core 2.0 remains alpha. Adapter 1.12.2 is deliberately capped below Core 1.11.13. A future candidate must requalify the complete dependency lock, Python and adapter options, artifact schemas, flags/aliases, warning names, result states and BuildTask collections, structured-log version/parser, native archive behavior, and retry/repair semantics. P0 App liveness evidence must never be reused as that qualification evidence.

## Cloud-mutation statement

This review used local repository reads, current official dbt documentation and schema registry, first-party GitHub release APIs, and official Python package metadata/distributions. It did not authenticate to Azure or Databricks, execute dbt or SQL, start or stop compute, or create, modify, or delete any cloud resource. No paid resource was started.

## Final disposition

- Frozen baseline 0.16 dbt verdict: `PASS`.
- Separate P0 live-smoke evidence dbt-boundary verdict: `PASS`.
- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- P0 dbt blockers: none.
- The P0 smoke accurately proves App process liveness only; it does not run or interpret dbt.
