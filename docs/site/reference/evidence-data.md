# Evidence data

The attended installation creates or verifies nine objects in the selected Unity
Catalog schema:

- four managed Delta tables;
- three read-only SQL views; and
- two managed Volumes.

The installer creates these product objects only after the administrator approves
the destination. The steady-state collector uses the existing objects and does not
run installation DDL.

## Health views

Normal operators and the App should read these views.

### `dbt_run_health`

One row for each observed dbt task attempt whose collection reached the attempt
registry.

| Field group | Important fields | Meaning |
| --- | --- | --- |
| Databricks task | `task_start_time`, `task_end_time`, `lakeflow_result_state` | When the task ran and how Databricks classified it. |
| Retrieval | `retrieval_state`, archive sizes and hashes | Whether the fixed staged files were acquired and preserved. |
| Capture | `capture_state`, `pair_state`, `issue_code` | Whether primary artifacts were present, safe, and mutually valid. |
| dbt summary | `dbt_version`, `adapter_type`, `command`, `result_count`, `status_counts_json` | Small allowlisted facts from accepted artifacts. |
| Publication | `collected_at`, `published_at` | When the collector processed and published the row. |

The view hides the raw archive location and the internal publication sentinel.

### `dbt_node_health`

One row for each accepted dbt result node.

| Field | Meaning |
| --- | --- |
| `unique_id` | dbt's stable identifier for the resource. |
| `resource_type` | Such as `model`, `seed`, or `test`. |
| `status` | dbt's native result, such as `success`, `pass`, or `error`. |
| `execution_time` | dbt's recorded duration in seconds. |
| `failures` | dbt's recorded failure count, when present. |
| `capture_state` | The evidence state for the parent attempt. |
| `lakeflow_result_state` | The Databricks task result for the parent attempt. |

The view does not expose compiled SQL, relation names, messages, adapter responses,
environment values, logs, or archive paths.

### `dbt_collection_health`

One row for each discovered or published collection attempt.

| Field | Meaning |
| --- | --- |
| `collector_state` | `DISCOVERED`, `COLLECTING`, `RETRYABLE`, `TERMINAL_FAILURE`, or `PUBLISHED`. |
| `collection_issue_code` | A safe static code, or `NULL` when no issue remains. |
| `collection_attempt_count` | Number of bounded collection claims. |
| `first_discovered_at` | When the reconciler first found the attempt. |
| `last_attempted_at` | When collection last tried the attempt. |
| `published_at` | When normalized evidence became published. |
| `last_reconciliation_run_id` | The last reconciler run associated with the attempt. |

Operational IDs are restricted metadata even when they appear in a health view.

## Restricted tables

| Object | Purpose |
| --- | --- |
| `dbtobsb_object_manifest` | One sealed row describing the installed object and runtime contract. |
| `dbt_artifact_registry` | The root row for each task attempt, archive custody, and publication state. |
| `dbt_invocations` | One allowlisted dbt invocation summary per accepted attempt. |
| `dbt_node_results` | Allowlisted model, seed, test, and other supported node results. |

An identical replay is a no-op. Different normalized content for the same task-run
key is a conflict and never overwrites the first record.

## Restricted Volumes

| Object | Purpose |
| --- | --- |
| `dbtobsb_stage` | Fixed per-attempt files uploaded by the observed Job. |
| `dbtobsb_raw` | Exact deterministic archives preserved by the collector before parsing. |

Raw archives can contain SQL, messages, paths, relation names, secrets, logs,
workspace structure, and Personal Data. Customer policy controls their access,
retention, export, and deletion.
