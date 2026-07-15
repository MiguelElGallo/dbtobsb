# Azure Databricks final re-review: P0 App smoke implementation

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform reviewer
- Eight-file implementation SHA-256: `3dfdce3c354b858a252904190ccbca7689d10fe883a818910c897acb9dcd3866`
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud activity: None. This review made no Azure, Databricks, authentication, App, Job, warehouse, cluster, or Unity Catalog call.

## Immutable input verification

The reviewed implementation scope was exactly:

- `databricks.yml`
- `app/app.yaml`
- `app/pyproject.toml`
- `app/uv.lock`
- `app/dbtobsb_app/__init__.py`
- `app/dbtobsb_app/main.py`
- `app/tests/test_main.py`
- `scripts/smoke_databricks_app.sh`

I globally sorted those paths, hashed each file, and hashed the resulting path-ordered records. The aggregate matched exactly:

```text
3dfdce3c354b858a252904190ccbca7689d10fe883a818910c897acb9dcd3866
```

No implementation, author, or evidence file was changed by this reviewer. This report is outside the frozen scope.

## Executive assessment

The implementation passes the bounded P0 App-smoke acceptance criteria. The Bundle is stopped by default and unbound; the FastAPI endpoint claims process liveness only; OAuth identity and token handling are fail-closed for the intended attended U2M route; the wrapper reads back `MEDIUM` before and after start; and every armed exit path attempts App stop and requires `STOPPED` before returning success.

No current finding blocks the already completed one-App personal-workspace smoke. The follow-ups below are product-installer hardening for P3, not missing safeguards for this frozen, attended P0 proof.

## Compute size and cost boundary

The final compute-size change is correct and testable:

- `EXPECTED_COMPUTE_SIZE` is fixed to the Apps API enum `MEDIUM`.
- After Bundle deploy and before any App run, the wrapper requires both `compute_status.state == STOPPED` and `compute_size == MEDIUM`.
- After the App runner completes, the wrapper requires `compute_status.state == ACTIVE`, `compute_size == MEDIUM`, and a Databricks Apps HTTPS URL.
- A size mismatch exits nonzero and reaches the stop cleanup before any health request.
- The local negative test supplies `LARGE`, proves the App is never run, and proves cleanup returns the fake resource to `STOPPED`.

Current official Azure Databricks documentation publishes Medium as the default size at 0.5 DBU/hour. Runtime readback is still necessary because a pre-existing App can be edited or drifted independently of an omitted/default declaration.

The script itself correctly refuses to call a successful stop request “cost stopped”: success requires a later `STOPPED` readback. Documentation baseline 0.18 separately records the attended cancellation deadline, planned usage, bounded successful-stop exposure, and unbounded failed-stop tail.

## App, Bundle, and resource safety

| Control | Frozen implementation evidence | Assessment |
|---|---|---|
| Deployment engine | `bundle.engine: direct` | Correct current engine for the App lifecycle field. |
| CLI compatibility | Bundle accepts only 1.7.0 and wrapper requires exact `Databricks CLI v1.7.0` output | Exact, fail-closed compatibility boundary. |
| Default lifecycle | `lifecycle.started: false` | Bundle create/update does not intentionally leave compute running. |
| Declared resources | No App `resources` block | P0 requests no warehouse, Job, secret, Volume, serving, or UC binding. |
| Live resource check | Both stopped and active App readbacks require `(.resources // []) | length == 0` | Remote binding drift blocks or stops the smoke. |
| Runtime command | `uvicorn dbtobsb_app.main:app` | Compatible with Apps-provided `UVICORN_HOST` and `UVICORN_PORT`. |
| Runtime persistence | Health state is process-local and non-authoritative | No product state is incorrectly kept on ephemeral App disk/memory. |
| Log event | Fixed JSON `health_check` event on stdout, queried before stop | Appropriate non-sensitive P0 evidence. |

The root and OpenAPI routes contain only non-sensitive shell metadata. Interactive Swagger/ReDoc routes are disabled, avoiding public CDN/runtime asset dependencies. `/api/health` explicitly reports `readiness: not_evaluated` and does not imply dbt, storage, authorization, capture, or product readiness.

## Identity and bearer-token safety

The attended personal-workspace path has the expected protections:

