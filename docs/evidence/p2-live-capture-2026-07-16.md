# P2 live Azure Databricks capture — 16 July 2026

This is a sanitized record of the first complete SQL-first dbtobsb capture. Workspace, user, Job, run, task, warehouse, and full Volume identifiers are intentionally omitted.

## Scope

The proof used:

- one personal Azure Databricks workspace;
- a disposable Unity Catalog catalog backed by Databricks Default Storage;
- serverless Jobs for bootstrap and collection;
- temporary serverless SQL warehouses only while dbt and final evidence queries ran;
- dbt Core `1.11.12` and dbt-databricks `1.12.2`;
- synthetic weather data only; and
- Databricks CLI `1.7.0` with OAuth U2M.

This proves one personal/test topology. It is not production or regulated qualification.

## Bootstrap evidence

The fixed `BOOTSTRAP_ALLOWED` Job completed twice. Both runs reported object manifest `dbtobsb.evidence.v0.2.0-alpha.1` and five verified table/view objects. Live inventory showed:

```text
managed Delta tables:  dbt_artifact_registry
                       dbt_invocations
                       dbt_node_results
views:                 dbt_run_health
                       dbt_node_health
managed Volume:        dbtobsb_raw
```

The second run did not replace the objects, proving the fixed create-and-verify path was idempotent in this topology.

## Two changed-seed dbt runs

After the first run, the synthetic seed changed by adding one Turku observation. The final checked-in seed contains seven observations. The project then built:

- `stg_weather`;
- `daily_weather_summary`; and
- `weather_alerts`.

The build also ran one seed and five tests, for nine result nodes total.

The exact live dbt arguments were:

```text
which=build
selector=observability_demo
select=[]
exclude=[]
indirect_selection=eager
full_refresh=null
```

The manifest and run-results invocation IDs were equal. The dbt file log attested log version `3`, dbt `1.11.12`, adapter `databricks`, and adapter version `1.12.2`.

## Native archive

The successful archive contained 24 members. Its relevant paths were:

```text
target/manifest.json
target/run_results.json
target/semantic_manifest.json
logs/dbtobsb-primary/dbt.log
```

The collector preserved the exact 246,386-byte archive before parsing. Its SHA-256 begins `dcc00d8fffaf6c7`. The full digest and raw Volume locator remain in the restricted customer-local registry.

## Published run evidence

The sanitized `dbt_run_health` result was:

| Run | Lakeflow result | Retrieval | Capture | Pair | Issue | dbt | Command | Results | Status counts |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| Initial transport attempt | `SUCCESS` | `UNAVAILABLE` | `ARCHIVE_UNAVAILABLE` | null | `DBT_ARCHIVE_LINK_NOT_HTTPS` | null | null | null | null |
| Changed-seed capture | `SUCCESS` | `RETRIEVED` | `COMPLETE` | `PAIR_VALID` | null | `1.11.12` | `build` | 9 | `{"pass":5,"success":4}` |

The first row is retained because capture failure is evidence; it is not rewritten as success or deleted from the user-facing history.

## Published node evidence

| Resource type | Native status | Nodes | Total execution seconds |
| --- | --- | ---: | ---: |
| model | `success` | 3 | 3.739 |
| seed | `success` | 1 | 3.948 |
| test | `pass` | 5 | 5.957 |

The accepted node names were the three weather models, the weather seed, and five tests. No compiled SQL, relation name, dbt message, adapter response, environment value, or raw log event was published to the health views.

## Idempotent replay

The complete collector run was invoked again for the same task attempt. Before and after replay:

- normalized digest was unchanged (`e0ed37c5abcbd87c…`);
- `collected_at` stayed `2026-07-16T05:05:42.372Z`;
- `published_at` stayed `2026-07-16T05:06:28.921Z`;
- invocation rows stayed at `1`; and
- node rows stayed at `9`.

This is live proof of the identical-replay no-op path for one complete attempt.

## Final packaged qualification

The release candidates were then rebuilt and redeployed as `dbtobsb-capture`
`0.2.0a3` and `dbtobsb-collector` `0.2.0a14`. The final bootstrap, dbt build,
and collector Jobs all completed with `SUCCESS`. The collector reported:

```json
{
  "capture_state": "COMPLETE",
  "node_count": 9,
  "pair_state": "PAIR_VALID",
  "retrieval_state": "RETRIEVED"
}
```

That final archive was 247,100 bytes and its normalized digest begins
`12edd7543996`. A second collector invocation used the exact stored attempt
metadata for the same dbt task. It completed with `SUCCESS`; the normalized
digest, `collected_at`, and `published_at` remained unchanged, with one
invocation row and nine node rows. This qualifies the identical-replay no-op
against the exact package versions named by the release, rather than only the
earlier development build.

## Native parser decision

The proof used the Databricks Jobs API for archive discovery, a Unity Catalog Volume for exact bytes, strict bounded Python for tar/JSON/dbt acceptance, typed Spark/Delta for publication, and Databricks SQL for analysis. SQL `read_files` was evaluated but not used as the acceptance boundary because it does not supply the required duplicate-key and cross-file proof. See [Decision 0003](../decisions/0003-native-hybrid-collector.md).

## Final running-compute state

After evidence queries completed, the workspace had zero running compute:

```text
active Job runs: 0
SQL warehouses:  0
clusters:        0
App compute:     STOPPED
```

The unscheduled Bundle Jobs and small disposable Unity Catalog evidence remain
for inspection. They do not represent running compute. The retained Delta tables
and managed-Volume archives can continue to incur storage charges until the owner
makes and executes an explicit retain-or-delete decision. The App was never needed
for the SQL-first capture.

## Open qualification gaps

The proof did not establish dedicated run identities, sealed Job parameters, production bootstrap ownership/authority retirement, raw retention/deletion, a native failed-dbt capture, or a vendor-backed internal artifact-transport contract. Those gaps are listed in [Compatibility and limitations](../operators/reference/compatibility-and-limitations.md).
