# Stop compute and uninstall

Use the lifecycle launcher from the same private checkout and macOS account that performed installation. It reads the protected installation state, pauses the reconciler, terminates active product Job runs, stops the App, and verifies the requested final state.

## Stop without removing data or configuration

`stop` is the safe default. It preserves all nine Unity Catalog objects, raw archives, Jobs, App bindings, grants, and installer state:

```console
uv run --project installer --no-sync dbtobsb stop
```

A successful stop can print this when the selected warehouse is already stopped:

```json
{"app_state":"STOPPED","event":"dbtobsb_stop_verified","reconciler_state":"PAUSED","warehouse_auto_stop_mins":5,"warehouse_cost_may_continue":false,"warehouse_managed_by_product":false,"warehouse_next_action":"NONE","warehouse_state":"STOPPED"}
```

The launcher does not stop or delete the selected customer SQL warehouse. Its Databricks auto-stop policy remains authoritative. When that unrelated warehouse is still running, the receipt instead reports `"warehouse_cost_may_continue":true`, `"warehouse_state":"RUNNING"`, and `"warehouse_next_action":"WAIT_FOR_AUTO_STOP_OR_USE_SEPARATELY_AUTHORIZED_DIRECT_STOP"`. Wait for auto-stop or use only a separately authorized direct stop for that exact dedicated warehouse.

## Retain evidence and remove the product runtime

Use retain when audit, incident, legal-hold, or customer retention policy requires the normalized evidence or raw archives:

```console
uv run --project installer --no-sync dbtobsb uninstall --retain
```

Read the consequence and type `RETAIN` interactively only after confirming the
retention decision. Do not pipe or prequeue the acknowledgement.

This removes the App, all three Jobs, Bundle state, product grants, bindings, and local installer state. It preserves the selected schema and all nine product objects under the existing combined-administrator owner.

## Delete product evidence

Delete only after an authorized owner confirms retention, legal hold, and required exports. This action removes the exact seven relational objects and two managed Volumes, including raw archives, but preserves the selected schema and unrelated objects:

```console
uv run --project installer --no-sync dbtobsb uninstall --delete
```

Read each warning when it appears. Type `DELETE`, then separately type
`DELETE PRODUCT DATA` only after confirming retention, legal hold, and required
exports. Do not pipe or prequeue either acknowledgement.

Both uninstall modes finish with a machine-readable `dbtobsb_uninstall_verified` receipt. If a command is interrupted, rerun the same mode; switching modes during an unfinished uninstall is rejected.

## Verify cost-bearing resources

After stop or uninstall, verify the resources from the receipt rather than changing unrelated workspace state:

```console
databricks jobs list-runs --active-only -p '<profile>' -o json
databricks warehouses get '<warehouse-id>' -p '<profile>' -o json
databricks clusters list -p '<profile>' -o json
```

For stop, `databricks apps get dbtobsb-smoke` must report `STOPPED`. For uninstall, the App and three product Jobs must be absent. The selected warehouse should be `STOPPED` after its configured auto-stop interval; if it is still running, stop that exact warehouse only when customer policy authorizes it. Serverless Job compute has no persistent cluster to delete.

Never delete a shared warehouse, catalog, schema, cluster, Job, or App merely to make a broad inventory empty. A failed or ambiguous lifecycle command is a recovery condition, not permission to remove unrelated resources manually.
