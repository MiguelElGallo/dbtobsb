# Fifteenth dbt Core re-review: P0 planning baseline 0.17

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97`
- Separate evidence input: `docs/evidence/p0-live-smoke-2026-07-15.md`
- Separate evidence SHA-256: `6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a`
- Review date: 2026-07-15
- Reviewer lens: dbt Core and dbt-databricks contract correctness
- Planning verdict: `PASS`
- Evidence dbt-boundary verdict: `PASS`
- Findings: none
- Cloud activity: none

## Executive verdict

Baseline 0.17 passes the focused dbt Core re-review. The cost-document changes correct a live-test process defect without changing the future dbt execution, artifact, structured-log, attempt-correlation, capture, result, privacy, or optional-AI contract.

The README now puts an explicit App cost envelope before the executable smoke command. The separate evidence record honestly preserves the historical omission, labels the run a technical pass with a cost-control process finding, gives only a conservative derived post-run DBU bound, and says that no second paid run was made to rewrite history. Cost state remains an operational fact; it is not a dbt result, capture predicate, or readiness signal.

The P0 smoke evidence also remains exact about its dbt boundary. It proves only that the packaged FastAPI process ran, served its process-liveness response, emitted one App stdout event, and returned to `STOPPED`. It explicitly denies dbt execution, artifact capture, product-data access, dependency readiness, and product readiness. No dbt Job, dbt command, artifact, dbt log, node result, warehouse, or cluster is claimed.

## Immutable scope and hash proof

The frozen planning set was reproduced with the requested sorted path-plus-content formula:

```sh
{
  printf '%s\n' README.md AGENTS.md docs/index.md
  rg --files docs/decisions docs/plans docs/research -g '*.md'
} | LC_ALL=C sort -u > /tmp/dbtobsb-baseline-017-files.txt

while IFS= read -r file; do
  shasum -a 256 "$file"
done < /tmp/dbtobsb-baseline-017-files.txt | shasum -a 256
```

Result:

```text
83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97  -
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

The evidence record is outside that aggregate and was verified separately:

```text
6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a  docs/evidence/p0-live-smoke-2026-07-15.md
```

This report is outside both frozen inputs. No author or evidence file was edited by this review.

## Cost-document delta assessment

| Change | Verdict | dbt conclusion |
|---|---|---|
| Cost envelope precedes the live command | `PASS` | Requiring approval before execution changes operator procedure only. It cannot alter dbt argv, flags, selector, vars, paths, artifacts, or outcomes. |
| App size fixed to `MEDIUM` | `PASS` | This is the P0 Databricks App compute size, not a dbt Job, warehouse, cluster, adapter, target, or thread setting. |
| Published rate and 10-minute/0.084-DBU bound | `PASS` | The estimate bounds App smoke exposure and remains separate from currency, billing reconciliation, future dbt Job cost, and native dbt status. |
| Schedule, cancellation, cleanup owner, and final state | `PASS` | These controls govern one App smoke. They do not add a schedule, dbt Job, arbitrary Job ID, or dbt control input. |
| Separate final inventory commands | `PASS` | App/warehouse/cluster state is platform lifecycle evidence. It does not create a dbt invocation, capture, or node/test outcome. |
| Historical process finding retained | `PASS` | The evidence does not let a final `STOPPED` state retroactively satisfy a missing pre-run approval. That is accurate governance and does not reinterpret dbt evidence. |
| Conservative post-run bound | `PASS` | The record identifies the whole object-create-to-stop window, says actual billable time was a subset, and does not call the estimate an invoice. No dbt cost attribution is implied. |
| No repeat paid run | `PASS` | Avoiding a second smoke to erase a documentation defect preserves honest evidence and introduces no dbt qualification claim. |

## Resolved dbt-contract regression check

