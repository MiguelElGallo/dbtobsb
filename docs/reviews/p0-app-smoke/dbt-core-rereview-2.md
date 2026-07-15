# P0 App implementation: second dbt Core re-review

- Reviewed input: exact frozen eight-file implementation set
- Frozen implementation SHA-256: `3dfdce3c354b858a252904190ccbca7689d10fe883a818910c897acb9dcd3866`
- Review date: 2026-07-15
- Reviewer lens: dbt Core execution, artifact, log, and product-claim boundaries
- Verdict: `PASS`
- Findings: none
- Cloud activity: none

## Executive verdict

The `3dfdce3…` implementation passes the second dbt Core re-review. The focused delta verifies that the live Databricks App reports compute size `MEDIUM` both before start and after it reaches `ACTIVE`, and adds a negative test proving that an unapproved size fails before `bundle run` and still enters verified cleanup.

This is App cost and lifecycle enforcement only. `MEDIUM` is never supplied to a dbt command, Job parameter, selector, vars, profile, target path, log path, artifact, event, AttemptKey, or native result. The implementation still cannot run dbt, import dbt, inspect a dbt project, read artifacts, parse dbt logs, call a dbt Job, or claim dbt/product readiness.

All local gates passed, including exactly 11 tests. No implementation file was edited by this review.

## Frozen scope and hash proof

The reviewed files are exactly:

- `app/app.yaml`
- `app/dbtobsb_app/__init__.py`
- `app/dbtobsb_app/main.py`
- `app/pyproject.toml`
- `app/tests/test_main.py`
- `app/uv.lock`
- `databricks.yml`
- `scripts/smoke_databricks_app.sh`

The globally sorted path-plus-content hash was reproduced with:

```sh
{
  printf '%s\n' \
    databricks.yml \
    app/app.yaml \
    app/pyproject.toml \
    app/uv.lock \
    app/dbtobsb_app/__init__.py \
    app/dbtobsb_app/main.py \
    app/tests/test_main.py \
    scripts/smoke_databricks_app.sh
} | LC_ALL=C sort > /tmp/dbtobsb-p0-impl-files.txt

while IFS= read -r file; do
  shasum -a 256 "$file"
done < /tmp/dbtobsb-p0-impl-files.txt | shasum -a 256
```

Result:

```text
3dfdce3c354b858a252904190ccbca7689d10fe883a818910c897acb9dcd3866  -
```

Each inner digest binds its path and content. This report is outside the implementation digest.

## Focused MEDIUM-size delta

| Delta | Verification | dbt conclusion |
|---|---|---|
| `EXPECTED_COMPUTE_SIZE='MEDIUM'` | The value is a fixed wrapper constant, not user input. | It governs only the P0 App resource and cannot become dbt compute configuration. |
| Stopped deployment readback | After deploy, the wrapper requires both `STOPPED` and `compute_size == MEDIUM` before inspecting zero bindings and before start. | A size mismatch cannot reach App invocation, much less a dbt execution path. |
| Active deployment readback | After the one App invocation, the wrapper requires `ACTIVE`, `compute_size == MEDIUM`, and the expected App URL shape. | The check remains App lifecycle validation and creates no dbt status mapping. |
| Failure cleanup | A size mismatch exits nonzero after `may_need_stop=1`; the exit trap issues App stop and verifies `STOPPED`. | Cleanup state cannot be represented as dbt success, failure, cancellation, or capture. |
| Configurable fake App size | The test double returns the requested `compute_size` on every App readback. | The fixture tests the remote App response field, not a dbt setting. |
| Negative `LARGE` test | The test requires nonzero exit, the `Expected stopped MEDIUM deployment` diagnostic, no `bundle run`, an App stop call, and final `STOPPED`. | It proves fail-before-start behavior without creating any dbt input or interpretation. |
| Existing success test | The fake App reports `MEDIUM` in both stopped and active reads; the successful path exercises both checks and verified cleanup. | App-size acceptance does not widen the health or future dbt surface. |

## dbt boundary proof