1. shell tracing is rejected before any token operation;
2. ambient `DATABRICKS_TOKEN` and `DATABRICKS_CLIENT_SECRET` are rejected;
3. ambient host, auth-type, and implicit-profile selectors are removed;
4. an explicit named profile must report OAuth U2M auth type `databricks-cli`, the exact expected canonical host, and the exact expected user before mutation;
5. the token is requested only after the App is active, Medium, and unbound;
6. curl receives the bearer header through stdin configuration rather than argv;
7. `--disable` is curl's first argument, preventing ambient curlrc behavior, and HTTPS/TLS 1.2 or newer is required;
8. the token variable is cleared before response parsing and is also cleared in cleanup; and
9. tests prove the token is absent from curl argv, stdout, and stderr.

The token is used only for the token-authenticated `/api/health` call. No credential is written to the Bundle, App environment, log event, repository, or evidence file.

## Cleanup safety

Cleanup is armed before `bundle deploy`, so a partial remote response cannot bypass the exit path. Once armed, cleanup:

- issues the idempotent App stop even if a preliminary state read would fail;
- waits up to the CLI stop timeout;
- performs a positive-integer-bounded independent readback loop;
- accepts only exact `STOPPED`;
- turns an otherwise successful command into failure when stop cannot be verified;
- prints quoted manual stop and state-read commands on cleanup failure; and
- runs on normal exit, error, `INT`, and `TERM`.

The tests prove successful cleanup, cleanup after HTTP failure, cleanup despite the first cleanup GET failing, and cleanup when an unexpected live binding or compute size is detected. No wrapper path can return zero after it has armed cleanup without an observed `STOPPED` state.

As with any client-side trap, `SIGKILL`, workstation loss, or a total control-plane outage cannot supply a mechanical hard cost ceiling. Baseline 0.18 now states that limit explicitly and requires an attended owner and independent final inventory.

## Local verification

All checks were local and non-cloud:

```text
uv sync --project app --locked --extra dev
resolved 31 packages; checked 30 packages

uv run --project app --extra dev pytest
11 passed in 3.44s

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

## Non-blocking product hardening

These items do not block the zero-App-baseline, attended P0 proof. They belong before the smoke wrapper becomes a reusable or unattended installer:

### DBX-SMOKE-F05: attest ownership before stopping a fixed-name pre-existing App

- Severity: Medium
- Target: P3 installer
- Evidence: Cleanup intentionally arms before deploy and always stops the fixed `dbtobsb-smoke` name. In the completed P0 workspace the preflight proved zero Apps, so this was safe. A future reusable run should not assume a same-name object belongs to this Bundle after a failed create/adoption attempt.
- Acceptance: Bind the scoped before inventory, Direct lineage/state, App identity, and intended ownership before mutation. If a foreign same-name App exists, fail before arming a stop against it. Never stop unrelated customer compute.

### DBX-SMOKE-F06: bind future evidence to non-sensitive source and deployment identities

- Severity: Low
- Target: P3/P8 evidence
- Evidence: The current repository record describes the run but does not retain the eight-file aggregate, Bundle plan digest, selected terminal snapshot/deployment digest, or a sanitized invocation record.
- Acceptance: Future evidence should retain non-secret source/config/plan hashes and a sanitized deployment reconciliation digest, while continuing to exclude host, account/workspace/user/App/SP IDs, tokens, signed URLs, raw logs, and customer data.

### DBX-SMOKE-F07: harden unattended signal and override behavior

- Severity: Low
- Target: P3 installer
- Evidence: `DBTOBSB_STOP_VERIFY_ATTEMPTS` has a positive lower bound but no maximum, and cleanup restores default `INT`/`TERM` handling while it performs the critical stop.
- Acceptance: Cap the retry override, define behavior for a second termination signal, and add stop-command-failure plus exhausted-readback tests. Continue to state that `SIGKILL` and machine loss require external recovery.

## Sources checked

- [Databricks Apps compute sizes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size)
- [Databricks Apps status](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status)
- [Databricks Apps environment](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/system-env)
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial)
- [Apps CLI commands](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/apps-commands)
- [App resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources)

## Verdict

`PASS_WITH_FOLLOW_UP`

The exact `3dfdce3c...` implementation is approved as a stopped-by-default, unbound, Medium-only, process-liveness P0 smoke. The frozen local gates pass, the prior cost/token/identity/resource/cleanup safeguards remain effective, and no platform blocker remains. The three follow-ups are explicitly deferred product-installer hardening and do not justify another paid P0 run.