| Contract | Baseline 0.17 result |
|---|---|
| Candidate runtime | `PASS` — `dbt-databricks==1.12.2`, `dbt-core==1.11.12`, `dbt-common==1.37.5`, Python 3.12.3, log version 3, and the exact wheel digest remain unchanged candidate pins. |
| Command surface | `PASS` — optional governed `dbt deps` followed by exactly one selector-scoped `dbt build` remains the only supported observed sequence. |
| Zero execution | `PASS` — `NoNodesForSelectionCriteria`, `NothingToDo`, and the independent non-empty-results/`DBT_EMPTY_EXECUTION` rule remain intact. |
| Artifact pair | `PASS` — exactly manifest v12 plus run-results v6, matching invocation UUID, exact Core version, `args.which=build`, manifest adapter type, and non-empty unique results remain mandatory. |
| Result resolution | `PASS` — IDs still resolve exactly once through nodes, unit tests, saved queries, exposures, or functions; manifest inventory remains distinct from executed results. |
| Structured logs | `PASS` — the seven ordered ordinal-local states remain `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID`; human `msg` remains excluded. |
| Capture precedence | `PASS` — `ARCHIVE_UNAVAILABLE`, `INVALID_CAPTURE_CONTRACT`, `COMPLETE`, `PARTIAL`, and `NOT_PRODUCED` remain total and independent of cost or App state. |
| Attempt and trust | `PASS` — native AttemptKey coordinates remain authoritative; collector-observed trust and cost/lifecycle fields cannot enter identity, hashes, validation, capture, or native outcomes. |
| Data minimization | `PASS` — raw/compiled SQL, vars, messages, arbitrary metadata/events, and sensitive environment values remain excluded from normal product tables. |
| Controlled actions | `PASS` — action, fence, actor, token, trust, deployment, and cost fields remain outside dbt argv, environment, selector, vars, paths, artifacts, events, and workload parameters. |
| Optional intelligence | `PASS` — Genie, MCP, and LLM assistance remain optional and outside the deterministic execution/capture path. |

`DBT-P0-001` through `DBT-P0-008` remain `RESOLVED — NO REGRESSION`. No new dbt finding is opened.

## Separate evidence assessment

| Evidence fact | Verdict | Boundary interpretation |
|---|---|---|
| Scope says private App process-liveness smoke | `PASS` | It is not described as a dbt run or observability-product test. |
| Response says `process_liveness` and `not_evaluated` | `PASS` | App liveness cannot be mistaken for dbt, dependency, artifact, collector, or product readiness. |
| One App `health_check` stdout event | `PASS` | It is not a dbt `info`/`data` event, has no dbt invocation identity or log version, and cannot prove build start. |
| Zero App bindings | `PASS` | The App could not read future product tables, artifacts, or collector state. |
| Zero warehouses and clusters | `PASS` | No SQL/dbt execution compute was created for this smoke. |
| No dbt Job | `PASS` | No scheduler, dbt command, selector, target/log path, manifest, run-results file, or native result existed to interpret. |
| Explicit denial of dbt/capture/readiness proof | `PASS` | The disclaimer matches the observed evidence exactly. |
| Final App `STOPPED` | `PASS` | This is cost/lifecycle evidence only and is not mapped to a dbt success. |

The record's post-run state readback uses the same operator and credential context and correctly does not present itself as independent human attestation. This review assessed the record's dbt claims; it did not rerun the cloud smoke.

## Current dbt references checked

- [About dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [Manifest JSON](https://docs.getdbt.com/reference/artifacts/manifest-json)
- [Run results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [Events and logs](https://docs.getdbt.com/reference/events-logging)
- [About dbt build](https://docs.getdbt.com/reference/commands/build)

These sources continue to make dbt invocation artifacts, executed results, and structured dbt events materially different from an application HTTP health response or generic App stdout event.

## Cloud and mutation statement

This review used local repository reads and current public dbt documentation. It made no Azure or Databricks authentication call, executed no dbt or SQL, started no compute, and created, changed, or deleted no cloud resource. No paid resource was started.

## Final disposition

- Planning baseline 0.17: `PASS`.
- Separate P0 evidence dbt boundary: `PASS`.
- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings: none.
- P0 dbt blockers: none.
- The cost controls govern App smoke execution only and do not contaminate dbt contracts.

