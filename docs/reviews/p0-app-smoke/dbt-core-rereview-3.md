# P0 App implementation: third dbt Core re-review

- Reviewed input: exact frozen eight-file implementation set
- Frozen implementation SHA-256: `0ad64adf3071944adddf501120713bb07c0e19d43e360a901d17dbe6bf7fa437`
- Review date: 2026-07-15
- Reviewer lens: dbt execution, artifact, log, status, and product-claim boundaries
- Verdict: **PASS**
- Contract tests: **12 passed**
- Findings: none
- Cloud/authentication activity: none

## Executive verdict

Implementation `0ad64a…` passes the dbt Core re-review and every declared local gate. The new dedicated-workspace guard checks visible Apps, warehouses, and clusters before Bundle validation or deployment and rejects an unrelated App without invoking any mutating command. That is a P0 cost/isolation control, not a dbt feature.

The implementation remains incapable of running or interpreting dbt. It has no dbt dependency, project, profile, command builder, shell/subprocess path in the App, Job, warehouse, cluster, selector, target/log path, artifact reader, structured-dbt-log parser, node-result model, or capture/readiness field. Its only runtime claim is App process liveness.

## Frozen scope and hash proof

The implementation set is exactly:

- `app/app.yaml`
- `app/dbtobsb_app/__init__.py`
- `app/dbtobsb_app/main.py`
- `app/pyproject.toml`
- `app/tests/test_main.py`
- `app/uv.lock`
- `databricks.yml`
- `scripts/smoke_databricks_app.sh`

The sorted path-plus-content procedure was:

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
} | LC_ALL=C sort > /tmp/dbtobsb-p0-impl-019-files.txt

while IFS= read -r file; do
  shasum -a 256 "$file"
done < /tmp/dbtobsb-p0-impl-019-files.txt | shasum -a 256
```

Result before and after local verification:

```text
0ad64adf3071944adddf501120713bb07c0e19d43e360a901d17dbe6bf7fa437  -
```

This report is outside the implementation digest.

## Twelve contract-test gates

| Test | Verified behavior | dbt conclusion |
| --- | --- | --- |
| 1. Health response | Exact six-field `process_liveness` body | No dbt or product readiness field exists. |
| 2. Health logger | One INFO stdout handler, no propagation | Fixed App event only; no dbt log parsing or streaming. |
| 3. Service index | Only service/version/phase and public API links | No project, Job, artifact, identity, or data disclosure. |
| 4. OpenAPI | Stable summaries, operation IDs, descriptions, and schemas | API contract explicitly denies product readiness. |
| 5. Interactive docs | `/docs` and `/redoc` disabled | No public runtime asset dependency is introduced. |
| 6. Bundle default | One stopped-by-default unbound App | No Job, warehouse, cluster, schedule, data binding, or dbt execution resource. |
| 7. Successful wrapper | Start, health, App-log observation, stop, and final `STOPPED` | App lifecycle cannot become a dbt outcome. |
| 8. Health failure | Nonzero result followed by verified stop | Failure/cleanup is not mapped to dbt success or failure. |
| 9. Transient cleanup read failure | Stop still occurs and is subsequently verified | An uncertain status read cannot suppress cleanup or create a dbt result. |
| 10. Unexpected resource binding | Reject before start and stop defensively | P0 cannot read future product/artifact data. |
| 11. Unapproved App size | Reject before start and stop defensively | `MEDIUM` is App compute, not a dbt target/thread/warehouse setting. |
| 12. Unrelated workspace | Exit `2` before Bundle validate/deploy/run/stop | Dedicated-workspace safety adds no dbt command or mutation. |

The twelfth test asserts that `bundle validate`, `bundle deploy`, `bundle run`, and `apps stop` are all absent when an unrelated visible App exists.

## Local verification

The locked local environment and all README gates passed:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages; checked 30 packages

uv run --project app --extra dev pytest
12 passed in 3.47s

uv run --project app --extra dev ruff check app/dbtobsb_app app/tests
All checks passed!

uv run --project app --extra dev ruff format --check app/dbtobsb_app app/tests
3 files already formatted

uv run --project app --extra dev ty check app/dbtobsb_app app/tests
All checks passed!

bash -n scripts/smoke_databricks_app.sh
passed

shellcheck scripts/smoke_databricks_app.sh
passed
```

