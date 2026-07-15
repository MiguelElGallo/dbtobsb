# Azure Databricks second final re-review: P0 App smoke implementation

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform reviewer
- Eight-file implementation SHA-256: `0ad64adf3071944adddf501120713bb07c0e19d43e360a901d17dbe6bf7fa437`
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
0ad64adf3071944adddf501120713bb07c0e19d43e360a901d17dbe6bf7fa437
```

No implementation, author, evidence, or template file was edited by this reviewer. This report is outside the frozen scope.

## Executive assessment

The new inventory preflight is correctly positioned before Bundle validation, deployment, and cleanup arming. It accepts only an empty observable workspace or one exact stopped, unbound, Medium `dbtobsb-smoke` App, plus zero visible warehouses and clusters. Any list/API/JSON/policy failure exits before mutation and before the wrapper can stop an App.

The prior stopped-by-default Bundle, live-size/binding readbacks, U2M identity checks, bearer-token protections, process-liveness-only API, and unconditional stop verification remain intact. The implementation is acceptable for the documented attended P0 dedicated-workspace route.

## Pinned CLI list semantics

I checked the exact Databricks CLI `v1.7.0` tag, which resolves to commit `2f68ee4951ef96fa9d99e40c8ebadccf08412d58`, rather than inferring behavior from a newer installed CLI.

The generated `apps list`, `warehouses list`, and `clusters list` commands all:

1. construct their SDK pagination iterator;
2. leave the total-result `--limit` at zero in this wrapper;
3. pass the iterator to `cmdio.RenderIterator`; and
4. under `-o json`, iterate `HasNext`/`Next` until exhaustion and render one JSON array.

Therefore, these invocations do not silently inspect only the first API page. A later-page error returns nonzero; with `set -e`, the command substitution aborts before `may_need_stop=1` or any Bundle command.

The pinned SDK `App` model includes `compute_size`, `compute_status`, and `resources`, so the preflight can evaluate the optional target's exact stopped/Medium/unbound state from the list output. Warehouses are limited to those accessible to the caller, and cluster-list semantics are the API's visible pinned/active/recent set. The implementation does not claim those APIs create omniscience: baseline 0.19 makes approved complete caller visibility and a dedicated workspace explicit P0 prerequisites and rejects partially visible workspaces.

## Pre-mutation safety

The wrapper's order is safe:

```text
tool/version checks
  -> exact named U2M profile, host, and user
  -> Apps/warehouses/clusters inventory and JSON policy
  -> Bundle validate
  -> arm stop cleanup
  -> Bundle deploy/run
```

At the inventory stage, `may_need_stop` is still zero. Consequently:

- an unrelated App produces exit `2` before validate/deploy/run and without `apps stop`;
- any visible warehouse or cluster produces exit `2` at the same boundary;
- a target App that is active, not Medium, bound, duplicated, or structurally incomplete fails the `jq -e` policy;
- denied, malformed, interrupted, or pagination-failed list output cannot become a clean result; and
- no cleanup trap mutates a pre-existing object merely because preflight failed.

The new negative test proves the unrelated-App path and its no-mutation command ordering. The warehouse/cluster checks are direct zero-length JSON predicates; the target-App predicate is exact and fail-closed.

## Prior App, identity, token, and cleanup safeguards

No regression was found:

| Control | Frozen behavior |
|---|---|
| Default App lifecycle | Direct Bundle declares `lifecycle.started: false`. |
| Resource boundary | No App resources are declared; stopped and active live readbacks both require zero bindings. |
| Compute boundary | Both stopped and active readbacks require exact `MEDIUM`; a mismatch stops and fails. |
| Authentication | Exact CLI, explicit profile, U2M auth type, canonical host, and exact user are required; ambient token/client-secret auth is rejected. |
| Bearer handling | Shell tracing is rejected; token is obtained only after safe live readback, passed to curl via stdin config, never argv, and cleared before parsing/cleanup. |
| Health claim | Exact response proves process liveness only; stdout event is fixed and non-sensitive; Swagger/ReDoc CDN surfaces remain disabled. |
| Cleanup arming | Armed immediately before deploy, so partial deploy responses reach stop; never armed for a failed inventory. |
| Stop proof | Stop command plus bounded independent readback must observe exact `STOPPED`; unverified cleanup makes success fail and prints quoted recovery commands. |

## Local verification

All checks were local and non-cloud, using the README commands:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages; checked 30 packages

uv run --project app --extra dev pytest
12 passed in 3.81s

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

The twelve tests cover the HTTP/OpenAPI/logging contracts, disabled interactive docs, stopped/unbound Bundle declaration, success cleanup, health-failure cleanup, cleanup after a failed read, live-binding rejection, compute-size rejection, and the new unrelated-workspace pre-mutation rejection.

## Follow-ups retained for the reusable installer

The new clean-workspace guard narrows risk but does not turn the P0 wrapper into a general installer. The prior hardening findings remain applicable:

### DBX-SMOKE-F05: bind same-name ownership before adopting or stopping

- Severity: Medium
- Target: P3 installer
- Current P0 boundary: A dedicated approved workspace may contain the residual stopped, unbound, Medium P0 App from the earlier smoke.
- Remaining product requirement: Before reusable or unattended operation, bind scoped before inventory, App identity, Direct lineage/state, and intended ownership. A foreign same-name App must fail before cleanup is armed; name alone must never authorize stopping customer compute.

### DBX-SMOKE-F06: bind future evidence to deployment identities

- Severity: Low
- Target: P3/P8 evidence
- Requirement: Retain non-sensitive implementation, plan, deployment, and final reconciliation digests while continuing to exclude host/account/workspace/user/App/SP IDs, credentials, signed URLs, raw logs, and customer data.

### DBX-SMOKE-F07: harden unattended termination behavior

- Severity: Low
- Target: P3 installer
- Requirement: Cap the stop-readback override, define second-signal behavior, and add explicit stop-command-failure and exhausted-readback tests. Continue to disclose that `SIGKILL`, workstation loss, and control-plane outage require external attended recovery.

These are not blockers for the documented one-operator, dedicated-workspace P0 proof. They are blockers to broadening this wrapper into a reusable installer.

## Sources checked

- [Databricks CLI `v1.7.0` Apps list implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/workspace/apps/apps.go#L1222-L1269)
- [Databricks CLI `v1.7.0` warehouses list implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/workspace/warehouses/warehouses.go#L892-L940)
- [Databricks CLI `v1.7.0` clusters list implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/workspace/clusters/clusters.go#L973-L1024)
- [Databricks CLI JSON iterator renderer](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/libs/cmdio/render.go#L87-L140)
- [Pinned SDK App model](https://github.com/databricks/databricks-sdk-go/blob/v0.154.0/service/apps/model.go#L14-L90)
- [Azure Databricks App compute sizes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size)
- [Azure Databricks App status](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status)
- [Databricks CLI Apps commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/apps-commands)
- [Databricks CLI warehouses commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/warehouses-commands)
- [Databricks CLI clusters commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/clusters-commands)

## Verdict

`PASS_WITH_FOLLOW_UP`

The exact `0ad64adf...` implementation is approved for the frozen attended P0 smoke. The new pre-mutation inventory is fully paginated within the caller's approved visibility, fail-closed, and positioned so failure cannot stop or deploy anything. All twelve tests and every local quality gate pass, and the prior App, identity, token, resource, compute-size, and cleanup safeguards did not regress. The retained follow-ups must be resolved before this wrapper is generalized into the P3 product installer.
