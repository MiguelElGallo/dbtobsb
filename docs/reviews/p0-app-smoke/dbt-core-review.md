# P0 FastAPI Databricks App smoke: dbt Core product review

**Review date:** 2026-07-15  
**Reviewer lens:** dbt Core product and artifact-contract correctness  
**Verdict:** **PASS**  
**Cloud activity:** None. This review made no Databricks, Azure, authentication, or resource calls.

## Executive verdict

The bounded P0 shell is an appropriate first application slice. It does not run dbt, import dbt, parse dbt artifacts, read dbt logs, call a Databricks Job, or claim that a dbt run is observable. Its health contract reports only that the HTTP process can serve a request. That keeps the future dbt execution and artifact-ingestion boundary intact.

No blocking or non-blocking dbt Core findings were identified in the frozen scope.

The product-category text, “Customer-local dbt Core observability for Databricks,” is not presented as a current operational result: the OpenAPI description immediately identifies the service as a bounded P0 shell with no data, job, secret, warehouse, or model-serving bindings. Neither response payload says that dbt is installed, ready, running, captured, or healthy.

## Frozen review scope

The author supplied this globally sorted scope hash:

```text
65308f907c1723a57668e688d50464237a36cdea25738a0fb5f527140b542c72
```

It was reproduced before review with:

```bash
{
  printf '%s\n' \
    databricks.yml \
    app/app.yaml \
    app/pyproject.toml \
    app/uv.lock \
    app/dbtobsb_app/__init__.py \
    app/dbtobsb_app/main.py \
    app/tests/test_main.py
} | LC_ALL=C sort | while IFS= read -r file; do
  shasum -a 256 "$file"
done | shasum -a 256
```

The reviewed files are exactly:

- `databricks.yml`
- `app/app.yaml`
- `app/pyproject.toml`
- `app/uv.lock`
- `app/dbtobsb_app/__init__.py`
- `app/dbtobsb_app/main.py`
- `app/tests/test_main.py`

This report is outside that frozen implementation scope.

## Findings

None.

## Proof by concern

| Concern | Evidence in the frozen slice | Assessment |
|---|---|---|
| Premature dbt execution | The application command starts only `uvicorn dbtobsb_app.main:app`. There is no dbt CLI invocation, Python dbt API, shell, or subprocess. | Clean boundary. |
| Premature dbt dependency | Runtime dependencies are FastAPI and Uvicorn. The complete lock contains no `dbt-core`, `dbt-databricks`, `databricks-sdk`, or similarly named dbt/Databricks package. | Clean boundary. |
| Premature artifact ingestion | No filesystem access, target/log path, JSON loading, artifact parser, manifest model, run-results model, or upload endpoint exists. | Clean boundary. |
| Misleading dbt state | `/` returns service discovery metadata only. `/api/health` returns only `status`, service name, and service version. | No dbt state is implied. |
| Misleading health semantics | The response model calls the endpoint “liveness,” and its handler says it confirms only that the application process can serve requests. | Appropriate first health contract. |
| dbt versus service version | `0.1.0` is consistently identified as the service/OpenAPI version; no field labels it as a dbt Core or adapter version. | No version ambiguity in the response contract. |
| Sensitive dbt data | The only application log added by the slice is `health_check status=ok`; responses contain no project, node, SQL, relation, argument, environment, artifact, or job data. | Appropriate for the zero-binding shell. |
| Databricks resource coupling | The Bundle declares one stopped App and no Job, warehouse, secret, UC object, model-serving resource, or application resource binding. | Preserves the planned staged boundary. |

## Why the artifact boundary matters

dbt’s current artifact contract makes a process-only health endpoint materially different from an observability-readiness endpoint:

- dbt produces artifacts as part of dbt invocations, writes them to `target/` by default, and permits a configured `target-path`.
- Artifact metadata includes the producing `dbt_version`, independently versioned `dbt_schema_version`, generation timestamp, adapter type, and `invocation_id`.
- `manifest.json` represents the project graph and resources, while `run_results.json` contains only executed nodes and their completed invocation timing/status data. A `unique_id` links a run result back to its manifest node.
- dbt explicitly warns that artifact schemas can change across dbt minor versions.
- dbt’s human-readable event message is not intended for machine consumption; for standard machine use, dbt recommends JSON-formatted structured logs.

