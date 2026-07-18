# Historical v0.2 first-capture tutorial

> This page records the earlier maintainer-operated v0.2 preview and its command shape. Do not use it to install v0.3. Start with [Wire a supported dbt Job](../how-to/wire-a-dbt-job.md) and the [v0.3 supported-release contract](../../releases/v0.3.0-support-contract.md).

In this tutorial you deploy the private preview, create its fixed evidence objects, run the synthetic weather project, and query the result. The App stays stopped.

The example assumes a non-production customer Azure Databricks workspace. It does
not support Databricks Free Edition, the retired Community Edition, AWS, or GCP.
Use synthetic data only.

## Before you start

You need:

- Databricks CLI `1.7.0` and an OAuth U2M profile;
- a pre-existing Unity Catalog catalog in which you can create a schema;
- serverless Jobs access;
- an existing SQL warehouse ID for the dbt task; and
- `uv` for local builds and checks.

The bootstrap does not create a catalog. In a serverless workspace that uses Databricks Default Storage, create the catalog through Catalog Explorer or serverless SQL first. [Default Storage requires serverless compute](https://learn.microsoft.com/en-us/azure/databricks/storage/default-storage).

Choose these local placeholders:

```text
<profile>          OAuth profile for the intended workspace
<warehouse-id>     existing SQL warehouse used only by dbt
<catalog>          pre-existing Unity Catalog catalog
<evidence-schema>  dedicated evidence schema, for example dbtobsb
<demo-schema>      dedicated synthetic model schema, for example dbtobsb_demo
```

## 1. Validate the source

```bash
uv sync --project capture --locked
uv run --project capture pytest capture/tests

uv sync --project collector --locked
uv run --project collector pytest collector/tests
```

Both suites must pass before a live deployment.

## 2. Validate and deploy the Bundle

```bash
databricks bundle validate -t smoke -p '<profile>' \
  --var 'warehouse_id=<warehouse-id>,evidence_catalog=<catalog>,evidence_schema=<evidence-schema>,demo_schema=<demo-schema>,raw_volume_name=dbtobsb_raw'

databricks bundle deploy -t smoke -p '<profile>' \
  --var 'warehouse_id=<warehouse-id>,evidence_catalog=<catalog>,evidence_schema=<evidence-schema>,demo_schema=<demo-schema>,raw_volume_name=dbtobsb_raw'
```

Deployment creates three unscheduled Jobs and keeps `dbtobsb-smoke` stopped. It does not run dbt or start App compute.

## 3. Run the fixed bootstrap

Assign one cleanup owner before continuing and keep [Stop compute and remove the
preview](../how-to/cleanup.md) open. The bootstrap and collector use billable
serverless Job compute while their runs are active. The dbt task and the queries
below use the selected SQL warehouse and can also incur compute cost. The cleanup
owner stays available through the final zero-running-compute readback and records
whether the retained evidence will be kept or deleted.

```bash
databricks bundle run dbtobsb_bootstrap -t smoke -p '<profile>' \
  --var 'warehouse_id=<warehouse-id>,evidence_catalog=<catalog>,evidence_schema=<evidence-schema>,demo_schema=<demo-schema>,raw_volume_name=dbtobsb_raw'
```

The successful task prints a single safe event:

```json
{"event":"dbtobsb_bootstrap_verified","manifest_version":"dbtobsb.evidence.v0.2.0-alpha.1","object_count":5}
```

The bootstrap may create these product objects in a production destination when an authorized administrator intentionally chooses one. That is valid. It is an attended, fixed, versioned DDL operation—not steady-state collection. Optionally run it again to test idempotency; that extra serverless Job run incurs additional compute usage.

## 4. Run the observed dbt build

```bash
databricks bundle run dbtobsb_demo -t smoke -p '<profile>' \
  --var 'warehouse_id=<warehouse-id>,evidence_catalog=<catalog>,evidence_schema=<evidence-schema>,demo_schema=<demo-schema>,raw_volume_name=dbtobsb_raw'
```

The Job first runs the fixed dbt command. Its `ALL_DONE` edge then passes native dynamic references to the separately defined collector Job. You do not enter a Job ID, run ID, task-run ID, selector, log path, or SQL statement.

A complete collector prints:

```json
{"capture_state":"COMPLETE","event":"dbtobsb_collection_published","node_count":9,"pair_state":"PAIR_VALID","retrieval_state":"RETRIEVED"}
```

## 5. Query the read views

Run this read-only query in Databricks SQL, replacing the two identifiers:

```sql
SELECT
  task_start_time,
  lakeflow_result_state,
  retrieval_state,
  capture_state,
  pair_state,
  issue_code,
  dbt_version,
  command,
  result_count,
  status_counts_json
FROM `<catalog>`.`<evidence-schema>`.`dbt_run_health`
ORDER BY task_start_time DESC;
```

Then summarize node evidence:

```sql
SELECT
  resource_type,
  status,
  COUNT(*) AS node_count,
  ROUND(SUM(execution_time), 3) AS execution_seconds
FROM `<catalog>`.`<evidence-schema>`.`dbt_node_health`
GROUP BY resource_type, status
ORDER BY resource_type, status;
```

`COMPLETE` and `PAIR_VALID` describe evidence quality. `lakeflow_result_state` and native node statuses describe execution outcome. Do not collapse them into one success flag.

## 6. Finish safely

Follow [Stop compute and remove the preview](../how-to/cleanup.md). At minimum, prove zero active runs, no test warehouse, no cluster, and stopped App compute.

The verified output from a real run is in [the live evidence page](../../evidence/p2-live-capture-2026-07-16.md).
