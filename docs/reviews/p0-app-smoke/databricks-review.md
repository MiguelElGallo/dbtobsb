# Final P0 App smoke candidate: Azure Databricks re-review

**Review date:** 2026-07-15  
**Reviewer lens:** Azure Databricks Apps, Declarative Automation Bundles, OAuth identity, deployment evidence, secret handling, and paid-compute cleanup  
**Verdict:** **PASS_WITH_FOLLOW_UP**  
**Blocking findings:** None  
**Cloud activity:** None. This review made no Databricks, Azure, authentication, or resource calls.

## Executive verdict

The final eight-file P0 App candidate is approved for the bounded live smoke exercise. All four findings from the prior Azure Databricks review are resolved:

1. cleanup submits an App stop request without first requiring a successful state read and performs bounded `STOPPED` readback;
2. curl disables ambient curlrc processing before accepting the OAuth bearer token;
3. the wrapper verifies zero live App resources both before start and after start; and
4. the OAuth U2M profile is bound to the exact expected workspace host and user before any mutation.

No new blocker was found. The App remains stopped by default, zero-binding, process-liveness-only, and compatible with the current Azure Databricks Apps Python and uv runtime. Every frozen local gate passed under the managed runtime's exact uv version.

The follow-ups in this report add more negative tests and supply-chain evidence. They do not block the single, attended P0 run because no current failure path can report success without a final observed `STOPPED` state.

## Frozen scope and hash proof

The reviewed implementation scope is exactly:

- `databricks.yml`
- `app/app.yaml`
- `app/pyproject.toml`
- `app/uv.lock`
- `app/dbtobsb_app/__init__.py`
- `app/dbtobsb_app/main.py`
- `app/tests/test_main.py`
- `scripts/smoke_databricks_app.sh`

The requested globally sorted path-and-content hash was reproduced before review:

```text
eff855524237e36909b282b5c030207b0478606e7f2b44a810082012d33f6a5c
```

Individual hashes:

| File | SHA-256 |
| --- | --- |
| `databricks.yml` | `d0f53887622010c27974fd9a1cf5ba708cedc404694e86361df825d417435b45` |
| `app/app.yaml` | `e08b266f4e0be736a260a53a5b2d22ebeae5a9c83f9479c916f0fc753111334c` |
| `app/pyproject.toml` | `90653dc48d2e01a81f66ec32735385be176e7df55a1d38c40821cee9b3e9c1fd` |
| `app/uv.lock` | `b7145c88938dcf34b2d88a2f18d54f362a7ca94f6709727ee2cc25801b05be5d` |
| `app/dbtobsb_app/__init__.py` | `4849b6ba1eb8a5a2c83293ff7be232ab01b66a9fdc0ee9c913b9bc8bf5d72bba` |
| `app/dbtobsb_app/main.py` | `63514752f4f3e4e4ccc3e4623b3bff13c8b999c64b6e720f0ba41beac48b90ab` |
| `app/tests/test_main.py` | `259852bd3dc5a58efd758a2c2c90ab4d171ce3a2aa545415681fca5f79db1f5b` |
| `scripts/smoke_databricks_app.sh` | `9bd90f4843eccf4c3c5fa5b0cc092e7983a5479de9e033454ceff37fb64a690a` |

Reproduction command:

```bash
printf '%s\n' \
  databricks.yml \
  app/app.yaml \
  app/pyproject.toml \
  app/uv.lock \
  app/dbtobsb_app/__init__.py \
  app/dbtobsb_app/main.py \
  app/tests/test_main.py \
  scripts/smoke_databricks_app.sh |
  LC_ALL=C sort |
  while IFS= read -r file; do shasum -a 256 "$file"; done |
  shasum -a 256
```

This report is outside the frozen scope. No implementation file was edited by this review.

## Prior finding disposition

