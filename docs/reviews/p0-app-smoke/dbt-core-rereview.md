# Final P0 App implementation: dbt Core re-review

**Review date:** 2026-07-15  
**Reviewer lens:** dbt Core product claims and execution/artifact contract boundaries  
**Verdict:** **PASS**  
**Findings:** None  
**Cloud activity:** None. This review made no Databricks, Azure, authentication, or resource calls.

## Executive verdict

The exact eight-file P0 candidate introduces no misleading dbt behavior or claim and no dbt execution, dependency, log, status, or artifact-boundary regression.

The App contract remains deliberately narrower than dbt observability: the process is `alive`, the check is `process_liveness`, product readiness is `not_evaluated`, and the phase is `p0_smoke`. The endpoint explicitly says it does not check dbt, Databricks resources, storage, capture, authorization, or product readiness.

The hardened wrapper remains an App smoke test only. It validates and deploys the zero-binding App, starts it deliberately, verifies the exact P0 HTTP payload and fixed App stdout event, and enters verified cleanup. It never runs dbt, supplies dbt inputs, reads dbt paths, parses dbt logs or artifacts, or translates App state into a dbt run result.

## Frozen scope and hash proof

The reviewed scope is exactly:

- `databricks.yml`
- `app/app.yaml`
- `app/pyproject.toml`
- `app/uv.lock`
- `app/dbtobsb_app/__init__.py`
- `app/dbtobsb_app/main.py`
- `app/tests/test_main.py`
- `scripts/smoke_databricks_app.sh`

The globally sorted path-and-content hash was reproduced before review:

```text
eff855524237e36909b282b5c030207b0478606e7f2b44a810082012d33f6a5c
```

Reproduction command:

```bash
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
} | LC_ALL=C sort | while IFS= read -r file; do
  shasum -a 256 "$file"
done | shasum -a 256
```

Each inner checksum line includes its path, so the outer digest binds both sorted paths and file contents. This report is outside the frozen implementation scope. No implementation file was edited by this review.

## Findings

None.

## dbt contract-boundary proof

| Concern | Evidence in the frozen candidate | Assessment |
|---|---|---|
| Current versus future product | The OpenAPI summary says “future dbt Core observability,” while response/schema text repeatedly calls this a P0 shell that is not the product. | Aspirational context, not a current capability claim. |
| Liveness versus dbt readiness | `alive`, `process_liveness`, `not_evaluated`, and `p0_smoke` are literal contract values. The endpoint expressly excludes dbt and capture checks. | A successful response cannot be read as dbt readiness or run health. |
| Service versus dbt version | Schema metadata names `0.1.0` the application-shell version. | No dbt Core, adapter, or artifact-schema version ambiguity. |
| App runtime | App startup is only `uvicorn dbtobsb_app.main:app`; application code has no shell or subprocess path. | The App cannot execute dbt. |
| Wrapper commands | The smoke wrapper invokes only the Databricks CLI, `jq`, and `curl`. | No dbt executable, Python dbt API, or generic command surface exists. |
| Dependencies | Runtime dependencies remain FastAPI and Uvicorn. The complete lock contains no `dbt-core`, `dbt-databricks`, Databricks SDK, or equivalent dbt/adapter package. | No premature runtime or adapter coupling. |
| dbt filesystem contract | No dbt project/profile path, target/log path, artifact scan, JSON artifact load, or artifact upload exists. | The future collector boundary remains untouched. |
| dbt log interpretation | The wrapper searches only `--source APP` for its fixed `health_check` marker. It never reads dbt stdout, `dbt.log`, human-readable dbt messages, or dbt structured events. | No accidental dbt log-parser contract. |
| dbt status interpretation | No response, wrapper branch, or test contains a dbt invocation, model, test, seed, node, adapter, or artifact status. | App/platform state is not mapped to native dbt outcome. |
| Sensitive dbt material | The API and fixed App log contain no SQL, compiled code, relation, CLI argument, selector, vars, environment metadata, project/node identifier, or raw artifact/log content. | Appropriate zero-data P0 surface for a regulated industry. |
| Live resource guard | The wrapper rejects any deployed or running App resource binding before treating smoke as successful. | Unexpected storage, Job, secret, warehouse, or other future coupling cannot silently enter this P0 proof. |
| Authentication hardening | Exact OAuth U2M host and user are checked, ambient token/client-secret auth and shell tracing are rejected, and curl/token handling is tested. | Platform trust is strengthened without creating a dbt identity or execution claim. |
| Cleanup hardening | Stop is always attempted once deployment may have occurred, verification retries are bounded, and an unverified stop changes success to failure. | Cost/lifecycle state remains separate from dbt result semantics. |
| CLI pin | Bundle and wrapper both constrain the Databricks CLI to version `1.7.0`. | This is a platform-tool pin, not an implicit dbt compatibility statement. |