| Concern | Evidence in the frozen implementation | Verdict |
|---|---|---|
| App process | Startup is only `uvicorn dbtobsb_app.main:app`; application code has no shell or subprocess path. | `PASS` — the App cannot execute dbt. |
| Wrapper commands | The wrapper directly requires and invokes Databricks CLI, `jq`, and `curl` only. | `PASS` — there is no dbt executable or Python dbt API. |
| Runtime dependencies | Runtime remains FastAPI plus Uvicorn; the lock has no dbt Core, dbt-databricks, Databricks SDK, or adapter runtime. | `PASS` — no premature dbt coupling. |
| Bundle resources | One stopped-by-default unbound App is declared; there is no Job, warehouse, cluster, schedule, secret, UC binding, or model-serving binding. | `PASS` — no dbt execution resource exists. |
| Compute-size meaning | Both checks read `.compute_size` from `databricks apps get`. | `PASS` — this is App compute, not dbt Job or SQL warehouse compute. |
| Health contract | The exact values remain `alive`, `process_liveness`, `not_evaluated`, and `p0_smoke`. | `PASS` — no dbt or product readiness is implied. |
| App stdout | The wrapper searches only App-source logs for its fixed `health_check` marker. | `PASS` — it does not parse dbt stdout, `dbt.log`, dbt `msg`, or structured dbt events. |
| Artifacts | No project/profile, target/log path, JSON artifact loader, manifest, run-results, upload, or parser exists. | `PASS` — no capture claim is possible. |
| Native outcomes | No response, branch, or test maps App state/size/cleanup to a dbt invocation, model, test, seed, node, adapter, or artifact result. | `PASS` — native dbt semantics remain untouched. |
| Sensitive dbt data | API and App log contain no SQL, compiled code, relation, CLI args, selector, vars, environment metadata, project/node ID, or raw artifact/log content. | `PASS` — the zero-data P0 surface remains appropriate. |
| Arbitrary execution input | Host, user, OAuth profile, and stop-attempt inputs are bounded platform controls; App size is fixed. | `PASS` — no user dbt command, flag, path, Job ID, Git ref, SQL, or compute setting is accepted. |

The generic word `dbt` in product descriptions is future-product context. The endpoint itself explicitly says that it does not check dbt, Databricks resources, storage, capture, authorization, or product readiness.

## Local verification

All non-cloud gates passed against the frozen implementation:

```text
uv run --frozen --extra dev pytest
11 passed in 3.28s

uv run --frozen --extra dev ruff check .
All checks passed!

uv run --frozen --extra dev ruff format --check .
3 files already formatted

uv run --frozen --extra dev ty check dbtobsb_app tests
All checks passed!

bash -n scripts/smoke_databricks_app.sh
passed

shellcheck scripts/smoke_databricks_app.sh
passed
```

The wrapper tests use temporary fake `databricks` and `curl` executables. They perform no authentication and contact no workspace.

## Contract interpretation against current dbt behavior

Current official dbt documentation continues to establish that:

- dbt artifacts are products of dbt invocations and are written to `target/` by default;
- manifest and run-results metadata carry versioned schema and invocation information;
- `run_results.json` represents executed nodes from a completed invocation; and
- human-readable event `msg` is not a machine-stable protocol, while version-qualified JSON structured events are the machine-readable boundary.

The P0 App produces and verifies none of those things. An App size readback and HTTP response cannot prove dbt runtime compatibility, project validity, artifact availability, invocation correlation, build completion, capture freshness, or native dbt outcome.

Primary references checked:

- [About dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [Manifest JSON](https://docs.getdbt.com/reference/artifacts/manifest-json)
- [Run results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [Events and logs](https://docs.getdbt.com/reference/events-logging)

## Later-slice gates preserved

This P0 approval does not authorize a dbt-facing shortcut. Later slices must still:

1. Keep `/api/health` process-liveness-only and add separately typed readiness only after reviewed bindings exist.
2. Run customer dbt in the pinned Databricks Job runtime, never through a generic App subprocess.
3. Introduce exact manifest, run-results, and structured-event parsing as a separately reviewed pure boundary.
4. Correlate compatible artifacts by invocation identity before claiming capture and preserve native dbt outcome separately from App, collector, capture, trust, freshness, and cost.
5. Reject unsupported schemas, event versions, and statuses closed or as explicit unknowns; never parse human `msg` as protocol.
6. Keep raw artifacts, logs, SQL/code, relations, CLI args/vars, and environment metadata out of ordinary responses and logs.
7. Reject free-form dbt commands, selectors, vars, paths, shell fragments, Job IDs, and workload parameters.
8. Re-review any App binding, dbt dependency, Job invocation, parser, capture/readiness field, or dbt version/status field before addition.

## Cloud and mutation statement

This review used local file reads, public dbt documentation, and local tests with fake executables. It made no Azure or Databricks authentication call, executed no dbt or SQL, started no compute, and created, changed, or deleted no cloud resource. No paid resource was started.

## Final disposition

- Frozen implementation `3dfdce3…`: `PASS`.
- Eleven-test and static-analysis gate: `PASS`.
- MEDIUM-size enforcement: App-only, fail-before-start, and dbt-neutral.
- New dbt findings: none.
- P0 dbt blockers: none.
- The implementation still proves App process liveness only and does not run or interpret dbt.
