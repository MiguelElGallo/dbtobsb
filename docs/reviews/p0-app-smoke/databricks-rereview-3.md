# Azure Databricks third final re-review: P0 App smoke implementation

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform reviewer
- Eight-file implementation SHA-256: `8b1865cd05ba5abbeef6634d80e01778affe5b03ee76cbdfe919be3d84355101`
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud activity: None. This review made no Azure, Databricks authentication, App, Job, warehouse, cluster, or Unity Catalog call.

## Immutable input verification

The scope remains exactly `databricks.yml`, `app/app.yaml`, `app/pyproject.toml`, `app/uv.lock`, `app/dbtobsb_app/__init__.py`, `app/dbtobsb_app/main.py`, `app/tests/test_main.py`, and `scripts/smoke_databricks_app.sh`. I recomputed the path-ordered aggregate and matched `8b1865cd...` exactly. No implementation file was edited by this reviewer.

## Secure-storage change

The new guard is correct and safely ordered:

```text
reject shell tracing
  -> require inputs
  -> reject ambient token/client secret
  -> reject inherited non-empty storage value other than secure
  -> export DATABRICKS_AUTH_STORAGE=secure
  -> tool/version/auth/inventory checks
  -> Bundle validate
  -> arm cleanup
  -> deploy/run
```

Current CLI documentation states that the environment storage setting takes precedence over profile configuration. A profile with only a plaintext token cache therefore fails when this wrapper forces the secure backend; the wrapper neither migrates nor copies that credential. Secure mode also remains exported for cleanup calls.

The rejection occurs before `may_need_stop` is armed and before the first CLI command. A local negative probe with `DATABRICKS_AUTH_STORAGE=plaintext` exited `2` with `Refusing non-secure Databricks authentication storage.` The fake CLI independently exits unless every invocation receives `secure`, so the normal success and failure tests exercise propagation across auth, inventory, deploy/run, logs, and stop.

## Token exception and prior safeguards

The P0 wrapper still needs one short-lived access token to call the token-protected App health URL. The exception is now accurately documented; the implementation itself did not weaken:

- tracing and ambient token/client-secret authentication are rejected;
- token acquisition occurs only after exact `ACTIVE`, `MEDIUM`, Databricks Apps URL, and zero-binding readback;
- the bearer header enters curl through stdin configuration, not argv;
- ambient curl configuration is disabled and TLS/HTTPS are required;
- the token is cleared before response parsing and again in cleanup; and
- tests prove the test token is absent from curl argv, stdout, and stderr.

No regression was found in exact U2M auth type/host/user checks, fully iterated caller-visible App/warehouse/cluster inventory, stopped-by-default Direct Bundle lifecycle, live Medium/resource-binding checks, process-liveness-only HTTP/OpenAPI/log contract, or unconditional stop/readback cleanup.

## Local verification

```text
uv sync --project app --locked --extra dev
Resolved 31 packages; checked 30 packages

uv run --project app --extra dev pytest
12 passed in 3.56s

ruff check / format check / ty check
passed

bash -n / shellcheck
passed

inherited plaintext-storage negative probe
exit 2 before any CLI call
```

## Retained product-installer follow-ups

The prior non-blocking follow-ups remain unchanged:

- `DBX-SMOKE-F05` (Medium, P3): bind App/Direct ownership before adopting or stopping a pre-existing same-name object; name alone cannot authorize customer-compute mutation.
- `DBX-SMOKE-F06` (Low, P3/P8): bind future evidence to non-sensitive implementation, plan, deployment, and reconciliation digests.
- `DBX-SMOKE-F07` (Low, P3): cap the stop-readback override, define second-signal behavior, and test stop-command failure/exhausted readback before unattended reuse.

These remain outside the one-operator, dedicated-workspace P0 acceptance boundary and block only generalizing this wrapper into the reusable installer.

## Sources checked

- [Databricks CLI token storage](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication#token-storage)
- [Databricks CLI stored-credentials behavior](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting#stored-credentials-error)
- [`databricks auth token`](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands#databricks-auth-token)
- [Pinned Apps list implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/workspace/apps/apps.go#L1222-L1269)
- [Pinned JSON iterator renderer](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/libs/cmdio/render.go#L87-L140)
- [Azure Databricks App status](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status)

## Verdict

`PASS_WITH_FOLLOW_UP`

The exact `8b1865cd...` implementation is approved for the frozen attended P0 smoke. Secure storage is forced before every CLI call, inherited non-secure storage fails before mutation, the development token exception remains tightly contained, all twelve tests and local gates pass, and no prior App, inventory, identity, cost, or cleanup safeguard regressed. The retained F05-F07 items remain prerequisites for a reusable P3 installer.