## Wrapper remains P0 App smoke only

The final wrapper does exactly these product-relevant operations:

1. Confirms the expected Databricks CLI, OAuth U2M profile, workspace host, and signed-in user.
2. Validates and deploys the stopped-by-default Bundle target.
3. Refuses any live App resource binding before start and checks again after start.
4. Starts only `dbtobsb_smoke` and verifies App compute state and the expected App URL form.
5. Calls only `/api/health` and requires the complete six-field P0 liveness response.
6. Looks only in App-source logs for the App’s fixed stdout health marker.
7. Stops App compute on success and error paths, retries state verification, and fails closed when stop cannot be verified.

It contains no dbt command, selector, `--vars`, project/profile directory, target/log location, artifact name, invocation identifier, node identifier, adapter configuration, or dbt result mapping.

The emitted stdout record is App-shell telemetry rather than a dbt event:

```json
{"event":"health_check","status":"alive","readiness":"not_evaluated","phase":"p0_smoke"}
```

It has no dbt event envelope, invocation identity, node information, adapter data, or product-readiness assertion.

## Final-delta regression assessment

The changes since the previously reviewed candidate strengthen operational safety without widening the dbt surface:

- Exact signed-in-user verification narrows the allowed Databricks identity; it does not configure a dbt user or profile.
- Stop verification now retries, always attempts the idempotent stop after possible deployment, and prints manual recovery commands when necessary; none of these states is represented as a dbt outcome.
- HTTPS curl constraints and token non-disclosure tests harden the App request only.
- Live resource-binding rejection actively preserves the P0 zero-binding promise.
- Additional wrapper tests exercise success, health failure, transient cleanup-read failure, resource-binding rejection, token handling, and verified stop behavior entirely with fake executables.

No changed line introduces dbt execution, artifact capture, dbt log interpretation, dbt status, dbt version support, or observability readiness.

## Contract interpretation against current dbt behavior

Current dbt documentation establishes that:

- dbt artifacts are produced by dbt invocations and written to `target/` by default;
- artifact metadata includes the producing dbt version, independently versioned artifact schema, adapter type, generation timestamp, and invocation ID;
- `run_results.json` represents a completed invocation and only its executed nodes; and
- dbt’s human-readable event `msg` is not intended as a machine-stable protocol, while JSON-formatted structured logs are the recommended machine-readable form.

The P0 App and wrapper produce or verify none of that dbt evidence. Reporting readiness as `not_evaluated` remains the correct contract.

Primary dbt references checked:

- [About dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [Run results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [Events and logs](https://docs.getdbt.com/reference/events-logging)

## Local verification

Every local, non-cloud gate rerun against the frozen implementation passed:

```text
uv run --frozen --extra dev pytest
10 passed in 3.19s

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

The wrapper tests substitute temporary fake `databricks` and `curl` executables. They do not authenticate or contact a workspace. Live Bundle validation was intentionally not rerun because cloud and authentication calls were excluded from this reviewer’s scope.

## Required follow-up gates

This P0 approval does not authorize a dbt-facing shortcut. Later slices must still satisfy these gates:

1. Keep `/api/health` process-liveness-only. Add separate typed readiness or installation status only after reviewed bindings and evidence exist.
2. Keep customer dbt execution in its pinned Databricks Job runtime; do not add a generic dbt subprocess or programmatic invocation to the App.
3. Introduce version-qualified `manifest.json`, `run_results.json`, and structured-event parsing as a separately reviewed pure boundary.
4. Correlate compatible artifacts by invocation identity before claiming a captured run. Preserve native dbt outcome separately from capture, collector, trust, freshness, and App state.
5. Reject unsupported artifact/event schema versions and unknown statuses closed or as explicit unknowns.
6. Do not parse human-readable dbt `msg` text as a stable protocol.
7. Keep raw artifacts, logs, compiled code, relations, CLI arguments/vars, and environment metadata out of ordinary API responses and App logs.
8. Keep service version, observed dbt version, adapter version, artifact-schema version, and compatibility range as separately named fields.
9. Do not add free-form dbt commands, selectors, vars, paths, shell fragments, or Job parameters to a public API.
10. Add dbt-facing claims only with their evidence source, trust state, freshness semantics, regulated-data allowlist, and negative tests.
11. Keep the App health event namespace and App-source log check distinct from future dbt structured-event ingestion.
12. Re-review any App binding, dbt dependency, Job invocation, artifact/log parser, capture field, readiness field, or dbt version/status field before it is added.

## Conclusion

The exact `eff85552…` P0 App implementation passes the dbt Core re-review. The hardened wrapper proves only the bounded, zero-binding App liveness contract and does not falsely run, capture, or interpret dbt. The future dbt runtime, artifact ingestion, correlation, regulated-data handling, and product-readiness contracts remain isolated for their own implementation and expert review.