| Prior finding | Disposition | Frozen-candidate evidence |
| --- | --- | --- |
| `DBX-SMOKE-001` — state-read failure could suppress STOP | **Resolved** | Cleanup lines 54-80 submit `databricks apps stop` unconditionally once `may_need_stop=1`. A successful stop is followed by a positive-integer-bounded readback loop. Zero exit requires observed `STOPPED`; otherwise the wrapper emits recovery commands and exits nonzero. The new test makes the first cleanup GET fail and proves STOP is still issued and subsequently verified. |
| `DBX-SMOKE-002` — ambient curlrc could expose the bearer token | **Resolved** | The invocation is `curl --disable --proto '=https' --tlsv1.2 --config -`; `--disable` is the first curl argument. The token remains in stdin configuration rather than argv and is unset immediately afterward. The success test verifies exact arguments and absence of the token from argv, stdout, and stderr. |
| `DBX-SMOKE-003` — zero bindings were not live-attested | **Resolved** | Post-deploy and post-start App JSON must both satisfy `(.resources // []) | length == 0`. Pre-start binding drift prevents `bundle run`; post-start drift triggers immediate cleanup. Failure copy does not print resource details. |
| `DBX-SMOKE-004` — profile was not bound to expected user | **Resolved** | `DBTOBSB_EXPECTED_USER` is mandatory. The wrapper extracts the verified top-level `.username` from `auth describe` and compares auth type, host, and user before `bundle validate`, `may_need_stop`, deploy, or run. A separate local negative probe confirmed a mismatch exits `2` before mutation. |

## Paid-compute and cleanup assessment

The cost-safety flow now has the correct ordering:

1. Validate tools, exact CLI version, OAuth U2M auth type, exact host, and exact user without mutation.
2. Validate the Bundle.
3. Arm cleanup before `bundle deploy` can create or reconcile the App.
4. Deploy the direct-engine declaration and require live `STOPPED` plus zero resources.
5. Explicitly run the App, require `ACTIVE`, require a Databricks Apps URL, and re-check zero resources.
6. Verify the exact process-liveness response and matching stdout event.
7. On success, error, `INT`, or `TERM`, issue the stop command and require independent `STOPPED` readback before returning zero.

The stop command itself waits up to 20 minutes. Successful stop then has a default maximum of ten read attempts with two-second delays. The attempt value is validated as a positive integer before any network operation. If STOP or its proof fails, output is explicit, the exit is nonzero, and copy-ready manual stop and state-check commands are emitted.

This is proportionate for an attended P0 exercise. As with any client-side cleanup, `SIGKILL`, machine loss, or a total control-plane outage cannot be solved by an EXIT trap; the operator must retain the printed recovery commands and independently confirm `STOPPED` before considering the exercise complete.

Azure Databricks documents that App compute is billable while running and not billable when stopped. See [Databricks Apps key concepts](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts) and the [Apps CLI command reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/apps-commands).

## Authentication and token assessment

The wrapper now provides a narrow personal-workspace auth boundary:

- named OAuth U2M profile only;
- ambient token and client-secret authentication rejected;
- ambient host, auth-type, and implicit-profile selectors removed;
- exact CLI-reported `databricks-cli` auth type required;
- exact expected host and user required before mutation;
- shell tracing rejected;
- short-lived token acquired only after the App is active and unbound;
- token supplied to curl over stdin rather than argv;
- default curl configuration disabled first;
- protocol constrained to HTTPS with TLS 1.2 or newer; and
- token variable cleared before contract and log checks.

Databricks CLI 1.7.0's `auth describe` verifies workspace credentials through the current-user API and returns the verified username in JSON. The pinned CLI's `auth token [PROFILE]` form is also valid. See [Authentication for the Databricks CLI](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication) and the [`auth` command reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands).

curl's documented requirement that `--disable` be the first argument is satisfied. See the [curl command-line manual](https://curl.se/docs/manpage.html).

## App and Bundle platform assessment

| Concern | Evidence | Assessment |
| --- | --- | --- |
| Deployment engine | `bundle.engine: direct` | Correct current engine; required for `lifecycle.started`. |
| Default cost state | `lifecycle.started: false` | App is created/reconciled stopped. |
| Declared access | No App `resources` field | Correct zero-binding P0 declaration, now backed by two live assertions. |
| CLI compatibility | Bundle accepts only 1.7.0 and wrapper requires exact `Databricks CLI v1.7.0` output | Semantically exact and consistent. |
| App runner | `bundle run dbtobsb_smoke` | Pinned CLI starts if needed, reconciles in-progress deployment state, creates a snapshot deployment, and waits for success. |
| Managed Python | `>=3.11,<3.12` | Compatible with current Apps Python 3.11. |
| Managed installer | Complete colocated `uv.lock` | Installs successfully with current Apps uv 0.10.2. |
| Runtime command | `uvicorn dbtobsb_app.main:app` | Valid because Apps sets `UVICORN_HOST=0.0.0.0` and `UVICORN_PORT`. |
| Logging | Fixed JSON event through a dedicated stdout handler | Compatible with App log collection and contains no sensitive fields. |
| Log timing | Event is queried before stop | Correct because App logs are not persisted after compute shutdown. |
| API claim | `process_liveness` with `readiness: not_evaluated` | Correctly avoids product, dbt, storage, or authorization readiness claims. |

