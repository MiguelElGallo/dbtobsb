# P0 App implementation: fourth dbt Core re-review

- Frozen implementation SHA-256: `8b1865cd05ba5abbeef6634d80e01778affe5b03ee76cbdfe919be3d84355101`
- Review date: 2026-07-15
- Reviewer lens: dbt boundary and P0 token-handling delta
- Verdict: **PASS**
- Contract tests: **12 passed**
- Findings: none
- Cloud/authentication activity: none

## Executive verdict

Implementation `8b1865c…` passes the focused review and all local gates. The delta forces OS-native secure Databricks authentication storage for the P0 wrapper and makes the fake CLI reject any test invocation that does not receive that setting.

The App implementation remains dbt-free. The token-output command exists only in the development smoke wrapper, after the App reaches `ACTIVE`, and serves one token-protected liveness request. No dbt dependency, Job, command builder, project/profile, selector, target/log path, artifact parser, dbt event parser, node result, or capture/readiness mapping exists.

## Frozen implementation scope

The digest covers exactly:

- `app/app.yaml`
- `app/dbtobsb_app/__init__.py`
- `app/dbtobsb_app/main.py`
- `app/pyproject.toml`
- `app/tests/test_main.py`
- `app/uv.lock`
- `databricks.yml`
- `scripts/smoke_databricks_app.sh`

The sorted path-plus-content aggregate reproduced before and after verification:

```text
8b1865cd05ba5abbeef6634d80e01778affe5b03ee76cbdfe919be3d84355101  -
```

This report is outside the implementation digest.

## Focused security delta

| Behavior | Verification | dbt conclusion |
| --- | --- | --- |
| Ambient credentials | Wrapper rejects `DATABRICKS_TOKEN` and `DATABRICKS_CLIENT_SECRET`. | No caller-supplied token or secret can become dbt input. |
| Secure storage | Wrapper rejects an inherited non-`secure` value and exports `DATABRICKS_AUTH_STORAGE=secure` before any CLI call. | Storage policy is isolated from future dbt argv/environment. |
| Shell tracing | Wrapper exits when xtrace is active. | Token cannot be emitted through traced shell commands. |
| Token command | `databricks auth token <explicit-profile>` runs only for the P0 health call. | It does not run dbt or authorize capture. |
| In-memory handoff | Token is captured in one shell variable; curl receives header configuration through stdin. | Secret is absent from curl argv and dbt has no process to inherit it. |
| Curl isolation | `--disable` is first, HTTPS is required, TLS 1.2 minimum is set, and `--config -` consumes stdin. | Ambient curl configuration cannot turn the P0 call into a dbt path. |
| Clearing | Token is unset immediately after curl and again at cleanup entry. | No later App-log, stop, or result path uses it. |
| Test assertions | Success test requires exact curl argv and proves the fake token is absent from argv, stdout, and stderr; every fake CLI call requires secure storage. | The narrow P0 exception is executable and bounded. |
| Production boundary | App and wrapper identify phase `p0_smoke`; health remains `readiness: not_evaluated`. | No production or dbt readiness is claimed. |

A separate non-network negative probe set `DATABRICKS_AUTH_STORAGE=plaintext`; the wrapper returned exit code `2` with `Refusing non-secure Databricks authentication storage.` before command discovery or any CLI/authentication call.

## dbt boundary proof

- Runtime dependencies are FastAPI and Uvicorn only; the lock contains no dbt Core, dbt-databricks, dbt-common, adapter, or Databricks SDK.
- App runtime is only `uvicorn dbtobsb_app.main:app`; App code has no shell or subprocess execution path.
- Bundle contains one stopped-by-default unbound App and no Job, warehouse, cluster, schedule, secret, or data binding.
- Wrapper invokes Databricks CLI, `jq`, and `curl` only; it accepts no dbt command, selector, vars, flag, path, Git ref, SQL, Job ID, or workload parameter.
- App stdout contains one fixed `health_check` event, not a dbt JSON event.
- No manifest, run-results, source-freshness, dbt log, archive, node/test status, or capture object is read or produced.
- App lifecycle, authentication, inventory, HTTP response, and cleanup states are never mapped to native dbt outcomes.

The App shell's Python 3.11 runtime remains separate from the future candidate Python 3.12 dbt Job runtime.

## Local verification

```text
uv sync --project app --locked --extra dev
Resolved 31 packages; checked 30 packages

uv run --project app --extra dev pytest
12 passed in 3.45s

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

Tests use temporary fake `databricks` and `curl` executables. No real profile, token, network request, workspace, or compute was used.

## Findings

None.

## Final disposition

- Frozen implementation `8b1865c…`: **PASS**.
- Twelve tests and all static gates: **PASS**.
- P0 token exception: bounded, non-persistent, and dbt-neutral.
- New dbt findings or blockers: none.