The wrapper tests prepend temporary fake `databricks` and `curl` executables. No real profile, token, network request, workspace, or paid compute was used.

## dbt boundary proof

| Concern | Frozen implementation evidence | Verdict |
| --- | --- | --- |
| App process | Runtime command is only `uvicorn dbtobsb_app.main:app`; App code has no subprocess, shell, or dynamic execution path. | **Pass** — cannot execute dbt. |
| Dependencies | Runtime is FastAPI/Uvicorn. The lock contains no dbt Core, dbt-databricks, dbt-common, Databricks SDK, or adapter. | **Pass** — no premature dbt coupling. |
| Bundle resources | Exactly one stopped-by-default App with no resource bindings is declared. | **Pass** — no dbt Job or SQL compute exists. |
| Wrapper surface | The wrapper directly invokes only Databricks CLI, `jq`, and `curl`; inputs are exact profile/host/user and a bounded test-only stop-attempt count. | **Pass** — no dbt executable, Python API, command fragment, selector, vars, path, or Job ID. |
| Workspace preflight | It requires no unrelated visible App and zero visible warehouses/clusters before Bundle validation. | **Pass** — platform inventory is not dbt evidence. |
| Health contract | Values are `alive`, `process_liveness`, `not_evaluated`, and `p0_smoke`; descriptions explicitly deny dbt and product readiness. | **Pass** — no false readiness. |
| App stdout | One fixed `health_check` marker is searched only in App-source logs. | **Pass** — no `dbt.log`, `MainReportVersion`, event `data`, or human `msg` interpretation. |
| Artifacts | No `manifest.json`, `run_results.json`, source freshness, target directory, archive, parser, upload, or normalization code exists. | **Pass** — no capture claim. |
| Native outcomes | No code maps App state, HTTP result, log marker, compute size, inventory, or stop state to a dbt invocation/node/test status. | **Pass** — dbt semantics remain untouched. |
| Sensitive data | Responses/events contain no SQL, compiled code, relation, args, selector, vars, project/node ID, environment metadata, artifact/log content, or customer data. | **Pass** — appropriate zero-data P0 surface. |

The App's Python 3.11 shell is separate from the future candidate Python 3.12 dbt Job runtime. Nothing in P0 qualifies or contradicts the future dbt runtime matrix.

## Later-slice gates preserved

This approval does not authorize a dbt-facing shortcut. A later slice must still introduce and review:

1. the pinned Job runtime and exact closed dbt argv;
2. immutable attempt/ordinal target and log paths;
3. exact manifest v12, run-results v6, and structured-event parsing;
4. invocation correlation and native outcome preservation;
5. missing/malformed/unknown evidence classifications;
6. restricted raw diagnostics and field-level minimization; and
7. explicit readiness separate from `/api/health` process liveness.

Any dbt dependency, Job, App binding, command builder, artifact/log parser, normalized result, or readiness field reopens dbt review.

## Findings

None.

## Cloud and mutation statement

This review ran only local dependency, test, lint, type, and shell-static checks. It made no Azure or Databricks authentication call, executed no dbt or SQL, started no compute, and changed no implementation or cloud resource.

## Final disposition

- Frozen implementation `0ad64a…`: **PASS**.
- Twelve contract tests: **PASS**.
- Lint, format, type, shell syntax, and ShellCheck: **PASS**.
- New dbt findings or P0 blockers: none.
- The implementation still proves only App process liveness and does not run, capture, or interpret dbt.