Relevant primary references:

- [Migrate to the direct deployment engine](https://docs.databricks.com/aws/en/dev-tools/bundles/direct)
- [Bundle configuration reference](https://docs.databricks.com/aws/en/dev-tools/bundles/reference)
- [Deploy a Databricks app](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/deploy)
- [Databricks Apps environment](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/system-env)
- [Logging and monitoring for Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/monitor)
- [Add resources to a Databricks app](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources)
- [Databricks SDK Apps model](https://github.com/databricks/databricks-sdk-go/blob/main/service/apps/model.go)
- [Pinned CLI 1.7.0 App runner source](https://github.com/databricks/cli/blob/v1.7.0/bundle/run/app.go)
- [Pinned CLI 1.7.0 direct App resource source](https://github.com/databricks/cli/blob/v1.7.0/bundle/direct/dresources/app.go)

## Local verification

All verification was isolated and non-cloud.

The official uv 0.10.2 macOS arm64 release previously downloaded from Astral's GitHub release and verified against its adjacent SHA-256 file was used against a temporary copy of only the frozen files. This is the exact uv version documented for the current Databricks Apps runtime.

```text
uv 0.10.2 (a788db7e5 2026-02-10)

uv sync --frozen --extra dev
passed

uv run --frozen --extra dev pytest
10 passed in 3.73s

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

The ten repository tests include fake-CLI proofs for:

- exact health, root, OpenAPI, and logger contracts;
- stopped and unbound Bundle declaration;
- successful smoke plus final `STOPPED`;
- HTTP-health failure plus cleanup;
- a failed first cleanup read followed by unconditional STOP and successful bounded readback; and
- an unexpected live resource binding rejected before start and followed by cleanup.

An additional local probe changed the expected username while using the same fake OAuth response. It proved exit code `2`, the expected mismatch message, and no deploy, run, or stop mutation.

Read-only local help for the pinned CLI command surface and the public Databricks CLI `v1.7.0` source were also inspected. No CLI command in this review contacted a Databricks workspace.

## Follow-up hardening

These are non-blocking for the attended P0 run and should be completed before turning the wrapper into a reusable product installer or unattended CI control:

1. Add repository tests for an expected-user mismatch, a binding that appears only after start, an exhausted STOPPED-readback loop, and a stop-command failure.
2. Add a hostile temporary curlrc test that enables tracing and proves `--disable` prevents token capture; the implementation is already correct, but the regression deserves executable coverage.
3. Consider reading state even when the stop command returns nonzero and issuing a small bounded retry of the idempotent stop. The current path is safely nonzero and prints recovery commands, but additional reconciliation would reduce operator work during transient failures.
4. Cap `DBTOBSB_STOP_VERIFY_ATTEMPTS` at a documented upper bound, not only a positive lower bound, before unattended use.
5. During cleanup, consider ignoring a second `INT`/`TERM` until the stop/readback section completes; no shell wrapper can protect against `SIGKILL` or machine loss.
6. Verify the distributed Databricks CLI binary or container using an approved checksum/signature in the installation or CI path. Exact version output is compatibility, not binary provenance.
7. Persist the active deployment ID, terminal `SUCCEEDED` status, and snapshot identity in the evidence record without printing sensitive workspace paths in ordinary output.

## Live-run acceptance evidence

For the eventual attended run, retain sanitized evidence of:

- exact CLI version and successful Bundle validation;
- exact expected host and user match, without logging tokens or the full auth document;
- post-deploy `STOPPED` and zero resources;
- successful explicit App run and `ACTIVE` with zero resources;
- exact health response and matching App stdout event; and
- the final `STOP VERIFIED: App compute state is STOPPED.` line.

Treat any nonzero wrapper exit as incomplete cleanup until the printed manual state command independently returns `STOPPED`. Do not leave the App running after evidence capture.

## Conclusion

The exact `eff85552…` P0 App candidate passes the Azure Databricks re-review with follow-up hardening. The four prior blockers are resolved, no new blocker was found, and exact-runtime local validation is green. It is approved for one bounded, attended live smoke run using the expected OAuth U2M user and host, provided the operator remains present through the final independently observed `STOPPED` confirmation.
