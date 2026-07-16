# Evidence tables and views

The fixed bootstrap creates or verifies three managed Delta tables, one managed Volume, and two SQL views in the selected Unity Catalog schema.

It is valid to run this bootstrap against production when an authorized administrator intentionally selects the production destination and approves the fixed object manifest. The ordinary collector uses only the existing objects and does not run DDL.

## Read views

Most operators should receive `SELECT` only on these views.

### `dbt_run_health`

One published row per Databricks dbt task run. It joins the attempt registry with the allowlisted invocation summary.

| Field group | Fields | Purpose |
| --- | --- | --- |
| Attempt correlation | `workspace_id`, `dbt_task_run_id`, `observed_job_id`, `observed_job_run_id`, `observed_task_key`, `repair_count`, `execution_count`, `attempt_number` | Correlate the installed Job and exact task attempt. Treat IDs as restricted operational metadata. |
| Native task | `task_start_time`, `task_end_time`, `lakeflow_result_state`, `logs_truncated` | Preserve Databricks task timing and result separately from evidence quality. |
| Evidence quality | `retrieval_state`, `capture_state`, `pair_state`, `issue_code` | Explain whether the native archive was retrieved and accepted. |
| Integrity | archive and primary-artifact hashes and sizes, `expected_node_count`, `normalized_digest`, `collected_at`, `published_at` | Support custody, replay, and completeness checks without exposing raw content. |
| dbt invocation | `invocation_id`, `generated_at`, `elapsed_time`, `dbt_version`, `adapter_type`, `command`, `result_count`, `status_counts_json` | Small allowlisted summary from accepted primary artifacts. |

The view excludes `raw_archive_locator` and the internal `collector_state` sentinel.

### `dbt_node_health`

One published row per accepted dbt result node.

| Field | Meaning |
| --- | --- |
| Attempt fields | Workspace, Job, task-run, task key, and invocation correlation. |
| `capture_state`, `lakeflow_result_state` | Evidence quality and native task result, kept separate. |
| `unique_id`, `resource_type`, `status` | dbt node identity, type, and native dbt status. |
| `execution_time`, `failures` | Allowlisted node timing and failure count. |

The view does not expose compiled SQL, relation names, messages, adapter responses, environment values, raw log events, or archive locators.

## Restricted tables

These are implementation and forensic surfaces. Do not grant ordinary dashboard or App users direct access.

### `dbt_artifact_registry`

The attempt root and publication sentinel. Its key is `(workspace_id, dbt_task_run_id)`.

It contains the full read-view attempt fields plus:

- `raw_archive_locator`, which reveals the restricted Volume location; and
- `collector_state`, which is `COLLECTING` until child readback succeeds and `PUBLISHED` afterward.

An identical replay is a no-op. Different normalized content for the same key is a conflict, never an overwrite.

### `dbt_invocations`

At most one accepted invocation projection per task-run key. It contains the dbt version, adapter type, command name, timing, result count, status-count JSON, and normalized digest.

### `dbt_node_results`

The accepted allowlisted node projection. Its natural publication key extends the task-run key with `unique_id`.

## Restricted managed Volume

`dbtobsb_raw` stores the exact native archive bytes before parsing. The object name is configurable at installation, but each archive path is constructed by fixed code and verified by size and SHA-256 readback.

Raw archives can contain Personal Data, secrets, SQL, messages, paths, relation names, logs, environment-derived values, and workspace topology. Access, retention, export, and deletion are customer policy decisions.

## Example queries

Latest invocation health:

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
FROM `<catalog>`.`<schema>`.`dbt_run_health`
ORDER BY task_start_time DESC;
```

Node outcome summary:

```sql
SELECT
  resource_type,
  status,
  COUNT(*) AS node_count,
  ROUND(SUM(execution_time), 3) AS execution_seconds
FROM `<catalog>`.`<schema>`.`dbt_node_health`
GROUP BY resource_type, status
ORDER BY resource_type, status;
```
