# Stop or uninstall dbtobsb

Run lifecycle commands from the same checkout and macOS account that installed the
product. The local protected state tells the launcher which resources belong to
this installation.

## Stop compute

Stopping is the safe default. It preserves the App, Jobs, configuration, grants,
tables, views, Volumes, and evidence.

```console
uv run --project installer --no-sync dbtobsb stop
```

Expected output:

```json
{"app_state":"STOPPED","event":"dbtobsb_stop_verified","reconciler_state":"PAUSED"}
```

The command does not delete or resize a customer warehouse. Its configured
auto-stop policy remains in effect.

## Remove the runtime but keep evidence

Use retain when policy requires the normalized rows or raw archives to remain:

```console
uv run --project installer --no-sync dbtobsb uninstall --retain
```

Read the consequence shown by the installer. Type `RETAIN` only after confirming
that the nine evidence objects must remain.

This removes the App, all three Jobs, product grants, bindings, Bundle state, and
local installer state. It keeps all nine product objects in the selected schema
under the existing administrator's ownership.

## Delete product evidence

!!! danger "This deletes tables, views, and raw archives"

    Continue only after an authorized owner checks retention, legal hold, and
    required exports. The command preserves the selected schema and unrelated
    objects, but the deleted dbtobsb evidence cannot be restored by this release.

```console
uv run --project installer --no-sync dbtobsb uninstall --delete
```

Read each prompt when it appears. Type `DELETE`, review the retention, legal-hold,
and export warning, and only then type `DELETE PRODUCT DATA`. Do not pipe or prequeue
these acknowledgements.

Both uninstall modes print a `dbtobsb_uninstall_verified` receipt. If the command
is interrupted, rerun the same mode. Do not switch between retain and delete during
an unfinished uninstall.

## Verify the final state

Use the installation's named profile. These checks name only dbtobsb resources;
they do not treat unrelated workspace resources as product compute.

After `stop`, check the App:

```console
databricks apps get dbtobsb-smoke --profile '<profile>' --output json \
  | jq -r '.compute_status.state'
```

The value must be `STOPPED`.

Check that each product Job exists and has no active run:

```console
for name in dbtobsb-observed dbtobsb-collector dbtobsb-reconciler; do
  job_id="$(databricks jobs list --name "$name" --profile '<profile>' --output json \
    | jq -er 'if length == 1 then .[0].job_id else error("expected one job") end')"
  databricks jobs list-runs --job-id "$job_id" --active-only \
    --profile '<profile>' --output json
done
```

Each active-run result must be an empty list. Then check the reconciler schedule:

```console
reconciler_id="$(databricks jobs list --name dbtobsb-reconciler \
  --profile '<profile>' --output json | jq -er '.[0].job_id')"
databricks jobs get "$reconciler_id" --profile '<profile>' --output json \
  | jq -r '.settings.schedule.pause_status'
```

The value must be `PAUSED`.

After either uninstall mode, `databricks apps get dbtobsb-smoke` must report that
the App does not exist, and each exact-name Job query must return an empty list:

```console
databricks apps get dbtobsb-smoke --profile '<profile>' --output json
for name in dbtobsb-observed dbtobsb-collector dbtobsb-reconciler; do
  databricks jobs list --name "$name" --profile '<profile>' --output json
done
```

If you used `--delete`, an evidence-schema owner must also confirm that the nine
dbtobsb tables, views, and Volumes are absent. If you used `--retain`, those nine
objects must remain under the existing administrator's ownership.

Stop only the exact customer warehouse when policy authorizes it. Never delete or
change unrelated Jobs, clusters, warehouses, catalogs, or schemas to make a broad
inventory look empty.