Therefore, an HTTP process being alive proves none of the following: dbt runtime compatibility, project validity, artifact availability, manifest/run-results pairing, run completion, collection freshness, or observability readiness. The P0 implementation correctly makes none of those claims.

Primary dbt references checked for this review:

- [About dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [Manifest JSON](https://docs.getdbt.com/reference/artifacts/manifest-json)
- [Run results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [Events and logs](https://docs.getdbt.com/reference/events-logging)

## Health-contract assessment

The exact P0 contract is suitable:

```json
{
  "status": "ok",
  "service": "dbtobsb",
  "version": "0.1.0"
}
```

`status: ok` means only “this application process served this request.” It does not collapse any of these future states into one green indicator:

1. App process liveness.
2. App resource-binding readiness.
3. Installer/current configuration trust.
4. Collector-observed configuration trust.
5. dbt artifact capture freshness and completeness.
6. Native dbt invocation/node outcome.

Keeping those dimensions separate is essential to avoid reporting a healthy app as a healthy dbt pipeline.

## Local verification

All checks below passed from `app/` against the frozen lock, without changing implementation files:

```text
uv run --frozen --extra dev pytest
3 passed in 0.14s

uv run --frozen --extra dev ruff check .
All checks passed!

uv run --frozen --extra dev ty check dbtobsb_app tests
All checks passed!
```

The tests prove the exact liveness payload, the exact public discovery payload, and OpenAPI exposure of the health operation.

## Required follow-up gates

These are gates for later slices, not defects in P0:

1. **Keep `/api/health` liveness-only.** Add a separate typed readiness or installation-status contract when bindings exist; do not redefine this endpoint to mean “dbt is observable.”
2. **Keep dbt execution out of the App.** The observed Databricks Job should invoke the customer’s pinned dbt Core/adapter runtime. The App must not add a generic dbt subprocess or Python programmatic invocation merely to obtain status.
3. **Introduce artifact parsing as a separately reviewed pure boundary.** Pin supported `manifest.json`, `run_results.json`, and structured-log schema/version expectations; reject unsupported versions closed.
4. **Correlate before claiming capture.** Require compatible artifact schemas and matching invocation identity before combining manifest, run results, and structured events. Preserve native dbt status separately from collection/capture status.
5. **Do not parse human-readable `msg` as a stable protocol.** Use version-qualified artifacts and JSON-formatted structured event fields; retain an explicit unknown path for new event or status values.
6. **Keep raw dbt material out of ordinary API responses and logs.** Future allowlists must exclude compiled SQL/code, relation names, CLI arguments/vars, environment metadata, adapter messages, raw logs, and raw artifacts unless a separately approved regulated-data design requires them.
7. **Do not expose unbacked dbt claims.** Add dbt version, adapter version, artifact freshness, Job status, run outcome, or trust fields only when the corresponding reviewed binding and evidence source exists.
8. **Keep compatibility labels explicit.** A future service version, observed dbt version, adapter version, supported-version range, and artifact schema version must be separate fields rather than overloaded as `version`.
9. **Reject arbitrary execution input.** Future routes must not accept free-form dbt commands, selectors, `--vars`, target/log paths, shell fragments, or Job parameters.
10. **Extend negative contract tests with the first dbt-facing slice.** Assert that liveness stays unchanged, readiness cannot be green without its bindings, unsupported artifact schemas fail closed, and sensitive/raw fields never enter public responses.

## Acceptance conclusion

The frozen implementation passes the dbt Core product review for the P0 smoke milestone. It is deliberately useful only as proof that a stopped-by-default Databricks App package can expose a minimal HTTP surface. That is the right scope: no dbt runtime, execution, artifact, log, or observability claim has been wired early, and the future collector/artifact design remains free to be reviewed as its own trust boundary.
